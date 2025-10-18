# Verify NEO Chat Deployment
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NEO Chat Deployment Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# Check Supabase
Write-Host "[1/3] Checking Supabase..." -ForegroundColor Yellow
$supabase = docker ps --filter "name=supabase-db" --filter "status=running" --format "{{.Names}}"
if ($supabase) {
    Write-Host "  SUCCESS: Supabase is running" -ForegroundColor Green
    docker ps --filter "name=supabase" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
} else {
    Write-Host "  FAILED: Supabase is not running" -ForegroundColor Red
    Write-Host "  Fix: cd docker\supabase && docker-compose up -d" -ForegroundColor Yellow
    $allGood = $false
}
Write-Host ""

# Check Evolution API
Write-Host "[2/3] Checking Evolution API..." -ForegroundColor Yellow
$evolution = docker ps --filter "name=evolution-api" --filter "status=running" --format "{{.Names}}"
if ($evolution) {
    Write-Host "  SUCCESS: Evolution API is running" -ForegroundColor Green
    docker ps --filter "name=evolution" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
} else {
    Write-Host "  WARNING: Evolution API is not running" -ForegroundColor Yellow
    Write-Host "  Fix: Run setup-evolution-api.bat" -ForegroundColor Yellow
}
Write-Host ""

# Check NEO Chat
Write-Host "[3/3] Checking NEO Chat API..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 5
    Write-Host "  SUCCESS: NEO Chat is running" -ForegroundColor Green
    Write-Host "  Status: $($response.status)" -ForegroundColor Gray
    Write-Host "  Version: $($response.version)" -ForegroundColor Gray
    Write-Host "  Database: $($response.database)" -ForegroundColor Gray
} catch {
    Write-Host "  FAILED: NEO Chat is not responding" -ForegroundColor Red
    Write-Host "  Fix: uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor Yellow
    $allGood = $false
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
if ($allGood) {
    Write-Host "  ALL SYSTEMS OPERATIONAL" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "You can access:" -ForegroundColor White
    Write-Host "  NEO Chat API:  http://localhost:8000" -ForegroundColor Gray
    Write-Host "  API Docs:      http://localhost:8000/docs" -ForegroundColor Gray
    Write-Host "  Health Check:  http://localhost:8000/health" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "  SOME SERVICES ARE DOWN" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Please fix the issues above and run this script again." -ForegroundColor Yellow
    Write-Host ""
}
