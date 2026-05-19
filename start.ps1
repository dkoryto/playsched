# start.ps1 - Launch PlaySched on Windows (PowerShell)
# Usage: .\start.ps1
# Or with execution policy bypass: powershell -ExecutionPolicy Bypass -File .\start.ps1

param(
    [string]$Port = "9093",
    [string]$HostAddr = "127.0.0.1"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$AppName = "PlaySched"
$PidFile = Join-Path $ScriptDir ".playsched.pid"
$LogFile = Join-Path $ScriptDir "app.log"

function Info($msg)  { Write-Host "[INFO]  $msg" -ForegroundColor Green }
function Warn($msg)  { Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Err($msg)   { Write-Host "[ERROR] $msg" -ForegroundColor Red }

# Check if .env exists
if (-not (Test-Path ".env")) {
    Err ".env file not found!"
    Write-Host "Please copy .env-sample to .env and configure it:"
    Write-Host "  copy .env-sample .env"
    exit 1
}

# Check if port is already in use
$PortInUse = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
if ($PortInUse) {
    Err "Port $Port is already in use."
    Write-Host "Another instance of $AppName may be running."
    Write-Host "Check: Get-NetTCPConnection -LocalPort $Port"
    exit 1
}

# Activate virtual environment if present
$VenvPaths = @("venv\Scripts\Activate.ps1", ".venv\Scripts\Activate.ps1")
foreach ($VenvPath in $VenvPaths) {
    if (Test-Path $VenvPath) {
        Info "Activating virtual environment ($(Split-Path -Parent $VenvPath))..."
        & $VenvPath
        break
    }
}

# Verify Python is available
$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    $PythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $PythonCmd) {
    Err "python/python3 not found in PATH. Please install Python 3."
    exit 1
}

$PythonExe = $PythonCmd.Source
$PythonVersion = & $PythonExe -c "import sys; print('.'.join(map(str, sys.version_info[:2])))"
Info "Using Python $PythonVersion ($PythonExe)"

# Verify dependencies
try {
    & $PythonExe -c "import flask, spotipy, apscheduler, dotenv" | Out-Null
} catch {
    Warn "Some Python dependencies appear to be missing."
    Write-Host "Install them with: pip install -r requirements.txt"
    exit 1
}

# Start the app
Info "Starting $AppName..."
Info "URL: https://${HostAddr}:$Port"
Info "Logs: $LogFile"

# Use Start-Process so it runs independently
$Process = Start-Process -FilePath $PythonExe -ArgumentList "run.py" -WorkingDirectory $ScriptDir `
    -WindowStyle Hidden -RedirectStandardOutput $LogFile -RedirectStandardError $LogFile -PassThru

$Process.Id | Out-File -FilePath $PidFile -Encoding ASCII -NoNewline

Start-Sleep -Seconds 2

# Verify it started
if (-not $Process.HasExited) {
    Info "$AppName started successfully (PID: $($Process.Id))."
    Write-Host ""
    Write-Host "Open your browser at: https://${HostAddr}:$Port"
    Write-Host "To stop: .\stop.ps1   or   taskkill /PID $($Process.Id) /F"
} else {
    Err "Failed to start $AppName. Check $LogFile for details."
    Remove-Item -Path $PidFile -Force -ErrorAction SilentlyContinue
    exit 1
}
