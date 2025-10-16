# Implementation Tasks: NEO Chat WhatsApp AI RAG Engine

**Branch**: `001-whatsapp-ai-rag-engine`  
**Date**: 2025-01-16  
**Plan**: [plan.md](./plan.md) | **Spec**: [spec.md](./spec.md)

---

## Task Summary

**Total Tasks**: 116  
**User Stories**: 6 (P1-P6)  
**Parallel Opportunities**: 42 tasks marked [P]  
**MVP Scope**: User Story 1 only (23 tasks including T039a)

---

## Implementation Strategy

### Incremental Delivery Approach

1. **MVP First** (User Story 1 - P1): Basic WhatsApp text conversation with knowledge base
   - Validates entire architecture end-to-end
   - Delivers immediate value
   - ~18 tasks

2. **Incremental Features** (User Stories 2-6): Add capabilities one at a time
   - Each story is independently testable
   - Can be deployed separately
   - User Story 2 (File Upload) is next priority

3. **Parallel Execution**: Tasks marked [P] can be implemented simultaneously
   - Different files, no dependencies
   - Speeds up development significantly

### Testing Strategy

Tests are included per spec requirements. Each user story has:
- Unit tests for services and agents
- Integration tests for external APIs
- End-to-end tests for complete user journeys

---

## Dependencies

### Story Completion Order

```
Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1) → Phase 4 (US2) → Phase 5 (US3) → Phase 6 (US4) → Phase 7 (US5) → Phase 8 (US6) → Phase 9 (Polish)
```

### Story Dependencies

- **US1** (P1): No dependencies - can start after foundational phase
- **US2** (P2): Depends on US1 (needs conversation flow)
- **US3** (P3): Depends on US1 (needs conversation flow)
- **US4** (P4): Depends on US1 (needs conversation flow)
- **US5** (P5): Depends on US1 (needs conversation flow)
- **US6** (P6): Depends on US1 (needs knowledge base operations)

### Parallel Execution Examples

**Within US1 (after foundational tasks)**:
- T019 [P] [US1] + T020 [P] [US1] + T021 [P] [US1] (Models)
- T022 [P] [US1] + T023 [P] [US1] + T024 [P] [US1] (Services)
- T025 [P] [US1] + T026 [P] [US1] + T027 [P] [US1] (Agents)

**Within US2 (after US1 complete)**:
- T040 [P] [US2] + T041 [P] [US2] + T042 [P] [US2] (File processors)

---

## Phase 1: Setup & Project Initialization

**Goal**: Create project structure, configure environment, set up development tools

- [ ] T001 Create project directory structure per plan.md (src/, tests/, docker/, scripts/)
- [ ] T002 Initialize Python project with pyproject.toml and requirements.txt
- [ ] T003 Create .env.example with all required environment variables (API keys, database config)
- [ ] T004 Set up .gitignore for Python project (venv/, .env, __pycache__/, etc.)
- [ ] T005 Create docker/Dockerfile with multi-stage build from source
- [ ] T006 Create docker/docker-compose.yml for local development
- [ ] T007 Create docker/supabase/docker-compose.yml for self-hosted Supabase
- [ ] T008 Create scripts/deploy.sh for Docker build from source with commit SHA tracking
- [ ] T009 Create scripts/setup_supabase.sh for Supabase initialization
- [ ] T010 Create README.md with project overview and setup instructions
- [ ] T011 Configure pytest in pytest.ini with async support
- [ ] T012 Create tests/conftest.py with shared test fixtures

---

## Phase 2: Foundational Infrastructure

**Goal**: Set up core infrastructure that all user stories depend on

### Database & Migrations

- [ ] T013 Create src/db/migrations/001_initial_schema.sql with users, documents, chunks, embeddings tables
- [ ] T014 Create src/db/migrations/002_create_indexes.sql with HNSW index on embeddings
- [ ] T015 Create src/db/supabase_client.py with connection pooling via Supavisor
- [ ] T016 Create scripts/run_migrations.sh to execute SQL migrations

### Core Utilities

- [ ] T017 [P] Create src/utils/logger.py with structured JSON logging (ISO 8601 timestamps)
- [ ] T018 [P] Create src/utils/config.py for environment variable management
- [ ] T019 [P] Create src/utils/phone_utils.py for E.164 phone number normalization
- [ ] T020 [P] Create src/utils/retry.py with exponential backoff (1s, 2s, 4s, 8s, 16s)

### FastAPI Application Setup

- [ ] T021 Create src/api/main.py with FastAPI app initialization
- [ ] T022 Create src/api/middleware/logging.py for request/response logging
- [ ] T023 Create src/api/middleware/error_handler.py for global error handling
- [ ] T024 Create src/api/routes/health.py for health check endpoint

---

## Phase 3: User Story 1 - Basic WhatsApp Text Conversation (P1)

**Goal**: Enable users to send text messages and receive AI responses based on their knowledge base

**Independent Test**: Send "Hello, what can you help me with?" via WhatsApp → Receive AI response within 10s → Verify conversation stored in knowledge base

### Models

- [ ] T025 [P] [US1] Create src/models/user.py with User Pydantic model
- [ ] T026 [P] [US1] Create src/models/message.py with Message Pydantic model
- [ ] T027 [P] [US1] Create src/models/chunk.py with Chunk Pydantic model
- [ ] T028 [P] [US1] Create src/models/webhook_events.py with Evolution API webhook schemas

### Database Repositories

- [ ] T029 [P] [US1] Create src/db/repositories/user_repository.py with CRUD operations
- [ ] T030 [P] [US1] Create src/db/repositories/chunk_repository.py with vector search
- [ ] T031 [P] [US1] Create src/db/repositories/embedding_repository.py with HNSW queries

### External Service Integrations

- [ ] T032 [P] [US1] Create src/services/whatsapp_service.py for Evolution API (send/receive messages)
- [ ] T033 [P] [US1] Create src/services/gemini_service.py for Gemini Flash 2.5 LLM inference
- [ ] T034 [P] [US1] Create src/services/vector_service.py for Supabase vector operations
- [ ] T035 [US1] Create src/services/knowledge_base.py for conversation storage and retrieval

### CrewAI Agents

- [ ] T036 [P] [US1] Create src/agents/retrieval_agent.py for vector search (top-5, threshold 0.7)
- [ ] T037 [P] [US1] Create src/agents/response_agent.py for LLM response generation
- [ ] T038 [P] [US1] Create src/agents/tool_agent.py for knowledge base operations
- [ ] T039 [US1] Create src/agents/crew_manager.py for sequential agent orchestration
- [ ] T039a [US1] Implement structured output schemas in response_agent.py for custom functions (FR-009)

### API Routes

- [ ] T040 [US1] Create src/api/routes/webhook.py for Evolution API webhook endpoint
- [ ] T041 [US1] Implement webhook message processing with FIFO queue per user

### Integration & Testing

- [ ] T042 [US1] Create tests/integration/test_whatsapp_integration.py for Evolution API
- [ ] T043 [US1] Create tests/integration/test_gemini_integration.py for Gemini API
- [ ] T044 [US1] Create tests/integration/test_supabase_integration.py for vector search
- [ ] T045 [US1] Create tests/e2e/test_text_conversation.py for complete user journey
- [ ] T046 [US1] Test: Send text message → Verify AI response within 10s → Verify storage

---

## Phase 4: User Story 2 - File Upload & Knowledge Base Enrichment (P2)

**Goal**: Enable users to upload documents and images, extract text, and store in knowledge base

**Independent Test**: Upload PDF via WhatsApp → Ask question about content → Verify AI responds with extracted information

**Note**: Tasks in this phase extend components created in US1 (whatsapp_service.py, webhook.py, tool_agent.py)

### Models & Services

- [ ] T047 [P] [US2] Create src/models/document.py with Document Pydantic model
- [ ] T048 [P] [US2] Create src/db/repositories/document_repository.py with CRUD operations
- [ ] T049 [P] [US2] Create src/services/file_processor.py for text extraction (PyPDF2, python-docx, openpyxl, python-pptx)
- [ ] T050 [P] [US2] Create src/services/vision_service.py for Google Cloud Vision OCR
- [ ] T051 [P] [US2] Create src/services/chunking_service.py for semantic chunking (100-2000 tokens)
- [ ] T052 [US2] Extend src/services/gemini_service.py to add embedding generation (text-embedding-004, 768 dims)

### File Processing Pipeline

- [ ] T053 [US2] Implement file download from WhatsApp media servers in whatsapp_service.py
- [ ] T054 [US2] Implement file size validation (16MB limit) with user notification
- [ ] T055 [US2] Implement file type detection and routing to appropriate processor
- [ ] T056 [US2] Implement RAG ingestion pipeline: extract → chunk → embed → store
- [ ] T057 [US2] Extend tool_agent.py to handle file processing tasks
- [ ] T058 [US2] Add file upload handling to webhook.py route

### Integration & Testing

- [ ] T059 [US2] Create tests/unit/test_file_processor.py for text extraction
- [ ] T060 [US2] Create tests/unit/test_chunking_service.py for semantic chunking
- [ ] T061 [US2] Create tests/integration/test_vision_integration.py for OCR
- [ ] T062 [US2] Create tests/e2e/test_file_upload.py for complete file upload journey
- [ ] T063 [US2] Test: Upload PDF → Ask question → Verify AI uses file content in response

---

## Phase 5: User Story 3 - Web Content Crawling (P3)

**Goal**: Enable users to share URLs for web crawling and knowledge base enrichment

**Independent Test**: Send URL via WhatsApp → Wait for crawl completion → Ask question → Verify AI responds with crawled content

**Note**: Tasks in this phase extend components created in US1 (webhook.py, tool_agent.py)

### Models & Services

- [ ] T064 [P] [US3] Create src/models/crawl_job.py with CrawlJob model (status, page count)
- [ ] T065 [P] [US3] Create src/db/repositories/crawl_job_repository.py with status tracking
- [ ] T066 [US3] Create src/services/crawler_service.py for Crawl4AI integration (async, JS rendering)

### Crawling Pipeline

- [ ] T067 [US3] Implement URL validation and domain boundary detection
- [ ] T068 [US3] Implement crawl configuration (unlimited depth, 100 page limit, robots.txt)
- [ ] T069 [US3] Implement Markdown extraction and RAG pipeline integration
- [ ] T070 [US3] Implement crawl job status tracking and user notifications
- [ ] T071 [US3] Extend tool_agent.py to handle web crawling tasks
- [ ] T072 [US3] Add URL handling to webhook.py route

### Integration & Testing

- [ ] T073 [US3] Create tests/integration/test_crawler_integration.py for Crawl4AI
- [ ] T074 [US3] Create tests/e2e/test_web_crawl.py for complete crawl journey
- [ ] T075 [US3] Test: Send URL → Verify crawl completion notification → Ask question → Verify response

---

## Phase 6: User Story 4 - Voice Message Processing (P4)

**Goal**: Enable users to send voice messages with transcription and AI processing

**Independent Test**: Send voice message → Receive text response → Verify transcription accuracy

**Note**: Tasks in this phase extend webhook.py created in US1

### Services

- [ ] T076 [US4] Create src/services/speech_service.py for Google Cloud Speech-to-Text (OGG, MP3, WAV)
- [ ] T077 [US4] Implement audio format detection and validation (60s duration limit)
- [ ] T078 [US4] Implement language support (en-US, es-ES, fr-FR, de-DE)
- [ ] T079 [US4] Implement transcription confidence handling (85% threshold)
- [ ] T080 [US4] Add voice message handling to webhook.py route
- [ ] T081 [US4] Store transcribed text in conversation history

### Integration & Testing

- [ ] T082 [US4] Create tests/integration/test_speech_integration.py for Speech-to-Text
- [ ] T083 [US4] Create tests/e2e/test_voice_message.py for complete voice journey
- [ ] T084 [US4] Test: Send voice message → Verify transcription → Verify AI response

---

## Phase 7: User Story 5 - Interactive Menu Navigation (P5)

**Goal**: Enable users to interact with List Messages and Reply Buttons for structured navigation

**Independent Test**: Send "/menu" → Receive List Message → Select option → Verify action executed

### Menu System

- [ ] T085 [US5] Extend whatsapp_service.py to support List Messages (up to 10 options)
- [ ] T086 [US5] Extend whatsapp_service.py to support Reply Buttons (up to 3 buttons)
- [ ] T087 [US5] Create menu configuration with options (Upload File, Crawl Website, Reset KB, Help)
- [ ] T088 [US5] Implement menu command detection ("/menu" or "menu")
- [ ] T089 [US5] Implement button callback handling in webhook.py
- [ ] T090 [US5] Implement multi-step workflow context management

### Integration & Testing

- [ ] T091 [US5] Create tests/e2e/test_menu_navigation.py for menu interactions
- [ ] T092 [US5] Test: Send "/menu" → Select option → Verify appropriate action

---

## Phase 8: User Story 6 - Knowledge Base Reset (P6)

**Goal**: Enable users to reset their entire knowledge base

**Independent Test**: Request reset → Confirm → Ask previously answered question → Verify no prior context

### Reset Functionality

- [ ] T093 [US6] Implement knowledge base reset in knowledge_base.py (delete all user data)
- [ ] T094 [US6] Implement reset confirmation flow with Reply Buttons
- [ ] T095 [US6] Implement reset command detection ("reset my knowledge base")
- [ ] T096 [US6] Add reset operation to tool_agent.py
- [ ] T097 [US6] Implement reset success notification

### Integration & Testing

- [ ] T098 [US6] Create tests/e2e/test_knowledge_base_reset.py for reset journey
- [ ] T099 [US6] Test: Request reset → Confirm → Verify all data deleted → Verify fresh start

---

## Phase 9: Polish & Cross-Cutting Concerns

**Goal**: Production readiness, monitoring, documentation

### Error Handling & Resilience

- [ ] T100 [P] Implement rate limiting for Gemini API (60 req/min)
- [ ] T101 [P] Implement rate limiting for WhatsApp (60 msg/min per user)
- [ ] T102 [P] Implement timeout configuration (30s Gemini, 10s Evolution, 5s Supabase)
- [ ] T103 [P] Add retry logic to all external API calls (exponential backoff)
- [ ] T104 [P] Implement user-facing error messages for all failure types

### Monitoring & Observability

- [ ] T105 [P] Add structured logging to all services (user_id, event_type, metadata)
- [ ] T106 [P] Implement performance metrics collection (response time, file processing time)
- [ ] T107 [P] Add health check endpoints for all external dependencies

### Documentation & Deployment

- [ ] T108 [P] Create deployment documentation with commit SHA tracking
- [ ] T109 [P] Create quickstart guide for local development
- [ ] T110 [P] Document environment variables and configuration
- [ ] T111 [P] Create API documentation (OpenAPI/Swagger)

### Final Integration Testing

- [ ] T112 Load testing: Verify 100+ concurrent users without degradation
- [ ] T113 End-to-end testing: Run all user story tests in sequence
- [ ] T114 Security audit: Verify RLS policies, API key storage, HTTPS/TLS
- [ ] T115 Performance validation: Verify all success criteria (SC-001 through SC-010)

---

## Task Execution Guide

### For MVP (User Story 1 Only)

Execute in order:
1. Phase 1: Setup (T001-T012)
2. Phase 2: Foundational (T013-T024)
3. Phase 3: US1 (T025-T046, including T039a)
4. Phase 9: Essential polish (T100-T104, T107)

**Estimated**: 23 core tasks + 8 polish tasks = 31 tasks for MVP

### For Full Feature Set

Execute phases in order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9

**Parallel opportunities**: 42 tasks marked [P] can run simultaneously

### Testing Approach

- Unit tests: Run after each service/agent implementation
- Integration tests: Run after external service integration
- E2E tests: Run after complete user story implementation
- Final validation: Run all tests before deployment

---

## Success Criteria Validation

After implementation, verify:

- ✅ **SC-001**: Response time <10s (95th percentile)
- ✅ **SC-002**: File processing <30s for 16MB files
- ✅ **SC-003**: 90% relevance score on test queries
- ✅ **SC-004**: 100+ concurrent users supported
- ✅ **SC-005**: 85% transcription accuracy
- ✅ **SC-006**: Web crawl <5min for 100 pages
- ✅ **SC-007**: Reset operation <10s
- ✅ **SC-008**: 99% uptime
- ✅ **SC-009**: 90% first interaction success rate
- ✅ **SC-010**: Recovery from Evolution API disconnection <5min

---

## Notes

- All file paths are relative to repository root
- [P] marker indicates parallelizable tasks (different files, no dependencies)
- [US#] marker indicates which user story the task belongs to
- Tests are included per spec requirements (independent test criteria for each story)
- MVP scope is User Story 1 only - delivers immediate value and validates architecture
- Each user story is independently testable and deployable
- Constitution principles validated: Docker build from source, MCP research complete, test-first approach, integration testing, observability, simplicity
