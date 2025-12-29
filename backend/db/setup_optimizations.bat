@echo off
REM Database Optimization Setup Script for Windows
REM Makes optimization tools accessible and provides quick access

echo 🗄️ Setting up Database Optimization Tools...

cd /d "%~dp0"

echo 📝 Creating convenience scripts...

REM Create optimization wrapper
echo @echo off > optimize.bat
echo cd /d "%%~dp0" >> optimize.bat
echo python optimize_database.py %%* >> optimize.bat

REM Create monitoring wrapper
echo @echo off > monitor.bat
echo cd /d "%%~dp0" >> monitor.bat
echo python monitoring_dashboard.py %%* >> monitor.bat

REM Create quick setup script
echo @echo off > quick_setup.bat
echo echo 🚀 Quick Database Optimization Setup >> quick_setup.bat
echo echo ==================================== >> quick_setup.bat
echo echo. >> quick_setup.bat
echo cd /d "%%~dp0" >> quick_setup.bat
echo echo 1. Checking database connection... >> quick_setup.bat
echo python -c "import sys; sys.path.append('..'); from db.database import get_db_url; from sqlalchemy import create_engine; engine = create_engine(get_db_url()); conn = engine.connect(); conn.execute('SELECT 1'); print('✅ Database connection successful')" >> quick_setup.bat
echo if errorlevel 1 ( >> quick_setup.bat
echo     echo ❌ Database connection failed >> quick_setup.bat
echo     pause >> quick_setup.bat
echo     exit /b 1 >> quick_setup.bat
echo ^) >> quick_setup.bat
echo echo. >> quick_setup.bat
echo echo 2. Applying basic optimizations ^(Phase 1^)... >> quick_setup.bat
echo python optimize_database.py --phase 1 >> quick_setup.bat
echo echo. >> quick_setup.bat
echo echo 3. Running health check... >> quick_setup.bat
echo python optimize_database.py --health >> quick_setup.bat
echo echo. >> quick_setup.bat
echo echo ✅ Quick setup completed! >> quick_setup.bat
echo echo. >> quick_setup.bat
echo echo Next steps: >> quick_setup.bat
echo echo - Start monitoring: monitor --server >> quick_setup.bat
echo echo - Apply all phases: optimize --all >> quick_setup.bat
echo echo - Check status: optimize --status >> quick_setup.bat
echo pause >> quick_setup.bat

REM Create help script
echo @echo off > help.bat
echo echo 🗄️ Database Optimization Tools Help >> help.bat
echo echo =================================== >> help.bat
echo echo. >> help.bat
echo echo Quick Commands: >> help.bat
echo echo   quick_setup          - Apply basic optimizations and health check >> help.bat
echo echo   optimize --all       - Apply all optimization phases >> help.bat
echo echo   optimize --status    - Check optimization status >> help.bat
echo echo   optimize --health    - Run database health check >> help.bat
echo echo   monitor --server     - Start monitoring dashboard >> help.bat
echo echo   monitor --report     - Generate performance report >> help.bat
echo echo. >> help.bat
echo echo Detailed Commands: >> help.bat
echo echo. >> help.bat
echo echo Optimization ^(optimize^): >> help.bat
echo echo   --phase 1              - Basic performance optimizations >> help.bat
echo echo   --phase 2              - Table partitioning ^(requires planning^) >> help.bat
echo echo   --phase 3              - Security enhancements >> help.bat
echo echo   --all                  - Apply all phases >> help.bat
echo echo   --status               - Check what's been applied >> help.bat
echo echo   --health               - Database health check >> help.bat
echo echo   --refresh              - Refresh analytics views >> help.bat
echo echo   --maintenance          - Run maintenance tasks >> help.bat
echo echo. >> help.bat
echo echo Monitoring ^(monitor^): >> help.bat
echo echo   --server               - Start web dashboard ^(port 5001^) >> help.bat
echo echo   --port 5002            - Use different port >> help.bat
echo echo   --report               - Generate performance report >> help.bat
echo echo   --alerts               - Check for alerts >> help.bat
echo echo   --json                 - Output in JSON format >> help.bat
echo echo. >> help.bat
echo echo Files: >> help.bat
echo echo   DATABASE_OPTIMIZATION_README.md  - Complete documentation >> help.bat
echo echo   DATABASE_REVIEW.md               - Original analysis >> help.bat
echo echo   migrations/                      - SQL optimization scripts >> help.bat
echo echo. >> help.bat
echo echo Examples: >> help.bat
echo echo   quick_setup                    # Quick start >> help.bat
echo echo   optimize --all                 # Full optimization >> help.bat
echo echo   monitor --server --port 5002   # Dashboard on port 5002 >> help.bat
echo echo   optimize --health              # Health check >> help.bat
echo echo   monitor --report --json        # JSON performance report >> help.bat
echo pause >> help.bat

echo ✅ Setup completed!
echo.
echo 📚 Available commands:
echo   quick_setup    - Quick optimization setup
echo   optimize       - Database optimization tool
echo   monitor        - Monitoring dashboard
echo   help           - Show detailed help
echo.
echo 🚀 Get started with: quick_setup
echo.
echo 📖 For complete documentation, see: DATABASE_OPTIMIZATION_README.md
pause