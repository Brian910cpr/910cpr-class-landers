import json
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "data" / "enrollware_export.xlsx"
OUTPUT_FILE = ROOT / "docs" / "public_schedule.json"


def normalize_col_name(value) -> str:
    if pd.isna(value):
        return ""
    return " ".join(str(value).replace("\n", " ").replace("\r", " ").split()).strip()


def load_excel_with_detected_header(input_file: Path) -> pd.DataFrame:
    raw = pd.read_excel(input_file, header=None)

    header_row_index = None

    for idx in range(min(len(raw), 10)):
        row_values = [normalize_col_name(v) for v in raw.iloc[idx].tolist()]
        row_set = set(v for v in row_values if v)

        # Your actual export starts with:
        # ID, Course, Start Date / Time, End Date / Time, Location, ...
        if {"ID", "Course", "Start Date / Time"}.issubset(row_set):
            header_row_index = idx
            break

        # Backup matches just in case Enrollware changes names a little
        if {"Course", "Location"}.issubset(row_set) and any("Date" in v for v in row_set):
            header_row_index = idx
            break

    if header_row_index is None:
        preview = []
        for idx in range(min(len(raw), 10)):
            preview.append([normalize_col_name(v) for v in raw.iloc[idx].tolist()])
        raise Exception(
            "Could not detect header row in enrollware_export.xlsx. "
            f"First rows preview: {preview}"
        )

    print(f"Header detected on row {header_row_index}", flush=True)

    df = pd.read_excel(input_file, header=header_row_index)
    df.columns = [normalize_col_name(c) for c in df.columns]
    return df


def pick_first_existing(row: pd.Series, candidates: list[str]):
    for col in candidates:
        if col in row.index and pd.notna(row[col]):
            return row[col]
    return None


def parse_start(row: pd.Series) -> pd.Timestamp:
    date_value = pick_first_existing(
        row,
        [
            "Start Date / Time",
            "Start Date/Time",
            "Date / Time",
            "Date/Time",
            "Date Time",
            "Start",
            "Start Date",
            "Class Date",
            "Date",
            "Starts",
        ],
    )

    time_value = pick_first_existing(
        row,
        [
            "Time",
            "Start Time",
            "Starts At",
        ],
    )

    if date_value is not None and time_value is not None:
        return pd.to_datetime(f"{date_value} {time_value}", errors="raise")

    if date_value is not None:
        return pd.to_datetime(date_value, errors="raise")

    raise KeyError(
        "No valid date column found. Expected one of: "
        "'Start Date / Time', 'Start Date/Time', 'Date / Time', 'Date/Time', "
        "'Date Time', 'Start', 'Start Date', 'Class Date', 'Date', 'Starts'"
    )


def safe_int(value, default: int = 0) -> int:
    if pd.isna(value):
        return default
    try:
        return int(float(value))
    except Exception:
        return default


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_FILE}")

    print(f"Loading Excel: {INPUT_FILE}", flush=True)
    df = load_excel_with_detected_header(INPUT_FILE)
    print("Detected columns:", list(df.columns), flush=True)

    sessions: list[dict] = []
    now = datetime.now()

    total = len(df)
    started = time.time()

    print(f"Processing {total} rows...", flush=True)

    for i, (_, row) in enumerate(df.iterrows(), 1):
        session_id = pick_first_existing(row, ["Class ID", "Session ID", "ID"])
        course_id = pick_first_existing(row, ["Course ID", "CourseID", "ID"])
        title = pick_first_existing(row, ["Course Name", "Class Name", "Title", "Course"])
        location = pick_first_existing(row, ["Location", "Site", "Venue"])
        seats_available = pick_first_existing(row, ["Seats Available", "Open Seats", "Seats"])
        register_url = pick_first_existing(row, ["Registration Link", "Register URL", "URL"])

        if session_id is None or title is None:
            continue

        start = parse_start(row)

        if start.to_pydatetime() < now:
            continue

        session_id_int = safe_int(session_id)

        # If export does not really include Course ID, fall back to ID-shaped value.
        # This keeps the file usable even before a cleaner mapping is added.
        course_id_int = safe_int(course_id, 0)

        session = {
            "session_id": session_id_int,
            "course_id": course_id_int,
            "course": str(title),
            "title": str(title),
            "start": start.strftime("%Y-%m-%d %H:%M:%S"),
            "location": "" if location is None else str(location),
            "seats_available": safe_int(seats_available, 0),
            "register_url": (
                str(register_url).strip()
                if register_url is not None and str(register_url).strip()
                else f"https://coastalcprtraining.enrollware.com/enroll?id={session_id_int}"
            ),
            "schedule_url": (
                f"https://coastalcprtraining.enrollware.com/schedule#ct{course_id_int}"
                if course_id_int
                else "https://coastalcprtraining.enrollware.com/site/coastalcprtraining/schedule"
            ),
        }

        sessions.append(session)

        if i % 250 == 0 or i == total:
            elapsed = time.time() - started
            rate = i / elapsed if elapsed > 0 else 0
            remaining = (total - i) / rate if rate > 0 else 0
            print(
                f"[{i}/{total}] {(i / total) * 100:.1f}% | "
                f"elapsed {elapsed:.1f}s | eta {remaining:.1f}s",
                flush=True,
            )

    sessions.sort(key=lambda x: x["start"])

    payload = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(sessions),
        "sessions": sessions,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Wrote {len(sessions)} future sessions to {OUTPUT_FILE}", flush=True)


if __name__ == "__main__":
    main()