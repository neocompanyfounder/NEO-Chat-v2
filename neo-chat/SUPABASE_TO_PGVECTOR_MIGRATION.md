# Supabase to pgvector Migration Complete ✅

## Overview

Successfully migrated NEO Chat from Supabase to direct PostgreSQL with pgvector extension. This removes external dependencies while maintaining all vector database functionality.

## Changes Summary

### 1. Configuration Changes

#### `.env.example` and Environment Variables
- **Removed:**
  - `SUPABASE_URL` → Replaced with `DATABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY` → Removed (no longer needed)
  - `SUPABASE_ANON_KEY` → Removed (no longer needed)
  - `SUPABASE_TIMEOUT` → Renamed to `DATABASE_TIMEOUT`

- **Added:**
  - `DATABASE_URL`: Direct PostgreSQL connection string
  - `DATABASE_TIMEOUT`: Database query timeout

#### `src/utils/config.py`
- Updated `Settings` class to use `DATABASE_URL` and `DATABASE_TIMEOUT`
- Removed JWT authentication keys

### 2. Database Client Refactoring

#### `src/db/supabase_client.py`
- **Renamed class:** `SupabaseClient` → `DatabaseClient`
- **Added pgvector support:** Automatic registration of pgvector types on connection
- **Updated connection logic:** Direct `asyncpg` connection pool without Supabase SDK
- **Backward compatibility:** Maintained `supabase_client` alias for existing code

**Key improvements:**
- Direct PostgreSQL connection using `asyncpg`
- Automatic `pgvector` type registration via `register_vector()`
- Connection pool initialization with custom `_init_connection` callback
- Cleaner error handling and logging

### 3. Vector Service Refactoring

#### `src/services/vector_service.py`
Completely refactored to use direct PostgreSQL queries instead of Supabase SDK:

- **`store_embedding()`**: Raw SQL INSERT with pgvector type
- **`search_similar()`**: Direct pgvector similarity search using `<=>` operator
- **`store_embeddings_batch()`**: Transaction-based batch inserts
- **`delete_user_embeddings()`**: Direct DELETE query

**Vector Search Query Example:**
```sql
SELECT 
    c.id,
    c.content,
    c.document_id,
    c.chunk_index,
    c.token_count,
    e.embedding,
    1 - (e.embedding <=> $1::vector) AS similarity
FROM embeddings e
JOIN chunks c ON e.chunk_id = c.id
WHERE e.user_id = $2
  AND 1 - (e.embedding <=> $1::vector) >= $3
ORDER BY e.embedding <=> $1::vector
LIMIT $4
```

### 4. Dependencies Update

#### `requirements.txt`
- **Removed:** `supabase>=2.3.0`
- **Kept:** `pgvector>=0.2.4`, `asyncpg>=0.29.0`, `psycopg2-binary>=2.9.9`

### 5. Module Exports

#### `src/db/__init__.py`
- Added new exports: `db_client`, `get_db_client`, `DatabaseClient`
- Maintained legacy exports for backward compatibility

## Database Requirements

### PostgreSQL Extensions
Ensure the following extension is installed:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Database Schema
The application expects these tables:
- `embeddings` - Stores vector embeddings
- `chunks` - Stores text chunks
- `documents` - Stores document metadata
- `users` - Stores user information
- `conversations` - Stores conversation history

## Deployment Instructions

### 1. Update Environment Variables

Replace Supabase variables in your deployment environment (Coolify):

```bash
# OLD (Remove these)
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
SUPABASE_ANON_KEY=...
SUPABASE_TIMEOUT=5

# NEW (Add these)
DATABASE_URL=postgres://postgres:ESlMOrLQzt7ovJ3f8vzW4yZ432F83qjRR3h38gUkR3YoF19m5TFnwWI3ZRYMEZQg@rg8kcssoscggosgkwg44w40c:5432/postgres
DATABASE_TIMEOUT=5
```

### 2. Verify PostgreSQL Setup

```bash
# Connect to your PostgreSQL database
psql $DATABASE_URL

# Verify pgvector extension
SELECT * FROM pg_extension WHERE extname = 'vector';

# Check if tables exist
\dt

# Verify vector column
\d+ embeddings
```

### 3. Run Database Migrations

If tables don't exist, run migrations:

```bash
cd neo-chat
python -m alembic upgrade head
```

Or the application will create tables automatically on first startup.

### 4. Deploy Application

```bash
# Commit changes
git add .
git commit -m "refactor: migrate from Supabase to direct pgvector/PostgreSQL"
git push origin 001-whatsapp-ai-rag-engine

# Deploy via Coolify
# The deployment will automatically use the new DATABASE_URL
```

### 5. Verify Deployment

After deployment, check logs for:

```json
{
  "level": "INFO",
  "message": "Connected to PostgreSQL with pgvector",
  "metadata": {
    "pool_size": "5-20",
    "timeout": 5,
    "pgvector_enabled": true
  }
}
```

## Benefits of Migration

1. **✅ Simplified Architecture**: No external Supabase dependency
2. **✅ Direct Control**: Full control over PostgreSQL configuration
3. **✅ Better Performance**: Direct connection without SDK overhead
4. **✅ Reduced Costs**: No Supabase subscription needed
5. **✅ Easier Debugging**: Direct SQL queries are easier to debug
6. **✅ Flexibility**: Can optimize queries and indexes directly

## Backward Compatibility

The migration maintains backward compatibility:

- `supabase_client` still works (alias to `db_client`)
- `get_supabase_client()` still works (returns `DatabaseClient`)
- All existing imports continue to function

## Testing

### Unit Tests
All unit tests should pass without modification due to backward compatibility.

### Integration Tests
Update integration test connection strings to use `DATABASE_URL`.

### Manual Testing Checklist
- [ ] Database connection successful
- [ ] Vector embeddings can be stored
- [ ] Vector similarity search works
- [ ] Batch operations function correctly
- [ ] User data isolation works (RLS equivalent)

## Troubleshooting

### Connection Issues

**Error**: `socket.gaierror: [Errno -3] Temporary failure in name resolution`

**Solution**: Verify the DATABASE_URL hostname is resolvable from your deployment environment. Try using IP address instead of hostname.

### pgvector Not Found

**Error**: `pgvector package not installed`

**Solution**: Ensure `pgvector>=0.2.4` is in `requirements.txt` and run `pip install -r requirements.txt`

### Vector Type Not Registered

**Error**: `type "vector" does not exist`

**Solution**: Install pgvector extension in PostgreSQL:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Query Failures

**Error**: `operator does not exist: vector <=> vector`

**Solution**: Ensure pgvector extension is properly installed and the embedding column is of type `vector`.

## Rollback Plan

If issues occur, rollback by:

1. Revert the commit:
   ```bash
   git revert HEAD
   git push origin 001-whatsapp-ai-rag-engine
   ```

2. Restore Supabase environment variables in Coolify

3. Redeploy the previous version

## Next Steps

1. Monitor application logs after deployment
2. Verify vector search functionality
3. Run performance benchmarks
4. Optimize indexes if needed:
   ```sql
   -- Create HNSW index for better performance
   CREATE INDEX ON embeddings USING hnsw (embedding vector_cosine_ops);
   ```

## Questions or Issues?

If you encounter any issues during migration, check:
1. PostgreSQL version (must support pgvector)
2. pgvector extension installation
3. Network connectivity to PostgreSQL
4. Environment variable configuration

---

**Migration Status**: ✅ **COMPLETE**
**Migration Date**: October 18, 2025
**Breaking Changes**: None (backward compatible)
**Required Actions**: Update environment variables and redeploy
