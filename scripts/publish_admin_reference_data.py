from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PEOPLE_PATH = ROOT / "data" / "config" / "people_catalog.json"
LOCATIONS_PATH = ROOT / "data" / "config" / "location_resource_map.json"
OUT_PEOPLE = ROOT / "docs" / "data" / "admin_people.json"
OUT_LOCATIONS = ROOT / "docs" / "data" / "admin_locations.json"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: Any) -> str:
    return str(value or "").strip()


def publish_people() -> None:
    source = read_json(PEOPLE_PATH)
    rows = []
    for person in source.get("people", []):
        if not isinstance(person, dict):
            continue
        certs = []
        for cert in person.get("certifications", []):
            if not isinstance(cert, dict):
                continue
            certs.append({
                "certification_code": clean(cert.get("certification_code")),
                "provider": clean(cert.get("provider")),
                "family": clean(cert.get("family")),
                "expiration_date": clean(cert.get("expiration_date")) or "UNKNOWN",
            })
        rows.append({
            "person_id": clean(person.get("person_id")),
            "display_name": clean(person.get("display_name")) or "Unnamed instructor",
            "email": clean(person.get("email")),
            "phone": clean(person.get("phone")),
            "instructor_id": clean((person.get("external_ids") or {}).get("instructor_id")),
            "job_association": clean(person.get("job_association")),
            "transfer_status": clean(person.get("transfer_status")),
            "last_verified": clean(person.get("last_verified")),
            "assignment_mode": clean(person.get("assignment_mode")),
            "scheduling_role": clean(person.get("scheduling_role")),
            "certifications": certs,
        })
    OUT_PEOPLE.parent.mkdir(parents=True, exist_ok=True)
    OUT_PEOPLE.write_text(json.dumps({
        "generated_at": datetime.now().astimezone().isoformat(),
        "people": rows,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def publish_locations() -> None:
    source = read_json(LOCATIONS_PATH)
    rows = []
    for location in source.get("locations", []):
        if not isinstance(location, dict):
            continue
        aliases = [clean(v) for v in location.get("aliases", []) if clean(v)]
        resources = []
        for resource in location.get("internal_resources", []):
            if not isinstance(resource, dict):
                continue
            resources.append({
                "resource_name": clean(resource.get("resource_name")),
                "aliases": [clean(v) for v in resource.get("aliases", []) if clean(v)],
                "confirmed_appointment_container": bool(resource.get("confirmed_appointment_container")),
                "notes": clean(resource.get("notes")),
            })
        rows.append({
            "location_key": clean(location.get("location_key")),
            "canonical_public_location": clean(location.get("canonical_public_location")),
            "public_display_name": clean(location.get("public_display_name")),
            "aliases": aliases,
            "internal_resources": resources,
        })
    OUT_LOCATIONS.parent.mkdir(parents=True, exist_ok=True)
    OUT_LOCATIONS.write_text(json.dumps({
        "generated_at": datetime.now().astimezone().isoformat(),
        "locations": rows,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    publish_people()
    publish_locations()
    print(f"Wrote {OUT_PEOPLE}")
    print(f"Wrote {OUT_LOCATIONS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
