@echo off
REM Start KYV Backend Server
echo Starting KYV Backend Server...
echo.
echo Backend will run on: http://localhost:8000
echo Health check: http://localhost:8000/health
echo API docs: http://localhost:8000/docs
echo.
echo To stop the server, press CTRL+C
echo.
uvicorn orchestrator:app --reload --host 0.0.0.0 --port 8000
pause 
