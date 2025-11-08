@echo off
chcp 65001 >nul
echo ========================================
echo Creating Test User
echo ========================================
echo.

cd backend
call venv\Scripts\activate.bat

REM Set PYTHONPATH
cd ..
set PYTHONPATH=%CD%
cd backend

echo Creating test user...
python -c "from backend.db.database import SessionLocal; from backend.db.models.user import User; from backend.services.auth_service import AuthService; db = SessionLocal(); existing = db.query(User).filter(User.email == 'test@example.com').first(); print('User already exists') if existing else (db.add(User(email='test@example.com', username='testuser', password_hash=AuthService.hash_password('test123'), role='admin', is_active=True)), db.commit(), print('✓ Test user created: test@example.com / test123'))"

echo.
echo ========================================
echo Test User Ready!
echo ========================================
echo.
echo Email: test@example.com
echo Password: test123
echo Role: admin
echo.
echo You can now login with these credentials.
echo.
pause
