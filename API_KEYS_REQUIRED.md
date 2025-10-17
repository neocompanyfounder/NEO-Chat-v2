# 🔑 NEO Chat - Required API Keys & Setup

**Complete guide to get all required API keys for deployment**

---

## 📋 Summary: What You Need

| Service | Required? | Cost | Time to Setup |
|---------|-----------|------|---------------|
| **Google Cloud API** | ✅ Yes | Free tier available | 5 minutes |
| **Database Passwords** | ✅ Yes | Free (self-generated) | 1 minute |
| **Evolution API Key** | ✅ Yes | Free (self-generated) | 1 minute |
| **Domain** | ✅ Yes | ~$10-20/year | Already have |
| **Hostinger VPS** | ✅ Yes | ~$5-20/month | Already have |

**Total Setup Time: ~10 minutes**  
**Monthly Cost: ~$5-20 (VPS only, Google free tier)**

---

## 1️⃣ Google Cloud API Key (REQUIRED)

### What It's For:
- **Gemini AI** - Conversational AI responses
- **Cloud Vision** - OCR for image text extraction
- **Cloud Speech-to-Text** - Voice message transcription

### How to Get It:

**Step 1: Create Google Cloud Account**
1. Go to: https://console.cloud.google.com
2. Sign in with your Google account
3. Accept terms and conditions

**Step 2: Create New Project**
1. Click project dropdown (top left)
2. Click **"New Project"**
3. Name: `NEO Chat`
4. Click **"Create"**

**Step 3: Enable Required APIs**

Enable these 3 APIs:

**A. Generative Language API (Gemini)**
1. Go to: https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com
2. Select your project
3. Click **"Enable"**

**B. Cloud Vision API**
1. Go to: https://console.cloud.google.com/apis/library/vision.googleapis.com
2. Click **"Enable"**

**C. Cloud Speech-to-Text API**
1. Go to: https://console.cloud.google.com/apis/library/speech.googleapis.com
2. Click **"Enable"**

**Step 4: Create API Key**
1. Go to: https://console.cloud.google.com/apis/credentials
2. Click **"+ Create Credentials"**
3. Select **"API Key"**
4. Copy the API key (starts with `AIza...`)
5. Click **"Restrict Key"** (recommended)
6. Under "API restrictions", select:
   - Generative Language API
   - Cloud Vision API
   - Cloud Speech-to-Text API
7. Click **"Save"**

**Your API Key:**
```
GOOGLE_API_KEY=AIzaSy...your_key_here
```

### 💰 Pricing (Free Tier):

**Gemini API:**
- Free: 15 requests/minute
- Free: 1,500 requests/day
- Paid: $0.00025 per 1K characters

**Cloud Vision API:**
- Free: 1,000 units/month
- Paid: $1.50 per 1,000 units

**Cloud Speech-to-Text API:**
- Free: 60 minutes/month
- Paid: $0.006 per 15 seconds

**Estimated Monthly Cost:**
- Light usage (< 100 users): **FREE**
- Medium usage (100-500 users): **$10-50**
- Heavy usage (500+ users): **$50-200**

---

## 2️⃣ Database Password (REQUIRED)

### What It's For:
- PostgreSQL database authentication
- Stores all user data, conversations, documents

### How to Generate:

**Option A: Linux/Mac**
```bash
openssl rand -base64 32
```

**Option B: Windows PowerShell**
```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
```

**Option C: Online Generator**
1. Go to: https://www.random.org/passwords/
2. Length: 32
3. Characters: All
4. Generate

**Example Output:**
```
POSTGRES_PASSWORD=x7k9m2p4r8t1w5y3q6s0v2n8b4c7f1j5
```

**⚠️ Important:**
- Use at least 32 characters
- Mix uppercase, lowercase, numbers
- Save securely (password manager)
- Never commit to Git

---

## 3️⃣ Redis Password (REQUIRED)

### What It's For:
- Caching frequently accessed data
- Rate limiting API requests
- Session management

### How to Generate:

Same as database password - generate another secure 32+ character password.

```bash
# Linux/Mac
openssl rand -base64 32

# Windows PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
```

**Example Output:**
```
REDIS_PASSWORD=p4r8t1w5y3q6s0v2n8b4c7f1j5x7k9m2
```

---

## 4️⃣ Evolution API Key (REQUIRED)

### What It's For:
- Authenticating requests to Evolution API
- WhatsApp integration security

### How to Generate:

Generate a secure random string (32+ characters).

```bash
# Linux/Mac
openssl rand -hex 32

# Windows PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
```

**Example Output:**
```
EVOLUTION_API_KEY=evo_k3m7p2r9t4w8y1q5s3v6n0b8c2f7j4
```

**⚠️ Important:**
- This is YOUR custom key (not from a service)
- You create it, Evolution API uses it
- Keep it secret and secure

---

## 5️⃣ Domain Configuration (REQUIRED)

### What You Have:
- Domain: `neoo.com.sa`
- Hostinger VPS with IP address

### DNS Records to Add:

**For NEO Chat Application:**
```
Type: A
Name: neochat
Value: YOUR_HOSTINGER_VPS_IP
TTL: 3600
```

**For Evolution API:**
```
Type: A
Name: evolution
Value: YOUR_HOSTINGER_VPS_IP
TTL: 3600
```

### How to Add DNS Records:

1. Login to your domain registrar
2. Go to DNS management
3. Add the A records above
4. Wait 5-10 minutes for propagation

### Verify DNS:
```bash
# Check if DNS is working
nslookup neochat.neoo.com.sa
nslookup evolution.neoo.com.sa
```

---

## 📝 Complete Environment Variables

After getting all keys, your environment variables should look like:

```bash
# ===== Google Cloud API =====
GOOGLE_API_KEY=AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ===== Database =====
POSTGRES_DB=neochat
POSTGRES_USER=neochat_user
POSTGRES_PASSWORD=x7k9m2p4r8t1w5y3q6s0v2n8b4c7f1j5

# ===== Redis =====
REDIS_PASSWORD=p4r8t1w5y3q6s0v2n8b4c7f1j5x7k9m2

# ===== Evolution API =====
EVOLUTION_API_KEY=evo_k3m7p2r9t4w8y1q5s3v6n0b8c2f7j4
EVOLUTION_SERVER_URL=https://evolution.neoo.com.sa
EVOLUTION_INSTANCE_NAME=neochat

# ===== Application =====
ENVIRONMENT=production
LOG_LEVEL=INFO
```

---

## ✅ Pre-Deployment Checklist

Before deploying, verify you have:

- [ ] **Google Cloud API Key** - Copied and saved
- [ ] **Google APIs Enabled** - Gemini, Vision, Speech
- [ ] **Database Password** - Generated (32+ chars)
- [ ] **Redis Password** - Generated (32+ chars)
- [ ] **Evolution API Key** - Generated (32+ chars)
- [ ] **DNS Records Added** - neochat & evolution subdomains
- [ ] **DNS Propagated** - Can resolve both domains
- [ ] **Coolify Access** - Can login to dashboard
- [ ] **Passwords Saved** - In secure password manager

---

## 🔒 Security Best Practices

### DO:
✅ Use password manager (1Password, Bitwarden, LastPass)  
✅ Generate strong passwords (32+ characters)  
✅ Rotate passwords every 90 days  
✅ Use different passwords for each service  
✅ Enable 2FA on Google Cloud account  
✅ Restrict API keys to specific APIs  
✅ Monitor API usage regularly  

### DON'T:
❌ Commit passwords to Git  
❌ Share API keys publicly  
❌ Use simple/short passwords  
❌ Reuse passwords across services  
❌ Store passwords in plain text files  
❌ Email passwords to yourself  

---

## 💰 Cost Breakdown

### One-Time Costs:
- Domain: ~$10-20/year (already have)
- Setup time: Free

### Monthly Costs:
- **Hostinger VPS**: $5-20/month (already have)
- **Google Cloud APIs**: 
  - Free tier: $0
  - Light usage: $0-10
  - Medium usage: $10-50
  - Heavy usage: $50-200
- **Evolution API**: Free (self-hosted)
- **PostgreSQL**: Free (self-hosted)
- **Redis**: Free (self-hosted)

**Total Monthly: $5-220** (depending on usage)  
**Most users: $5-15/month** (VPS + free tier APIs)

---

## 🆘 Troubleshooting

### Google API Key Not Working

**Check:**
1. API key is correct (starts with `AIza`)
2. All 3 APIs are enabled
3. API key restrictions allow the APIs
4. Billing is enabled (even for free tier)

**Test:**
```bash
curl "https://generativelanguage.googleapis.com/v1/models?key=YOUR_API_KEY"
```

### Can't Generate Passwords

**Use Online Generator:**
1. https://www.random.org/passwords/
2. https://passwordsgenerator.net/
3. https://bitwarden.com/password-generator/

**Settings:**
- Length: 32
- Include: Uppercase, lowercase, numbers
- Exclude: Special characters (for compatibility)

### DNS Not Resolving

**Wait:**
- DNS propagation takes 5-60 minutes
- Check with: `nslookup neochat.neoo.com.sa`

**Verify:**
- A record points to correct IP
- TTL is set (3600 recommended)
- No typos in subdomain name

---

## 📞 Need Help?

### Google Cloud Support:
- Documentation: https://cloud.google.com/docs
- Support: https://cloud.google.com/support
- Community: https://stackoverflow.com/questions/tagged/google-cloud-platform

### Evolution API Support:
- Documentation: https://doc.evolution-api.com
- GitHub: https://github.com/EvolutionAPI/evolution-api
- Discord: https://discord.gg/evolution-api

### Coolify Support:
- Documentation: https://coolify.io/docs
- Discord: https://discord.gg/coolify
- GitHub: https://github.com/coollabsio/coolify

---

## 🎯 Quick Reference

### Generate All Passwords at Once:

**Linux/Mac:**
```bash
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)"
echo "REDIS_PASSWORD=$(openssl rand -base64 32)"
echo "EVOLUTION_API_KEY=$(openssl rand -hex 32)"
```

**Windows PowerShell:**
```powershell
Write-Host "POSTGRES_PASSWORD=$(-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_}))"
Write-Host "REDIS_PASSWORD=$(-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_}))"
Write-Host "EVOLUTION_API_KEY=$(-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_}))"
```

### Save to Password Manager:

Create entry: **"NEO Chat Production"**

```
Service: NEO Chat
URL: https://neochat.neoo.com.sa

GOOGLE_API_KEY: AIzaSy...
POSTGRES_PASSWORD: x7k9m2...
REDIS_PASSWORD: p4r8t1...
EVOLUTION_API_KEY: evo_k3...

Notes: Production deployment on Hostinger
Created: 2025-01-17
```

---

**✅ Once you have all these keys, you're ready to deploy!**

**Next Step:** Follow `COOLIFY_QUICK_SETUP.md` for deployment instructions.
