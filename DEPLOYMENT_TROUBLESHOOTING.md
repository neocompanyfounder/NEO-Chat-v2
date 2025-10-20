# Deployment Troubleshooting Guide

## Current Error: Bad Gateway (502)

This means the deployment platform can reach the server but the application isn't responding.

## Common Causes & Solutions

### 1. ❌ Application Not Starting

**Check:**
```bash
# SSH into your server
ssh user@neoo.com.sa

# Check if container is running
docker ps | grep neo-chat

# Check container logs
docker logs neo-chat-app --tail 100
```

**Common Issues:**
- Missing environment variables in `.env`
- Database connection failure
- Port already in use

### 2. ❌ Wrong Branch in Git

**Error:** `fatal: Remote branch main not found`

**Solution:**
```bash
# Check your current branch
git branch

# If you're on 'master' instead of 'main', either:
# Option A: Rename branch to main
git branch -m master main
git push -u origin main

# Option B: Configure deployment to use 'master' branch
```

### 3. ❌ Missing .env File

The deployment needs environment variables. Make sure your `.env` file is properly configured on the server.

**Required Variables:**
```env
# Evolution API
EVOLUTION_API_URL=http://eapi.neoo.com.sa:8080
EVOLUTION_API_KEY=your_key_here
EVOLUTION_INSTANCE_NAME=your_instance

# Google Cloud
GOOGLE_API_KEY=your_gemini_key

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### 4. ❌ Port Configuration

**Check if port 8000 is accessible:**
```bash
# On server
curl http://localhost:8000/health

# From outside
curl http://neochat.neoo.com.sa/health
```

### 5. ❌ Health Check Failing

The deployment platform checks `/health` endpoint. If it fails, the deployment fails.

**Test health endpoint:**
```bash
# Inside container
docker exec neo-chat-app curl http://localhost:8000/health

# Should return:
# {"status":"healthy","timestamp":"..."}
```

## Step-by-Step Deployment Fix

### Step 1: Fix Git Branch
```bash
cd "C:\Users\Admin\Documents\Coding\NEO Chat v2"

# Check current branch
git branch

# If not on 'main', create and push it
git checkout -b main
git push -u origin main
```

### Step 2: Commit All Changes
```bash
git add .
git commit -m "Fix deployment configuration"
git push origin main
```

### Step 3: Configure Environment Variables on Server

SSH into your server and create/update the `.env` file:
```bash
ssh user@neoo.com.sa
cd /path/to/neo-chat
nano neo-chat/.env
```

Paste your environment variables and save.

### Step 4: Manual Deployment Test

Before using the deployment platform, test manually:
```bash
# On server
docker build -t neo-chat:latest -f Dockerfile .
docker run -d --name neo-chat-app -p 8000:8000 --env-file neo-chat/.env neo-chat:latest

# Wait 30 seconds for startup
sleep 30

# Test
curl http://localhost:8000/health
```

### Step 5: Check Logs

```bash
# View startup logs
docker logs neo-chat-app

# Follow logs in real-time
docker logs neo-chat-app -f
```

## Expected Successful Logs

You should see:
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
{"timestamp": "...", "level": "INFO", "message": "Starting NEO Chat application"}
{"timestamp": "...", "level": "INFO", "message": "Connected to PostgreSQL with pgvector"}
{"timestamp": "...", "level": "INFO", "message": "All services and agents initialized"}
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Deployment Platform Configuration

### For Coolify:
1. Go to your Coolify dashboard
2. Select your NEO Chat application
3. Check:
   - ✅ Branch: `main` (or `master`)
   - ✅ Port: `8000`
   - ✅ Health Check Path: `/health`
   - ✅ Environment Variables: All set

### For Other Platforms:
- **Port**: 8000
- **Health Check**: `/health`
- **Start Command**: `uvicorn src.api.main:app --host 0.0.0.0 --port 8000`
- **Build Command**: Uses Dockerfile automatically

## Quick Fixes

### Fix 1: Restart Deployment
Sometimes just redeploying fixes the issue:
1. Go to deployment dashboard
2. Click "Redeploy" or "Restart"
3. Wait for deployment to complete

### Fix 2: Check Database Connection
```bash
# Test database connection from server
docker run --rm -it --env-file neo-chat/.env postgres:15 psql $DATABASE_URL -c "SELECT 1"
```

### Fix 3: Simplify for Testing
Temporarily disable health check to see if app starts:
```dockerfile
# Comment out in Dockerfile
# HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
#     CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1
```

## Get Help

If still not working, collect these logs:
```bash
# Container logs
docker logs neo-chat-app > neo-chat-logs.txt

# Container status
docker ps -a | grep neo-chat > container-status.txt

# System info
docker info > docker-info.txt
```

Then share these files for debugging.
