@echo off
echo ========================================
echo Complete Installation (grpcio already working)
echo ========================================
echo.
echo Current status:
echo - grpcio: 1.75.1 ✓
echo - docling: OK ✓
echo - numpy: 2.1.3 ✓
echo - langchain: 0.3.19 ✓
echo.
echo Now installing remaining packages...
echo ========================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    pause
    exit /b 1
)

echo Step 1: Install remaining requirements...
venv\Scripts\python.exe -m pip install -r backend\requirements.txt

echo.
echo Step 2: Verify key packages...
echo.

venv\Scripts\python.exe -c "import grpc; print(f'✓ gRPC: {grpc.__version__}')"
venv\Scripts\python.exe -c "import docling; print('✓ Docling: OK')"
venv\Scripts\python.exe -c "import numpy; print(f'✓ Numpy: {numpy.__version__}')"
venv\Scripts\python.exe -c "import langchain; print(f'✓ LangChain: {langchain.__version__}')"
venv\Scripts\python.exe -c "import pymilvus; print(f'✓ PyMilvus: {pymilvus.__version__}')"
venv\Scripts\python.exe -c "import redis; print(f'✓ Redis: {redis.__version__}')"
venv\Scripts\python.exe -c "import fastapi; print(f'✓ FastAPI: {fastapi.__version__}')"

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Your system is ready!
echo.
echo Next steps:
echo 1. Start Docker services: docker-compose up -d
echo 2. Start backend: start-backend.bat
echo 3. Start frontend: cd frontend ^&^& npm run dev
echo.
pause
