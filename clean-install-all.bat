@echo off
echo ========================================
echo Clean Install - All Packages
echo ========================================
echo.
echo This will:
echo 1. Uninstall all packages
echo 2. Clean pip cache
echo 3. Reinstall everything from requirements.txt
echo.
echo WARNING: This will take 10-20 minutes
echo ========================================
echo.
pause

REM Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    pause
    exit /b 1
)

echo.
echo Step 1: Uninstalling all packages...
venv\Scripts\python.exe -m pip freeze > installed_packages.txt
venv\Scripts\python.exe -m pip uninstall -r installed_packages.txt -y
del installed_packages.txt

echo.
echo Step 2: Cleaning pip cache...
venv\Scripts\python.exe -m pip cache purge

echo.
echo Step 3: Upgrading pip, setuptools, wheel...
venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel

echo.
echo Step 4: Installing requirements.txt...
echo This may take 10-20 minutes, please wait...
venv\Scripts\python.exe -m pip install -r backend\requirements.txt

echo.
echo ========================================
echo Verification
echo ========================================
echo.

echo Checking key packages...
venv\Scripts\python.exe -c "import numpy; print(f'✓ Numpy: {numpy.__version__}')"
venv\Scripts\python.exe -c "import pydantic; print(f'✓ Pydantic: {pydantic.__version__}')"
venv\Scripts\python.exe -c "import transformers; print(f'✓ Transformers: {transformers.__version__}')"
venv\Scripts\python.exe -c "import langchain; print(f'✓ LangChain: {langchain.__version__}')"
venv\Scripts\python.exe -c "import cv2; print(f'✓ OpenCV: {cv2.__version__}')"
venv\Scripts\python.exe -c "try: import docling; print('✓ Docling: OK'); except Exception as e: print(f'✗ Docling: {e}')"

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Test: venv\Scripts\python backend\test_docling_integration.py
echo 2. Start: start-backend.bat
echo.
pause
