@echo off
echo Installing Tool Execution Dependencies...
echo.

cd backend

echo Activating virtual environment...
call venv\Scripts\activate

echo.
echo Installing duckduckgo-search...
pip install duckduckgo-search>=6.0.0

echo.
echo Installation complete!
echo.
echo You can now start the backend server:
echo   cd backend
echo   uvicorn main:app --reload
echo.
pause
