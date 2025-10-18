# Implementation Plan: NEO Chat WhatsApp AI RAG Engine

**Branch**: `001-whatsapp-ai-rag-engine` | **Date**: 2025-01-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-whatsapp-ai-rag-engine/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

NEO Chat is a WhatsApp-based AI assistant that provides personalized responses grounded in user-specific knowledge bases. The system integrates a personal WhatsApp number via Evolution API, processes messages through a CrewAI multi-agent framework powered by Google Gemini Flash 2.5, and maintains per-user RAG pipelines using Supabase vector database with pgvector. Users can upload files (PDF, DOCX, XLSX, PPTX, images), share website URLs for crawling (via Crawl4AI), and send voice messages (transcribed via Google Cloud Speech-to-Text). All interactions and uploaded content are stored in the user's personal knowledge base, enabling context-aware AI responses. The system supports WhatsApp's native interactive components (List Messages, Reply Buttons) and allows users to reset their knowledge base on demand.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI (async web framework), CrewAI (multi-agent orchestration), Google Gemini API (LLM + embeddings), Supabase (self-hosted vector DB with pgvector), Evolution API (WhatsApp connector), Crawl4AI (web crawler), Google Cloud Speech-to-Text (voice transcription)  
**Storage**: Supabase PostgreSQL with pgvector extension, HNSW indexing for vector similarity search  
**Testing**: pytest (unit tests), pytest-asyncio (async tests), integration tests for external APIs  
**Target Platform**: Linux server (Docker containers), self-hosted deployment
**Project Type**: Single backend service (API server)  
**Performance Goals**: <10s response time (95th percentile), 100+ concurrent users, <30s file processing (16MB), <5min web crawl (100 pages)  
**Constraints**: 16MB file size limit (WhatsApp), 60 req/min rate limit (Gemini API), 32,768 token context window (Gemini), 768-dimension embeddings (text-embedding-004)  
**Scale/Scope**: Multi-user system with per-user knowledge bases, 59 functional requirements across 6 categories (WhatsApp, AI Engine, RAG Pipeline, Web Crawling, Voice Processing, Data Management, Security)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Reference**: `.specify/memory/constitution.md`

### Principle I: Docker Build from Source ✓

- [x] All Docker deployments clone from GitHub and build from source
- [x] No pre-built images from registries
- [x] Build process documented with commit SHA tracking

**Status**: ✓ PASS  
**Evidence**: Dockerfile will use multi-stage builds from source. All services (Supabase, Evolution API if containerized) will be built from cloned repositories with commit SHA tracking in deployment scripts.

### Principle II: MCP Query First ✓

- [x] MCP queries executed before planning phase
- [x] Available sources discovered via `mcp0_get_available_sources`
- [x] Query results documented in `research.md`
- [x] Technical patterns and architecture decisions informed by MCP

**Status**: ✓ PASS  
**Evidence**: Completed 5 MCP queries covering CrewAI, Gemini API, Supabase, Evolution API, and Crawl4AI. All results documented in [research.md](./research.md). Architecture decisions (agent roles, vector indexing, API integration patterns) directly informed by MCP findings.

### Principle III: Test-First Development ✓

- [x] Tests requested in feature specification (User Stories include "Independent Test" sections)
- [x] Test strategy defined before implementation
- [x] Red-Green-Refactor cycle planned

**Status**: ✓ PASS  
**Evidence**: Spec includes 6 user stories with independent test scenarios. Test strategy: unit tests for core functions, integration tests for external APIs (Evolution, Gemini, Supabase), end-to-end tests for user journeys. Will use pytest with async support.

### Principle IV: Integration Testing ✓

- [x] Integration points identified
- [x] Contract tests planned for service boundaries
- [x] External API integration tests defined

**Status**: ✓ PASS  
**Evidence**: 6 external integration points identified: Evolution API (WhatsApp), Gemini API (LLM + embeddings), Google Cloud Speech-to-Text, Google Cloud Vision (OCR), Supabase (database), Crawl4AI (web crawler). Contract tests will validate request/response schemas. Integration tests will use test instances/mock data.

### Principle V: Observability & Logging ✓

- [x] Logging strategy defined
- [x] Error handling approach documented
- [x] Performance metrics identified

**Status**: ✓ PASS  
**Evidence**:  
- **Logging**: Structured JSON logging (FR-030a) with fields: timestamp (ISO 8601), user_id, event_type, message, metadata. Log levels: ERROR, WARN, INFO, DEBUG (FR-030b)  
- **Error Handling**: Exponential backoff retry (FR-031a: 1s, 2s, 4s, 8s, 16s, max 5 attempts). Timeouts defined per API (FR-031b). User notifications on failures (FR-031c)  
- **Metrics**: Response time (SC-001: <10s), file processing time (SC-002: <30s), concurrent users (SC-004: 100+), uptime (SC-008: 99%)

### Principle VI: Simplicity & YAGNI ✓

- [x] Solution starts with simplest approach
- [x] Complexity justified in Complexity Tracking section (if any)
- [x] No premature optimization or abstraction

**Status**: ✓ PASS  
**Evidence**: Architecture uses proven, simple patterns: FastAPI for API server, CrewAI sequential collaboration (not complex hierarchical), standard text extraction libraries (PyPDF2, python-docx), HNSW indexing (industry standard). No custom frameworks or premature abstractions. Complexity tracking section below documents any justified complexity.

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
neo-chat/
├── src/
│   ├── api/                    # FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── routes/           # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── webhook.py     # Evolution API webhook endpoint
│   │   │   └── health.py      # Health check endpoint
│   │   └── middleware/       # Request/response middleware
│   │       ├── __init__.py
│   │       ├── logging.py     # Structured logging middleware
│   │       └── error_handler.py
│   ├── agents/                 # CrewAI agents
│   │   ├── __init__.py
│   │   ├── crew_manager.py   # CrewAI orchestration
│   │   ├── retrieval_agent.py # Vector search agent
│   │   ├── response_agent.py  # LLM response agent
│   │   └── tool_agent.py      # File/crawl processing agent
│   ├── services/               # Business logic services
│   │   ├── __init__.py
│   │   ├── whatsapp_service.py   # Evolution API integration
│   │   ├── gemini_service.py     # Gemini API (LLM + embeddings)
│   │   ├── speech_service.py     # Google Cloud Speech-to-Text
│   │   ├── vision_service.py     # Google Cloud Vision (OCR)
│   │   ├── vector_service.py     # Supabase vector operations
│   │   ├── crawler_service.py    # Crawl4AI integration
│   │   ├── file_processor.py     # File text extraction
│   │   ├── chunking_service.py   # Semantic text chunking
│   │   └── knowledge_base.py     # Knowledge base operations
│   ├── models/                 # Data models (Pydantic)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── message.py
│   │   ├── document.py
│   │   ├── chunk.py
│   │   └── webhook_events.py     # Evolution API webhook schemas
│   ├── db/                     # Database layer
│   │   ├── __init__.py
│   │   ├── supabase_client.py    # Supabase connection
│   │   ├── repositories/         # Data access layer
│   │   │   ├── __init__.py
│   │   │   ├── user_repository.py
│   │   │   ├── document_repository.py
│   │   │   ├── chunk_repository.py
│   │   │   └── embedding_repository.py
│   │   └── migrations/           # SQL migration scripts
│   │       ├── 001_initial_schema.sql
│   │       └── 002_create_indexes.sql
│   ├── utils/                  # Utility functions
│   │   ├── __init__.py
│   │   ├── logger.py          # Structured logging setup
│   │   ├── phone_utils.py     # E.164 normalization
│   │   ├── retry.py           # Exponential backoff retry
│   │   └── config.py          # Configuration management
│   └── __init__.py
├── tests/
│   ├── unit/                   # Unit tests
│   │   ├── test_services/
│   │   ├── test_agents/
│   │   ├── test_utils/
│   │   └── test_models/
│   ├── integration/            # Integration tests
│   │   ├── test_whatsapp_integration.py
│   │   ├── test_gemini_integration.py
│   │   ├── test_supabase_integration.py
│   │   ├── test_crawler_integration.py
│   │   └── test_speech_integration.py
│   ├── e2e/                    # End-to-end tests
│   │   ├── test_text_conversation.py
│   │   ├── test_file_upload.py
│   │   ├── test_web_crawl.py
│   │   ├── test_voice_message.py
│   │   └── test_knowledge_base_reset.py
│   ├── fixtures/               # Test fixtures
│   │   ├── sample_files/
│   │   └── mock_responses/
│   └── conftest.py             # Pytest configuration
├── docker/
│   ├── Dockerfile              # Multi-stage build from source
│   ├── docker-compose.yml      # Local development setup
│   └── supabase/               # Supabase self-hosted config
│       ├── docker-compose.yml
│       └── .env.example
├── scripts/
│   ├── deploy.sh               # Deployment script (git clone + build)
│   ├── setup_supabase.sh       # Supabase initialization
│   └── run_migrations.sh       # Database migration runner
├── .env.example                # Environment variables template
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Development dependencies
├── pyproject.toml              # Project metadata
├── pytest.ini                  # Pytest configuration
├── README.md
└── .gitignore
```

**Structure Decision**: Single backend service architecture selected. This is a Python FastAPI application with clear separation of concerns:

- **api/**: HTTP layer (routes, middleware)
- **agents/**: CrewAI multi-agent orchestration
- **services/**: Business logic and external API integrations
- **models/**: Pydantic data models for type safety
- **db/**: Database layer with repository pattern for data access
- **utils/**: Shared utilities (logging, retry, config)
- **tests/**: Comprehensive test suite (unit, integration, e2e)

This structure supports async operations, clear dependency injection, and testability. All external integrations are isolated in service modules for easy mocking and testing.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

**Status**: No violations - all Constitution principles passed ✓

All architecture decisions follow simplicity principles:
- Standard FastAPI patterns (no custom framework)
- CrewAI sequential collaboration (simplest multi-agent pattern)
- Repository pattern for data access (industry standard, aids testability)
- Standard text extraction libraries (PyPDF2, python-docx, etc.)
- HNSW indexing (proven vector search algorithm)

No unjustified complexity introduced.

