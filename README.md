# Transaction Processing Service

**Production-grade FastAPI template** built as the foundation for my **AI Engineer / ML Engineer portfolio** (Fintech domain).

---

## Overview

Clean Architecture (`src/` layout) backend service designed with real production standards in mind.
This skeleton will be extended with:
- Real-time transaction processing (Kafka)
- Fraud detection (Classical ML + LLM)
- RAG/Agent capabilities
- Full MLOps pipeline

## Architecture

```mermaid
flowchart TD
    subgraph Client["External Clients"]
        A[Mobile / Web Apps]
        B[Payment Partners & Banks]
    end

    subgraph API["FastAPI Service"]
        C[API Layer<br/>/api/v1]
        D[Core Layer<br/>config, logger, security]
        E[Schemas<br/>Pydantic v2]
    end

    subgraph Data["Data & Future Components"]
        F[(PostgreSQL)]
        G[Kafka Streams]
        H[ML Models & Feature Store]
        I[LLM Agents]
    end

    A --> C
    B --> C

    C --> D
    C --> E

    D --> F
    D --> G
    D --> H
    D --> I
```
