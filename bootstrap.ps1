# One-command setup for the Garmin recovery-data sync project, for Windows.
#
# What this does, in order:
#   1. Checks for Python 3.12+ and installs it via winget if it's missing
#      (winget is built into Windows 10/11, no admin password needed for
#      a per-user install).
#   2. Downloads this project into $HOME\garmin-ai (or updates it if you've
#      already run this before) -- no git required.
#   3. Creates a private Python virtual environment inside that folder and
#      installs the two required packages.
#   4. Runs the sync script for you. The first time, it will ask for your
#      Garmin email and password right here in this window (password
#      hidden while you type) and save a login token so you won't be asked
#      again.
#
# This script never touches anything outside $HOME\garmin-ai and your
# Python installation, and it never writes anything back to your Garmin
# account.

$ErrorActionPreference = "Stop"

$TargetDir = Join-Path $HOME "garmin-ai"
$RepoZipUrl = "https://github.com/migueljreiser-oss/MyGarmin/archive/refs/heads/claude/garmin-watch-connection-kc6cps.zip"

Write-Host "== Garmin recovery-data sync: setup ==" -ForegroundColor Cyan
Write-Host ""

# --- 1. Check Python --------------------------------------------------------
function Get-GoodPython {
    foreach ($cmd in @("python3.13", "python3.12", "python", "py")) {
        $exe = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($exe) {
            try {
                $verOut = & $cmd --version 2>&1
                if ($verOut -match "(\d+)\.(\d+)") {
                    $maj = [int]$Matches[1]; $min = [int]$Matches[2]
                    if ($maj -gt 3 -or ($maj -eq 3 -and $min -ge 12)) {
                        return $cmd
                    }
                }
            } catch {}
        }
    }
    return $null
}

$PythonCmd = Get-GoodPython

if (-not $PythonCmd) {
    Write-Host "Python 3.12 or newer was not found."
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        Write-Host "Installing Python 3.12 via winget (per-user, no admin password needed)..."
        winget install -e --id Python.Python.3.12 --source winget --accept-package-agreements --accept-source-agreements
        Write-Host "Please close this window, open a NEW PowerShell window, and run this command again so Windows picks up the new Python install."
        exit 1
    } else {
        Write-Host "winget isn't available on this PC, so this script can't install Python automatically."
        Write-Host "Install Python 3.12+ from https://www.python.org/downloads/ (check 'Add python.exe to PATH' during install), then re-run this command."
        exit 1
    }
}

Write-Host "Using $PythonCmd ($(& $PythonCmd --version))"
Write-Host ""

# --- 2. Get the project ------------------------------------------------------
Write-Host "Downloading the project into $TargetDir ..."
$tempZip = Join-Path $env:TEMP "garmin-ai.zip"
$tempExtract = Join-Path $env:TEMP "garmin-ai-extract"
Invoke-WebRequest -Uri $RepoZipUrl -OutFile $tempZip
if (Test-Path $tempExtract) { Remove-Item $tempExtract -Recurse -Force }
Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force
$extractedRoot = Get-ChildItem $tempExtract | Select-Object -First 1
New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
Copy-Item -Path (Join-Path $extractedRoot.FullName "*") -Destination $TargetDir -Recurse -Force
Remove-Item $tempZip, $tempExtract -Recurse -Force
Write-Host ""

# --- 3. Set up the virtual environment --------------------------------------
Set-Location $TargetDir
if (-not (Test-Path ".venv")) {
    Write-Host "Creating a private Python environment..."
    & $PythonCmd -m venv .venv
}
$VenvPython = Join-Path $TargetDir ".venv\Scripts\python.exe"
Write-Host "Installing required packages..."
& $VenvPython -m pip install --quiet --upgrade pip
& $VenvPython -m pip install --quiet -r requirements.txt
Write-Host ""

# --- 4. Run it ---------------------------------------------------------------
Write-Host "== Setup complete. Starting the Garmin sync (this is where it may ask for your login) ==" -ForegroundColor Cyan
Write-Host ""
& $VenvPython garmin_sync.py --days 3
