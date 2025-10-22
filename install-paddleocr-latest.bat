@echo off
REM PaddleOCR 최신 버전 설치 스크립트 (Windows)
REM GitHub: https://github.com/PaddlePaddle/PaddleOCR

echo ========================================
echo PaddleOCR 최신 버전 설치
echo ========================================
echo.

REM 1. 기존 버전 제거
echo [1/4] 기존 버전 제거 중...
pip uninstall -y paddlepaddle-gpu paddlepaddle paddleocr paddlex modelscope torch torchvision torchaudio

REM 2. PaddlePaddle GPU 버전 설치 (CUDA 11.8)
echo.
echo [2/4] PaddlePaddle GPU 설치 중...
echo CUDA 11.8 버전 사용
python -m pip install paddlepaddle-gpu==3.0.0b1 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/

REM 3. PaddleOCR 최신 버전 설치
echo.
echo [3/4] PaddleOCR 설치 중...
pip install "paddleocr>=2.7.0"

REM 4. 필수 의존성 설치
echo.
echo [4/4] 필수 의존성 설치 중...
pip install shapely pyclipper imgaug lmdb opencv-python opencv-contrib-python Pillow

echo.
echo ========================================
echo 설치 완료!
echo ========================================
echo.
echo 설치된 버전 확인:
python -c "import paddle; print(f'PaddlePaddle: {paddle.__version__}')"
python -c "import paddleocr; print(f'PaddleOCR: {paddleocr.__version__}')"
echo.
echo GPU 사용 가능 여부:
python -c "import paddle; print(f'CUDA Available: {paddle.is_compiled_with_cuda()}')"
python -c "import paddle; print(f'GPU Count: {paddle.device.cuda.device_count() if paddle.is_compiled_with_cuda() else 0}')"
echo.
pause
