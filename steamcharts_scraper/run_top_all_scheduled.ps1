# C:\GameSearch\steamcharts_scraper\run_top_all_scheduled.ps1
$ErrorActionPreference = 'Stop'

# 1) Paths
$ProjectRoot = "C:\GameSearch"
$RepoRoot    = Join-Path $ProjectRoot "steamcharts_scraper"
$RunnerPs1   = Join-Path $RepoRoot "run_top_all.ps1"  # <-- your working script
$VenvPython  = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$DbPath      = Join-Path $RepoRoot "db\catalog.db"

# 2) Logs
$LogDir = Join-Path $ProjectRoot "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Tag    = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$OutLog = Join-Path $LogDir "topall_$Tag.out.log"
$ErrLog = Join-Path $LogDir "topall_$Tag.err.log"
$Transcript = Join-Path $LogDir "topall_$Tag.transcript.txt"
Start-Transcript -Path $Transcript -Force | Out-Null

# 3) Ensure working dir (defensive against Scheduler default)
Set-Location $ProjectRoot
"PWD: $((Get-Location).Path)" | Tee-Object -FilePath $OutLog -Append | Out-Null

# 4) Sanity checks
$mustExist = @($RunnerPs1, $VenvPython)
foreach ($p in $mustExist) { if (-not (Test-Path $p)) { throw "Missing path: $p" } }
New-Item -ItemType Directory -Force -Path (Split-Path $DbPath) | Out-Null

# 5) Prevent overlapping runs
$LockFile = Join-Path $ProjectRoot ".run_top_all.lock"
if (Test-Path $LockFile) {
  "Lock file present; exiting." | Tee-Object -FilePath $OutLog -Append | Out-Null
  Stop-Transcript | Out-Null
  exit 0
}
New-Item -ItemType File -Path $LockFile -Force | Out-Null

try {
  # 6) Run your working script (capture stdout/stderr)
  #    We invoke PowerShell explicitly so Task Scheduler context matches.
# 6) Run your working script (capture stdout/stderr via Start-Process)
$RunnerExe  = "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe"
$RunnerArgs = @('-ExecutionPolicy','Bypass','-NoProfile','-File', $RunnerPs1)

$proc = Start-Process -FilePath $RunnerExe `
                      -ArgumentList $RunnerArgs `
                      -RedirectStandardOutput $OutLog `
                      -RedirectStandardError  $ErrLog `
                      -NoNewWindow -PassThru -Wait

if ($proc.ExitCode -ne 0) {
  throw "run_top_all.ps1 exited with code $($proc.ExitCode). See logs: $OutLog / $ErrLog"
}

  # 7) Quick DB integrity check (works even if your runner already did the load)
  $PyCheck = @"
import sqlite3, os, sys
db = r"$DbPath"
print("db path:", db, "exists:", os.path.exists(db))
con = sqlite3.connect(db, timeout=20)
c = con.cursor()
apps_tab = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='apps'").fetchone()
snaps_tab = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='snapshots'").fetchone()
print("has apps table:", bool(apps_tab), "has snapshots table:", bool(snaps_tab))
if snaps_tab:
    row = c.execute("SELECT COUNT(*), MAX(timestamp) FROM snapshots").fetchone()
    print("snapshots count:", row[0], "latest ts:", row[1])
con.close()
"@
  $PyCheck | & $VenvPython - 1>> $OutLog 2>> $ErrLog

} finally {
  Remove-Item $LockFile -ErrorAction SilentlyContinue
  Stop-Transcript | Out-Null
}
