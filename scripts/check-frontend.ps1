# Frontend check before push (same as CI)
# Usage: .\scripts\check-frontend.ps1

$ErrorActionPreference = "Stop"
$frontend = Join-Path $PSScriptRoot ".." "frontend"

Push-Location $frontend
try {
    Write-Host "Running ESLint..." -ForegroundColor Cyan
    npm run lint
    if ($LASTEXITCODE -ne 0) { exit 1 }
    Write-Host "Running TypeScript check..." -ForegroundColor Cyan
    npx tsc --noEmit
    if ($LASTEXITCODE -ne 0) { exit 1 }
    Write-Host "Frontend check passed" -ForegroundColor Green
} finally {
    Pop-Location
}
