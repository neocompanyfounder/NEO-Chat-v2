@echo off
REM Evolution API Setup Script for Windows
REM This script creates the docker-compose.yml and starts Evolution API

echo ========================================
echo Evolution API Setup for NEO Chat
echo ========================================
echo.

REM Create evolution-api directory
if not exist "evolution-api" mkdir evolution-api
cd evolution-api

REM Create docker-compose.yml
echo Creating docker-compose.yml...
(
echo version: '3.8'
echo.
echo services:
echo   evolution-api:
echo     image: atendai/evolution-api:latest
echo     container_name: evolution-api
echo     ports:
echo       - "8080:8080"
echo     environment:
echo       # Server Configuration
echo       - SERVER_URL=http://localhost:8080
echo       - SERVER_PORT=8080
echo.      
echo       # Authentication - IMPORTANT: Use the key from .env.example
echo       - AUTHENTICATION_API_KEY=f8e7d6c5b4a3928170695847362514039281706958473625140392817069584736
echo.      
echo       # Database (optional - uses in-memory by default^)
echo       - DATABASE_ENABLED=false
echo.      
echo       # Webhooks
echo       - WEBHOOK_GLOBAL_ENABLED=true
echo       - WEBHOOK_GLOBAL_URL=http://host.docker.internal:8000/api/webhook
echo.      
echo       # WhatsApp Settings
echo       - QRCODE_LIMIT=30
echo       - QRCODE_COLOR=#198754
echo.      
echo     volumes:
echo       - evolution_instances:/evolution/instances
echo       - evolution_store:/evolution/store
echo     restart: unless-stopped
echo.
echo volumes:
echo   evolution_instances:
echo   evolution_store:
) > docker-compose.yml

echo ✓ docker-compose.yml created
echo.

REM Start Docker containers
echo Starting Evolution API...
docker-compose up -d

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo ✓ Evolution API is starting!
    echo ========================================
    echo.
    echo Evolution API URL: http://localhost:8080
    echo API Key: f8e7d6c5b4a3928170695847362514039281706958473625140392817069584736
    echo.
    echo Waiting 10 seconds for startup...
    timeout /t 10 /nobreak >nul
    echo.
    echo ========================================
    echo Next Steps:
    echo ========================================
    echo 1. Check logs: docker logs evolution-api
    echo 2. Create instance: See SETUP_EVOLUTION_API.md
    echo 3. Connect WhatsApp: Scan QR code
    echo 4. Update neo-chat/.env with Evolution API details
    echo.
    echo Your .env.example is already configured!
    echo Just copy it: cd ../neo-chat ^&^& copy .env.example .env
    echo.
) else (
    echo.
    echo ✗ Failed to start Evolution API
    echo Please check Docker is running and try again
    echo.
)

cd ..
pause
