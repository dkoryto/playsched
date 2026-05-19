# stop.ps1 - Stop PlaySched on Windows (PowerShell)
# Usage: .\stop.ps1

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PidFile = Join-Path $ScriptDir ".playsched.pid"
$Port = "9093"

function Info($msg)  { Write-Host "[INFO]  $msg" -ForegroundColor Green }
function Warn($msg)  { Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Err($msg)   { Write-Host "[ERROR] $msg" -ForegroundColor Red }

if (Test-Path $PidFile) {
    $Pid = Get-Content $PidFile -Raw
    $Pid = $Pid.Trim()
    $Proc = Get-Process -Id $Pid -ErrorAction SilentlyContinue
    if ($Proc) {
        Info "Stopping PlaySched (PID: $Pid)..."
        Stop-Process -Id $Pid -Force
        Start-Sleep -Seconds 1
        Remove-Item -Path $PidFile -Force -ErrorAction SilentlyContinue
        Info "Stopped."
        exit 0
    } else {
        Warn "PID file exists but process $Pid is not running. Cleaning up..."
        Remove-Item -Path $PidFile -Force -ErrorAction SilentlyContinue
    }
}

# Fallback: kill by port
$Connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
if ($Connection) {
    $OwningProcess = $Connection.OwningProcess
    Info "Stopping PlaySched found on port $Port (PID: $OwningProcess)..."
    Stop-Process -Id $OwningProcess -Force
    Info "Stopped."
    exit 0
}

Write-Host "PlaySched does not appear to be running."
