# Evolution API Setup Guide

Evolution API is required for WhatsApp integration in NEO Chat.

## Option 1: Docker Setup (Recommended)

### Quick Start

```bash
# Create a directory for Evolution API
mkdir evolution-api
cd evolution-api

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  evolution-api:
    image: atendai/evolution-api:latest
    container_name: evolution-api
    ports:
      - "8080:8080"
    environment:
      # Server Configuration
      - SERVER_URL=http://localhost:8080
      - SERVER_PORT=8080
      
      # Authentication
      - AUTHENTICATION_API_KEY=your-secure-api-key-here-change-this
      
      # Database (optional - uses in-memory by default)
      - DATABASE_ENABLED=false
      
      # Webhooks
      - WEBHOOK_GLOBAL_ENABLED=true
      - WEBHOOK_GLOBAL_URL=http://host.docker.internal:8000/api/webhook
      
      # WhatsApp Settings
      - QRCODE_LIMIT=30
      - QRCODE_COLOR=#198754
      
    volumes:
      - evolution_instances:/evolution/instances
      - evolution_store:/evolution/store
    restart: unless-stopped

volumes:
  evolution_instances:
  evolution_store:
EOF

# Start Evolution API
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Generate Secure API Key

```bash
# Generate a random API key
openssl rand -hex 32
# Example output: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
```

### Update Your .env File

After starting Evolution API:
1. Copy the API key you generated
2. Update your NEO Chat `.env` file:

```bash
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
EVOLUTION_INSTANCE_NAME=neo-chat
```

---

## Option 2: Cloud Deployment

### Deploy to Railway

1. Go to [Railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub"
3. Use repository: `EvolutionAPI/evolution-api`
4. Add environment variables:
   - `AUTHENTICATION_API_KEY`: Your secure key
   - `SERVER_URL`: Your Railway URL (e.g., `https://your-app.railway.app`)
5. Deploy and note your URL

### Deploy to Render

1. Go to [Render.com](https://render.com)
2. New Web Service → Connect Evolution API repository
3. Set environment variables (same as above)
4. Deploy

---

## Step 2: Create WhatsApp Instance

Once Evolution API is running:

### Using cURL

```bash
# Create instance
curl -X POST http://localhost:8080/instance/create \
  -H "apikey: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "instanceName": "neo-chat",
    "qrcode": true,
    "integration": "WHATSAPP-BAILEYS"
  }'
```

### Using Postman/Insomnia

**POST** `http://localhost:8080/instance/create`

**Headers:**
- `apikey`: your-api-key-here
- `Content-Type`: application/json

**Body:**
```json
{
  "instanceName": "neo-chat",
  "qrcode": true,
  "integration": "WHATSAPP-BAILEYS"
}
```

---

## Step 3: Connect WhatsApp

### Get QR Code

```bash
# Get QR code
curl -X GET http://localhost:8080/instance/connect/neo-chat \
  -H "apikey: your-api-key-here"
```

Response will include:
```json
{
  "base64": "data:image/png;base64,iVBORw0KGgoAAAANS...",
  "code": "1@abc123...",
  "pairingCode": "ABCD-1234"
}
```

### Scan QR Code

1. Open WhatsApp on your phone
2. Go to **Settings** → **Linked Devices**
3. Tap **Link a Device**
4. Scan the QR code from the response
5. Wait for connection confirmation

**OR use Pairing Code:**
1. Open WhatsApp on your phone
2. Go to **Settings** → **Linked Devices**
3. Tap **Link a Device**
4. Tap **Link with phone number instead**
5. Enter the pairing code (e.g., `ABCD-1234`)

---

## Step 4: Verify Connection

```bash
# Check instance status
curl -X GET http://localhost:8080/instance/connectionState/neo-chat \
  -H "apikey: your-api-key-here"
```

Expected response:
```json
{
  "instance": {
    "instanceName": "neo-chat",
    "status": "open"
  },
  "state": "open"
}
```

---

## Step 5: Set Webhook

```bash
# Configure webhook to point to NEO Chat
curl -X POST http://localhost:8080/webhook/set/neo-chat \
  -H "apikey: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://localhost:8000/api/webhook",
    "webhook_by_events": false,
    "webhook_base64": false,
    "events": [
      "MESSAGES_UPSERT",
      "MESSAGES_UPDATE",
      "CONNECTION_UPDATE"
    ]
  }'
```

---

## Testing

### Send Test Message

```bash
# Send a test message
curl -X POST http://localhost:8080/message/sendText/neo-chat \
  -H "apikey: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "number": "1234567890",
    "text": "Hello from NEO Chat!"
  }'
```

---

## Troubleshooting

### QR Code Not Appearing
- Check Evolution API logs: `docker-compose logs -f`
- Ensure port 8080 is not in use
- Try restarting: `docker-compose restart`

### Connection Keeps Dropping
- Check your internet connection
- Ensure WhatsApp is not logged in elsewhere
- Try recreating the instance

### Webhook Not Receiving Messages
- Verify NEO Chat is running on port 8000
- Check webhook URL is correct
- Use ngrok for local testing: `ngrok http 8000`

### Instance Not Found
- List all instances: `curl -X GET http://localhost:8080/instance/fetchInstances -H "apikey: your-key"`
- Recreate if needed

---

## Production Considerations

### Security
- Use strong API keys (32+ characters)
- Enable HTTPS for production
- Use environment variables for secrets
- Implement rate limiting

### Scaling
- Use PostgreSQL for database (set `DATABASE_ENABLED=true`)
- Deploy behind a reverse proxy (nginx)
- Use Redis for session management
- Monitor with health checks

### Backup
```bash
# Backup instances
docker cp evolution-api:/evolution/instances ./backup/

# Restore
docker cp ./backup/instances evolution-api:/evolution/
```

---

## Useful Commands

```bash
# List all instances
curl -X GET http://localhost:8080/instance/fetchInstances \
  -H "apikey: your-key"

# Delete instance
curl -X DELETE http://localhost:8080/instance/delete/neo-chat \
  -H "apikey: your-key"

# Logout WhatsApp
curl -X DELETE http://localhost:8080/instance/logout/neo-chat \
  -H "apikey: your-key"

# Restart instance
curl -X PUT http://localhost:8080/instance/restart/neo-chat \
  -H "apikey: your-key"
```

---

## Next Steps

After Evolution API is set up:
1. ✅ Update `.env` with your Evolution API URL and key
2. ✅ Start NEO Chat: `uvicorn src.api.main:app --reload`
3. ✅ Send a WhatsApp message to your connected number
4. ✅ Verify NEO Chat receives and responds

---

## Resources

- [Evolution API Documentation](https://doc.evolution-api.com)
- [Evolution API GitHub](https://github.com/EvolutionAPI/evolution-api)
- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)

---

**Need Help?** Check Evolution API logs or NEO Chat logs for detailed error messages.
