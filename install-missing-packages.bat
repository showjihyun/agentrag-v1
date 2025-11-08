@echo off
chcp 65001 >nul
echo ========================================
echo Installing Missing Packages
echo ========================================
echo.

cd backend

if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo Installing email-validator...
pip install email-validator>=2.0.0

echo.
echo Verifying installation...
python -c "import email_validator; print('✓ email-validator installed successfully')"

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
pause
