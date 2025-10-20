# Evolution API Webhook Setup Guide

## Your Setup
- **Evolution API**: http://eapi.neoo.com.sa:8080
- **NEO Chat Local**: http://localhost:8000
- **Webhook Endpoint**: /webhook/evolution

## Option 1: Using ngrok (Recommended for Testing)

1. Download ngrok: https://ngrok.com/download
2. Run ngrok to expose your local server:
   ```bash
   ngrok http 8000
   ```
3. Copy the ngrok URL (e.g., `https://abc123.ngrok.io`)
4. Configure Evolution API webhook to: `https://abc123.ngrok.io/webhook/evolution`

## Option 2: Deploy to a Server with Public IP

If you have a server with a public IP, deploy there and use:
```
http://your-server-ip:8000/webhook/evolution
```

## Configure Evolution API Webhook

### Using Evolution API Dashboard:
1. Go to http://eapi.neoo.com.sa:8080
2. Navigate to your instance settings
3. Set webhook URL to your NEO Chat endpoint
4. Enable webhook events for: `messages.upsert`

### Using Evolution API REST:
```bash
curl -X POST http://eapi.neoo.com.sa:8080/instance/webhook \
  -H "apikey: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook": {
      "url": "YOUR_NEOCHAT_WEBHOOK_URL/webhook/evolution",
      "enabled": true,
      "events": ["messages.upsert"]
    }
  }'
```

## Test the Webhook

Once configured, send a WhatsApp message from +966556265604 and check:
```bash
docker logs neo-chat-app --tail 50
```

You should see:
- `POST /webhook/evolution` - Webhook received
- `Webhook event received` - Event processed
- `Gemini response generated` - AI response created
- `WhatsApp text message sent` - Response sent back
