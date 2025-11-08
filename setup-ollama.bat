@echo off
chcp 65001 >nul
echo ========================================
echo Ollama Setup Guide
echo ========================================
echo.

echo Checking if Ollama is installed...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Ollama is not installed!
    echo.
    echo Please install Ollama from: https://ollama.ai
    echo.
    echo After installation:
    echo 1. Restart this script
    echo 2. Or manually run: ollama pull llama3.1:8b
    echo.
    pause
    exit /b 1
)

echo [OK] Ollama is installed
ollama --version
echo.

echo Checking if Ollama service is running...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ollama service is not running
    echo.
    echo Starting Ollama service...
    start "Ollama Service" ollama serve
    timeout /t 3 /nobreak >nul
)

echo [OK] Ollama service is running
echo.

echo Checking installed models...
ollama list
echo.

echo Checking if llama3.1:8b is installed...
ollama list | findstr "llama3.1:8b" >nul
if errorlevel 1 (
    echo [INFO] llama3.1:8b not found. Downloading...
    echo This may take a while (about 4.7GB)...
    echo.
    ollama pull llama3.1:8b
    
    if errorlevel 1 (
        echo [ERROR] Failed to download model
        pause
        exit /b 1
    )
    
    echo.
    echo [OK] Model downloaded successfully!
) else (
    echo [OK] llama3.1:8b is already installed
)

echo.
echo ========================================
echo Ollama Setup Complete!
echo ========================================
echo.
echo Available models:
ollama list
echo.
echo You can now use the Agentic RAG system.
echo.
pause
