# Transaction Processing Service

**Production-grade FastAPI template** built as the foundation for my **AI Engineer / ML Engineer portfolio** (Fintech domain).

---

## Overview

A clean architecture transaction processing service with:
- Real-time transaction validation API
- PostgreSQL persistence with SQLAlchemy + Alembic
- Statistical analytics & risk scoring
- Ready for ML models and LLM agents

## Architecture

```mermaid
flowchart TD
    subgraph Client["External Clients"]
        A[Mobile / Web Apps]
        B[Payment Partners]
    end

    subgraph API["FastAPI Service"]
        C[API Layer<br/>/api/v1]
        D[Core Layer<br/>config, logger, database]
        E[Schemas<br/>Pydantic v2]
    end

    subgraph Data["Data Layer"]
        F[(PostgreSQL)]
    end

    subgraph Analytics["Analytics & ML"]
        G[Statistics Endpoint]
        H[Fraud Risk Scoring]
        I[Future ML Models]
    end

    A --> C
    B --> C

    C --> D
    C --> E

    D --> F

    C --> G
    C --> H
```
