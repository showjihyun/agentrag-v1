# Restart Ollama with GPU

Write-Host "============================================================" -ForegroundColor Green
Write-Host "Restarting Ollama for GPU Usage" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green

# 1. Stop Ollama
Write-Host "`n[1] Stopping Ollama..." -ForegroundColor Yellow
try {
    Stop-Process -Name ollama -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "Ollama stopped" -ForegroundColor Green
} catch {
    Write-Host "Ollama was not running" -ForegroundColor Yellow
}

# 2. Check GPU
Write-Host "`n[2] Checking GPU..." -ForegroundColor Yellow
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

# 3. Set environment variables for GPU
Write-Host "`n[3] Setting GPU environment variables..." -ForegroundColor Yellow
$env:OLLAMA_GPU_LAYERS = "999"
$env:CUDA_VISIBLE_DEVICES = "0"
Write-Host "OLLAMA_GPU_LAYERS=999" -ForegroundColor Cyan
Write-Host "CUDA_VISIBLE_DEVICES=0" -ForegroundColor Cyan

# 4. Start Ollama
Write-Host "`n[4] Starting Ollama..." -ForegroundColor Yellow
Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden
Start-Sleep -Seconds 3

# 5. Verify Ollama is running
Write-Host "`n[5] Verifying Ollama..." -ForegroundColor Yellow
$ollamaProcess = Get-Process ollama -ErrorAction SilentlyContinue
if ($ollamaProcess) {
    Write-Host "Ollama is running (PID: $($ollamaProcess.Id))" -ForegroundColor Green
} else {
    Write-Host "Failed to start Ollama" -ForegroundColor Red
    exit 1
}

# 6. Preload model
Write-Host "`n[6] Preloading model to GPU..." -ForegroundColor Yellow
Write-Host "This may take a few seconds..." -ForegroundColor Cyan
ollama run gpt-oss "" 2>$null
Write-Host "Model loaded" -ForegroundColor Green

# 7. Quick test
Write-Host "`n[7] Quick GPU test..." -ForegroundColor Yellow
$startTime = Get-Date
ollama run gpt-oss "Hi"
$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

Write-Host "`nResponse time: $([math]::Round($duration, 2)) seconds" -ForegroundColor Cyan

if ($duration -lt 2) {
    Write-Host "SUCCESS! GPU is working!" -ForegroundColor Green
} else {
    Write-Host "Still slow. May need driver update or model redownload." -ForegroundColor Yellow
}

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "Restart Complete" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Monitor GPU: nvidia-smi -l 1" -ForegroundColor Cyan
Write-Host "2. Restart backend: cd backend; uvicorn main:app --reload --port 8000" -ForegroundColor Cyan
Write-Host "3. Test query: 'What is BigValue address?'" -ForegroundColor Cyan
