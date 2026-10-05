"""Read-only release preflight; does not publish or infer room availability.

Input is an explicitly sourced resource-coverage snapshot, not the lab fixture.
Run: python -m scripts.layered_resource_readiness SNAPSHOT.json
Exit 2 means blocked. This check alone never proves production scheduling.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def timestamp(value):
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError("timestamp requires timezone")
    return parsed.astimezone(timezone.utc)


def audit(snapshot, now=None):
    now = now or datetime.now(timezone.utc)
    if now.utcoffset() is None:
        raise ValueError("now requires timezone")
    issues, intersections = [], []

    def issue(code, source=None):
        issues.append({"code": code, "source_id": source})

    def valid(row, layer):
        ident = row.get("id")
        try:
            start, end = timestamp(row["start"]), timestamp(row["end"])
            observed = timestamp(row["observed_at"])
            ttl = float(row["freshness_minutes"])
            if not ident or not row.get("source") or row.get("status") != "known_complete":
                raise ValueError("missing provenance or coverage")
            if end <= start or ttl <= 0:
                raise ValueError("invalid interval or freshness")
            if observed > now or (now - observed).total_seconds() > ttl * 60:
                issue("stale_or_future_" + layer, ident)
                return None
            return start, end
        except (KeyError, ValueError, TypeError):
            issue("invalid_" + layer + "_coverage", ident)
            return None

    rooms = snapshot.get("room_availability", [])
    instructors = snapshot.get("instructor_availability", [])
    commitments = snapshot.get("commitment_coverage", [])
    if not rooms:
        issue("missing_room_availability")
    if not instructors:
        issue("missing_instructor_availability")
    resource_ids = {r.get("id") for r in snapshot.get("resources", [])
                    if r.get("active") is True and r.get("location")}
    valid_rooms, valid_instructors, valid_commitments = [], [], []
    for row in rooms:
        interval = valid(row, "room")
        if row.get("resource_id") not in resource_ids or not row.get("location"):
            issue("unresolved_room_resource", row.get("id"))
            continue
        # The current layered engine models a single room. Student seat capacity
        # is a different quantity and must never be substituted here.
        if row.get("simultaneous_classes") != 1:
            issue("unsupported_or_unknown_room_concurrency", row.get("id"))
            continue
        if interval:
            valid_rooms.append((row, interval))
    for row in instructors:
        interval = valid(row, "instructor")
        if not row.get("instructor_id") or not row.get("locations"):
            issue("unresolved_instructor", row.get("id"))
        elif interval:
            valid_instructors.append((row, interval))
    for row in commitments:
        interval = valid(row, "commitment")
        if interval:
            valid_commitments.append((row, interval))
    for room, (rs, re) in valid_rooms:
        for instructor, (ins, ine) in valid_instructors:
            if room["location"] not in instructor["locations"]:
                continue
            start, end = max(rs, ins), min(re, ine)
            if start >= end:
                continue
            covered = any(c.get("instructor_id") == instructor["instructor_id"]
                          and c.get("location") == room["location"]
                          and cs <= start and end <= ce
                          for c, (cs, ce) in valid_commitments)
            if not covered:
                issue("missing_complete_commitment_coverage", instructor["id"])
                continue
            intersections.append({"room_source_id": room["id"],
                                  "instructor_source_id": instructor["id"],
                                  "resource_id": room["resource_id"],
                                  "instructor_id": instructor["instructor_id"],
                                  "location": room["location"],
                                  "start": start.isoformat(), "end": end.isoformat()})
    if not intersections:
        issue("no_proven_resource_intersections")
    return {"schema_version": "layered-resource-readiness.v1",
            "checked_at": now.isoformat(),
            "state": "BLOCKED" if issues else "RESOURCE_INPUTS_READY",
            "issues": issues, "intersections": intersections,
            "counts": {"resources": len(snapshot.get("resources", [])),
                       "room_windows": len(rooms), "instructor_windows": len(instructors),
                       "proven_intersections": len(intersections)},
            "limitation": "Readiness only; qualification, occupancy, booking links, roster gates and rendered offers still require independent proof."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    args = parser.parse_args()
    report = audit(json.loads(args.snapshot.read_text(encoding="utf-8")))
    print(json.dumps(report, indent=2))
    return 2 if report["state"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
