from __future__ import annotations
import argparse, json
from pathlib import Path
from ew_ingest import load_normalized

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--course-export", required=True)
    ap.add_argument("--class-report", required=True)
    ap.add_argument("--output", required=True)
    args=ap.parse_args()
    payload=load_normalized(Path(args.course_export), Path(args.class_report))
    out={"build":{"source_course_export":args.course_export,"source_class_report":args.class_report,"course_count":len(payload["courses"]),"session_count":len(payload["sessions"])},"courses":payload["courses"],"sessions":payload["sessions"]}
    p=Path(args.output); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {p}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
