# Backend Restart Script for Windows PowerShell
# This script stops all Python processes and provides instructions to restart

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "Backend Restart Script" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host ""

# Step 1: Stop Python processes
Write-Host "Step 1: Stopping Python processes..." -ForegroundColor Yellow
$pythonProcesses = Get-Process python* -ErrorAction SilentlyContinue

if ($pythonProcesses) {
    Write-Host "Found $($pythonProcesses.Count) Python process(es)" -ForegroundColor Cyan
    foreach ($proc in $pythonProcesses) {
        Write-Host "  Stopping PID $($proc.Id): $($proc.ProcessName)" -ForegroundColor Gray
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "✅ All Python processes stopped" -ForegroundColor Green
} else {
    Write-Host "ℹ️  No Python processes found" -ForegroundColor Gray
}

Write-Host ""

# Step 2: Verify ColPali installation
Write-Host "Step 2: Verifying ColPali installation..." -ForegroundColor Yellow
$colpaliCheck = python -c "from colpali_engine.models import ColPali; print('OK')" 2>&1

if ($colpaliCheck -match "OK") {
    Write-Host "✅ ColPali is installed and importable" -ForegroundColor Green
} else {
    Write-Host "❌ ColPali import failed!" -ForegroundColor Red
    Write-Host "Error: $colpaliCheck" -ForegroundColor Red
    Write-Host ""
    Write-Host "Run this to fix:" -ForegroundColor Yellow
    Write-Host "  python -m pip install colpali-engine --no-cache-dir" -ForegroundColor Cyan
    exit 1
}

Write-Host ""

# Step 3: Instructions
Write-Host "Step 3: Start backend" -ForegroundColor Yellow
Write-Host "Run these commands in a NEW terminal:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  cd backend" -ForegroundColor White
Write-Host "  uvicorn main:app --reload --port 8000" -ForegroundColor White
Write-Host ""

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "✅ Ready to restart backend!" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
