# Architecture

## 1. Business Architecture

The Procurement Operations Agent supports internal procurement teams throughout the early stages of a purchase request.

An employee or business unit submits a procurement need. The platform investigates the request, checks applicable procurement guidance, searches the supplier market and historical tenders, evaluates available options, and determines whether the request can proceed or requires human review.

```mermaid
flowchart LR

    A[Business Unit / Employee] --> B[Purchase Request]

    B --> C[Procurement AI Platform]

    C --> D[Understand Requirements]
    C --> E[Check Procurement Rules]
    C --> F[Research Suppliers & Market]
    C --> G[Evaluate Options]
    C --> H[Assess Risk & Approval]

    D --> I[Procurement Recommendation]
    E --> I
    F --> I
    G --> I
    H --> I

    I --> J{Human Approval Required?}

    J -->|Yes| K[Procurement / Manager Review]
    J -->|No| L[Request Ready to Proceed]

    K --> M[Approved / Rejected / Revised]
```

### Example

A department submits:

> We need 40 laptops for our Barcelona office with a maximum budget of €45,000 and delivery within three weeks.

The platform may:

1. Extract the requirements.
2. Determine which procurement rules and evaluation criteria apply.
3. Investigate previous comparable procurements.
4. Search for relevant suppliers.
5. Compare supplier options.
6. Identify risks or missing information.
7. Produce an evidence-backed recommendation.
8. Escalate the request when human approval is required.

The platform acts as an **AI procurement analyst**, not an autonomous purchasing system.

---

# 2. Multi-Agent Architecture

The platform uses specialized agents coordinated by a central orchestration layer.

```mermaid
flowchart TD

    U[Purchase Request] --> O[Procurement Orchestrator]

    O --> RA[Requirements Agent]
    O --> PA[Policy Agent]
    O --> SA[Supplier Research Agent]
    O --> EA[Evaluation Agent]
    O --> RAA[Risk & Approval Agent]

    RA --> O
    PA --> O
    SA --> O
    EA --> O
    RAA --> O

    O --> F[Final Recommendation]

    F --> H{Human Review Required?}

    H -->|Yes| HR[Human Approval]
    H -->|No| C[Complete Analysis]
```

### Agent Responsibilities

**Procurement Orchestrator**

Coordinates the workflow, maintains state and decides which specialist agent should execute next.

**Requirements Agent**

Extracts and structures information such as:

* product or service required
* quantity
* budget
* delivery constraints
* technical requirements
* missing information

**Policy Agent**

Uses RAG to retrieve relevant procurement rules, evaluation guidance and sustainability criteria.

**Supplier Research Agent**

Searches external procurement and supplier sources, including historical tenders from TED.

**Evaluation Agent**

Compares candidate suppliers and procurement options using price and non-price criteria.

**Risk & Approval Agent**

Evaluates risk, uncertainty and approval requirements using deterministic rules and Jev-based structured decisions.

---

# 3. Technical Architecture

```mermaid
flowchart TD

    USER[Internal User] --> API[API Gateway]
    API --> APP[Lambda / FastAPI]

    APP --> ORCH[LangGraph Supervisor / Orchestrator]

    ORCH --> REQ[Requirements Agent]
    ORCH --> POL[Policy Agent]
    ORCH --> SUP[Supplier Research Agent]
    ORCH --> EVA[Evaluation Agent]
    ORCH --> RISK[Risk & Approval Agent]

    REQ --> STATE[Shared Procurement State]
    POL --> STATE
    SUP --> STATE
    EVA --> STATE
    RISK --> STATE

    STATE --> ORCH

    POL --> RAG[RAG Knowledge Base]
    RAG --> S3[S3 Documents]
    RAG --> VEC[S3 Vectors]

    SUP --> TED[TED API]
    SUP --> EXT[Supplier / Company APIs]

    REQ --> BEDROCK[Amazon Bedrock]
    POL --> BEDROCK
    SUP --> BEDROCK
    EVA --> BEDROCK
    RISK --> BEDROCK

    RISK --> JEV[Jev API]
    RISK --> RULES[Python Business Rules]

    ORCH --> DECISION{Enough evidence?}

    DECISION -->|No| ORCH
    DECISION -->|Yes| FINAL[Final Procurement Recommendation]

    FINAL --> APPROVAL{Human approval required?}

    APPROVAL -->|Yes| HUMAN[Procurement / Manager Review]
    APPROVAL -->|No| DONE[Analysis Complete]

    HUMAN --> DONE

    STATE --> DB[DynamoDB]
    APP --> LOGS[CloudWatch]
```

---

# 4. Technology Responsibilities

| Component               | Responsibility                                    |
| ----------------------- | ------------------------------------------------- |
| Python                  | Core application and deterministic business logic |
| FastAPI                 | Application API                                   |
| LangGraph               | Multi-agent orchestration and state transitions   |
| LangChain               | LLM, retrieval and tool integrations              |
| Amazon Bedrock          | LLM reasoning and embeddings                      |
| Bedrock Knowledge Bases | RAG retrieval                                     |
| S3                      | Procurement source documents                      |
| S3 Vectors              | Vector storage                                    |
| TED API                 | Historical and current public procurement data    |
| Jev                     | Structured AI decisions                           |
| DynamoDB                | Procurement requests, workflow state and results  |
| Lambda                  | Serverless application execution                  |
| API Gateway             | Public API endpoint                               |
| CloudWatch              | Logging and monitoring                            |
| Docker                  | Local development and reproducible environments   |
| GitHub Actions          | Testing and CI/CD                                 |
| Terraform               | Infrastructure as Code in a later phase           |

---

# 5. Data Separation

The platform distinguishes between knowledge that should be indexed and information that should be retrieved dynamically.

```mermaid
flowchart LR

    A[Procurement Agent]

    A --> B[RAG Knowledge]
    A --> C[Live / External Data]

    B --> B1[Procurement Regulations]
    B --> B2[Evaluation Guidance]
    B --> B3[Value for Money Guidance]
    B --> B4[Green Procurement Criteria]
    B --> B5[Procurement Case Studies]

    C --> C1[TED API]
    C --> C2[Supplier Information]
    C --> C3[Company Information]
```

RAG answers questions such as:

> What rules or evaluation criteria apply?

External tools answer questions such as:

> Which suppliers or comparable procurements currently exist?

---

# 6. Design Principles

The initial architecture follows several constraints:

* Serverless-first AWS architecture to minimize idle cost.
* Multiple specialized agents rather than one unrestricted agent.
* Human approval for consequential procurement decisions.
* Public, real-world procurement data wherever possible.
* Clear separation between LLM reasoning and deterministic business rules.
* Evidence-backed recommendations with traceable sources.
* Agents may investigate and recommend, but V1 will not autonomously place purchase orders.
