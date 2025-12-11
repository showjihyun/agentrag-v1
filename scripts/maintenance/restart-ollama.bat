@echo off
chcp 65001 >nul
echo ========================================
echo Restarting Ollama Service
echo ========================================
echo.

echo Stopping Ollama processes...
taskkill /F /IM ollama.exe 2>nul
timeout /t 2 /nobreak >nul

echo Starting Ollama service...
start "Ollama Service" ollama serve

echo Waiting for service to start...
timeout /t 3 /nobreak >nul

echo.
echo Testing Ollama connection...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ollama service may not be ready yet
    echo Please wait a few seconds and try again
) else (
    echo [OK] Ollama service is running
)

echo.
echo ========================================
echo Ollama Restarted!
echo ========================================
echo.
pause
