from pathlib import Path

import pymupdf
import chromadb
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
VECTOR_STORE_PATH = PROJECT_ROOT / "data" / "chroma"

pdfs = [
    f"{DATA_DIR}/Criteria_for_Computers_monitors_tablets_and_smartphones.pdf",
    f"{DATA_DIR}/EU_Directive_2014_24_EU.pdf",
    f"{DATA_DIR}/making_socially_responsible_public_procurement_work.pdf",
    f"{DATA_DIR}/value_for_money.pdf",
    f"{DATA_DIR}/World_Bank_Evaluating_Bids_and_Proposals.pdf",
    f"{DATA_DIR}/World_Bank_Procurement_Regulations.pdf"
]

def get_section_from_toc(toc, page_number):
    """Get the section title for a given page number based on the table of contents."""
    current_section = None
    for entry in toc:
        _, entry_title, entry_page = entry
        if entry_page <= page_number:
            current_section = entry_title
        else:
            break
    return current_section


def create_chroma_collection_from_pdfs(pdf_paths: list[Path], collection_name: str) -> chromadb.api.models.Collection:
    """Create a Chroma collection from a list of PDF paths."""
    # 1. PDF ingestion, text extraction and metadata engineering 
    docs = []
    for pdf_path in pdf_paths:
        pdf = pymupdf.open(pdf_path)
        # Used to get the section (Based on the index "Table Of Contents")
        toc = pdf.get_toc() # Looks like: [1, 'Introduction', 1], [1, 'Scope', 2], [1, 'Definitions', 3], ...
        
        for page_number, page in enumerate(pdf, start=1):
            text=page.get_text("text")
            docs.append(Document(
                page_content=text,
                metadata={
                    "source": Path(pdf_path).name,
                    "page_number": page_number,
                    "section": get_section_from_toc(toc, page_number)
                }
            ))
    # 2. Chunking with source/page metadata
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=300,
    )

    # We use .split_documents() instead of .split_text() because we want to preserve the metadata (source, page_number, section) for each chunk autmatically (it just creates more smaller documents)
    chunks = text_splitter.split_documents(docs)

    # Let's add a chunk_id as metadata as well
    for chunk_id, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = f"chunk-{chunk_id}"
    
    # 3. Embedding generation
    # Load a pretrained Sentence Transformer model
    embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    # Transform into embeddings
    texts = [chunk.page_content for chunk in chunks]
    embeddings = embedding_model.encode(texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    # 4. Local vector store
    # Create the client and store it under data/chroma (this is where the embeddings will be stored)
    chroma_client = chromadb.PersistentClient(path=VECTOR_STORE_PATH)

    # Create the collection (store the documents + embeddings)
    collection = chroma_client.get_or_create_collection(name=collection_name)

    # Add each document's text, embeddings and metadata
    collection.upsert(
        ids=[chunk.metadata["chunk_id"] for chunk in chunks],
        documents=[chunk.page_content for chunk in chunks],
        embeddings=embeddings.tolist(),
        metadatas=[chunk.metadata for chunk in chunks],
    )
    
    return collection

def load_collection(collection_name: str) -> chromadb.api.models.Collection:
    """Load an existing Chroma collection."""
    chroma_client = chromadb.PersistentClient(path=VECTOR_STORE_PATH)
    return chroma_client.get_collection(name=collection_name)

def search_collection(collection_name: str, query: str, top_k: int = 5) -> list[dict]:
    embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    query_embedding = embedding_model.encode(
        query=query,
        normalize_embeddings=True,
    ).tolist()
    
    collection = load_collection(collection_name)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    return results

def main():
    # 5. Similarity search
    queries = [
        "What are the award criteria?",
        "What sustainability requirements apply to computers?",
        "What does value for money mean in procurement?",
    ]

    for query in queries:
        results = search_collection("my_collection", query)

        print(f"\nQUERY: {query}")
        for document, metadata, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            print(metadata)
            print(document[:300])
            print("Distance:", distance)
        
if __name__ == "__main__":
    main()