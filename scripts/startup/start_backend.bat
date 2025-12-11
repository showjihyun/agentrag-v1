@echo off
echo Starting backend server...
cd backend
python -m uvicorn main:app --reload --port 8000
