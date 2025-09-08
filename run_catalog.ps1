<# run_catalog.ps1
   Build app ID list from SQLite (apps/snapshots/union), scrape app details, then upsert into SQLite.
#>

$ErrorActionPreference = "Stop"

# --- PATHS ---
$RepoRoot   = $PSScriptRoot
$DataDir    = Join-Path $RepoRoot "data"
$ScrapyDir  = Join-Path $RepoRoot "steamcharts_scraper"
$DbDir      = Join-Path $RepoRoot "steamcharts_scraper\db"
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"

# --- CONFIG ---
# Where to read ids from: apps | snapshots | union
$IdSource  = "apps"
# Only include apps with NULL/old last_refreshed. 0 = include all.
$StaleDays = 30

# --- PREP ---
if (-not (Test-Path $DataDir)) { New-Item -ItemType Directory -Path $DataDir | Out-Null }
if (-not (Test-Path $VenvPython)) { throw "Can't find venv python: $VenvPython" }
if (-not (Test-Path (Join-Path $ScrapyDir "scrapy.cfg"))) { throw "scrapy.cfg missing under $ScrapyDir" }

# 1) Export app_ids from DB
$IdsFile = Join-Path $DataDir "app_ids_from_db.txt"
$MakeIds = Join-Path $DbDir "make_app_ids.py"

if (-not (Test-Path $MakeIds)) { throw "Missing $MakeIds - add steamcharts_scraper\db\make_app_ids.py" }

Write-Host "Exporting IDs from DB: source=$IdSource, staleDays=$StaleDays"
$argsList = @("--source", $IdSource, "--out", $IdsFile)
if ($StaleDays -gt 0) { $argsList += @("--stale-days", $StaleDays) }

& $VenvPython $MakeIds @argsList

# 2) Run catalog spider -> timestamped output
$today   = Get-Date -Format "MMddyyyy"
$catalog = Join-Path $DataDir ("catalog_{0}.json" -f $today)
if (Test-Path $catalog) {
  $n = 2
  do {
    $catalog = Join-Path $DataDir ("catalog_{0}_{1}.json" -f $today, $n)
    $n++
  } while (Test-Path $catalog)
}

Push-Location $ScrapyDir
try {
  Write-Host ""
  Write-Host "Scraping app details into $catalog"
  $scrapyArgs = @(
    "-m","scrapy","crawl","steam_app_catalog",
    "-O",$catalog,
    "-s","FEED_EXPORT_ENCODING=utf-8",
    "-s","LOG_LEVEL=INFO",
    "-s","AUTOTHROTTLE_ENABLED=True",
    "-s","AUTOTHROTTLE_START_DELAY=0.5",
    "-s","AUTOTHROTTLE_MAX_DELAY=3",
    "-s","DOWNLOAD_DELAY=0.2",
    "-a","app_ids_file=$IdsFile",
    "-a","stale_days=30"
  )
  & $VenvPython @scrapyArgs
  Write-Host ""
  Write-Host "Saved: $catalog"
}
finally {
  Pop-Location
}

# 3) Upsert into SQLite
$Upsert = Join-Path $DbDir "upsert_catalog.py"
if (Test-Path $Upsert) {
  Write-Host ""
  Write-Host "Upserting into SQLite..."
  & $VenvPython $Upsert $catalog
  Write-Host "Catalog upsert complete."
} else {
  Write-Host "Missing $Upsert - skipping DB upsert."
}
