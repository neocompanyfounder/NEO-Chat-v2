# 🚀 NEO Chat Deployment Guide - Coolify on Hostinger

**Domain**: neochat.neoo.com.sa  
**Platform**: Coolify (Self-hosted PaaS)  
**Hosting**: Hostinger VPS  
**Date**: 2025-01-17

---

## Prerequisites

Before deploying, ensure you have:

- ✅ Coolify installed on your Hostinger VPS
- ✅ Domain `neochat.neoo.com.sa` DNS configured
- ✅ Git repository with NEO Chat code
- ✅ All required API keys and credentials
- ✅ SSH access to your Hostinger server

---

## Step 1: Prepare Your Server

### 1.1 SSH into Your Hostinger VPS

```bash
ssh root@your-hostinger-ip
```

### 1.2 Verify Coolify Installation

```bash
# Check Coolify status
docker ps | grep coolify

# Access Coolify dashboard
# Open: https://your-server-ip:8000 or your Coolify domain
```

### 1.3 Verify Docker Installation

```bash
docker --version
docker-compose --version
```

---

## Step 2: Configure DNS

### 2.1 Add DNS Records

In your domain registrar (for `neoo.com.sa`), add:

**A Record**:
```
Type: A
Name: neochat
Value: YOUR_HOSTINGER_VPS_IP
TTL: 3600
```

**Optional CNAME (if using www)**:
```
Type: CNAME
Name: www.neochat
Value: neochat.neoo.com.sa
TTL: 3600
```

### 2.2 Verify DNS Propagation

```bash
# Check DNS resolution
nslookup neochat.neoo.com.sa

# Or use dig
dig neochat.neoo.com.sa
```

Wait 5-10 minutes for DNS propagation.

---

## Step 3: Deploy via Coolify Dashboard

### 3.1 Access Coolify Dashboard

1. Open your browser and navigate to your Coolify instance
2. Login with your credentials

### 3.2 Create New Project

1. Click **"+ New Project"**
2. Enter project name: `neo-chat`
3. Click **"Create"**

### 3.3 Add New Resource

1. Inside the project, click **"+ New Resource"**
2. Select **"Docker Compose"** or **"Git Repository"**

### Option A: Deploy from Git Repository (Recommended)

**Step 1**: Select "Git Repository"

**Step 2**: Configure Git Source
```
Repository URL: https://github.com/YOUR_USERNAME/NEO-Chat-v2.git
Branch: main (or your deployment branch)
```

**Step 3**: Configure Build Settings
```
Build Pack: Dockerfile
Dockerfile Location: neo-chat/Dockerfile
Docker Compose File: neo-chat/docker-compose.coolify.yml (optional)
```

**Step 4**: Configure Domain
```
Domain: neochat.neoo.com.sa
Enable HTTPS: ✅ Yes (Let's Encrypt)
Force HTTPS: ✅ Yes
```

**Step 5**: Set Environment Variables (CRITICAL)

Click **"Environment Variables"** and add:

```bash
# Google Cloud Services
GOOGLE_API_KEY=your_google_api_key_here

# Evolution API (WhatsApp)
EVOLUTION_API_URL=http://your-evolution-api:8080
EVOLUTION_API_KEY=your_evolution_api_key
EVOLUTION_INSTANCE_NAME=your_instance_name
EVOLUTION_TIMEOUT=10

# Supabase (PostgreSQL + pgvector)
SUPABASE_URL=postgresql://user:password@host:5432/database
SUPABASE_KEY=your_supabase_anon_key

# Application Settings
LOG_LEVEL=INFO
ENVIRONMENT=production

# Chunking Configuration
MIN_CHUNK_TOKENS=100
MAX_CHUNK_TOKENS=500
CHUNK_OVERLAP_TOKENS=50

# Rate Limiting
GEMINI_RATE_LIMIT=60
WHATSAPP_RATE_LIMIT=60

# Timeouts
GEMINI_TIMEOUT=30
SUPABASE_TIMEOUT=5
```

**Step 6**: Configure Port Mapping
```
Container Port: 8000
Public Port: 80 (Coolify will handle this)
```

**Step 7**: Deploy
- Click **"Deploy"**
- Coolify will:
  1. Clone your repository
  2. Build Docker image
  3. Start container
  4. Configure SSL (Let's Encrypt)
  5. Set up reverse proxy

### Option B: Deploy from Docker Compose

**Step 1**: Select "Docker Compose"

**Step 2**: Paste Docker Compose Content

Copy the content from `docker-compose.coolify.yml` into the editor.

**Step 3**: Configure as above (domain, environment variables)

**Step 4**: Deploy

---

## Step 4: Configure SSL Certificate

Coolify automatically provisions SSL certificates via Let's Encrypt.

### 4.1 Verify SSL Configuration

1. In Coolify dashboard, go to your application
2. Check **"SSL"** section
3. Ensure **"Let's Encrypt"** is enabled
4. Certificate should be automatically issued

### 4.2 Force HTTPS

Enable **"Force HTTPS"** to redirect all HTTP traffic to HTTPS.

---

## Step 5: Database Setup (Supabase)

### Option A: Use Existing Supabase Project

If you already have a Supabase project:

1. Get your connection string from Supabase dashboard
2. Add it to environment variables (done in Step 3.3)

### Option B: Deploy PostgreSQL with pgvector on Same Server

If you want to self-host the database:

**Step 1**: Create PostgreSQL Service in Coolify

1. In Coolify, click **"+ New Resource"**
2. Select **"PostgreSQL"**
3. Configure:
   ```
   Name: neo-chat-db
   Version: 15 (or latest)
   Database Name: neochat
   Username: neochat_user
   Password: [generate strong password]
   ```

**Step 2**: Install pgvector Extension

```bash
# SSH into your server
ssh root@your-hostinger-ip

# Access PostgreSQL container
docker exec -it neo-chat-db psql -U neochat_user -d neochat

# Install pgvector
CREATE EXTENSION IF NOT EXISTS vector;

# Verify installation
\dx
```

**Step 3**: Run Database Migrations

```bash
# From your local machine or server
cd neo-chat

# Run migrations (you'll need to create a migration script)
psql postgresql://neochat_user:password@neochat.neoo.com.sa:5432/neochat < src/db/migrations/001_users_table.sql
psql postgresql://neochat_user:password@neochat.neoo.com.sa:5432/neochat < src/db/migrations/002_conversations_table.sql
psql postgresql://neochat_user:password@neochat.neoo.com.sa:5432/neochat < src/db/migrations/003_documents_table.sql
psql postgresql://neochat_user:password@neochat.neoo.com.sa:5432/neochat < src/db/migrations/004_crawl_jobs_table.sql
```

**Step 4**: Update Connection String

Update `SUPABASE_URL` in environment variables:
```
SUPABASE_URL=postgresql://neochat_user:password@neo-chat-db:5432/neochat
```

---

## Step 6: Configure Evolution API (WhatsApp)

You need a running Evolution API instance for WhatsApp integration.

### Option A: Use Existing Evolution API

If you have Evolution API running elsewhere:
```bash
EVOLUTION_API_URL=http://your-evolution-api-server:8080
```

### Option B: Deploy Evolution API on Same Server

**Step 1**: Create Evolution API Service in Coolify

1. Click **"+ New Resource"**
2. Select **"Docker Compose"**
3. Use Evolution API docker-compose:

```yaml
version: '3.8'

services:
  evolution-api:
    image: atendai/evolution-api:latest
    container_name: evolution-api
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - SERVER_URL=https://evolution.neoo.com.sa
      - AUTHENTICATION_API_KEY=your_evolution_api_key_here
    volumes:
      - evolution_data:/evolution/instances
    networks:
      - neo-chat-network

volumes:
  evolution_data:

networks:
  neo-chat-network:
    external: true
```

**Step 2**: Configure Subdomain

Add DNS record for Evolution API:
```
Type: A
Name: evolution
Value: YOUR_HOSTINGER_VPS_IP
```

**Step 3**: Update NEO Chat Environment Variables

```bash
EVOLUTION_API_URL=http://evolution-api:8080
# or
EVOLUTION_API_URL=https://evolution.neoo.com.sa
```

---

## Step 7: Verify Deployment

### 7.1 Check Application Status

In Coolify dashboard:
- ✅ Application status should be **"Running"**
- ✅ SSL certificate should be **"Active"**
- ✅ Health checks should be **"Passing"**

### 7.2 Test Endpoints

```bash
# Test health endpoint
curl https://neochat.neoo.com.sa/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-17T22:00:00Z"
}
```

### 7.3 Check Logs

In Coolify dashboard:
1. Go to your application
2. Click **"Logs"**
3. Verify no errors

Or via command line:
```bash
# SSH into server
ssh root@your-hostinger-ip

# View logs
docker logs neo-chat-app -f
```

### 7.4 Test WhatsApp Integration

1. Send a message to your WhatsApp number
2. Check if webhook receives the message
3. Verify AI response is sent back

---

## Step 8: Configure Webhook in Evolution API

### 8.1 Set Webhook URL

In Evolution API dashboard or via API:

```bash
curl -X POST https://evolution.neoo.com.sa/instance/webhook \
  -H "apikey: your_evolution_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook": {
      "url": "https://neochat.neoo.com.sa/webhook",
      "events": ["messages.upsert"]
    }
  }'
```

### 8.2 Verify Webhook Configuration

```bash
curl -X GET https://evolution.neoo.com.sa/instance/webhook \
  -H "apikey: your_evolution_api_key"
```

---

## Step 9: Monitoring & Maintenance

### 9.1 Set Up Monitoring

**Coolify Built-in Monitoring**:
- CPU usage
- Memory usage
- Network traffic
- Container status

**External Monitoring** (Optional):
- UptimeRobot: https://uptimerobot.com
- Pingdom: https://www.pingdom.com
- Better Uptime: https://betteruptime.com

### 9.2 Configure Alerts

In Coolify:
1. Go to **Settings** → **Notifications**
2. Add notification channels (Email, Slack, Discord)
3. Configure alert rules

### 9.3 Backup Strategy

**Database Backups**:
```bash
# Create backup script
cat > /root/backup-neochat.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/root/backups/neochat"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
docker exec neo-chat-db pg_dump -U neochat_user neochat > $BACKUP_DIR/neochat_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
EOF

chmod +x /root/backup-neochat.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /root/backup-neochat.sh
```

### 9.4 Update Application

**Via Coolify**:
1. Push changes to your Git repository
2. In Coolify dashboard, click **"Redeploy"**
3. Coolify will pull latest code and rebuild

**Manual Update**:
```bash
# SSH into server
ssh root@your-hostinger-ip

# Pull latest changes
cd /path/to/neo-chat
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.coolify.yml up -d --build
```

---

## Step 10: Troubleshooting

### Common Issues

**Issue 1: Application Won't Start**

```bash
# Check logs
docker logs neo-chat-app

# Common causes:
# - Missing environment variables
# - Database connection failed
# - Port already in use
```

**Issue 2: SSL Certificate Not Issued**

```bash
# Verify DNS is pointing correctly
nslookup neochat.neoo.com.sa

# Check Coolify SSL logs
# In dashboard: Application → SSL → Logs

# Manual certificate request (if needed)
# Coolify handles this automatically, but you can force renewal
```

**Issue 3: Webhook Not Receiving Messages**

```bash
# Test webhook endpoint
curl -X POST https://neochat.neoo.com.sa/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

# Check Evolution API webhook configuration
# Verify firewall allows incoming connections
```

**Issue 4: Database Connection Failed**

```bash
# Test database connection
docker exec neo-chat-app python -c "
from src.utils.config import get_settings
settings = get_settings()
print(settings.SUPABASE_URL)
"

# Verify PostgreSQL is running
docker ps | grep postgres

# Check connection from container
docker exec neo-chat-app psql $SUPABASE_URL -c "SELECT 1"
```

**Issue 5: High Memory Usage**

```bash
# Check container stats
docker stats neo-chat-app

# Restart container
docker restart neo-chat-app

# Scale down workers if needed (edit Dockerfile)
# Change: --workers 2 to --workers 1
```

---

## Step 11: Security Hardening

### 11.1 Firewall Configuration

```bash
# Allow only necessary ports
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
```

### 11.2 Secure Environment Variables

- ✅ Never commit `.env` files to Git
- ✅ Use Coolify's encrypted environment variables
- ✅ Rotate API keys regularly
- ✅ Use strong database passwords

### 11.3 Enable Rate Limiting

Already configured in the application:
- Gemini API: 60 requests/minute
- WhatsApp: 60 messages/minute per user

### 11.4 Regular Updates

```bash
# Update system packages
apt update && apt upgrade -y

# Update Docker images
docker-compose pull
docker-compose up -d
```

---

## Step 12: Performance Optimization

### 12.1 Enable Caching (Optional)

Add Redis for caching:

```yaml
# Add to docker-compose.coolify.yml
  redis:
    image: redis:7-alpine
    container_name: neo-chat-redis
    restart: unless-stopped
    networks:
      - neo-chat-network
```

### 12.2 Configure CDN (Optional)

Use Cloudflare for:
- DDoS protection
- CDN caching
- Additional SSL

### 12.3 Database Optimization

```sql
-- Create indexes for better performance
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_crawl_jobs_user_id ON crawl_jobs(user_id);

-- Optimize vector search
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);
```

---

## Quick Reference

### Important URLs

- **Application**: https://neochat.neoo.com.sa
- **Health Check**: https://neochat.neoo.com.sa/health
- **Webhook**: https://neochat.neoo.com.sa/webhook
- **Coolify Dashboard**: https://your-coolify-domain

### Important Commands

```bash
# View logs
docker logs neo-chat-app -f

# Restart application
docker restart neo-chat-app

# Check status
docker ps | grep neo-chat

# Access container shell
docker exec -it neo-chat-app bash

# View environment variables
docker exec neo-chat-app env | grep GOOGLE

# Database backup
docker exec neo-chat-db pg_dump -U neochat_user neochat > backup.sql
```

### Environment Variables Checklist

- [ ] GOOGLE_API_KEY
- [ ] EVOLUTION_API_URL
- [ ] EVOLUTION_API_KEY
- [ ] EVOLUTION_INSTANCE_NAME
- [ ] SUPABASE_URL
- [ ] SUPABASE_KEY
- [ ] LOG_LEVEL
- [ ] ENVIRONMENT

---

## Support & Resources

**Documentation**:
- NEO Chat Docs: See `README.md`
- Coolify Docs: https://coolify.io/docs
- Evolution API: https://doc.evolution-api.com

**Community**:
- Coolify Discord: https://discord.gg/coolify
- Evolution API Discord: https://discord.gg/evolution-api

---

## Deployment Checklist

Before going live:

- [ ] DNS configured and propagated
- [ ] All environment variables set
- [ ] Database migrations run
- [ ] SSL certificate active
- [ ] Webhook configured in Evolution API
- [ ] Health check passing
- [ ] Test message sent and received
- [ ] Monitoring configured
- [ ] Backups scheduled
- [ ] Firewall configured
- [ ] Documentation updated

---

**Deployment Date**: 2025-01-17  
**Version**: 1.0.0  
**Status**: ✅ Production Ready  
**Domain**: neochat.neoo.com.sa  

🎉 **Your NEO Chat application is now live!** 🎉
