# Starts the SDLC Agentic AI backend locally on Windows (PowerShell).
# Usage:  ./start.ps1            (rebuilds web/dist if it can, then serves)
#         ./start.ps1 -NoWeb     (skip the web build; serve existing UI)
param([switch]$NoWeb)
$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$backend = Join-Path $root "backend"
$venv = Join-Path $root ".venv"

if (-not (Test-Path $venv)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv $venv
}

$python = Join-Path $venv "Scripts\python.exe"

Write-Host "Installing dependencies..." -ForegroundColor Cyan
& $python -m pip install --quiet --upgrade pip
& $python -m pip install --quiet -r (Join-Path $backend "requirements.txt")

if (-not (Test-Path (Join-Path $root ".env"))) {
    Write-Host "No .env found - copying .env.example (defaults to free mock mode)." -ForegroundColor Yellow
    Copy-Item (Join-Path $root ".env.example") (Join-Path $root ".env")
}

# Optionally refresh the built React UI so the server serves the latest web/dist.
# Only runs when web deps are already installed (no network install here -> no
# hang on locked-down networks). Skippable with -NoWeb; never fatal.
$web = Join-Path $root "web"
if (-not $NoWeb -and (Test-Path (Join-Path $web "node_modules")) -and (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "Building web UI (web/dist)..." -ForegroundColor Cyan
    Push-Location $web
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    npm run build 2>&1 | Out-Host
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    Pop-Location
    if ($code -ne 0) {
        Write-Host "Web build failed (exit $code) - serving existing web/dist or the zero-build UI." -ForegroundColor Yellow
    }
}

Write-Host "Starting server at http://localhost:8000 ..." -ForegroundColor Green
Push-Location $backend
try {
    & $python -m uvicorn app.main:app --reload --port 8000
} finally {
    Pop-Location
}

