#!/usr/bin/env python3
"""Pull your Garmin Connect activities and daily wellness data and save
them as plain-English markdown notes plus a data.json file.

Run this on YOUR OWN computer, never in a chat. It only reads data from
your Garmin account (via the python-garminconnect library) -- it never
writes, edits, or deletes anything on your Garmin account.

Usage:
    python3 garmin_sync.py --days 7

First run: if no saved login is found, you'll be asked for your Garmin
email and password (password hidden, via getpass) and, if your account
uses it, a 2FA code. After that, a session token is saved to
~/.garminconnect so future runs (including automatic daily runs) don't
need your password again.
"""
import argparse
import getpass
import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

TOKEN_STORE = os.path.expanduser("~/.garminconnect")
SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR / "garmin"
DATA_JSON = OUTPUT_DIR / "data.json"


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def prompt_mfa() -> str:
    return input("2FA / verification code from Garmin: ").strip()


def get_client() -> Garmin:
    have_saved_session = os.path.exists(TOKEN_STORE)
    interactive = sys.stdin.isatty()

    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")

    if not have_saved_session and not email and not password:
        if not interactive:
            print(
                "No saved Garmin login found and this is a non-interactive run "
                "(e.g. an automatic/scheduled run). Run this script by hand once "
                "first: python3 garmin_sync.py",
                file=sys.stderr,
            )
            sys.exit(1)
        print("First-time setup: logging in to Garmin Connect.")
        email = input("Garmin email: ").strip()
        password = getpass.getpass("Garmin password (hidden, not shown or saved): ")

    client = Garmin(email=email, password=password, prompt_mfa=prompt_mfa)

    try:
        client.login(TOKEN_STORE)
    except (GarminConnectAuthenticationError, GarminConnectConnectionError) as err:
        if have_saved_session and interactive and not (email and password):
            print("Saved session expired or was rejected. Please log in again.")
            email = input("Garmin email: ").strip()
            password = getpass.getpass("Garmin password (hidden, not shown or saved): ")
            client = Garmin(email=email, password=password, prompt_mfa=prompt_mfa)
            client.login(TOKEN_STORE)
        else:
            print(f"Could not log in to Garmin Connect: {err}", file=sys.stderr)
            sys.exit(1)
    except GarminConnectTooManyRequestsError as err:
        print(f"Garmin is rate-limiting login attempts, try again later: {err}", file=sys.stderr)
        sys.exit(1)

    return client


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def dig(d, *path, default=None):
    cur = d
    for p in path:
        if isinstance(cur, dict):
            cur = cur.get(p)
        elif isinstance(cur, list) and isinstance(p, int) and -len(cur) <= p < len(cur):
            cur = cur[p]
        else:
            return default
    return default if cur is None else cur


def first(d, *keys, default=None):
    for k in keys:
        v = d.get(k) if isinstance(d, dict) else None
        if v is not None:
            return v
    return default


def fmt_hms(seconds):
    if not seconds:
        return None
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m"
    return f"{m}m {s}s"


def fmt_hm_short(seconds):
    if not seconds:
        return None
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, _ = divmod(rem, 60)
    return f"{h}h {m:02d}m"


def slugify(text):
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text or "activity").strip("-").lower()
    return text or "activity"


def safe_call(fn, *args):
    """Call a Garmin API method, treating any error as 'no data'."""
    try:
        return fn(*args)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Wellness (one day at a time)
# ---------------------------------------------------------------------------

def collect_wellness_for_day(client: Garmin, day: date) -> dict:
    d = day.isoformat()
    return {
        "date": d,
        "sleep": safe_call(client.get_sleep_data, d),
        "hrv": safe_call(client.get_hrv_data, d),
        "resting_heart_rate": safe_call(client.get_rhr_day, d),
        "body_battery": safe_call(client.get_body_battery, d, d),
        "stress": safe_call(client.get_all_day_stress, d),
        "steps": safe_call(client.get_steps_data, d),
        "training_readiness": safe_call(client.get_training_readiness, d),
        "training_status": safe_call(client.get_training_status, d),
    }


def render_wellness_markdown(w: dict) -> str:
    d = w["date"]
    lines = [f"# Recovery & wellness -- {d}", ""]

    # Sleep
    sleep = w.get("sleep") or {}
    dto = dig(sleep, "dailySleepDTO", default={}) or {}
    sleep_seconds = first(dto, "sleepTimeSeconds")
    score = dig(dto, "sleepScores", "overall", "value")
    quality = dig(dto, "sleepScores", "overall", "qualifierKey")
    lines.append("## Sleep")
    if sleep_seconds:
        line = f"- Total sleep: {fmt_hms(sleep_seconds)}"
        if score:
            line += f" (sleep score: {score}"
            if quality:
                line += f", rated \"{quality.replace('_', ' ')}\""
            line += ")"
        lines.append(line)
        deep = first(dto, "deepSleepSeconds")
        light = first(dto, "lightSleepSeconds")
        rem = first(dto, "remSleepSeconds")
        awake = first(dto, "awakeSleepSeconds")
        stage_bits = []
        if deep:
            stage_bits.append(f"deep {fmt_hms(deep)}")
        if light:
            stage_bits.append(f"light {fmt_hms(light)}")
        if rem:
            stage_bits.append(f"REM {fmt_hms(rem)}")
        if awake:
            stage_bits.append(f"awake {fmt_hms(awake)}")
        if stage_bits:
            lines.append(f"- Stages: {', '.join(stage_bits)}")
        spo2 = first(dto, "averageSpO2Value")
        resp = first(dto, "averageRespirationValue")
        if spo2:
            lines.append(f"- Average blood oxygen (SpO2): {spo2}%")
        if resp:
            lines.append(f"- Average respiration rate: {resp} breaths/min")
    else:
        lines.append("- No sleep data recorded for this day.")
    lines.append("")

    # HRV
    hrv = w.get("hrv") or {}
    hrv_summary = dig(hrv, "hrvSummary", default={}) or {}
    last_night_avg = first(hrv_summary, "lastNightAvg")
    weekly_avg = first(hrv_summary, "weeklyAvg")
    status = first(hrv_summary, "status")
    lines.append("## Heart Rate Variability (HRV)")
    if last_night_avg:
        line = f"- Last night's average HRV: {last_night_avg} ms"
        if weekly_avg:
            line += f" (7-day average: {weekly_avg} ms)"
        if status:
            line += f" -- status: {status.replace('_', ' ').title()}"
        lines.append(line)
    else:
        lines.append("- No HRV data recorded for this day.")
    lines.append("")

    # Resting heart rate
    rhr = w.get("resting_heart_rate") or {}
    rhr_value = dig(rhr, "allMetrics", "metricsMap", "WELLNESS_RESTING_HEART_RATE", 0, "value")
    lines.append("## Resting Heart Rate")
    if rhr_value:
        lines.append(f"- Resting heart rate: {rhr_value} bpm")
    else:
        lines.append("- No resting heart rate data recorded for this day.")
    lines.append("")

    # Body battery
    bb = w.get("body_battery") or []
    bb_entry = bb[0] if isinstance(bb, list) and bb else (bb if isinstance(bb, dict) else {})
    charged = first(bb_entry, "charged")
    drained = first(bb_entry, "drained")
    bb_values = dig(bb_entry, "bodyBatteryValuesArray", default=[]) or []
    start_level = bb_values[0][1] if bb_values and len(bb_values[0]) > 1 else None
    end_level = bb_values[-1][1] if bb_values and len(bb_values[-1]) > 1 else None
    lines.append("## Body Battery")
    if charged or drained or start_level is not None:
        bits = []
        if start_level is not None and end_level is not None:
            bits.append(f"went from {start_level} to {end_level}")
        if charged:
            bits.append(f"recharged {charged} points")
        if drained:
            bits.append(f"drained {drained} points")
        lines.append(f"- {'; '.join(bits)}" if bits else "- Data recorded, see data.json for detail.")
    else:
        lines.append("- No body battery data recorded for this day.")
    lines.append("")

    # Stress
    stress = w.get("stress") or {}
    avg_stress = first(stress, "avgStressLevel", "overallStressLevel")
    rest_min = first(stress, "restStressDuration")
    low_min = first(stress, "lowStressDuration")
    med_min = first(stress, "mediumStressDuration")
    high_min = first(stress, "highStressDuration")
    lines.append("## Stress")
    if avg_stress and avg_stress >= 0:
        lines.append(f"- Average stress level: {avg_stress}/100")
        breakdown = []
        for label, secs in (("resting", rest_min), ("low", low_min), ("medium", med_min), ("high", high_min)):
            if secs:
                breakdown.append(f"{label} {fmt_hms(secs)}")
        if breakdown:
            lines.append(f"- Time in each zone: {', '.join(breakdown)}")
    else:
        lines.append("- No stress data recorded for this day.")
    lines.append("")

    # Steps
    steps = w.get("steps") or []
    total_steps = sum(first(entry, "steps", default=0) or 0 for entry in steps) if isinstance(steps, list) else None
    lines.append("## Steps")
    if total_steps:
        lines.append(f"- Total steps: {total_steps:,}")
    else:
        lines.append("- No step data recorded for this day.")
    lines.append("")

    # Training readiness
    tr = w.get("training_readiness") or []
    tr_entry = tr[0] if isinstance(tr, list) and tr else (tr if isinstance(tr, dict) else {})
    tr_score = first(tr_entry, "score")
    tr_level = first(tr_entry, "level")
    lines.append("## Training Readiness")
    if tr_score is not None:
        line = f"- Training readiness score: {tr_score}/100"
        if tr_level:
            line += f" ({tr_level.replace('_', ' ').title()})"
        lines.append(line)
        for factor_key, label in (
            ("sleepScoreFactorPercent", "sleep"),
            ("hrvFactorPercent", "HRV"),
            ("recoveryTimeFactorPercent", "recovery time"),
            ("acwrFactorPercent", "training load"),
        ):
            val = first(tr_entry, factor_key)
            if val is not None:
                lines.append(f"  - Contributing factor -- {label}: {val}%")
    else:
        lines.append("- No training readiness data recorded for this day.")
    lines.append("")

    lines.append("_Full raw numbers for this day are in `garmin/data.json`._")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Activities
# ---------------------------------------------------------------------------

def meters_to_km_mi(meters):
    if not meters:
        return None, None
    km = meters / 1000
    mi = meters / 1609.344
    return round(km, 2), round(mi, 2)


def render_activity_markdown(a: dict) -> str:
    name = first(a, "activityName", default="Untitled activity")
    activity_type = dig(a, "activityType", "typeKey", default="activity").replace("_", " ")
    start = first(a, "startTimeLocal", default="")
    duration = first(a, "duration")
    distance = first(a, "distance")
    calories = first(a, "calories")
    avg_hr = first(a, "averageHR")
    max_hr = first(a, "maxHR")
    aerobic_te = first(a, "aerobicTrainingEffect")
    anaerobic_te = first(a, "anaerobicTrainingEffect")
    elevation_gain = first(a, "elevationGain")

    km, mi = meters_to_km_mi(distance)

    lines = [f"# {name}", "", f"- Type: {activity_type.title()}", f"- Date/time: {start}"]
    if duration:
        lines.append(f"- Duration: {fmt_hms(duration)}")
    if km:
        lines.append(f"- Distance: {km} km ({mi} mi)")
    if calories:
        lines.append(f"- Calories: {int(calories)}")
    if avg_hr:
        line = f"- Heart rate: avg {int(avg_hr)} bpm"
        if max_hr:
            line += f", max {int(max_hr)} bpm"
        lines.append(line)
    if elevation_gain:
        lines.append(f"- Elevation gain: {round(elevation_gain)} m")
    if aerobic_te or anaerobic_te:
        lines.append(
            f"- Training effect: aerobic {aerobic_te or 0}, anaerobic {anaerobic_te or 0} (0-5 scale)"
        )
    lines.append("")
    lines.append("_Full raw numbers for this activity are in `garmin/data.json`._")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=7, help="How many past days of data to pull (default 7)")
    args = parser.parse_args()

    client = get_client()

    try:
        name = client.get_full_name()
        print(f"Logged in to Garmin Connect as: {name}")
    except Exception:
        print("Logged in to Garmin Connect.")

    (OUTPUT_DIR / "wellness").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "activities").mkdir(parents=True, exist_ok=True)

    if DATA_JSON.exists():
        with open(DATA_JSON) as f:
            data = json.load(f)
    else:
        data = {"wellness": {}, "activities": {}}

    today = date.today()
    days = [today - timedelta(days=i) for i in range(args.days)]

    print(f"\nPulling wellness data for the last {args.days} day(s)...")
    for day in days:
        w = collect_wellness_for_day(client, day)
        data["wellness"][day.isoformat()] = w
        md_path = OUTPUT_DIR / "wellness" / f"{day.isoformat()}.md"
        md_path.write_text(render_wellness_markdown(w))
        print(f"  - {day.isoformat()}: saved {md_path.relative_to(SCRIPT_DIR)}")

    print(f"\nPulling activities from the last {args.days} day(s)...")
    cutoff = today - timedelta(days=args.days - 1)
    activities = safe_call(client.get_activities, 0, 50) or []
    saved = 0
    for a in activities:
        start_str = first(a, "startTimeLocal", default="")
        try:
            a_date = datetime.strptime(start_str[:10], "%Y-%m-%d").date()
        except ValueError:
            continue
        if a_date < cutoff:
            continue
        activity_id = str(first(a, "activityId", default=start_str))
        data["activities"][activity_id] = a
        name = first(a, "activityName", default="activity")
        filename = f"{start_str[:10]}_{slugify(name)}.md"
        md_path = OUTPUT_DIR / "activities" / filename
        md_path.write_text(render_activity_markdown(a))
        print(f"  - {start_str[:10]}: {name} -> saved {md_path.relative_to(SCRIPT_DIR)}")
        saved += 1
    if not saved:
        print("  (no activities found in that window)")

    with open(DATA_JSON, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"\nAll raw data saved to {DATA_JSON.relative_to(SCRIPT_DIR)}")
    print("Done. This never wrote anything back to your Garmin account -- read-only.")


if __name__ == "__main__":
    main()
