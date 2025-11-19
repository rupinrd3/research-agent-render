@echo off
REM ============================================================================
REM Agentic AI Research Lab - Complete Setup Script (Windows)
REM ============================================================================
REM This script sets up both backend and frontend for first-time use
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo    Agentic AI Research Lab - Complete Setup
echo ============================================================================
echo.
echo This will set up both the backend (Python/FastAPI) and frontend (Next.js)
echo.
echo Prerequisites:
echo   - Python 3.11+ (preferably 3.12 or 3.13)
echo   - Node.js 18+ and npm
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause >nul

REM ============================================================================
REM STEP 1: Check Prerequisites
REM ============================================================================

echo.
echo [1/6] Checking prerequisites...
echo ----------------------------------------

REM Check Python
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% found

REM Check Node.js
echo Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)
for /f "tokens=1" %%i in ('node --version 2^>^&1') do set NODE_VERSION=%%i
echo [OK] Node.js %NODE_VERSION% found

echo.
echo [OK] All prerequisites met!
echo.

REM ============================================================================
REM STEP 2: Backend Setup
REM ============================================================================

echo.
echo [2/6] Setting up Backend (Python/FastAPI)...
echo ----------------------------------------

cd backend

REM Create virtual environment
echo Creating Python virtual environment...
if exist "venv" (
    echo [INFO] Virtual environment already exists, skipping
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        cd ..
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)

REM Activate and install
echo Activating virtual environment...
call venv\Scripts\activate

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing Python dependencies (this may take 3-5 minutes)...
if exist "requirements_fixed.txt" (
    echo [INFO] Using requirements_fixed.txt for Python 3.13 compatibility
    pip install -r requirements_fixed.txt
) else (
    pip install -r requirements.txt
)

if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies
    echo See DEPENDENCY_FIX.md for solutions
    call deactivate
    cd ..
    pause
    exit /b 1
)

echo [OK] Python dependencies installed

call deactivate

REM Setup .env
if not exist ".env" (
    if exist ".env.example" (
        echo Creating .env from template...
        copy .env.example .env >nul
        echo [OK] .env file created
    )
)

cd ..
echo [OK] Backend setup complete!

REM ============================================================================
REM STEP 3: Frontend Setup
REM ============================================================================

echo.
echo [3/6] Setting up Frontend (Next.js)...
echo ----------------------------------------

cd frontend

echo Installing npm packages (this may take 2-3 minutes)...
if exist "node_modules" (
    echo [INFO] node_modules exists, skipping install
) else (
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install npm packages
        cd ..
        pause
        exit /b 1
    )
)

echo [OK] npm packages installed

REM Setup .env.local
if not exist ".env.local" (
    if exist ".env.local.example" (
        echo Creating .env.local from template...
        copy .env.local.example .env.local >nul
        echo [OK] .env.local file created
    ) else (
        (
            echo NEXT_PUBLIC_API_URL=http://localhost:8000
            echo NEXT_PUBLIC_WS_URL=ws://localhost:8000
            echo NODE_ENV=development
        ) > .env.local
        echo [OK] .env.local file created
    )
)

cd ..
echo [OK] Frontend setup complete!

REM ============================================================================
REM STEP 4: Create runtime directory
REM ============================================================================

echo.
echo [4/6] Creating runtime directories...
if not exist "runtime" mkdir runtime
echo [OK] Runtime directory ready

REM ============================================================================
REM STEP 5: Final Steps
REM ============================================================================

echo.
echo [5/6] Finalizing setup...
echo.
echo ============================================================================
echo    Setup Complete!
echo ============================================================================
echo.
echo IMPORTANT: Configure API Keys
echo.
echo   1. Open: backend\.env
echo   2. Add at least ONE API key:
echo      - OPENAI_API_KEY=sk-...
echo      - GOOGLE_API_KEY=...
echo      - OPENROUTER_API_KEY=sk-or-...
echo.
echo Next Steps:
echo   1. Configure API keys in backend\.env
echo   2. Run: start.bat
echo   3. Access: http://localhost:3000
echo.
echo Documentation: FINAL_STATUS_REPORT.md
echo.
pause
endlocal
