#!/usr/bin/env bash
# One-command setup for the Garmin recovery-data sync project.
#
# What this does, in order:
#   1. Checks for Python 3.12+ (the minimum python-garminconnect needs) and
#      offers to install it via Homebrew on macOS if it's missing.
#   2. Downloads this project into ~/garmin-ai (or re-uses it if you've
#      already run this before).
#   3. Creates a private Python virtual environment inside that folder and
#      installs the two required packages.
#   4. Runs the sync script for you. The first time, it will ask for your
#      Garmin email and password right here in this terminal (never
#      anywhere else) and save a login token so you won't be asked again.
#
# This script never touches anything outside ~/garmin-ai and your Python
# installation, and it never writes anything back to your Garmin account.

set -euo pipefail

TARGET_DIR="${GARMIN_AI_DIR:-$HOME/garmin-ai}"
REPO_URL="https://github.com/migueljreiser-oss/MyGarmin.git"
REPO_BRANCH="claude/garmin-watch-connection-kc6cps"

echo "== Garmin recovery-data sync: setup =="
echo

# --- 1. Check Python -------------------------------------------------------
PYTHON_BIN=""
for candidate in python3.13 python3.12 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
        version="$("$candidate" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
        major="${version%%.*}"
        minor="${version##*.}"
        if [ "$major" -gt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -ge 12 ]; }; then
            PYTHON_BIN="$candidate"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "Python 3.12 or newer was not found."
    if [ "$(uname -s)" = "Darwin" ]; then
        if command -v brew >/dev/null 2>&1; then
            echo "Installing Python 3.12 with Homebrew (this only affects your user account, no admin password needed)..."
            brew install python@3.12
            PYTHON_BIN="python3.12"
        else
            echo "Homebrew isn't installed, so this script can't install Python automatically."
            echo "Install Python 3.12+ from https://www.python.org/downloads/ and then re-run this command."
            exit 1
        fi
    else
        echo "Please install Python 3.12+ using your system's package manager, e.g.:"
        echo "  sudo apt update && sudo apt install -y python3.12 python3.12-venv"
        echo "Then re-run this command."
        exit 1
    fi
fi

echo "Using $($PYTHON_BIN --version)"
echo

# --- 2. Get the project ------------------------------------------------------
if [ -d "$TARGET_DIR/.git" ]; then
    echo "Found existing project at $TARGET_DIR, updating it..."
    git -C "$TARGET_DIR" fetch origin "$REPO_BRANCH"
    git -C "$TARGET_DIR" checkout "$REPO_BRANCH"
    git -C "$TARGET_DIR" pull origin "$REPO_BRANCH"
else
    echo "Downloading the project into $TARGET_DIR ..."
    git clone --branch "$REPO_BRANCH" "$REPO_URL" "$TARGET_DIR"
fi
echo

# --- 3. Set up the virtual environment --------------------------------------
cd "$TARGET_DIR"
if [ ! -d .venv ]; then
    echo "Creating a private Python environment..."
    "$PYTHON_BIN" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
echo "Installing required packages..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo

# --- 4. Run it ---------------------------------------------------------------
echo "== Setup complete. Starting the Garmin sync (this is where it may ask for your login) =="
echo
python3 garmin_sync.py --days 3
