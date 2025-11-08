@echo off
chcp 65001 >nul
cd backend
call venv\Scripts\activate.bat

echo Checking Alembic heads...
alembic heads

echo.
echo Checking current revision...
alembic current

echo.
echo Checking history...
alembic history

pause
