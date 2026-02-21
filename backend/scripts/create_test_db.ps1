# Create contentfactory_test database for pytest
# Run from project root: .\backend\scripts\create_test_db.ps1
# Or from backend/: .\scripts\create_test_db.ps1
# Requires: .env in project root with POSTGRES_USER, POSTGRES_PASSWORD

$backendDir = Split-Path $PSScriptRoot -Parent
$projectRoot = Split-Path $backendDir -Parent

# Load .env from project root (or backend/)
$envFile = Join-Path $projectRoot ".env"
if (-not (Test-Path $envFile)) {
    $envFile = Join-Path $backendDir ".env"
}
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $val = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $val, "Process")
        }
    }
}

$user = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "admin" }
$pass = if ($env:POSTGRES_PASSWORD) { $env:POSTGRES_PASSWORD } else { "contentfactory" }

# Prefer docker exec when postgres container is running
$containerName = "contentfactory-postgres"
$dockerRunning = docker ps -q -f "name=$containerName" 2>$null
if ($dockerRunning) {
    Write-Host "Creating contentfactory_test via docker exec..."
    docker exec $containerName psql -U $user -d postgres -c "CREATE DATABASE contentfactory_test;" 2>$null
} else {
    Write-Host "Creating contentfactory_test via local psql..."
    $env:PGPASSWORD = $pass
    & psql -h localhost -U $user -d postgres -c "CREATE DATABASE contentfactory_test;" 2>$null
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "Note: contentfactory_test may already exist. Run: docker compose run --rm -e TEST_DATABASE_URL=postgresql+asyncpg://$user`:$pass@postgres:5432/contentfactory_test backend pytest -v"
}
