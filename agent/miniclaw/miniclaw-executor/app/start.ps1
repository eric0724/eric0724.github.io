# Miniclaw Executor - PowerShell Startup Script
Set-Location -Path $PSScriptRoot
Write-Host "=== Miniclaw Executor Starting ===" -ForegroundColor Cyan

# Check Node.js
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Node.js not found. Please install Node.js first: https://nodejs.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

$nodeVersion = node --version
Write-Host "[OK] Node.js version: $nodeVersion" -ForegroundColor Green

# Install dependencies if needed
if (-not (Test-Path "node_modules")) {
    Write-Host "[INFO] Installing dependencies..." -ForegroundColor Yellow
    npm install
}

Write-Host "[START] Launching server... " -ForegroundColor Green -NoNewline
if (Test-Path "$PSScriptRoot\server.js") {
    Write-Host "server.js (full)" -ForegroundColor Green
    node server.js
} else {
    Write-Host "miniclaw-runner.js (light, server.js missing)" -ForegroundColor Yellow
    node miniclaw-runner.js
}
Read-Host "Press Enter to exit"
