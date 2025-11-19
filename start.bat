@echo off
REM ============================================================================
REM Agentic AI Research Lab - Start Script (Windows)
REM ============================================================================
REM This script starts both backend (FastAPI) and frontend (Next.js)
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo    Agentic AI Research Lab - Starting Application
echo ============================================================================
echo.

REM Check if setup was run
if not exist "backend\venv" (
    echo [ERROR] Backend virtual environment not found!
    echo Please run setup.bat first
    echo.
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo [ERROR] Frontend dependencies not found!
    echo Please run setup.bat first
    echo.
    pause
    exit /b 1
)

REM Check if API keys are configured
cd backend
call venv\Scripts\activate
python -c "import os; from dotenv import load_dotenv; load_dotenv(); keys = [os.getenv('OPENAI_API_KEY'), os.getenv('GOOGLE_API_KEY'), os.getenv('OPENROUTER_API_KEY')]; has_key = any(k for k in keys if k and k.strip()); exit(0 if has_key else 1)" 2>nul
if errorlevel 1 (
    echo [WARNING] No API keys configured in backend\.env
    echo.
    echo The application will not work without at least one API key.
    echo Please add your API key to backend\.env
    echo.
    echo Continue anyway? (y/N^)
    set /p CONTINUE=
    if /i not "!CONTINUE!"=="y" (
        call deactivate
        cd ..
        exit /b 1
    )
)
call deactivate
cd ..

REM Create runtime directory for PID files
if not exist "runtime" mkdir runtime

REM Kill any existing processes
echo Checking for existing processes...
taskkill /F /FI "WINDOWTITLE eq Agentic Research - Backend*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Agentic Research - Frontend*" >nul 2>&1
timeout /t 1 >nul

REM Start Backend
echo.
echo [1/2] Starting Backend (FastAPI on port 8000)...
start "Agentic Research - Backend" /MIN cmd /c "cd backend && venv\Scripts\activate && echo Backend starting on http://localhost:8000 && echo API Docs: http://localhost:8000/docs && echo. && uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for backend to start
echo Waiting for backend to initialize...
timeout /t 5 >nul

REM Start Frontend
echo [2/2] Starting Frontend (Next.js on port 3000)...
start "Agentic Research - Frontend" /MIN cmd /c "cd frontend && echo Frontend starting on http://localhost:3000 && echo. && npm run dev"

REM Wait for frontend to start
echo Waiting for frontend to initialize...
timeout /t 3 >nul

echo.
echo ============================================================================
echo    Application Started Successfully!
echo ============================================================================
echo.
echo Services:
echo   [*] Backend API:    http://localhost:8000
echo   [*] API Docs:       http://localhost:8000/docs
echo   [*] Frontend UI:    http://localhost:3000
echo.
echo The application is now running in separate windows.
echo.
echo To access the application:
echo   1. Open your browser
echo   2. Go to: http://localhost:3000
echo   3. Start researching!
echo.
echo To stop the application:
echo   - Run: stop.bat
echo   - Or close both terminal windows
echo.
echo Press any key to open the frontend in your browser...
pause >nul

REM Open browser
start http://localhost:3000

echo.
echo Browser opened. You can close this window safely.
echo The application will continue running in the background windows.
echo.
echo To stop: Run stop.bat or close the backend/frontend windows
echo.
timeout /t 3 >nul

endlocal
