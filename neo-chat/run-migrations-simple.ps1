# Simple Database Migration Script
Write-Host "Running Database Migrations..." -ForegroundColor Cyan

# Check Supabase container
$container = docker ps --filter "name=supabase-db" --format "{{.Names}}"
if (-not $container) {
    Write-Host "ERROR: Supabase database not running" -ForegroundColor Red
    Write-Host "Start it with: cd docker\supabase; docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host "Found container: $container" -ForegroundColor Green

# Run migration 001
Write-Host "Running 001_initial_schema.sql..." -ForegroundColor Cyan
$sql1 = Get-Content "src\db\migrations\001_initial_schema.sql" -Raw
$result1 = $sql1 | docker exec -i $container psql -U postgres -d postgres 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS: 001_initial_schema.sql" -ForegroundColor Green
} else {
    Write-Host "FAILED: 001_initial_schema.sql" -ForegroundColor Red
    Write-Host $result1
}

# Run migration 002
Write-Host "Running 002_create_indexes.sql..." -ForegroundColor Cyan
$sql2 = Get-Content "src\db\migrations\002_create_indexes.sql" -Raw
$result2 = $sql2 | docker exec -i $container psql -U postgres -d postgres 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS: 002_create_indexes.sql" -ForegroundColor Green
} else {
    Write-Host "FAILED: 002_create_indexes.sql" -ForegroundColor Red
    Write-Host $result2
}

Write-Host "Migrations complete!" -ForegroundColor Green
