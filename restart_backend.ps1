# Restart Backend Server Script

Write-Host "🔄 Restarting Backend Server..." -ForegroundColor Cyan

# Step 1: Kill existing Python processes
Write-Host "`n📍 Step 1: Stopping existing backend server..." -ForegroundColor Yellow
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*agenticRag*"}

if ($pythonProcesses) {
    Write-Host "   Found $($pythonProcesses.Count) Python process(es) to stop" -ForegroundColor Gray
    $pythonProcesses | ForEach-Object {
        Write-Host "   Stopping process $($_.Id)..." -ForegroundColor Gray
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
    Write-Host "   ✅ Stopped existing processes" -ForegroundColor Green
} else {
    Write-Host "   ℹ️  No existing backend process found" -ForegroundColor Gray
}

# Step 2: Stay in project root (don't navigate to backend)
Write-Host "`n📍 Step 2: Checking project structure..." -ForegroundColor Yellow
$projectRoot = $PSScriptRoot
$backendPath = Join-Path $projectRoot "backend"
if (Test-Path $backendPath) {
    Write-Host "   ✅ Backend directory found: $backendPath" -ForegroundColor Green
} else {
    Write-Host "   ❌ Backend directory not found!" -ForegroundColor Red
    exit 1
}

# Step 3: Check if virtual environment exists
Write-Host "`n📍 Step 3: Checking virtual environment..." -ForegroundColor Yellow
$venvPath = Join-Path $backendPath "venv"
if (Test-Path $venvPath) {
    Write-Host "   ✅ Virtual environment found" -ForegroundColor Green
    $pythonExe = Join-Path $venvPath "Scripts\python.exe"
} else {
    Write-Host "   ℹ️  No virtual environment, using system Python" -ForegroundColor Gray
    $pythonExe = "python"
}

# Ensure we're in the project root
Set-Location $projectRoot
Write-Host "   ✅ Working directory: $projectRoot" -ForegroundColor Green

# Step 4: Start the server
Write-Host "`n📍 Step 4: Starting backend server..." -ForegroundColor Yellow
Write-Host "   Command: $pythonExe -m uvicorn backend.main:app --reload --port 8000" -ForegroundColor Gray
Write-Host "`n🚀 Server starting..." -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor Green
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "`n⚠️  Press Ctrl+C to stop the server`n" -ForegroundColor Yellow

# Start the server
& $pythonExe -m uvicorn backend.main:app --reload --port 8000
