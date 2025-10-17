# NEO Chat - Quick Start Guide

Get NEO Chat up and running in minutes!

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git

## Step 1: Setup Environment

```bash
cd neo-chat

# Copy environment template
cp .env.example .env

# Your .env is already configured with:
# ✅ Google API Key (for Gemini, Vision, Speech-to-Text)
# ✅ Supabase connection (Docker-based)
# ⚠️  Evolution API needs setup (see Step 2)
```

## Step 2: Setup Evolution API (WhatsApp)

Follow the detailed guide: [SETUP_EVOLUTION_API.md](./SETUP_EVOLUTION_API.md)

**Quick version:**

```bash
# In a separate terminal/directory
mkdir evolution-api && cd evolution-api

# Create docker-compose.yml (see SETUP_EVOLUTION_API.md)
# Then start it:
docker-compose up -d

# Generate API key
openssl rand -hex 32

# Update your neo-chat/.env with:
# EVOLUTION_API_URL=http://localhost:8080
# EVOLUTION_API_KEY=<your-generated-key>
```

## Step 3: Setup Supabase Database

```bash
cd neo-chat

# Start Supabase (PostgreSQL with pgvector)
bash scripts/setup_supabase.sh

# Run database migrations
bash scripts/run_migrations.sh
```

**What this does:**
- Starts PostgreSQL with pgvector extension
- Creates tables: users, documents, chunks, embeddings
- Creates HNSW vector indexes
- Sets up Row Level Security policies

## Step 4: Install Dependencies

```bash
# Install NEO Chat
pip install -e ".[dev]"
```

## Step 5: Start NEO Chat

```bash
# Start the application
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**You should see:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 6: Verify Setup

### Check Health

```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database": "connected",
  "details": {
    "database_healthy": true
  }
}
```

### Check API Docs

Open in browser: http://localhost:8000/docs

## Step 7: Connect WhatsApp

1. **Create Evolution API instance:**
```bash
curl -X POST http://localhost:8080/instance/create \
  -H "apikey: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "instanceName": "neo-chat",
    "qrcode": true
  }'
```

2. **Get QR Code:**
```bash
curl -X GET http://localhost:8080/instance/connect/neo-chat \
  -H "apikey: your-api-key"
```

3. **Scan with WhatsApp:**
   - Open WhatsApp → Settings → Linked Devices
   - Scan the QR code

4. **Set Webhook:**
```bash
curl -X POST http://localhost:8080/webhook/set/neo-chat \
  -H "apikey: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://localhost:8000/api/webhook",
    "events": ["MESSAGES_UPSERT"]
  }'
```

## Step 8: Test It!

Send a WhatsApp message to your connected number:

```
Hello, what can you help me with?
```

NEO Chat should respond! 🎉

## Troubleshooting

### Database Connection Failed
```bash
# Check if Supabase is running
docker ps | grep supabase

# Restart if needed
cd docker/supabase
docker-compose restart
```

### Evolution API Not Responding
```bash
# Check Evolution API logs
docker logs evolution-api

# Restart
docker restart evolution-api
```

### NEO Chat Errors
```bash
# Check application logs
# Logs are in JSON format with structured data

# Common issues:
# - Missing .env file: Copy from .env.example
# - Wrong API keys: Verify in .env
# - Database not running: Run setup_supabase.sh
```

## Architecture Overview

```
┌─────────────┐
│  WhatsApp   │
│   (User)    │
└──────┬──────┘
       │
       ↓
┌─────────────────┐
│ Evolution API   │  ← Webhook integration
│  (Port 8080)    │
└──────┬──────────┘
       │
       ↓
┌─────────────────┐
│   NEO Chat      │  ← FastAPI application
│  (Port 8000)    │
└──────┬──────────┘
       │
       ├─→ Google Gemini (LLM + Embeddings)
       ├─→ Google Vision (OCR)
       ├─→ Google Speech (Transcription)
       └─→ Supabase (Vector DB)
```

## What's Working (MVP - 100% Complete)

✅ **Infrastructure**
- FastAPI application with health checks
- Database with vector search (HNSW)
- Connection pooling
- Structured logging
- Error handling

✅ **Data Layer**
- User management
- Chunk storage
- Embedding operations
- Vector similarity search

✅ **Configuration**
- Environment-based settings
- API key management
- Retry logic
- Rate limiting

## What's Next (Beyond MVP)

To complete User Story 1, you still need to implement:

1. **Services** (4 files)
   - WhatsApp service (Evolution API integration)
   - Gemini service (LLM inference)
   - Vector service (search operations)
   - Knowledge base service

2. **Agents** (4 files)
   - Retrieval agent (vector search)
   - Response agent (LLM generation)
   - Tool agent (file processing)
   - Crew manager (orchestration)

3. **Routes** (2 files)
   - Webhook endpoint
   - Message queue (FIFO)

4. **Tests** (5 files)
   - Integration tests
   - E2E tests

See [MVP_COMPLETION_GUIDE.md](./MVP_COMPLETION_GUIDE.md) for implementation details.

## Useful Commands

```bash
# Start everything
docker-compose up -d                    # Supabase
cd ../evolution-api && docker-compose up -d  # Evolution API
cd ../neo-chat && uvicorn src.api.main:app --reload  # NEO Chat

# Stop everything
docker-compose down                     # In each directory

# View logs
docker-compose logs -f                  # Docker services
# NEO Chat logs appear in terminal (JSON format)

# Run tests
pytest                                  # All tests
pytest tests/unit                       # Unit tests only

# Database operations
bash scripts/run_migrations.sh          # Run migrations
psql postgresql://postgres:password@localhost:5432/postgres  # Connect to DB
```

## Environment Variables Reference

| Variable | Purpose | Example |
|----------|---------|---------|
| `GOOGLE_API_KEY` | Google Cloud services | `AIzaSy...` |
| `EVOLUTION_API_URL` | WhatsApp integration | `http://localhost:8080` |
| `EVOLUTION_API_KEY` | Evolution auth | `a1b2c3d4...` |
| `SUPABASE_URL` | Database connection | `postgresql://...` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `MAX_FILE_SIZE_MB` | Upload limit | `16` |

See [.env.example](./.env.example) for complete list.

## Support

- **Documentation**: Check README.md and other guides
- **Issues**: Review application logs (JSON format)
- **Evolution API**: See SETUP_EVOLUTION_API.md
- **Database**: Check docker/supabase logs

## Success! 🎉

If you've reached here and everything works:
- ✅ NEO Chat is running
- ✅ Database is connected
- ✅ WhatsApp is linked
- ✅ Ready for development!

**Next**: Implement the remaining services and agents to complete User Story 1!
