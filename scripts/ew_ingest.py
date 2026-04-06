
from __future__ import annotations

import json
import re
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from openpyxl import load_workbook

META_COMMENT_RE = re.compile(r"<!--\s*META:\s*(\{.*?\})\s*-->", re.DOTALL | re.IGNORECASE)
LONGDESC_RE = re.compile(r'longdesc="([^"]+)"', re.IGNORECASE)
IMG_NAME_RE = re.compile(r'name="([^"]+)"', re.IGNORECASE)
IMG_TITLE_RE = re.compile(r'title="([^"]+)"', re.IGNORECASE)
ITALIC_RE = re.compile(r"<i>(.*?)</i>", re.IGNORECASE | re.DOTALL)
BR_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")

def clean_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unescape(text.replace("\xa0", " "))
    text = BR_RE.sub(" | ", text)
    text = TAG_RE.sub(" ", text)
    text = WHITESPACE_RE.sub(" ", text).strip(" |")
    return text.strip()

def parse_currency(value: Any):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = clean_text(value).replace("$", "").replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None

def slugify(value: str) -> str:
    text = clean_text(value).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "item"

def extract_meta_json(description: Any) -> Dict[str, Any]:
    if description is None:
        return {}
    match = META_COMMENT_RE.search(str(description))
    if not match:
        return {}
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}

def extract_course_html_bits(course_html: Any) -> Dict[str, Any]:
    text = "" if course_html is None else str(course_html)
    longdesc_match = LONGDESC_RE.search(text)
    longdesc = unescape(longdesc_match.group(1)) if longdesc_match else None

    longdesc_map: Dict[str, str] = {}
    if longdesc:
        for chunk in longdesc.split("|"):
            if ":" in chunk:
                k, v = chunk.split(":", 1)
                longdesc_map[k.strip()] = v.strip()

    name_match = IMG_NAME_RE.search(text)
    title_match = IMG_TITLE_RE.search(text)
    italic_match = ITALIC_RE.search(text)
    primary_title = clean_text(text.split("<br", 1)[0])
    subtitle = clean_text(italic_match.group(1)) if italic_match else ""

    return {
        "raw_html": text,
        "display_title": primary_title,
        "subtitle": subtitle,
        "course_id_from_img_name": name_match.group(1).strip() if name_match else None,
        "img_title": clean_text(title_match.group(1)) if title_match else None,
        "longdesc": longdesc,
        "longdesc_map": longdesc_map,
    }

def workbook_rows(path: Path) -> Tuple[List[str], Iterable[Dict[str, Any]]]:
    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = ws.iter_rows(values_only=True)
    headers = [str(h).strip() if h is not None else "" for h in next(rows)]

    def gen():
        for row in rows:
            yield {headers[i]: row[i] if i < len(row) else None for i in range(len(headers))}
    return headers, gen()

def normalize_course_row(row: Dict[str, Any]) -> Dict[str, Any]:
    meta = extract_meta_json(row.get("Description"))
    name = clean_text(row.get("Name"))
    desc_text = clean_text(row.get("Description"))
    course_id = meta.get("course_id")
    if isinstance(course_id, str) and course_id.isdigit():
        course_id = int(course_id)

    price = meta.get("price")
    if price is None:
        price = parse_currency(row.get("Class Price"))

    return {
        "source_name": name,
        "title": name.split("|")[0].strip() if "|" in name else name,
        "name_slug": slugify(name),
        "description_html": row.get("Description") or "",
        "description_text": desc_text,
        "discipline": clean_text(row.get("Discipline")),
        "add_ons": clean_text(row.get("Add-ons")),
        "class_price": price,
        "shipping_price": parse_currency(row.get("Shipping Price")),
        "keycode_bank": clean_text(row.get("Keycode Bank")),
        "card_type": clean_text(row.get("Card Type")),
        "secondary_card_type": clean_text(row.get("Secondary Card Type")),
        "ecard_code": clean_text(row.get("eCard Code")),
        "online_only": clean_text(row.get("Online Only?")).lower() == "yes",
        "allows_unscheduled_students": clean_text(row.get("Allows Unscheduled Students?")).lower() == "yes",
        "course_id": course_id,
        "meta_key": meta.get("meta_key"),
        "course_type": meta.get("course_type"),
        "certifying_body": meta.get("certifying_body"),
        "delivery": meta.get("delivery"),
        "family": meta.get("family") or clean_text(row.get("Discipline")),
        "manual_required": meta.get("manual_required"),
        "manual_options": meta.get("manual_options") or [],
        "cross_sell_addons": meta.get("cross_sell_addons") or [],
        "renewal_cycle_months": meta.get("renewal_cycle_months"),
        "meta": meta,
    }

def normalize_class_row(row: Dict[str, Any]) -> Dict[str, Any]:
    bits = extract_course_html_bits(row.get("Course"))
    longdesc_map = bits.get("longdesc_map", {})
    start_dt = row.get("Start Date / Time")
    end_dt = row.get("End Date / Time")

    course_id = bits.get("course_id_from_img_name") or longdesc_map.get("r")
    if isinstance(course_id, str) and course_id.isdigit():
        course_id = int(course_id)

    raw_location = clean_text(row.get("Location")).lstrip(":").strip()

    return {
        "id": int(row.get("ID")) if row.get("ID") is not None else None,
        "course_raw": row.get("Course") or "",
        "course_display_title": bits.get("display_title") or clean_text(row.get("Course")),
        "course_subtitle": bits.get("subtitle") or "",
        "course_img_title": bits.get("img_title") or "",
        "course_id": course_id,
        "meta_key": longdesc_map.get("t"),
        "certifying_body": longdesc_map.get("cb"),
        "source_code": longdesc_map.get("src"),
        "price": parse_currency(longdesc_map.get("p")),
        "delivery_code": longdesc_map.get("d"),
        "start": start_dt.isoformat() if isinstance(start_dt, datetime) else str(start_dt or ""),
        "end": end_dt.isoformat() if isinstance(end_dt, datetime) else str(end_dt or ""),
        "date": start_dt.date().isoformat() if isinstance(start_dt, datetime) else "",
        "year": start_dt.year if isinstance(start_dt, datetime) else None,
        "location": raw_location,
        "client": clean_text(row.get("Client")),
        "instructor": clean_text(row.get("Instructor")),
        "assistants": clean_text(row.get("Assistants")),
        "students": int(row.get("Students")) if isinstance(row.get("Students"), (int, float)) else 0,
        "seats": int(row.get("Seats")) if isinstance(row.get("Seats"), (int, float)) else 0,
        "hours": float(row.get("Hours")) if isinstance(row.get("Hours"), (int, float)) else None,
        "registration_link": clean_text(row.get("Registration Link")),
        "html_bits": bits,
        "longdesc_map": longdesc_map,
    }

def load_courses_xlsx(path: Path) -> List[Dict[str, Any]]:
    _, rows = workbook_rows(path)
    return [normalize_course_row(row) for row in rows]

def load_classes_xlsx(path: Path) -> List[Dict[str, Any]]:
    _, rows = workbook_rows(path)
    return [normalize_class_row(row) for row in rows]

def match_classes_to_courses(classes: List[Dict[str, Any]], courses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_course_id: Dict[Any, Dict[str, Any]] = {}
    by_meta_key: Dict[str, Dict[str, Any]] = {}
    by_title: Dict[str, Dict[str, Any]] = {}

    for course in courses:
        if course.get("course_id") not in (None, ""):
            by_course_id[course["course_id"]] = course
        if course.get("meta_key"):
            by_meta_key[str(course["meta_key"]).strip().upper()] = course
        if course.get("title"):
            by_title[clean_text(course["title"]).lower()] = course
        if course.get("source_name"):
            by_title[clean_text(course["source_name"]).lower()] = course

    out: List[Dict[str, Any]] = []
    for item in classes:
        matched = None
        if item.get("course_id") in by_course_id:
            matched = by_course_id[item["course_id"]]
        elif item.get("meta_key") and str(item["meta_key"]).strip().upper() in by_meta_key:
            matched = by_meta_key[str(item["meta_key"]).strip().upper()]
        else:
            matched = by_title.get(clean_text(item.get("course_display_title")).lower())

        merged = dict(item)
        if matched:
            merged["matched_course"] = matched
            merged["family"] = matched.get("family") or item.get("certifying_body") or "Other"
            merged["course_title"] = matched.get("title") or item.get("course_display_title")
            merged["certifying_body"] = matched.get("certifying_body") or item.get("certifying_body")
            merged["delivery"] = matched.get("delivery") or item.get("delivery_code")
            merged["meta_key"] = matched.get("meta_key") or item.get("meta_key")
            if merged.get("price") is None:
                merged["price"] = matched.get("class_price")
        else:
            merged["matched_course"] = None
            merged["family"] = item.get("certifying_body") or "Other"
            merged["course_title"] = item.get("course_display_title")
            merged["delivery"] = item.get("delivery_code")
        out.append(merged)
    return out

def topic_slug_for_session(session: Dict[str, Any]) -> str:
    title = clean_text(session.get("course_title") or session.get("course_display_title"))
    family = clean_text(session.get("family"))
    cert_body = clean_text(session.get("certifying_body"))
    test = f"{title} {family}".lower()

    if "bls" in test:
        return "bls"
    if "acls" in test:
        return "acls"
    if "pals" in test:
        return "pals"
    if "heartsaver" in test:
        return "heartsaver"
    if "red cross" in test or cert_body.lower() == "arc":
        return "red-cross"
    if "hsi" in test or cert_body.lower() == "hsi":
        return "hsi"
    if "uscg" in test or "coast guard" in test:
        return "uscg"
    if "instructor" in test:
        return "instructor"
    if "family" in test and "friends" in test:
        return "family-friends"
    if "aed" in test:
        return "aed"
    if "first aid" in test:
        return "first-aid"
    return "misc"

def location_slug(location: str) -> str:
    return slugify(location or "unknown-location")

def session_slug(session: Dict[str, Any]) -> str:
    sid = session.get("id")
    if sid not in (None, ""):
        return str(sid)
    return slugify(f"{session.get('course_title','session')}-{session.get('start','')}-{session.get('location','')}")

def course_slug(course: Dict[str, Any]) -> str:
    cid = course.get("course_id")
    title = course.get("title") or course.get("source_name") or "course"
    if cid not in (None, ""):
        return f"{slugify(title)}-{cid}"
    return slugify(title)
