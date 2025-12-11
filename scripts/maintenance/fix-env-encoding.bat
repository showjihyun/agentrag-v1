@echo off
chcp 65001 >nul
echo ========================================
echo Fixing .env file encoding issue
echo ========================================
echo.

if not exist ".env" (
    echo [ERROR] .env file not found
    pause
    exit /b 1
)

echo [1] Backing up current .env file...
copy .env .env.backup >nul
echo [OK] Backup created: .env.backup
echo.

echo [2] Converting .env to UTF-8...
powershell -Command "Get-Content .env -Encoding Default | Set-Content .env.utf8 -Encoding UTF8"
if errorlevel 1 (
    echo [ERROR] Failed to convert encoding
    pause
    exit /b 1
)
echo.

echo [3] Replacing original file...
move /Y .env.utf8 .env >nul
echo [OK] .env file converted to UTF-8
echo.

echo ========================================
echo Encoding fix complete!
echo ========================================
echo.
echo If you still have issues, you can restore from backup:
echo   copy .env.backup .env
echo.
pause
