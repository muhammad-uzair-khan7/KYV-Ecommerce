@echo off
REM Start KYV Frontend with Streamlit

echo ========================================
echo      KYV Frontend Startup
echo ========================================
echo.
echo Frontend will open at: http://localhost:8501
echo.
echo Make sure backend is running first:
echo   Run: run_backend.bat
echo.
echo Press any key to start frontend...
pause

streamlit run FRONTEND.py --logger.level=info
pause
