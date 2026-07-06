# OpenS2P Architecture

## Overview

OpenS2P is an AI-powered, open-source Source-to-Pay (S2P) platform designed for organizations of all sizes. The platform follows a modular architecture to ensure scalability, maintainability, and extensibility.

## Architecture

```
                        Web Browser
                              │
                    NiceGUI / Web UI
                              │
                        REST API (FastAPI)
                              │
        ┌───────────────┬───────────────┬───────────────┐
        │               │               │               │
 Authentication    Business Logic    AI Services   Integrations
        │               │               │               │
        └───────────────┴───────────────┴───────────────┘
                              │
                     SQLAlchemy ORM
                              │
                          MariaDB
```

## Technology Stack

| Layer | Technology |
|--------|------------|
| Frontend | NiceGUI |
| Backend | FastAPI |
| ORM | SQLAlchemy |
| Database | MariaDB |
| Authentication | JWT |
| AI | OpenAI / Local LLM |
| Deployment | Docker |
| API | REST |

## Design Principles

- Modular architecture
- API-first
- Multi-company support
- Multi-language
- Secure by default
- Cloud and on-premise deployment
- AI-ready
