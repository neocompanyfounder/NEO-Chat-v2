# Database Migration Script for Windows/PowerShell
# Runs SQL migrations against Supabase PostgreSQL

Write-Host "🔄 Running Database Migrations" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
$dockerRunning = docker ps 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check if Supabase container exists
$supabaseContainer = docker ps --filter "name=supabase-db" --format "{{.Names}}"
if (-not $supabaseContainer) {
    Write-Host "❌ Supabase database container not found." -ForegroundColor Red
    Write-Host "   Run: cd docker\supabase && docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Supabase database container found: $supabaseContainer" -ForegroundColor Green
Write-Host ""

# Migrations directory
$migrationsDir = "src\db\migrations"

if (-not (Test-Path $migrationsDir)) {
    Write-Host "❌ Migrations directory not found: $migrationsDir" -ForegroundColor Red
    exit 1
}

# Get all SQL files sorted
$migrations = Get-ChildItem -Path $migrationsDir -Filter "*.sql" | Sort-Object Name

if ($migrations.Count -eq 0) {
    Write-Host "⚠️  No migration files found in $migrationsDir" -ForegroundColor Yellow
    exit 0
}

Write-Host "Found $($migrations.Count) migration(s)" -ForegroundColor Cyan
Write-Host ""

# Run each migration
$successCount = 0
$failCount = 0

foreach ($migration in $migrations) {
    Write-Host "Running: $($migration.Name)" -ForegroundColor Cyan
    
    # Read the SQL file content
    $sqlContent = Get-Content -Path $migration.FullName -Raw
    
    # Execute SQL using docker exec with stdin
    $result = $sqlContent | docker exec -i $supabaseContainer psql -U postgres -d postgres 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Success" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host "  ❌ Failed" -ForegroundColor Red
        Write-Host "  Error: $result" -ForegroundColor Red
        $failCount++
    }
    Write-Host ""
}

# Summary
Write-Host "==============================" -ForegroundColor Cyan
Write-Host "Migration Summary:" -ForegroundColor Cyan
Write-Host "  Success: $successCount" -ForegroundColor Green

if ($failCount -gt 0) {
    Write-Host "  Failed:  $failCount" -ForegroundColor Red
} else {
    Write-Host "  Failed:  $failCount" -ForegroundColor Green
}

Write-Host ""

if ($failCount -eq 0) {
    Write-Host "All migrations completed successfully!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Some migrations failed. Please check the errors above." -ForegroundColor Red
    exit 1
}
