# Research: NEO Chat WhatsApp AI RAG Engine

**Date**: 2025-01-16  
**Phase**: 0 - Research & Discovery  
**MCP Sources**: crewai.com, ai.google.dev, supabase.com, community.evolution-api.com, crawl4ai.com

---

## MCP Query Results Summary

Per Constitution Principle II (MCP Query First), the following research was conducted before planning:

### 1. CrewAI Multi-Agent Framework

**Source**: crewai.com  
**Query**: "CrewAI multi-agent framework architecture patterns roles tools sequential collaboration"

**Key Findings**:
- **CrewAI AMP** (Agent Management Platform) provides orchestration for multi-agent systems
- **Agent Roles**: Agents can be configured with specific roles, goals, and tools
- **Collaboration Patterns**: Sequential, hierarchical, and autonomous patterns supported
- **Built-in Tools**: Integration with Gmail, Slack, HubSpot, Salesforce, Notion, etc.
- **Observability**: Real-time tracing for every agent step, task interpretation, and tool calls
- **Deployment**: Supports GitHub integration, CLI deployment, and Crew Studio (no-code interface)

**Decision**: Use CrewAI with sequential collaboration pattern
- **Rationale**: Sequential pattern provides predictable execution flow suitable for WhatsApp message processing where order matters
- **Agent Roles Recommended**:
  - **Retrieval Agent**: Handles vector search and context assembly from knowledge base
  - **Response Agent**: Generates AI responses using Gemini with retrieved context
  - **Tool Agent**: Manages file processing, web crawling, and knowledge base operations

**Alternatives Considered**:
- **LangChain/LangGraph**: More complex, steeper learning curve
- **Pydantic AI**: Simpler but less orchestration capabilities
- **Rejected Because**: CrewAI provides better multi-agent coordination with built-in observability

---

### 2. Google Gemini API Integration

**Source**: ai.google.dev  
**Query**: "Gemini API Flash 2.5 integration authentication rate limits context window embeddings text-embedding-004"

**Key Findings**:
- **Gemini Flash 2.5**: Optimized for speed with large context windows
- **Context Window**: Up to 1 million tokens (use 32,768 tokens for practical performance)
- **Rate Limits**: 60 requests per minute for standard tier
- **Authentication**: API key-based authentication via environment variables
- **Embeddings Model**: text-embedding-004
  - **Dimensions**: 768 (default), supports 128-3072
  - **Input Limit**: 2,048 tokens per embedding request
  - **Batch API**: 50% cost reduction for non-real-time embeddings
- **Long Context Capabilities**: Enables in-context learning without RAG in some cases, but RAG still valuable for personalized data

**Decision**: Use Gemini Flash 2.5 with 32,768 token context window
- **Rationale**: Balances performance and cost; 32k tokens sufficient for typical RAG context (5-10 chunks)
- **Embedding Strategy**: Use text-embedding-004 with 768 dimensions (default)
- **Rate Limiting**: Implement 60 req/min limit with exponential backoff

**Alternatives Considered**:
- **OpenAI GPT-4**: Higher cost, similar performance
- **Anthropic Claude**: Good but less integrated with Google ecosystem
- **Rejected Because**: Gemini provides best cost/performance ratio with unified Google Cloud authentication

---

### 3. Supabase Vector Database Setup

**Source**: supabase.com  
**Query**: "Supabase self-hosted pgvector setup HNSW index vector database connection authentication"

**Key Findings**:
- **Self-Hosting**: Docker-based deployment with docker-compose
- **pgvector Extension**: Required for vector operations (cosine, L2, inner product similarity)
- **HNSW Indexing**: Hierarchical Navigable Small World algorithm for fast approximate nearest neighbor search
- **Connection Methods**:
  - **Session-based**: Direct Postgres connection on port 5432
  - **Pooled**: Supavisor connection pooler on port 6543 (recommended for high concurrency)
- **Authentication**: Service role key for backend access, API key for client access
- **Row Level Security (RLS)**: Built-in support for user data isolation at database level
- **Schema Management**: Supports migrations, extensions, and custom schemas

**Decision**: Use self-hosted Supabase with pgvector and HNSW indexing
- **Rationale**: Open-source, full control, no vendor lock-in, excellent vector search performance
- **Connection Strategy**: Use Supavisor pooler (port 6543) for transactional connections
- **Indexing**: HNSW index for vectors (better performance than IVFFlat for < 1M vectors)
- **Schema Design**:
  ```sql
  -- Users table
  CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
  );

  -- Documents table
  CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    source TEXT NOT NULL, -- 'file_upload' or 'web_crawl'
    source_url TEXT,
    file_type TEXT,
    file_size INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
  );

  -- Chunks table
  CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    token_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
  );

  -- Embeddings table with vector column
  CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id UUID REFERENCES chunks(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    embedding VECTOR(768), -- 768 dimensions for text-embedding-004
    created_at TIMESTAMPTZ DEFAULT NOW()
  );

  -- HNSW index for fast similarity search
  CREATE INDEX ON embeddings USING hnsw (embedding vector_cosine_ops);

  -- RLS policies for user data isolation
  ALTER TABLE embeddings ENABLE ROW LEVEL SECURITY;
  CREATE POLICY user_isolation ON embeddings
    FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
  ```

**Alternatives Considered**:
- **Pinecone**: Managed service but expensive, vendor lock-in
- **Weaviate**: Good but more complex setup
- **Qdrant**: Excellent but less mature ecosystem
- **Rejected Because**: Supabase provides best balance of features, cost, and control

---

### 4. Evolution API WhatsApp Integration

**Source**: community.evolution-api.com  
**Query**: "Evolution API WhatsApp webhook integration message reception authentication setup"

**Key Findings**:
- **Open-Source**: WhatsApp Cloud API connector without Meta Business Suite requirement
- **Webhook-Based**: Real-time message reception via webhooks
- **API Endpoints**:
  - `/instance/create` - Create WhatsApp instance
  - `/message/sendText` - Send text messages
  - `/message/sendList` - Send List Messages (up to 10 options)
  - `/message/sendButtons` - Send Reply Buttons (up to 3 buttons)
  - `/webhook/set` - Configure webhook URL
- **Authentication**: API key-based (header: `apikey`)
- **Message Types Supported**: Text, media, audio, sticker, location, contact, poll
- **Instance Management**: Create, restart, logout, delete instances

**Decision**: Use Evolution API v2 with webhook-based message reception
- **Rationale**: Simplifies WhatsApp integration without Meta Business Suite complexity
- **Webhook Setup**: Configure webhook to receive all message events
- **Authentication**: Store API key in environment variable, pass in request headers

**Alternatives Considered**:
- **Direct WhatsApp Cloud API**: Requires Meta Business Suite, more complex
- **Twilio WhatsApp API**: Commercial service, higher cost
- **Rejected Because**: Evolution API provides simplest path to personal WhatsApp number integration

---

### 5. Crawl4AI Web Crawler

**Source**: crawl4ai.com  
**Query**: "Crawl4AI web crawler JavaScript rendering headless browser content extraction rate limiting"

**Key Findings**:
- **LLM-Friendly**: Generates clean Markdown output optimized for RAG pipelines
- **JavaScript Rendering**: Headless browser support for dynamic content
- **Async Architecture**: Built on AsyncWebCrawler for high performance
- **Content Extraction**: CSS selectors, XPath, or LLM-based extraction
- **Features**:
  - Adaptive crawling (knows when to stop)
  - Session management and cookie handling
  - Proxy support and stealth modes
  - robots.txt compliance
  - Rate limiting built-in
- **Deployment**: Python package (pip install crawl4ai) or Docker

**Decision**: Use Crawl4AI with async architecture and JavaScript rendering
- **Rationale**: Purpose-built for LLM/RAG use cases, generates clean Markdown
- **Configuration**:
  - Enable JavaScript rendering for dynamic sites
  - Set max depth: unlimited until 100 pages or domain boundary
  - Respect robots.txt
  - Implement rate limiting (1 request per second default)
- **Content Extraction**: Use Markdown generation (default) for RAG pipeline

**Alternatives Considered**:
- **Scrapy**: More complex, not LLM-optimized
- **Beautiful Soup**: No JavaScript rendering, manual implementation
- **Playwright**: Lower-level, requires more code
- **Rejected Because**: Crawl4AI provides best out-of-box experience for RAG use cases

---

## Technology Stack Summary

### Backend Framework
- **Language**: Python 3.11+
- **Framework**: FastAPI (async, high performance, OpenAPI docs)
- **Rationale**: Async support essential for concurrent WhatsApp messages, FastAPI provides excellent developer experience

### AI & Agent Framework
- **Agent Orchestration**: CrewAI (sequential collaboration)
- **LLM**: Google Gemini Flash 2.5 (32,768 token context)
- **Embeddings**: Google Gemini text-embedding-004 (768 dimensions)
- **Voice Transcription**: Google Cloud Speech-to-Text API
- **Rationale**: Unified Google Cloud ecosystem, consistent authentication, cost-effective

### Data & Storage
- **Vector Database**: Supabase (self-hosted) with pgvector extension
- **Indexing**: HNSW for fast similarity search
- **Connection**: Supavisor pooler for high concurrency
- **Rationale**: Open-source, full control, excellent vector search performance

### Integrations
- **WhatsApp**: Evolution API v2 (webhook-based)
- **Web Crawling**: Crawl4AI (async, JavaScript rendering)
- **Rationale**: Simplest integration paths, purpose-built for use cases

### Text Processing
- **PDF**: PyPDF2
- **Word**: python-docx
- **Excel**: openpyxl
- **PowerPoint**: python-pptx
- **OCR**: Google Cloud Vision API
- **Chunking**: Semantic chunking by paragraphs (100-2000 tokens)
- **Rationale**: Standard libraries, proven reliability

### Infrastructure
- **Deployment**: Docker (build from source per Constitution Principle I)
- **Secrets Management**: Environment variables (Docker secrets in production)
- **Logging**: Structured JSON logging (timestamp, user_id, event_type, message, metadata)
- **Rationale**: Follows project constitution, industry best practices

---

## Architecture Decisions

### 1. Message Processing Flow

```
WhatsApp Message → Evolution API Webhook → FastAPI Endpoint → CrewAI Orchestration
  ↓
Retrieval Agent: Query embedding → Vector search (Supabase) → Top-5 chunks
  ↓
Response Agent: Assemble context → Gemini Flash 2.5 → Generate response
  ↓
Tool Agent: Send response via Evolution API → Store conversation in knowledge base
```

### 2. RAG Pipeline Flow

```
File Upload (WhatsApp) → Download media → Extract text (PyPDF2/python-docx/OCR)
  ↓
Semantic chunking (100-2000 tokens) → Generate embeddings (Gemini text-embedding-004)
  ↓
Store chunks + embeddings (Supabase) → Index with HNSW
```

### 3. Web Crawl Flow

```
URL submission (WhatsApp) → Crawl4AI (async, JS rendering) → Extract Markdown
  ↓
Semantic chunking → Generate embeddings → Store in knowledge base
  ↓
Notify user via WhatsApp (completion message)
```

### 4. Error Handling Strategy

- **Exponential Backoff**: 1s, 2s, 4s, 8s, 16s (max 5 attempts)
- **Timeouts**:
  - Gemini API: 30 seconds
  - Evolution API: 10 seconds
  - Supabase queries: 5 seconds
- **User Notifications**: Specific error messages when retry limit exceeded
- **Logging**: All errors logged with context (user_id, operation, error details)

---

## Performance Targets

Based on spec success criteria and research findings:

- **Response Time**: <10 seconds for text queries (95th percentile) - **Achievable** with Gemini Flash 2.5
- **File Processing**: <30 seconds for files up to 16MB - **Achievable** with async processing
- **Concurrent Users**: 100+ users without degradation - **Achievable** with FastAPI + Supavisor pooling
- **Crawl Speed**: 100 pages in <5 minutes - **Achievable** with Crawl4AI async architecture
- **Vector Search**: <100ms for top-5 retrieval - **Achievable** with HNSW indexing

---

## Security Considerations

- **API Keys**: All stored in environment variables, never in code
- **HTTPS/TLS**: All external API communications encrypted
- **Data Isolation**: Supabase RLS policies enforce user-level access control
- **Phone Number Validation**: E.164 format normalization
- **Rate Limiting**: Prevent abuse (60 msg/min per user for WhatsApp)

---

## Next Steps

1. ✅ MCP research complete
2. ⬜ Fill out plan.md Technical Context
3. ⬜ Define project structure
4. ⬜ Create data-model.md
5. ⬜ Generate API contracts
6. ⬜ Create quickstart.md
7. ⬜ Update agent context

---

## References

- [CrewAI Documentation](https://docs.crewai.com/)
- [Google Gemini API Docs](https://ai.google.dev/gemini-api/docs)
- [Supabase Self-Hosting Guide](https://supabase.com/docs/guides/self-hosting/docker)
- [Evolution API Reference](https://doc.evolution-api.com/)
- [Crawl4AI Documentation](https://docs.crawl4ai.com/)
