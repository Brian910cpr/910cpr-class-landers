from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
DEBUG_DIR = ROOT / "debug"
CSV_PATH = DEBUG_DIR / "sitewide_link_button_audit.csv"
MD_PATH = DEBUG_DIR / "sitewide_link_button_audit.md"

PUBLIC_HOSTS = {"910cpr.com", "www.910cpr.com", "brian910cpr.github.io"}
ENROLLWARE_HOSTS = {"coastalcprtraining.enrollware.com", "www.enrollware.com", "enrollware.com"}
SKIP_SCHEMES = {"data", "javascript"}
NON_PUBLIC_DIRECTORIES = {"admin", "control-center"}


def public_html_files() -> list[Path]:
    return [
        path
        for path in sorted(DOCS_DIR.rglob("*.html"))
        if not NON_PUBLIC_DIRECTORIES.intersection(path.relative_to(DOCS_DIR).parts)
        and "REVERT TO THIS" not in path.name
        and "LONGLIST" not in path.name
    ]


@dataclass
class AuditRow:
    source_file: str
    source_url: str
    element_type: str
    visible_text: str
    title: str
    aria_label: str
    href: str
    normalized_destination: str
    destination_type: str
    inferred_source_context: str
    inferred_destination_context: str
    confidence: str
    status: str
    notes: str


def clean_text(value: str | None, limit: int = 220) -> str:
    if not value:
        return ""
    text = re.sub(r"\s+", " ", value).strip()
    if len(text) > limit:
        return text[: limit - 3].rstrip() + "..."
    return text


def read_html(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def source_url(path: Path) -> str:
    rel = path.relative_to(DOCS_DIR).as_posix()
    if rel == "index.html":
        return "https://www.910cpr.com/"
    if rel.endswith("/index.html"):
        return "https://www.910cpr.com/" + rel[: -len("index.html")]
    return "https://www.910cpr.com/" + rel


def normalize_internal_href(href: str, source_file: Path) -> tuple[str, str]:
    parsed = urlparse(href)
    raw_path = unquote(parsed.path or "")
    fragment = unquote(parsed.fragment or "")

    if href.startswith("#"):
        rel = source_file.relative_to(DOCS_DIR).as_posix()
        public_path = "/" if rel == "index.html" else "/" + rel
        return public_path, fragment

    if parsed.scheme in {"http", "https"}:
        path = raw_path or "/"
    elif href.startswith("/"):
        path = raw_path or "/"
    else:
        target = (source_file.parent / raw_path).resolve()
        try:
            path = "/" + target.relative_to(DOCS_DIR.resolve()).as_posix()
        except ValueError:
            path = "/" + raw_path.lstrip("/")

    if not path.startswith("/"):
        path = "/" + path
    return path, fragment


def expected_file_for_public_path(path: str) -> Path:
    if path in {"", "/"}:
        return DOCS_DIR / "index.html"
    clean = path.split("?", 1)[0]
    if clean.endswith("/"):
        return DOCS_DIR / clean.lstrip("/") / "index.html"
    target = DOCS_DIR / clean.lstrip("/")
    if target.suffix:
        return target
    html_target = target.with_suffix(".html")
    if html_target.exists():
        return html_target
    return target / "index.html"


def load_anchor_index(html_files: list[Path]) -> dict[Path, set[str]]:
    out: dict[Path, set[str]] = {}
    for path in html_files:
        soup = BeautifulSoup(read_html(path), "html.parser")
        anchors: set[str] = set()
        for tag in soup.find_all(True):
            tag_id = tag.get("id")
            tag_name = tag.get("name")
            if tag_id:
                anchors.add(str(tag_id))
            if tag.name == "a" and tag_name:
                anchors.add(str(tag_name))
        out[path] = anchors
    return out


def classify_destination(href: str, source_file: Path) -> tuple[str, str, Path | None, str]:
    href = href.strip()
    if not href:
        return "missing_or_empty", "", None, ""
    parsed = urlparse(href)
    scheme = parsed.scheme.lower()
    host = parsed.netloc.lower()

    if scheme in SKIP_SCHEMES:
        return "suspicious", href, None, ""
    if scheme in {"tel", "sms"}:
        return "phone", href, None, ""
    if scheme == "mailto":
        return "external", href, None, ""
    if href.startswith("#"):
        path, fragment = normalize_internal_href(href, source_file)
        return "anchor", path + "#" + fragment, expected_file_for_public_path(path), fragment
    if scheme in {"http", "https"} and host in ENROLLWARE_HOSTS:
        return "enrollware_booking", href, None, ""
    if scheme in {"http", "https"} and host not in PUBLIC_HOSTS:
        return "external", href, None, ""

    path, fragment = normalize_internal_href(href, source_file)
    target_file = expected_file_for_public_path(path)
    if path.startswith("/classes/") and target_file.name != "index.html":
        dest_type = "class_lander"
    elif path in {
        "/bls.html",
        "/acls.html",
        "/pals.html",
        "/heartsaver.html",
        "/arc.html",
        "/hsi.html",
        "/uscg-elementary-first-aid-cpr.html",
        "/group-training.html",
    }:
        dest_type = "course_hub"
    else:
        dest_type = "internal_page"
    normalized = path + (("#" + fragment) if fragment else "")
    return dest_type, normalized, target_file, fragment


def infer_source_context(tag, soup: BeautifulSoup, source_file: Path) -> str:
    candidates = []
    for selector in [
        "article",
        "section",
        "nav",
        "header",
        "footer",
        ".slug-pill",
        ".course-jump-card",
        ".class-finder-card",
        ".class-category-card",
        ".training-option-card",
        ".home-course-tile",
    ]:
        found = tag.find_parent(selector)
        if found:
            candidates.append(clean_text(found.get_text(" ", strip=True), 260))
            break
    if not candidates:
        parent = tag.parent
        if parent:
            candidates.append(clean_text(parent.get_text(" ", strip=True), 260))
    h1 = soup.find("h1")
    page_title = clean_text(h1.get_text(" ", strip=True) if h1 else source_file.stem, 80)
    context = candidates[0] if candidates else ""
    return clean_text(f"{page_title} | {context}", 300)


def infer_destination_context(dest_type: str, href: str, normalized: str) -> str:
    if dest_type == "enrollware_booking":
        parsed = urlparse(href)
        qs = parse_qs(parsed.query)
        parts = []
        for key in ["courseId", "id", "appointmentDayId", "startTime"]:
            if key in qs:
                parts.append(f"{key}={qs[key][0]}")
        return "Enrollware booking: " + ", ".join(parts) if parts else "Enrollware link without recognized booking params"
    if dest_type == "phone":
        return "Phone call link"
    if dest_type == "external":
        return "External link"
    if dest_type == "anchor":
        return f"Anchor target {normalized}"
    if dest_type == "course_hub":
        return f"Course hub {normalized}"
    if dest_type == "class_lander":
        return f"Specific class page {normalized}"
    return f"Internal page {normalized}"


def label_keywords(text: str) -> set[str]:
    low = text.lower()
    mapping = {
        "bls": ["bls"],
        "acls": ["acls"],
        "pals": ["pals"],
        "heartsaver": ["heartsaver"],
        "first_aid": ["first aid"],
        "cpr_aed": ["cpr aed", "cpr/aed", "cpr / aed", "cpr + aed"],
        "pediatric": ["pediatric", "childcare", "children"],
        "red_cross": ["red cross"],
        "hsi": ["hsi", "ashi"],
        "uscg": ["uscg", "maritime"],
        "group": ["group", "workplace", "on-site", "onsite"],
    }
    out = set()
    for key, values in mapping.items():
        if any(value in low for value in values):
            out.add(key)
    if re.search(r"\barc\b", low):
        out.add("red_cross")
    return out


def destination_keywords(dest_type: str, normalized: str, href: str) -> set[str]:
    low = (normalized + " " + href).lower()
    out = label_keywords(low.replace("-", " "))
    course_id_map = {
        "209806": "bls",
        "209807": "acls",
        "209808": "pals",
        "209809": "heartsaver",
        "329495": "heartsaver",
        "445670": "hsi",
    }
    qs = parse_qs(urlparse(href).query)
    course_id = (qs.get("courseId") or qs.get("id") or [""])[0]
    if course_id in course_id_map:
        out.add(course_id_map[course_id])
    if dest_type == "enrollware_booking":
        out.add("booking")
    return out


def classify_row(
    dest_type: str,
    visible_text: str,
    title: str,
    aria_label: str,
    href: str,
    normalized: str,
    target_file: Path | None,
    fragment: str,
    anchor_index: dict[Path, set[str]],
    source_context: str,
) -> tuple[str, str, str]:
    label = " ".join(x for x in [visible_text, title, aria_label] if x)
    label_keys = label_keywords(label)
    dest_keys = destination_keywords(dest_type, normalized, href)
    notes: list[str] = []

    if dest_type == "missing_or_empty":
        if source_context.startswith("BUTTON_CONTROL |"):
            return "MEDIUM", "REVIEW", "button control requires browser interaction verification"
        return "LOW", "BROKEN", "empty href"
    if dest_type == "suspicious":
        return "LOW", "SUSPICIOUS", "javascript/data link or otherwise non-navigable href"
    if dest_type in {"internal_page", "class_lander", "course_hub", "anchor"}:
        if target_file is None or not target_file.exists():
            return "LOW", "BROKEN", f"internal target file missing: {target_file}"
        if fragment == "ForwardToEnrollware" and dest_type == "class_lander":
            return "HIGH", "OK", "class lander action fragment used to forward booking intent"
        if fragment and fragment not in anchor_index.get(target_file, set()):
            return "LOW", "BROKEN", f"anchor missing on target page: #{fragment}"
    if dest_type == "enrollware_booking":
        qs = parse_qs(urlparse(href).query)
        has_course = bool(qs.get("courseId") or qs.get("id"))
        if urlparse(href).path.rstrip("/").endswith("/schedule") and urlparse(href).fragment.startswith("ct"):
            return "MEDIUM", "OK", "Enrollware course schedule anchor; exact listed class is not encoded in URL"
        if urlparse(href).path.rstrip("/").endswith("/schedule"):
            return "MEDIUM", "OK", "Broad Enrollware schedule link; not a specific booking URL"
        if urlparse(href).path in {"", "/"}:
            return "MEDIUM", "OK", "Broad Enrollware site link; not a specific booking URL"
        if not has_course:
            notes.append("Enrollware link has no courseId/id parameter")
            return "LOW", "SUSPICIOUS", "; ".join(notes)
        if "appointmentDayId" in qs and "startTime" not in qs:
            notes.append("appointmentDayId present without startTime")
            return "LOW", "SUSPICIOUS", "; ".join(notes)

    # Label/context mismatch checks for the highest-risk course families.
    high_risk = {"bls", "acls", "pals", "heartsaver", "first_aid", "cpr_aed", "pediatric", "red_cross", "hsi", "uscg"}
    label_course_keys = label_keys & high_risk
    dest_course_keys = dest_keys & high_risk
    if label_course_keys and dest_course_keys:
        incompatible = {
            ("bls", "acls"),
            ("bls", "pals"),
            ("acls", "pals"),
            ("red_cross", "hsi"),
            ("red_cross", "uscg"),
            ("hsi", "uscg"),
        }
        for left, right in incompatible:
            if left in label_course_keys and right in dest_course_keys:
                return "LOW", "SUSPICIOUS", f"label suggests {left}, destination suggests {right}"
            if right in label_course_keys and left in dest_course_keys:
                return "LOW", "SUSPICIOUS", f"label suggests {right}, destination suggests {left}"
        if "first_aid" in label_course_keys and "cpr_aed" not in label_course_keys and "cpr_aed" in dest_course_keys:
            return "LOW", "SUSPICIOUS", "label suggests first-aid-only, destination suggests CPR/AED path"

    if not visible_text and not aria_label and dest_type not in {"anchor"}:
        return "LOW", "REVIEW", "link has no visible text or aria-label"
    if dest_type == "enrollware_booking":
        return "MEDIUM", "OK", "; ".join(notes) if notes else "booking parameters present; exact row match needs spot check"
    if label_course_keys and not dest_course_keys and dest_type in {"internal_page", "course_hub"}:
        return "MEDIUM", "REVIEW", "course-like label points to a generic/internal page"
    if not label_course_keys and dest_type in {"class_lander", "course_hub"} and visible_text.lower() in {"details", "more info", "learn more", "view course options"}:
        return "MEDIUM", "OK", "generic CTA to course/class page"
    return "HIGH", "OK", "; ".join(notes)


def extract_elements(path: Path, soup: BeautifulSoup) -> list:
    elements = list(soup.find_all("a"))
    # Include non-link buttons so dead visual controls are visible in the audit.
    for button in soup.find_all("button"):
        if button.find_parent("a"):
            continue
        if button.get("data-tab-target"):
            continue
        elements.append(button)
    return elements


def audit() -> list[AuditRow]:
    html_files = public_html_files()
    anchor_index = load_anchor_index(html_files)
    rows: list[AuditRow] = []
    for path in html_files:
        html = read_html(path)
        soup = BeautifulSoup(html, "html.parser")
        for element in extract_elements(path, soup):
            href = ""
            element_type = element.name
            if element.name == "a":
                href = str(element.get("href") or "")
            elif element.name == "button":
                href = str(element.get("formaction") or element.get("data-href") or element.get("data-target") or element.get("data-tab-target") or "")
                element_type = "button"

            title = clean_text(element.get("title"))
            aria_label = clean_text(element.get("aria-label"))
            visible_text = clean_text(element.get_text(" ", strip=True))
            dest_type, normalized, target_file, fragment = classify_destination(href, path)
            source_ctx = infer_source_context(element, soup, path)
            if element.name == "button" and not href:
                source_ctx = "BUTTON_CONTROL | " + source_ctx
            dest_ctx = infer_destination_context(dest_type, href, normalized)
            confidence, status, notes = classify_row(
                dest_type,
                visible_text,
                title,
                aria_label,
                href,
                normalized,
                target_file,
                fragment,
                anchor_index,
                source_ctx,
            )
            rows.append(
                AuditRow(
                    source_file=str(path.relative_to(ROOT)).replace("\\", "/"),
                    source_url=source_url(path),
                    element_type=element_type,
                    visible_text=visible_text,
                    title=title,
                    aria_label=aria_label,
                    href=href,
                    normalized_destination=normalized,
                    destination_type=dest_type,
                    inferred_source_context=source_ctx,
                    inferred_destination_context=dest_ctx,
                    confidence=confidence,
                    status=status,
                    notes=notes,
                )
            )
    return rows


def write_csv(rows: list[AuditRow]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(rows[0]).keys()) if rows else [field.name for field in AuditRow.__dataclass_fields__.values()])
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def markdown_table(rows: list[AuditRow], limit: int = 50) -> str:
    if not rows:
        return "_None found._\n"
    lines = ["| Status | Confidence | Source | Text | Destination | Notes |", "|---|---:|---|---|---|---|"]
    for row in rows[:limit]:
        lines.append(
            "| {status} | {confidence} | `{source}` | {text} | `{dest}` | {notes} |".format(
                status=row.status,
                confidence=row.confidence,
                source=row.source_file,
                text=clean_text(row.visible_text or row.aria_label or row.title or "(no text)", 80).replace("|", "\\|"),
                dest=clean_text(row.normalized_destination or row.href, 90).replace("|", "\\|"),
                notes=clean_text(row.notes, 120).replace("|", "\\|"),
            )
        )
    if len(rows) > limit:
        lines.append(f"\n_Showing first {limit} of {len(rows)} items. See CSV for all rows._")
    return "\n".join(lines) + "\n"


def duplicate_label_sections(rows: list[AuditRow]) -> tuple[list[tuple[str, list[str]]], list[AuditRow]]:
    destinations_by_label: dict[str, set[str]] = defaultdict(set)
    rows_by_label: dict[str, list[AuditRow]] = defaultdict(list)
    for row in rows:
        label = clean_text(row.visible_text or row.aria_label or row.title)
        if not label or len(label) > 80:
            continue
        if label.lower() in {"details", "book this class", "more info", "learn more", "view course options"}:
            continue
        destinations_by_label[label].add(row.normalized_destination or row.href)
        rows_by_label[label].append(row)
    duplicates = sorted(
        [(label, sorted(dests)) for label, dests in destinations_by_label.items() if len(dests) > 1],
        key=lambda item: (-len(item[1]), item[0].lower()),
    )
    duplicate_rows = []
    for label, _dests in duplicates[:25]:
        duplicate_rows.extend(rows_by_label[label][:3])
    return duplicates, duplicate_rows


def write_markdown(rows: list[AuditRow]) -> None:
    counts = Counter(row.status for row in rows)
    type_counts = Counter(row.destination_type for row in rows)
    confidence_counts = Counter(row.confidence for row in rows)
    broken = [row for row in rows if row.status == "BROKEN"]
    suspicious = [row for row in rows if row.status == "SUSPICIOUS"]
    enrollware_suspicious = [row for row in rows if row.destination_type == "enrollware_booking" and row.status != "OK"]
    internal_mismatch = [row for row in rows if row.destination_type in {"internal_page", "class_lander", "course_hub", "anchor"} and row.status != "OK"]
    low_confidence = [row for row in rows if row.confidence == "LOW" and row.status != "OK"]
    duplicates, duplicate_rows = duplicate_label_sections(rows)

    lines = [
        "# Sitewide Link / Button Audit",
        "",
        "Audit-only report. No links, public pages, Enrollware behavior, deployment settings, or source data were changed by this script.",
        "",
        "## 1. Summary Counts",
        "",
        f"- Public HTML files scanned: {len(public_html_files())}",
        f"- Links/buttons scanned: {len(rows)}",
        f"- Broken: {counts.get('BROKEN', 0)}",
        f"- Suspicious: {counts.get('SUSPICIOUS', 0)}",
        f"- Review: {counts.get('REVIEW', 0)}",
        f"- Low confidence needing review: {len(low_confidence)}",
        "",
        "### By Destination Type",
        "",
    ]
    for key, value in sorted(type_counts.items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "### By Confidence", ""])
    for key, value in sorted(confidence_counts.items()):
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## 2. Broken Links",
            "",
            markdown_table(broken),
            "## 3. Suspicious/Misdirected Links",
            "",
            markdown_table(suspicious),
            "## 4. Enrollware Booking-Link Mismatches",
            "",
            markdown_table(enrollware_suspicious),
            "## 5. Internal Page Mismatches",
            "",
            markdown_table(internal_mismatch),
            "## 6. Duplicate Labels With Different Destinations",
            "",
            f"- Duplicate label groups found: {len(duplicates)}",
            "",
            markdown_table(duplicate_rows),
            "## 7. Low-Confidence Items Needing Brian Review",
            "",
            markdown_table(low_confidence),
            "## 8. Recommended Fixes",
            "",
        ]
    )
    if broken:
        lines.append("- Fix broken internal targets or remove links before the next public deploy.")
    if suspicious:
        lines.append("- Review suspicious course-label/destination mismatches, especially Heartsaver First Aid vs First Aid CPR AED and BLS/ACLS/PALS routing.")
    if duplicates:
        lines.append("- Review duplicate labels with multiple destinations; many generic CTAs are expected, but course-name labels should be consistent.")
    if low_confidence:
        lines.append("- Spot-check low-confidence generic booking links against their visible class row/date/time before treating them as fully audited.")
    if not (broken or suspicious or low_confidence):
        lines.append("- No immediate fixes identified by the automated audit.")
    lines.extend(["", f"Full CSV: `{CSV_PATH.relative_to(ROOT).as_posix()}`", ""])
    MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    rows = audit()
    write_csv(rows)
    write_markdown(rows)
    counts = Counter(row.status for row in rows)
    low_confidence = sum(1 for row in rows if row.confidence == "LOW" and row.status != "OK")
    print(f"Public files scanned: {len(public_html_files())}")
    print(f"Links/buttons scanned: {len(rows)}")
    print(f"Broken: {counts.get('BROKEN', 0)}")
    print(f"Suspicious: {counts.get('SUSPICIOUS', 0)}")
    print(f"Low confidence needing review: {low_confidence}")
    print(f"Wrote: {CSV_PATH}")
    print(f"Wrote: {MD_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
