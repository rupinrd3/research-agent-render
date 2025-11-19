@echo off
REM ============================================================================
REM Agentic AI Research Lab - Stop Script (Windows)
REM ============================================================================
REM This script stops all running backend and frontend processes
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo    Agentic AI Research Lab - Stopping Application
echo ============================================================================
echo.

echo Stopping all services...
echo.

REM Method 1: Kill by window title (most reliable)
echo [1/4] Stopping by window title...
taskkill /F /FI "WINDOWTITLE eq Agentic Research - Backend*" >nul 2>&1
if not errorlevel 1 (
    echo [OK] Backend window closed
) else (
    echo [INFO] No backend window found
)

taskkill /F /FI "WINDOWTITLE eq Agentic Research - Frontend*" >nul 2>&1
if not errorlevel 1 (
    echo [OK] Frontend window closed
) else (
    echo [INFO] No frontend window found
)

REM Method 2: Kill by port (backup method)
echo.
echo [2/4] Checking for processes on ports 8000 and 3000...

REM Kill process on port 8000 (Backend)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    set PID=%%a
    if defined PID (
        echo Found process on port 8000 (PID: !PID!^)
        taskkill /F /PID !PID! >nul 2>&1
        if not errorlevel 1 (
            echo [OK] Stopped backend process
        )
    )
)

REM Kill process on port 3000 (Frontend)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    set PID=%%a
    if defined PID (
        echo Found process on port 3000 (PID: !PID!^)
        taskkill /F /PID !PID! >nul 2>&1
        if not errorlevel 1 (
            echo [OK] Stopped frontend process
        )
    )
)

REM Method 3: Kill Python processes running uvicorn
echo.
echo [3/4] Stopping uvicorn processes...
tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH | findstr /I "uvicorn" >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=2 delims=," %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH ^| findstr /I "uvicorn"') do (
        set PID=%%~a
        echo Stopping Python/uvicorn (PID: !PID!^)
        taskkill /F /PID !PID! >nul 2>&1
    )
    echo [OK] Stopped Python/uvicorn processes
) else (
    echo [INFO] No uvicorn processes found
)

REM Method 4: Kill Node processes running Next.js
echo.
echo [4/4] Stopping Next.js processes...
tasklist /FI "IMAGENAME eq node.exe" /FO CSV /NH | findstr /I "next-server" >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=2 delims=," %%a in ('tasklist /FI "IMAGENAME eq node.exe" /FO CSV /NH ^| findstr /I "next"') do (
        set PID=%%~a
        echo Stopping Node/Next.js (PID: !PID!^)
        taskkill /F /PID !PID! >nul 2>&1
    )
    echo [OK] Stopped Node/Next.js processes
) else (
    echo [INFO] No Next.js processes found
)

REM Clean up PID files if they exist
if exist "runtime\backend.pid" del /F /Q "runtime\backend.pid" >nul 2>&1
if exist "runtime\frontend.pid" del /F /Q "runtime\frontend.pid" >nul 2>&1

echo.
echo ============================================================================
echo    Application Stopped
echo ============================================================================
echo.
echo All services have been stopped.
echo.
echo To start again: Run start.bat
echo.
timeout /t 3 >nul

endlocal
