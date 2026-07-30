from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import date, datetime, timedelta
from typing import Any


HEADER_ALIASES = {
    "ecard_code": {
        "ecard code", "ecard number", "ecard #", "card code", "card number",
    },
    "first_name": {"first name", "firstname", "first", "given name"},
    "last_name": {"last name", "lastname", "last", "surname", "family name"},
    "full_name": {"name", "participant", "participant name", "student name"},
    "email": {"email", "email address", "e-mail", "e-mail address"},
    "course": {
        "course", "course name", "course module", "course modules",
        "training", "certification", "credential",
    },
    "class_date": {
        "course date", "class date", "completion date", "completed date",
    },
    "issue_date": {"issue date", "issued date", "ecard issue date"},
    "expiration_date": {
        "expiration date", "expiry date", "expires", "expiration", "expiry",
    },
    "corporate_customer": {
        "corporate customer", "customer", "account", "billing account",
        "organization", "company", "employer",
    },
}

COURSE_ALIASES = (
    (re.compile(r"\b(bls|basic life support)\b", re.I), "BLS"),
    (re.compile(r"\b(heartsaver total|hs total)\b", re.I), "HS_TOTAL"),
    (re.compile(r"\bacls\b|advanced cardiovascular life support", re.I), "ACLS"),
    (re.compile(r"\bpals\b|pediatric advanced life support", re.I), "PALS"),
    (re.compile(r"child cpr.*infant cpr|infant cpr.*child cpr", re.I), "CHILD_INFANT_CPR"),
    (re.compile(r"\bheartsaver\b", re.I), "HEARTSAVER_OTHER"),
)

SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return re.sub(r"\s+", " ", str(value).replace("\u00a0", " ")).strip()


def canonical_header(value: Any) -> str:
    text = clean_text(value).casefold()
    text = re.sub(r"[_/.-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    for canonical, aliases in HEADER_ALIASES.items():
        if text in aliases:
            return canonical
    return text


def normalize_email(value: Any) -> str | None:
    text = clean_text(value).casefold()
    if not text:
        return None
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", text):
        return None
    return text


def normalize_ecard(value: Any) -> tuple[str, str | None]:
    raw = clean_text(value)
    if not raw:
        return "", "missing_ecard_code"
    if re.fullmatch(r"\d+\.0+", raw):
        raw = raw.split(".", 1)[0]
    normalized = re.sub(r"[\s-]+", "", raw).upper()
    if not re.fullmatch(r"[A-Z0-9]+", normalized):
        return normalized, "malformed_ecard_code"
    if normalized.isdigit() and len(normalized) != 12:
        return normalized, "unexpected_ecard_length"
    return normalized, None


def _ascii_words(value: str) -> list[str]:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^A-Za-z0-9,' -]+", " ", value)
    return re.findall(r"[A-Za-z0-9]+", value.casefold())


def split_name(first: Any, last: Any, full: Any = "") -> tuple[str, str, str, str]:
    first_text, last_text, full_text = clean_text(first), clean_text(last), clean_text(full)
    raw = " ".join(part for part in (first_text, last_text) if part) or full_text
    if not first_text and not last_text and full_text:
        if "," in full_text:
            left, right = (part.strip() for part in full_text.split(",", 1))
            last_text, first_text = left, right
        else:
            parts = full_text.split()
            first_text = parts[0] if parts else ""
            last_text = " ".join(parts[1:]) if len(parts) > 1 else ""
    first_words = _ascii_words(first_text)
    last_words = _ascii_words(last_text)
    if last_words and last_words[-1] in SUFFIXES:
        suffix = last_words.pop()
        last_words.append(suffix)
    normalized = " ".join(first_words + last_words)
    return first_text, last_text, normalized, raw


def normalize_course(value: Any) -> str:
    raw = clean_text(value)
    if not raw:
        return "UNKNOWN"
    for pattern, canonical in COURSE_ALIASES:
        if pattern.search(raw):
            return canonical
    return "UNKNOWN"


def parse_date(value: Any) -> tuple[str | None, str | None]:
    if value is None or clean_text(value) == "":
        return None, None
    if isinstance(value, datetime):
        return value.date().isoformat(), None
    if isinstance(value, date):
        return value.isoformat(), None
    if isinstance(value, (int, float)) and 1 <= float(value) <= 100000:
        parsed = date(1899, 12, 30) + timedelta(days=int(float(value)))
        return parsed.isoformat(), None
    text = clean_text(value)
    formats = (
        "%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%m-%d-%Y", "%m-%d-%y",
        "%Y/%m/%d",
    )
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date().isoformat(), None
        except ValueError:
            pass
    return None, f"malformed_date:{text}"


def compatible_course(source: str, required: str) -> bool:
    required_normalized = normalize_course(required)
    if source == "UNKNOWN" or required_normalized == "UNKNOWN":
        return False
    return source == required_normalized


def stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def assign_fingerprints(record: Any) -> None:
    semantic = {
        "ecard_code": record.ecard_code,
        "normalized_name": record.normalized_name,
        "email": record.email,
        "normalized_course": record.normalized_course,
        "class_date": record.class_date,
        "issue_date": record.issue_date,
        "expiration_date": record.expiration_date,
        "raw": record.raw_record,
    }
    record.record_fingerprint = stable_hash({"v": 1, **semantic})
    identity = (
        {"ecard_code": record.ecard_code}
        if record.ecard_code
        else {
            "normalized_name": record.normalized_name,
            "email": record.email,
            "normalized_course": record.normalized_course,
            "class_date": record.class_date,
        }
    )
    record.identity_fingerprint = stable_hash({"v": 1, **identity})
