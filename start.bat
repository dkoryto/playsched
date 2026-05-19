@echo off
REM start.bat - Launch PlaySched on Windows (CMD / Batch)
REM Usage: start.bat

setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "APP_NAME=PlaySched"
set "PORT=9093"
set "HOST=127.0.0.1"
set "PID_FILE=.playsched.pid"
set "LOG_FILE=app.log"

echo [INFO]  Starting %APP_NAME%...

REM Check if .env exists
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo Please copy .env-sample to .env and configure it:
    echo   copy .env-sample .env
    exit /b 1
)

REM Check if port is already in use
netstat -ano | findstr ":%PORT% " | findstr "LISTENING" >nul
if !errorlevel! equ 0 (
    echo [ERROR] Port %PORT% is already in use.
    echo Another instance of %APP_NAME% may be running.
    echo Check: netstat -ano ^| findstr ":%PORT% "
    exit /b 1
)

REM Activate virtual environment if present
if exist "venv\Scripts\activate.bat" (
    echo [INFO]  Activating virtual environment (venv)...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo [INFO]  Activating virtual environment (.venv)...
    call .venv\Scripts\activate.bat
)

REM Verify Python is available
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] python not found in PATH. Please install Python 3.
    exit /b 1
)

for /f "tokens=*" %%a in ('python -c "import sys; print(\".\".join(map(str, sys.version_info[:2])))"') do (
    set "PYTHON_VERSION=%%a"
)
echo [INFO]  Using Python %PYTHON_VERSION%

REM Verify dependencies (quick import check)
python -c "import flask, spotipy, apscheduler, dotenv" >nul 2>&1
if !errorlevel! neq 0 (
    echo [WARN]  Some Python dependencies appear to be missing.
    echo Install them with: pip install -r requirements.txt
    exit /b 1
)

REM Start the app in background using start command
echo [INFO]  URL: https://%HOST%:%PORT%
echo [INFO]  Logs: %LOG_FILE%

start /B python run.py > "%LOG_FILE%" 2>&1

REM Save PID (Windows doesn't have easy PID capture in batch, use wmic after delay)
timeout /t 2 /nobreak >nul

for /f "tokens=*" %%a in ('wmic process where "name='python.exe' and CommandLine like '%%run.py%%'" get ProcessId /value ^| findstr "ProcessId"') do (
    for /f "tokens=2 delims==" %%b in ("%%a") do (
        set "PID=%%b"
        echo %%b > "%PID_FILE%"
    )
)

if exist "%PID_FILE%" (
    echo [INFO]  %APP_NAME% started successfully.
    echo.
    echo Open your browser at: https://%HOST%:%PORT%
    echo To stop: taskkill /PID %PID% /F
) else (
    echo [ERROR] Failed to start %APP_NAME%. Check %LOG_FILE% for details.
    exit /b 1
)

endlocal
