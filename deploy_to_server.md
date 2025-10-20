# Deploy NEO Chat to Server

## If deploying to the same server as Evolution API (eapi.neoo.com.sa)

### 1. Copy files to server
```bash
# From your local machine
scp -r neo-chat/ user@eapi.neoo.com.sa:/opt/neo-chat/
scp Dockerfile user@eapi.neoo.com.sa:/opt/neo-chat/
scp docker-compose.yml user@eapi.neoo.com.sa:/opt/neo-chat/
```

### 2. SSH into server
```bash
ssh user@eapi.neoo.com.sa
```

### 3. Build and run on server
```bash
cd /opt/neo-chat
docker build -t neo-chat:latest -f Dockerfile .
docker run -d --name neo-chat-app -p 8000:8000 --env-file neo-chat/.env neo-chat:latest
```

### 4. Configure Evolution API webhook
Since both are on the same server:
```
Webhook URL: http://localhost:8000/webhook/evolution
# OR
Webhook URL: http://eapi.neoo.com.sa:8000/webhook/evolution
```

### 5. Test
```bash
# Check logs
docker logs neo-chat-app -f

# Send a WhatsApp message from +966556265604
```

## If deploying to a different server

### 1. Ensure port 8000 is open
```bash
# On your server
sudo ufw allow 8000
```

### 2. Get your server's public IP
```bash
curl ifconfig.me
```

### 3. Configure Evolution API webhook
```
Webhook URL: http://YOUR-SERVER-IP:8000/webhook/evolution
```

## Quick Test Without Deployment

Use the test_webhook.ps1 script to simulate a message:
```powershell
powershell -ExecutionPolicy Bypass -File test_webhook.ps1
```

This will show you that the app is working, even if Evolution API can't reach it yet.
