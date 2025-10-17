@echo off
echo ========================================
echo Testing Backend API
echo ========================================
echo.

echo Please make sure backend is running first!
echo Run: start-backend.bat
echo.
echo Press any key to test API endpoints...
pause > nul

echo.
echo Testing /health endpoint...
curl http://localhost:8000/health
echo.
echo.

echo Testing /docs endpoint...
curl -I http://localhost:8000/docs
echo.
echo.

echo Testing /api/documents endpoint...
curl http://localhost:8000/api/documents
echo.
echo.

echo ========================================
echo Test Complete
echo ========================================
pause
