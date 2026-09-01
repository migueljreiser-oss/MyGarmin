# garmin-ai

Pulls your own Garmin Connect data -- recent workouts plus daily recovery
numbers (sleep, HRV, resting heart rate, body battery, stress, steps,
training readiness) -- onto your computer as plain-English markdown notes
and a `data.json` file, using the open-source
[`python-garminconnect`](https://github.com/cyberjunky/python-garminconnect)
library.

**Read-only.** This never writes, edits, or deletes anything in your
Garmin account.

## One-time setup

Paste this into your Mac/Linux Terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/migueljreiser-oss/MyGarmin/claude/garmin-watch-connection-kc6cps/bootstrap.sh | bash
```

This will:
1. Check for Python 3.12+ (installing it via Homebrew on macOS if it's missing).
2. Download this project into `~/garmin-ai`.
3. Set up a private Python environment and install the two required packages.
4. Ask for your Garmin email and password right there in the terminal
   (hidden while you type, via `getpass`), plus a 2FA code if your account
   uses it, and log in.
5. Pull your last 3 days of data as a first test.

Your password is never saved anywhere. After the first successful login, a
session token is saved to `~/.garminconnect` (outside this project folder)
so future runs don't ask for your password again.

## Running it again later

```bash
cd ~/garmin-ai
source .venv/bin/activate
python3 garmin_sync.py --days 7
```

## What you get

```
garmin-ai/
  garmin/
    data.json                 <- all the raw numbers, structured by day/activity
    wellness/2026-09-01.md    <- one plain-English note per day
    activities/2026-09-01_morning-run.md   <- one note per workout
```

## Automatic daily runs

To have it sync every morning on its own:

```bash
cd ~/garmin-ai
./install_daily_run.sh
```

This installs a per-user scheduled job (launchd on macOS, cron on Linux)
that runs `garmin_sync.py --days 1` every morning. No password is needed
for these runs since the saved login token is reused. Output is logged to
`sync.log` in the project folder.

To remove it later, see the instructions the script prints after installing.

## Security notes

- Your password is only ever typed into your own terminal and used to talk
  directly to Garmin's servers -- it's never written to disk or shown again.
- The saved session token at `~/.garminconnect/garmin_tokens.json` lets you
  skip logging in again. Delete that folder to sign out.
- This project only calls read (`get_*`) methods from `python-garminconnect`.
  It never calls anything that changes your Garmin account.
