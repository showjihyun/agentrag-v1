@echo off
chcp 65001 >nul
REM ============================================
REM Agent Builder - Windows Stop Script
REM ============================================

echo.
echo ========================================
echo   Stopping Agent Builder servers...
echo ========================================
echo.

REM Stop backend process (port 8000)
echo [1/2] Stopping backend server...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo Stopping process on port 8000: %%a
    taskkill /F /PID %%a >nul 2>&1
)
echo Backend server stopped.
echo.

REM Stop frontend process (port 3000)
echo [2/2] Stopping frontend server...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    echo Stopping process on port 3000: %%a
    taskkill /F /PID %%a >nul 2>&1
)
echo Frontend server stopped.
echo.

REM Kill uvicorn processes
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Agent Builder - Backend*" >nul 2>&1

REM Kill node processes
taskkill /F /IM node.exe /FI "WINDOWTITLE eq Agent Builder - Frontend*" >nul 2>&1

echo ========================================
echo   All servers stopped successfully.
echo ========================================
echo.
pause
