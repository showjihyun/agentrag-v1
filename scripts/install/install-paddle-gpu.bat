@echo off
chcp 65001 >nul
echo ========================================
echo   Installing PaddlePaddle GPU
echo ========================================
echo.
echo This will install PaddlePaddle GPU with CUDA support.
echo Note: This may downgrade protobuf, which is required by PaddlePaddle.
echo.

REM Check virtual environment
if not exist "backend\venv" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv backend\venv
    pause
    exit /b 1
)

echo Activating virtual environment...
cd backend
call venv\Scripts\activate.bat

echo.
echo Step 1: Installing PaddlePaddle GPU...
echo This will install CUDA-enabled PaddlePaddle.
echo.

pip install paddlepaddle-gpu==2.6.2 -i https://pypi.tuna.tsinghua.edu.cn/simple

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [WARNING] Failed with mirror, trying official PyPI...
    pip install paddlepaddle-gpu==2.6.2
    
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo [ERROR] Failed to install paddlepaddle-gpu
        echo.
        echo Please check:
        echo 1. CUDA is installed (CUDA 11.8 or 12.0 recommended)
        echo 2. Internet connection
        echo.
        deactivate
        cd ..
        pause
        exit /b 1
    )
)

echo.
echo Step 2: Verifying installation...
python -c "import paddle; print(f'PaddlePaddle {paddle.__version__} installed')"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PaddlePaddle verification failed
    deactivate
    cd ..
    pause
    exit /b 1
)

echo.
echo Step 3: Checking CUDA availability...
python -c "import paddle; print(f'CUDA available: {paddle.device.is_compiled_with_cuda()}'); print(f'GPU count: {paddle.device.cuda.device_count() if paddle.device.is_compiled_with_cuda() else 0}')"

echo.
echo Step 4: Downgrading protobuf for compatibility...
pip install "protobuf>=3.1.0,<=3.20.2" --force-reinstall

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo PaddlePaddle GPU is now installed.
echo.
echo Note: protobuf was downgraded to 3.20.2 for compatibility.
echo This may affect pymilvus. If you need pymilvus, you may need to:
echo   1. Use pymilvus without paddlepaddle-gpu, OR
echo   2. Run them in separate environments
echo.
echo To check GPU: python -c "import paddle; print(paddle.device.is_compiled_with_cuda())"
echo.

deactivate
cd ..
pause
