from __future__ import annotations
import argparse, json
from datetime import datetime
from pathlib import Path

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--schedule-json", required=True)
    ap.add_argument("--output", required=True)
    args=ap.parse_args()
    data=json.loads(Path(args.schedule_json).read_text(encoding="utf-8"))
    now=datetime.now()
    sessions=[]
    for s in data.get("sessions", []):
        try:
            if s.get("start") and datetime.fromisoformat(s["start"]) >= now:
                sessions.append(s)
        except Exception:
            pass
    sessions.sort(key=lambda s: s.get("start") or "")
    out={"build":{"source_schedule_json":args.schedule_json,"session_count":len(sessions)},"sessions":sessions}
    p=Path(args.output); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {p}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
