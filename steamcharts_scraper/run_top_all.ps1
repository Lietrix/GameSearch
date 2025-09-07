<#  
  run_top_all.ps1
  Run the SteamCharts "top all" spider and save output without overwriting.

  Output pattern:
    data\steamcharts_top_all_MMDDYYYY.json
    data\steamcharts_top_all_MMDDYYYY_2.json (2nd run same day), etc.
#>

$ErrorActionPreference = "Stop"

# --- USER CONFIG (easy to change) ----
# Stop when avg players drop below this value (0 = no threshold; arg omitted)
$MinPlayers = 150

# Max number of pages to scrape (0 = unlimited; arg omitted)
$MaxPages   = 0

# --- PROJECT CONFIG ----
$SpiderName  = "steamcharts_top_all"
$ProjectRoot = $PSScriptRoot
$DataDir     = Join-Path $ProjectRoot "data"
$VenvPython  = Join-Path (Join-Path $ProjectRoot "..") ".venv\Scripts\python.exe"

# --- PREP ----
if (-not (Test-Path $VenvPython)) {
  throw "Can't find venv python: $VenvPython`nMake sure your venv exists at C:\GameSearch\.venv and Python is installed."
}

if (-not (Test-Path (Join-Path $ProjectRoot "scrapy.cfg"))) {
  throw "scrapy.cfg not found in $ProjectRoot. Place this script in your Scrapy project root."
}

if (-not (Test-Path $DataDir)) { New-Item -ItemType Directory -Path $DataDir | Out-Null }

# Build base name with MMDDYYYY
$today    = Get-Date -Format "MMddyyyy"
$baseName = "steamcharts_top_all_$today"
$outFile  = Join-Path $DataDir "$baseName.json"

# If today's file already exists, append _2, _3, ...
if (Test-Path $outFile) {
  $n = 2
  do {
    $outFile = Join-Path $DataDir ("{0}_{1}.json" -f $baseName, $n)
    $n++
  } while (Test-Path $outFile)
}

# --- RUN ----
Push-Location $ProjectRoot
try {
  Write-Host "▶ Running spider '$SpiderName' with settings:" -ForegroundColor Cyan
  Write-Host ("   MinPlayers = {0}" -f ($(if ($MinPlayers -gt 0) { $MinPlayers } else { "None (no threshold)" })))
  Write-Host ("   MaxPages   = {0}" -f ($(if ($MaxPages -gt 0)   { $MaxPages   } else { "Unlimited" })))
  Write-Host "   Output     = $outFile`n"

  $scrapyArgs = @(
    "-m", "scrapy",
    "crawl", $SpiderName,
    "-O", $outFile,
    "-s", "FEED_EXPORT_ENCODING=utf-8",
    "-s", "LOG_LEVEL=INFO"
  )

  if ($MinPlayers -gt 0) { $scrapyArgs += @("-a", "min_players=$MinPlayers") }
  if ($MaxPages   -gt 0) { $scrapyArgs += @("-a", "max_pages=$MaxPages") }

  & $VenvPython @scrapyArgs

  Write-Host "`n✅ Saved:" -ForegroundColor Green
  Write-Host "   $outFile"

  # Immediately load into SQLite
  $DbLoader = Join-Path $PSScriptRoot "db\load_snapshot.py"
  if (Test-Path $DbLoader) {
    Write-Host "`n→ Loading snapshot into SQLite..."
    & $VenvPython $DbLoader $outFile
  } else {
    Write-Host "(!) Skipping DB load; missing $DbLoader"
  }


}
finally {
  Pop-Location
}
