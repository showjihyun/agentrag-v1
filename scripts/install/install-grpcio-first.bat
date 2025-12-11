@echo off
echo ========================================
echo Installing grpcio binary first
echo ========================================
echo.
echo This will install pre-built grpcio binary to avoid compilation issues.
echo.

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo.
echo Step 1: Installing grpcio binary...
pip install --only-binary :all: grpcio>=1.60.0,<2.0.0

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Failed to install grpcio binary
    echo.
    echo Trying alternative method...
    pip install grpcio>=1.60.0,<2.0.0 --prefer-binary
    
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo [ERROR] Still failed. Please check your internet connection.
        pause
        exit /b 1
    )
)

echo.
echo [SUCCESS] grpcio installed successfully!
echo.
echo Now you can install the rest of the requirements:
echo   pip install -r backend\requirements.txt
echo.
pause
