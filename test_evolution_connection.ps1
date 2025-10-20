# Test Evolution API Connection
$envFile = "neo-chat/.env"

# Read .env file
$envVars = @{}
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
        $envVars[$matches[1].Trim()] = $matches[2].Trim()
    }
}

$evolutionUrl = $envVars['EVOLUTION_API_URL']
$evolutionKey = $envVars['EVOLUTION_API_KEY']
$instanceName = $envVars['EVOLUTION_INSTANCE_NAME']

Write-Host "Testing Evolution API Connection..." -ForegroundColor Cyan
Write-Host "URL: $evolutionUrl" -ForegroundColor Yellow
Write-Host ""

# Test 1: Check if Evolution API is reachable
Write-Host "1. Testing Evolution API endpoint..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$evolutionUrl/instance/fetchInstances" -Method GET -Headers @{
        "apikey" = $evolutionKey
    } -ErrorAction Stop
    Write-Host "   SUCCESS - Evolution API is reachable!" -ForegroundColor Green
    Write-Host "   Instances found: $($response.Count)" -ForegroundColor Green
} catch {
    Write-Host "   FAILED - Cannot reach Evolution API" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 2: Check specific instance
Write-Host "2. Testing instance: $instanceName..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$evolutionUrl/instance/connectionState/$instanceName" -Method GET -Headers @{
        "apikey" = $evolutionKey
    } -ErrorAction Stop
    Write-Host "   SUCCESS - Instance is accessible!" -ForegroundColor Green
    Write-Host "   State: $($response.state)" -ForegroundColor Green
} catch {
    Write-Host "   FAILED - Cannot access instance" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Configure webhook in Evolution API to point to your NEO Chat server" -ForegroundColor White
Write-Host "2. Use ngrok or similar to expose localhost:8000 if testing locally" -ForegroundColor White
Write-Host "3. Webhook URL should be: http://your-server:8000/webhook/evolution" -ForegroundColor White
