@echo off
echo Starting ngrok tunnel to expose localhost:8000...
echo.
echo After ngrok starts, copy the HTTPS URL (e.g., https://abc123.ngrok.io)
echo Then configure Evolution API webhook to: https://YOUR-NGROK-URL/webhook/evolution
echo.
pause
ngrok http 8000
