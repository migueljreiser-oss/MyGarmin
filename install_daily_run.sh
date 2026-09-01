#!/usr/bin/env bash
# Sets up an automatic daily run of garmin_sync.py, so your recovery data
# refreshes every morning without you doing anything.
#
# On macOS this installs a per-user launchd job (no admin password needed).
# On Linux this installs a per-user cron job.
#
# Safe to re-run: it replaces any previously installed job with this one.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_HOUR="${1:-6}"   # local hour to run at, default 6am

if [ "$(uname -s)" = "Darwin" ]; then
    PLIST="$HOME/Library/LaunchAgents/com.garmin-ai.sync.plist"
    mkdir -p "$HOME/Library/LaunchAgents"
    cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.garmin-ai.sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PROJECT_DIR/.venv/bin/python3</string>
        <string>$PROJECT_DIR/garmin_sync.py</string>
        <string>--days</string>
        <string>1</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key><integer>$RUN_HOUR</integer>
        <key>Minute</key><integer>0</integer>
    </dict>
    <key>StandardOutPath</key><string>$PROJECT_DIR/sync.log</string>
    <key>StandardErrorPath</key><string>$PROJECT_DIR/sync.log</string>
    <key>WorkingDirectory</key><string>$PROJECT_DIR</string>
</dict>
</plist>
EOF
    launchctl unload "$PLIST" >/dev/null 2>&1 || true
    launchctl load "$PLIST"
    echo "Installed. garmin_sync.py will now run automatically every day at ${RUN_HOUR}:00."
    echo "Log output goes to $PROJECT_DIR/sync.log"
    echo "To undo: launchctl unload $PLIST && rm $PLIST"
else
    CRON_LINE="0 $RUN_HOUR * * * cd $PROJECT_DIR && $PROJECT_DIR/.venv/bin/python3 garmin_sync.py --days 1 >> $PROJECT_DIR/sync.log 2>&1"
    ( crontab -l 2>/dev/null | grep -v "garmin_sync.py" ; echo "$CRON_LINE" ) | crontab -
    echo "Installed. garmin_sync.py will now run automatically every day at ${RUN_HOUR}:00."
    echo "Log output goes to $PROJECT_DIR/sync.log"
    echo "To undo: crontab -l | grep -v garmin_sync.py | crontab -"
fi
