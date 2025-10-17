# NEO Chat - WhatsApp AI RAG Engine

A WhatsApp-based AI assistant that provides personalized responses grounded in user-specific knowledge bases.

## 🏗️ Architecture

- **Agent Framework**: CrewAI (multi-agent orchestration)
- **LLM**: Google Gemini Flash 2.5
- **Embeddings**: Google Gemini text-embedding-004 (768 dimensions)
- **Vector DB**: Supabase (self-hosted) with pgvector + HNSW indexing
- **WhatsApp**: Evolution API v2 (webhook-based)
- **Web Crawler**: Crawl4AI (async, JavaScript rendering)
- **Voice**: Google Cloud Speech-to-Text

## 📋 Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git
- Google Cloud API Key (Gemini + Vision + Speech-to-Text)
- Evolution API instance
- Supabase (self-hosted)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd neo-chat
cp .env.example .env
# Edit .env with your API keys
```

### 2. Install Dependencies

```bash
pip install -e ".[dev]"
```

### 3. Setup Supabase

```bash
cd docker/supabase
docker-compose up -d
cd ../..
./scripts/run_migrations.sh
```

### 4. Run Application

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## 📁 Project Structure

```
neo-chat/
├── src/
│   ├── api/              # FastAPI application
│   │   ├── routes/       # API endpoints
│   │   └── middleware/   # Request/response middleware
│   ├── agents/           # CrewAI agents
│   ├── services/         # Business logic & external APIs
│   ├── models/           # Pydantic data models
│   ├── db/               # Database layer
│   │   ├── repositories/ # Data access
│   │   └── migrations/   # SQL migrations
│   └── utils/            # Utilities (logging, retry, config)
├── tests/                # Test suite
├── docker/               # Docker configurations
└── scripts/              # Deployment & setup scripts
```

## 🔧 Implementation Status

### ✅ Completed (Phase 1 - Setup)
- [x] T001: Project structure created
- [x] T002: Python project initialized (pyproject.toml)
- [x] T003: Environment variables template (.env.example)
- [x] T004: .gitignore configured
- [x] T005-T012: **TODO** - Docker, scripts, pytest config

### 🚧 In Progress (Phase 2 - Foundational)
- [ ] T013-T016: Database migrations
- [ ] T017-T020: Core utilities (logger ✅, config ✅, phone_utils, retry)
- [ ] T021-T024: FastAPI app setup

### 📝 Pending (Phase 3 - US1)
- [ ] T025-T046: User Story 1 implementation
- [ ] T039a: Structured outputs (FR-009)

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/integration/test_whatsapp_integration.py
```

## 📚 Implementation Guide

### Next Steps

1. **Complete Phase 1**: Implement T005-T012 (Docker, scripts)
2. **Database Setup**: Run T013-T016 (migrations, Supabase client)
3. **Core Utilities**: Implement T019-T020 (phone_utils, retry)
4. **FastAPI App**: Create T021-T024 (main.py, middleware, health)
5. **Models**: Implement T025-T028 (User, Message, Chunk, WebhookEvents)
6. **Services**: Build T032-T035 (WhatsApp, Gemini, Vector, KnowledgeBase)
7. **Agents**: Create T036-T039a (Retrieval, Response, Tool, CrewManager)
8. **Routes**: Implement T040-T041 (webhook endpoint, FIFO queue)
9. **Testing**: Execute T042-T046 (integration & E2E tests)

### Code Examples from MCP

**FastAPI Async Webhook**:
- See Crawl4AI async patterns for parallel processing
- Use FastAPI's `BackgroundTasks` for FIFO queue

**CrewAI Agent Setup**:
```python
from crewai import Agent, Task, Crew

# Example from MCP query
agent = Agent(
    role="Retrieval Agent",
    goal="Search vector database for relevant context",
    llm="gemini/gemini-2.0-flash-exp",
    tools=[vector_search_tool]
)
```

**Supabase Vector Search**:
- Use pgvector's cosine similarity
- HNSW index for fast approximate search
- Top-5 retrieval with 0.7 threshold

## 🔐 Security

- All API keys in environment variables (never in code)
- HTTPS/TLS for all external communications
- Supabase RLS policies for user data isolation
- Phone number normalization to E.164 format

## 📊 Success Criteria

- Response time: <10s (95th percentile)
- File processing: <30s for 16MB files
- Concurrent users: 100+ supported
- Uptime: 99%

## 🤝 Contributing

1. Follow the task list in `specs/001-whatsapp-ai-rag-engine/tasks.md`
2. Write tests first (TDD approach)
3. Run linters: `black src/ && ruff src/`
4. Ensure all tests pass before committing

## 📄 License

MIT License - See LICENSE file for details

## 🔗 References

- [Specification](../specs/001-whatsapp-ai-rag-engine/spec.md)
- [Implementation Plan](../specs/001-whatsapp-ai-rag-engine/plan.md)
- [Task Breakdown](../specs/001-whatsapp-ai-rag-engine/tasks.md)
- [Research Findings](../specs/001-whatsapp-ai-rag-engine/research.md)
