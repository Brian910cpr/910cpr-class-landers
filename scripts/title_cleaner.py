# D:\Users\ten77\Documents\GitHub\910cpr-class-landers\scripts\title_cleaner.py

import re
import unicodedata
from html import unescape

MANUAL_TITLE_OVERRIDES = {
    "AHA - PALS Provider Plus - Online / Skills Session": "AHA PALS Provider Plus Skills Session",
    "Healthcare Provider: BLS Course Basic Life Support BLS for healthcare professionals trains participants to promptly recognize several life-threatening emergencies": "AHA BLS Provider CPR Class",
}

BAD_PREFIXES = (
    "z personal event",
    "personal event - not available",
    "personal event - not availible",
    "cardiopartners",
    "heartsaver institute",
    "other programs",
)

NOISE_PHRASES = [
    "instructor-led classroom for expired or new",
    "instructor-led classroom program for",
    "online coursework with in-person skills testing",
    "blended learning with in-person, instructor-led skills session",
    "an assessment-only session for experienced providers needing to renew their certification",
    "an assessment-only session for experienced providers ready to test out and renew certification",
    "need a reliable cpr class for your team?",
    "flexible scheduling, simple pricing, and a proven track record of reliability.",
    "we show up on time, every time.",
    "we show up-on time, every time.",
    "contact us today!",
    "same day certification",
    "receive the same card as the in-person class but significantly more convenient.",
    "become an instructor and teach cpr, first aid, or bls through aha, hsi, or red cross.",
]

SPANISH_KEEP = [
    "primeros auxilios",
    "rcp",
    "dea",
    "familiares y amigos",
]


def strip_accents_and_weird(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def basic_clean(raw: str) -> str:
    if raw is None:
        return ""

    text = unescape(str(raw))
    text = strip_accents_and_weird(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"[\u200b-\u200f\u202a-\u202e]", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    for phrase in NOISE_PHRASES:
        text = re.sub(re.escape(phrase), " ", text, flags=re.IGNORECASE)

    text = re.sub(r"\s+", " ", text).strip(" -|:")
    return text


def looks_internal_or_junk(title: str) -> bool:
    t = title.lower().strip()
    return any(t.startswith(x) for x in BAD_PREFIXES)


def has_any(text: str, terms) -> bool:
    tl = text.lower()
    return any(term.lower() in tl for term in terms)


def detect_brand(text: str) -> str:
    tl = text.lower()

    if "american red cross" in tl or tl.startswith("arc ") or "arc -" in tl:
        return "ARC"
    if "american heart association" in tl or tl.startswith("aha ") or "aha -" in tl:
        return "AHA"
    if tl.startswith("hsi ") or " hsi " in tl:
        return "HSI"

    return ""


def clean_osha_title(text: str) -> str:
    tl = text.lower()

    if "osha 10" in tl and "construction" in tl:
        return "OSHA 10 Construction"
    if "osha 10" in tl and "general" in tl:
        return "OSHA 10 General Industry"
    if "osha 30" in tl and "construction" in tl:
        return "OSHA 30 Construction"
    if "osha 30" in tl and "general" in tl:
        return "OSHA 30 General Industry"
    if "fall protection" in tl:
        return "OSHA Fall Protection Awareness"
    if "back safety" in tl or "safe lifting" in tl:
        return "OSHA Back Safety and Safe Lifting"

    return ""


def clean_special_title(text: str) -> str:
    tl = text.lower()

    if "stop the bleed" in tl:
        return "Stop the Bleed Class"

    if "cpr for divers" in tl:
        return "CPR for Divers Class"

    if "family & friends" in tl or "familiares y amigos" in tl:
        return "Family & Friends CPR Class"

    if "infant cpr" in tl and "choking" in tl:
        return "Infant CPR and Choking Relief Class"

    if "elementary first aid" in tl and "online" in tl:
        return "USCG Elementary First Aid Online"

    if "elementary first aid" in tl:
        return "USCG Elementary First Aid Class"

    return ""


def clean_instructor_title(text: str) -> str:
    tl = text.lower()

    if "instructor update" in tl:
        return "AHA Instructor Update"

    if "become an american heart association instructor" in tl:
        if "bls, acls & pals" in tl or "bls acls pals" in tl:
            return "AHA BLS ACLS and PALS Instructor Course"
        if "bls" in tl:
            return "AHA BLS Instructor Course"
        if "acls" in tl:
            return "AHA ACLS Instructor Course"
        if "pals" in tl:
            return "AHA PALS Instructor Course"
        if "heartsaver" in tl:
            return "AHA Heartsaver Instructor Course"

    if "instructor renewal" in tl:
        if "bls" in tl:
            return "AHA BLS Instructor Renewal"
        if "acls" in tl:
            return "AHA ACLS Instructor Renewal"
        if "pals" in tl:
            return "AHA PALS Instructor Renewal"

    return ""


def clean_core_title(text: str) -> str:
    tl = text.lower()
    brand = detect_brand(text)

    osha = clean_osha_title(text)
    if osha:
        return osha

    special = clean_special_title(text)
    if special:
        return special

    instructor = clean_instructor_title(text)
    if instructor:
        return instructor

    is_blended = has_any(text, [
        "blended learning",
        "online class with in-person skill session",
        "online + in-person skills",
        "online c in-person skills",
        "online or skills session",
        "heartcode",
        "skills session",
        "skills testing",
        "in-person skills",
    ])

    is_challenge = has_any(text, ["challenge", "assessment-only", "test out"])
    is_group = has_any(text, ["group", "on-site", "onsite"])
    is_spanish = has_any(text, SPANISH_KEEP)

    if "acls" in tl:
        if "instructor" in tl:
            return "AHA ACLS Instructor Course"
        if is_blended:
            return f"{brand or 'AHA'} ACLS HeartCode Skills Session"
        return f"{brand or 'AHA'} ACLS Provider Class"

    if "pals provider plus" in tl:
        return "AHA PALS Provider Plus Skills Session"

    if "pals" in tl:
        if "instructor" in tl:
            return "AHA PALS Instructor Course"
        if is_blended:
            return f"{brand or 'AHA'} PALS HeartCode Skills Session"
        return f"{brand or 'AHA'} PALS Provider Class"

    if re.search(r"\bbls\b", tl):
        if "instructor" in tl:
            return f"{brand or 'AHA'} BLS Instructor Course"
        if is_challenge:
            return f"{brand or 'AHA'} BLS Renewal Challenge"
        if is_blended:
            if brand == "AHA":
                return "AHA BLS HeartCode Skills Session"
            if brand == "ARC":
                return "ARC BLS Blended Learning Skills Session"
            if brand == "HSI":
                return "HSI BLS Blended Learning Skills Session"
        if is_group:
            return f"{brand or 'AHA'} Onsite Group BLS Class"
        return f"{brand or 'AHA'} BLS Provider CPR Class"

    if "heartsaver" in tl and "pediatric" in tl and ("cpr" in tl or "aed" in tl or "first aid" in tl):
        if is_blended:
            return "AHA Heartsaver Pediatric First Aid CPR AED Skills Session"
        return "AHA Heartsaver Pediatric First Aid CPR AED Class"

    if "heartsaver" in tl and "k-12" in tl:
        return "AHA Heartsaver K-12 CPR AED Class"

    if "heartsaver" in tl and "first aid" in tl and ("cpr" in tl or "aed" in tl):
        if is_blended:
            return "AHA Heartsaver First Aid CPR AED Skills Session"
        return "AHA Heartsaver First Aid CPR AED Class"

    if "heartsaver" in tl and ("cpr" in tl or "aed" in tl):
        if is_blended:
            return "AHA Heartsaver CPR AED Skills Session"
        return "AHA Heartsaver CPR AED Class"

    if brand == "HSI" and "first aid" in tl and ("cpr" in tl or "aed" in tl):
        if "pediatric" in tl:
            return "HSI Pediatric First Aid CPR AED Class"
        if is_blended:
            return "HSI First Aid CPR AED Blended Learning Skills Session"
        return "HSI First Aid CPR AED Class"

    if brand == "HSI" and ("cpr" in tl or "aed" in tl):
        if is_blended:
            return "HSI CPR AED Blended Learning Skills Session"
        return "HSI CPR AED Class"

    if brand == "ARC" and "first aid" in tl and ("cpr" in tl or "aed" in tl):
        if is_blended:
            return "ARC First Aid CPR AED Blended Learning Skills Session"
        return "ARC First Aid CPR AED Class"

    if brand == "ARC" and ("cpr" in tl or "aed" in tl):
        if is_blended:
            return "ARC CPR AED Blended Learning Skills Session"
        return "ARC CPR AED Class"

    if "asls" in tl:
        if is_blended or "online" in tl:
            return "AHA ASLS Online Skills Session"
        return "AHA ASLS Provider Class"

    if is_spanish:
        return text

    return text


def normalize_course_title(raw_title: str) -> str | None:
    if raw_title is None:
        return None

    raw_text = unescape(str(raw_title)).strip()
    if raw_text in MANUAL_TITLE_OVERRIDES:
        return MANUAL_TITLE_OVERRIDES[raw_text]

    cleaned = basic_clean(raw_title)
    if not cleaned:
        return None

    if cleaned in MANUAL_TITLE_OVERRIDES:
        return MANUAL_TITLE_OVERRIDES[cleaned]

    if looks_internal_or_junk(cleaned):
        return None

    final_title = clean_core_title(cleaned)
    final_title = re.sub(r"\s+", " ", final_title).strip(" -|:")

    return final_title or None


def seo_title_for_session(course_title: str, city: str = "", state: str = "NC") -> str:
    base = normalize_course_title(course_title) or basic_clean(course_title) or "CPR Class"
    if city:
        return f"{base} in {city}, {state}"
    return base