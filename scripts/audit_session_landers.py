from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

try:
    from scripts.build_landers import normalize_session_record, same_course_family, is_mapped
except ModuleNotFoundError:
    from build_landers import normalize_session_record, same_course_family, is_mapped


CTA_RE = re.compile(r'<div class="cta-row">\s*<a[^>]+href="([^"]+)"[^>]*>\s*Register Now\s*</a>', re.I)
UPCOMING_RE = re.compile(
    r'<div class="upcoming-card[^"]*"[^>]*data-session-id="([^"]+)"(?P<body>.*?)</div>\s*</div>',
    re.I | re.S,
)
HREF_RE = re.compile(r'<a[^>]+href="([^"]+)"[^>]*>\s*Register\s*</a>', re.I)
FAVICON_RE = re.compile(r'<link[^>]+rel="(?:shortcut icon|icon|apple-touch-icon)"', re.I)


def load_sessions(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [normalize_session_record(item) for item in data.get("sessions", [])]


def sample_for(sessions: list[dict[str, Any]], family: str, body: str = "AHA") -> dict[str, Any] | None:
    for session in sessions:
        if (
            str(session.get("mapped_family") or "").lower() == family.lower()
            and str(session.get("mapped_certifying_body") or "").upper() == body.upper()
            and session.get("session_id")
        ):
            return session
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit generated 910CPR session landers.")
    parser.add_argument("--data-file", default="data/sessions_current.json")
    parser.add_argument("--docs-dir", default="docs")
    parser.add_argument("--output", default="debug/session_lander_product_audit.json")
    args = parser.parse_args()

    root = Path.cwd()
    docs_dir = (root / args.docs_dir).resolve()
    classes_dir = docs_dir / "classes"
    sessions = load_sessions((root / args.data_file).resolve())
    by_id = {str(s.get("session_id") or ""): s for s in sessions if s.get("session_id")}

    html_paths = sorted(path for path in classes_dir.glob("*.html") if path.stem.isdigit())
    html_ids = {path.stem for path in html_paths}
    missing_pages: list[dict[str, Any]] = []
    main_link_mismatches: list[dict[str, Any]] = []
    alternate_link_mismatches: list[dict[str, Any]] = []
    alternate_cross_family: list[dict[str, Any]] = []
    missing_mapping_fields: list[dict[str, Any]] = []
    favicon_missing: list[str] = []
    product_layout_missing: list[str] = []

    required_fields = ["mapped_certifying_body", "mapped_family", "mapped_delivery_mode", "registration_url"]
    for session in sessions:
        sid = str(session.get("session_id") or "")
        path = classes_dir / f"{sid}.html"
        if not path.exists():
            missing_pages.append({"session_id": sid, "reason": "missing generated html"})
            continue

        if is_mapped(session):
            missing = [field for field in required_fields if not session.get(field)]
            if missing:
                missing_mapping_fields.append({"session_id": sid, "missing": missing})

        html = path.read_text(encoding="utf-8", errors="ignore")
        if not FAVICON_RE.search(html):
            favicon_missing.append(str(path.relative_to(root)))
        if "confidence-block" not in html or "trust-snippet" not in html or "course-description-priority" not in html:
            product_layout_missing.append(str(path.relative_to(root)))

        expected_register = str(session.get("registration_url") or "")
        main_match = CTA_RE.search(html)
        actual_register = main_match.group(1) if main_match else ""
        if actual_register != expected_register:
            main_link_mismatches.append(
                {
                    "session_id": sid,
                    "expected": expected_register,
                    "actual": actual_register,
                    "reason": "main Register Now href mismatch",
                }
            )

        for match in UPCOMING_RE.finditer(html):
            alt_sid = match.group(1)
            alt = by_id.get(alt_sid)
            href_match = HREF_RE.search(match.group("body"))
            actual_alt_href = href_match.group(1) if href_match else ""
            if not alt:
                alternate_link_mismatches.append(
                    {"session_id": sid, "alternate_session_id": alt_sid, "actual": actual_alt_href, "reason": "alternate not in source"}
                )
                continue
            expected_alt_href = str(alt.get("registration_url") or "")
            if actual_alt_href != expected_alt_href:
                alternate_link_mismatches.append(
                    {
                        "session_id": sid,
                        "alternate_session_id": alt_sid,
                        "expected": expected_alt_href,
                        "actual": actual_alt_href,
                    }
                )
            if not same_course_family(session, alt):
                alternate_cross_family.append(
                    {
                        "session_id": sid,
                        "alternate_session_id": alt_sid,
                        "session_body": session.get("mapped_certifying_body"),
                        "session_family": session.get("mapped_family"),
                        "alternate_body": alt.get("mapped_certifying_body"),
                        "alternate_family": alt.get("mapped_family"),
                    }
                )

    sample_specs = {
        "aha_bls_provider": ("BLS", "AHA"),
        "aha_acls": ("ACLS", "AHA"),
        "aha_pals": ("PALS", "AHA"),
        "heartsaver": ("Heartsaver", "AHA"),
        "arc": ("", "ARC"),
        "hsi": ("", "HSI"),
        "uscg_elementary_first_aid": ("USCG", "AHA"),
    }
    samples: dict[str, str | None] = {}
    for key, (family, body) in sample_specs.items():
        found = None
        if family:
            found = sample_for(sessions, family, body)
        else:
            for session in sessions:
                if str(session.get("mapped_certifying_body") or "").upper() == body:
                    found = session
                    break
        samples[key] = str((classes_dir / f"{found['session_id']}.html").resolve()) if found else None

    index_paths = [docs_dir / "index.html", docs_dir / "bls.html", docs_dir / "acls.html", docs_dir / "pals.html"]
    hub_favicon_missing = [
        str(path.relative_to(root))
        for path in index_paths
        if path.exists() and not FAVICON_RE.search(path.read_text(encoding="utf-8", errors="ignore"))
    ]

    unmapped = [s for s in sessions if not is_mapped(s)]
    report = {
        "sessions_source": str((root / args.data_file).resolve()),
        "generated_class_pages": len(html_paths),
        "source_sessions": len(sessions),
        "pages_updated": sum(1 for s in sessions if (classes_dir / f"{s.get('session_id')}.html").exists()),
        "extra_numeric_class_pages_not_in_source": sorted(html_ids - set(by_id.keys())),
        "mapped_sessions": len(sessions) - len(unmapped),
        "unmapped_or_uncertain_course_mappings": len(unmapped),
        "unmapped_examples": [
            {
                "session_id": s.get("session_id"),
                "course_id": s.get("course_id"),
                "course_name": s.get("course_name"),
                "registration_url": s.get("registration_url"),
                "mapping_status": s.get("mapping_status"),
                "mapping_notes": s.get("mapping_notes", []),
            }
            for s in unmapped[:50]
        ],
        "missing_pages": missing_pages,
        "sessions_missing_validation_fields": missing_mapping_fields,
        "main_registration_link_mismatches": main_link_mismatches,
        "alternate_registration_link_mismatches": alternate_link_mismatches,
        "alternate_cross_family_or_body": alternate_cross_family,
        "favicon_missing_class_pages": favicon_missing[:100],
        "favicon_missing_hub_pages": hub_favicon_missing,
        "product_layout_missing_pages": product_layout_missing[:100],
        "sample_pages": samples,
    }

    output_path = (root / args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not (missing_pages or main_link_mismatches or alternate_link_mismatches or alternate_cross_family or favicon_missing or product_layout_missing) else 1


if __name__ == "__main__":
    raise SystemExit(main())
