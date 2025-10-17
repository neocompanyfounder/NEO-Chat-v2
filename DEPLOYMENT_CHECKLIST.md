# ✅ NEO Chat Deployment Checklist

**Follow this step-by-step checklist for successful deployment**

---

## 📋 Pre-Deployment (15 minutes)

### Step 1: Get Google Cloud API Key
- [ ] Go to https://console.cloud.google.com
- [ ] Create new project: "NEO Chat"
- [ ] Enable Generative Language API (Gemini)
- [ ] Enable Cloud Vision API
- [ ] Enable Cloud Speech-to-Text API
- [ ] Create API key
- [ ] Restrict API key to the 3 APIs above
- [ ] Copy and save API key: `AIzaSy...`

### Step 2: Generate Secure Passwords
- [ ] Generate POSTGRES_PASSWORD (32+ chars)
- [ ] Generate REDIS_PASSWORD (32+ chars)
- [ ] Generate EVOLUTION_API_KEY (32+ chars)
- [ ] Save all passwords in password manager

**Quick generate (run 3 times):**
```bash
# Linux/Mac
openssl rand -base64 32

# Windows PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
```

### Step 3: Configure DNS
- [ ] Login to domain registrar
- [ ] Add A record: `neochat.neoo.com.sa` → Your VPS IP
- [ ] Add A record: `evolution.neoo.com.sa` → Your VPS IP
- [ ] Wait 5-10 minutes for DNS propagation
- [ ] Verify with: `nslookup neochat.neoo.com.sa`

---

## 🚀 Deployment in Coolify (10 minutes)

### Step 4: Create Project
- [ ] Login to Coolify dashboard
- [ ] Click "+ New Project"
- [ ] Name: "neo-chat"
- [ ] Click "Create"

### Step 5: Add Docker Compose Resource
- [ ] Click "+ New Resource"
- [ ] Select "Docker Compose"
- [ ] Copy content from `docker-compose.coolify.yml`
- [ ] Paste into Coolify editor

### Step 6: Configure Environment Variables
- [ ] Click "Environment Variables" tab
- [ ] Add the following variables:

```bash
GOOGLE_API_KEY=your_google_api_key_here
POSTGRES_DB=neochat
POSTGRES_USER=neochat_user
POSTGRES_PASSWORD=your_generated_password_1
REDIS_PASSWORD=your_generated_password_2
EVOLUTION_API_KEY=your_generated_password_3
EVOLUTION_SERVER_URL=https://evolution.neoo.com.sa
EVOLUTION_INSTANCE_NAME=neochat
ENVIRONMENT=production
LOG_LEVEL=INFO
```

- [ ] Verify all variables are set correctly
- [ ] Save environment variables

### Step 7: Deploy
- [ ] Click "Deploy" button
- [ ] Wait for build to complete (3-5 minutes)
- [ ] Check logs for any errors
- [ ] Verify all 4 services are running:
  - [ ] neo-chat-postgres (green)
  - [ ] neo-chat-redis (green)
  - [ ] neo-chat-evolution (green)
  - [ ] neo-chat-app (green)

---

## 📱 WhatsApp Connection (5 minutes)

### Step 8: Access Evolution API
- [ ] Open https://evolution.neoo.com.sa
- [ ] Verify Evolution API dashboard loads

### Step 9: Create WhatsApp Instance
- [ ] Click "Create Instance" or similar
- [ ] Instance name: `neochat`
- [ ] API key: (use your EVOLUTION_API_KEY)
- [ ] Click "Create"
- [ ] QR code should appear

### Step 10: Scan QR Code
- [ ] Open WhatsApp on your phone
- [ ] Go to Settings → Linked Devices
- [ ] Click "Link a Device"
- [ ] Scan the QR code from Evolution API
- [ ] Wait for connection confirmation

### Step 11: Configure Webhook
- [ ] In Evolution API, go to instance settings
- [ ] Set webhook URL: `https://neochat.neoo.com.sa/webhook`
- [ ] Enable events: `messages.upsert`
- [ ] Save webhook configuration

**Or via API:**
```bash
curl -X POST https://evolution.neoo.com.sa/instance/webhook \
  -H "apikey: YOUR_EVOLUTION_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook": {
      "url": "https://neochat.neoo.com.sa/webhook",
      "events": ["messages.upsert"]
    }
  }'
```

---

## ✅ Verification (5 minutes)

### Step 12: Test Health Endpoint
- [ ] Open browser: https://neochat.neoo.com.sa/health
- [ ] Should return: `{"status": "healthy", ...}`

**Or via curl:**
```bash
curl https://neochat.neoo.com.sa/health
```

### Step 13: Test WhatsApp Bot
- [ ] Send text message to your WhatsApp number
- [ ] Bot should respond within 10 seconds
- [ ] Response should be AI-generated

### Step 14: Test File Upload
- [ ] Send a PDF or image to WhatsApp
- [ ] Bot should acknowledge receipt
- [ ] Ask question about the file
- [ ] Bot should answer based on file content

### Step 15: Test Voice Message
- [ ] Send voice message to WhatsApp
- [ ] Bot should transcribe it
- [ ] Bot should respond to transcribed text

---

## 🔧 Post-Deployment Configuration (10 minutes)

### Step 16: Configure Monitoring
- [ ] In Coolify, go to Settings → Notifications
- [ ] Add email for alerts
- [ ] Enable health check alerts
- [ ] Test notification

### Step 17: Set Up Backups
- [ ] Schedule daily database backups
- [ ] Test backup restoration
- [ ] Document backup location

**Backup command:**
```bash
docker exec neo-chat-postgres pg_dump -U neochat_user neochat > backup_$(date +%Y%m%d).sql
```

### Step 18: Security Hardening
- [ ] Verify SSL certificates are active
- [ ] Check firewall rules (ports 80, 443, 22 only)
- [ ] Verify environment variables are not exposed
- [ ] Test rate limiting

### Step 19: Documentation
- [ ] Save all credentials in password manager
- [ ] Document any customizations made
- [ ] Create incident response plan
- [ ] Share access with team (if applicable)

---

## 📊 Performance Verification

### Step 20: Load Testing (Optional)
- [ ] Test with 10 concurrent users
- [ ] Verify response times < 10 seconds
- [ ] Check memory usage
- [ ] Check CPU usage
- [ ] Monitor error rates

### Step 21: Feature Testing
- [ ] Test text conversation
- [ ] Test PDF upload
- [ ] Test DOCX upload
- [ ] Test image upload with OCR
- [ ] Test web crawling
- [ ] Test voice messages
- [ ] Test interactive menus (if implemented)
- [ ] Test knowledge base reset (if implemented)

---

## 🎯 Go-Live Checklist

### Before Going Live:
- [ ] All services running and healthy
- [ ] SSL certificates active
- [ ] WhatsApp connected and responding
- [ ] All features tested
- [ ] Monitoring configured
- [ ] Backups scheduled
- [ ] Team trained (if applicable)
- [ ] Documentation complete
- [ ] Incident response plan ready

### After Going Live:
- [ ] Monitor logs for first 24 hours
- [ ] Check error rates
- [ ] Verify API usage within limits
- [ ] Collect user feedback
- [ ] Document any issues
- [ ] Plan for scaling if needed

---

## 🆘 Troubleshooting Quick Reference

### Services Won't Start
```bash
# Check logs
docker logs neo-chat-app -f

# Common issues:
# - Missing environment variables
# - Invalid Google API key
# - Weak passwords
```

### WhatsApp Not Responding
```bash
# Check Evolution API
curl https://evolution.neoo.com.sa/

# Check webhook
curl https://neochat.neoo.com.sa/webhook -X POST -d '{"test":"data"}'

# Verify Evolution API logs
docker logs neo-chat-evolution -f
```

### Database Connection Failed
```bash
# Test database
docker exec -it neo-chat-postgres psql -U neochat_user -d neochat -c "SELECT 1"

# Check pgvector
docker exec -it neo-chat-postgres psql -U neochat_user -d neochat -c "\dx"
```

### SSL Certificate Issues
```bash
# Verify DNS
nslookup neochat.neoo.com.sa

# Check Coolify SSL logs
# In dashboard: Application → SSL → Logs
```

---

## 📞 Support Contacts

### If You Need Help:

**Coolify Issues:**
- Docs: https://coolify.io/docs
- Discord: https://discord.gg/coolify

**Evolution API Issues:**
- Docs: https://doc.evolution-api.com
- Discord: https://discord.gg/evolution-api

**Google Cloud Issues:**
- Support: https://cloud.google.com/support
- Docs: https://cloud.google.com/docs

**NEO Chat Issues:**
- Check: `COOLIFY_DEPLOYMENT.md` Step 10 (Troubleshooting)
- Review: `PROJECT_100_PERCENT_COMPLETE.md`

---

## ✨ Success Criteria

Your deployment is successful when:

✅ All 4 services are running (postgres, redis, evolution, neo-chat)  
✅ Health endpoint returns healthy status  
✅ SSL certificates are active (https works)  
✅ WhatsApp is connected and responding  
✅ Bot responds to text messages within 10 seconds  
✅ File uploads work correctly  
✅ Voice messages are transcribed  
✅ No errors in logs  
✅ Monitoring is configured  
✅ Backups are scheduled  

---

## 🎉 Deployment Complete!

Once all items are checked:

✅ **Your NEO Chat bot is live!**  
✅ **Users can interact via WhatsApp**  
✅ **All features are working**  
✅ **System is monitored and backed up**  

**Next Steps:**
1. Monitor usage for first week
2. Collect user feedback
3. Plan for feature enhancements
4. Scale if needed

---

**Deployment Date:** _______________  
**Deployed By:** _______________  
**Production URL:** https://neochat.neoo.com.sa  
**Status:** ⬜ In Progress | ⬜ Complete  

**Notes:**
_______________________________________
_______________________________________
_______________________________________

---

**🚀 Happy Deploying!**
