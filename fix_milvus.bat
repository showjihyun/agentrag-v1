@echo off
echo ========================================
echo Milvus Collection Fix Script
echo ========================================
echo.
echo WARNING: This will delete all Milvus data!
echo You will need to re-upload documents.
echo.
pause

cd backend
call venv\Scripts\activate.bat
python scripts\fix_collection_now.py

echo.
echo ========================================
echo Next Steps:
echo 1. Restart backend server
echo 2. Re-upload documents in UI
echo 3. Test search functionality
echo ========================================
pause
