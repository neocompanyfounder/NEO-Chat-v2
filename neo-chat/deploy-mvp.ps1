# NEO Chat MVP Deployment Script
# This script sets up and starts all required services

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NEO Chat MVP Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Start Supabase
Write-Host "[1/5] Starting Supabase..." -ForegroundColor Yellow
Push-Location "docker\supabase"
docker-compose up -d
if ($LASTEXITCODE -eq 0) {
    Write-Host "  SUCCESS: Supabase started" -ForegroundColor Green
} else {
    Write-Host "  FAILED: Could not start Supabase" -ForegroundColor Red
    Pop-Location
    exit 1
}
Pop-Location
Write-Host ""

# Wait for Supabase to be ready
Write-Host "  Waiting for Supabase to be ready..." -ForegroundColor Cyan
Start-Sleep -Seconds 10
Write-Host ""

# Step 2: Run Migrations
Write-Host "[2/5] Running database migrations..." -ForegroundColor Yellow
powershell -ExecutionPolicy Bypass -File run-migrations-simple.ps1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  SUCCESS: Migrations completed" -ForegroundColor Green
} else {
    Write-Host "  FAILED: Migrations failed" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 3: Setup Evolution API
Write-Host "[3/5] Setting up Evolution API..." -ForegroundColor Yellow
Write-Host "  Please run setup-evolution-api.bat in a separate terminal" -ForegroundColor Cyan
Write-Host "  Press Enter when Evolution API is running..." -ForegroundColor Cyan
Read-Host
Write-Host ""

# Step 4: Start NEO Chat
Write-Host "[4/5] Starting NEO Chat server..." -ForegroundColor Yellow
Write-Host "  Server will start in a new window..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload"
Start-Sleep -Seconds 5
Write-Host ""

# Step 5: Verify Everything
Write-Host "[5/5] Verifying services..." -ForegroundColor Yellow
Write-Host ""

# Check Supabase
Write-Host "Checking Supabase..." -ForegroundColor Cyan
$supabase = docker ps --filter "name=supabase" --format "{{.Names}}"
if ($supabase) {
    Write-Host "  RUNNING: $($supabase -join ', ')" -ForegroundColor Green
} else {
    Write-Host "  NOT RUNNING" -ForegroundColor Red
}
Write-Host ""

# Check Evolution API
Write-Host "Checking Evolution API..." -ForegroundColor Cyan
$evolution = docker ps --filter "name=evolution" --format "{{.Names}}"
if ($evolution) {
    Write-Host "  RUNNING: $evolution" -ForegroundColor Green
} else {
    Write-Host "  NOT RUNNING (run setup-evolution-api.bat)" -ForegroundColor Yellow
}
Write-Host ""

# Check NEO Chat
Write-Host "Checking NEO Chat..." -ForegroundColor Cyan
Start-Sleep -Seconds 3
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "  RUNNING: Health check passed" -ForegroundColor Green
    Write-Host "  Response: $($response.Content)" -ForegroundColor Gray
} catch {
    Write-Host "  NOT RESPONDING (check the server window)" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deployment Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services:" -ForegroundColor White
Write-Host "  Supabase:      http://localhost:8000 (Kong API Gateway)" -ForegroundColor Gray
Write-Host "  NEO Chat:      http://localhost:8000" -ForegroundColor Gray
Write-Host "  Evolution API: http://localhost:8080" -ForegroundColor Gray
Write-Host ""
Write-Host "API Documentation:" -ForegroundColor White
Write-Host "  http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor White
Write-Host "  1. If Evolution API is not running, run: setup-evolution-api.bat" -ForegroundColor Gray
Write-Host "  2. Connect WhatsApp (see SETUP_EVOLUTION_API.md)" -ForegroundColor Gray
Write-Host "  3. Test by sending a WhatsApp message" -ForegroundColor Gray
Write-Host ""
Write-Host "Deployment complete!" -ForegroundColor Green
