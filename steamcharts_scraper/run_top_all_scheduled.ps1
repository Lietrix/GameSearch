<# run_top_all_scheduled.ps1
   Wrapper that runs run_top_all.ps1 and writes a log per run.
#>

$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$LogDir      = Join-Path $ProjectRoot "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$stamp   = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = Join-Path $LogDir "run_$stamp.log"

# Optional: ensure PowerShell policy lets scripts run
# Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force

# Run and tee the output to log
try {
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "run_top_all.ps1") 2>&1 | Tee-Object -FilePath $logFile
  Write-Host "Log saved: $logFile"
} catch {
  $_ | Out-String | Tee-Object -FilePath $logFile
  exit 1
}
