def parse_flex(value):
    """
    Ultra-tolerant date finder:
      - Handles JS Date strings like 'Sat Sep 20 2025 17:00:00 GMT-0400 (Eastern Daylight Time)'
      - Handles ISO, 'YYYY-MM-DD HH:MM', 'M/D/YYYY H:MM AM', 'Jan 5, 2026 9:00 AM'
      - Understands Excel date serials like 45678 or 45678.5
      - Ignores trailing text after a dash/em dash
    Returns datetime or None.
    """
    if value is None: 
        return None
    s = to_str(value).strip()
    if not s: 
        return None

    # trim “ — details …” or “ – details …”
    s = re.sub(r"\s*[–—-]\s*.*$", "", s)
    s = s.replace("@", " ").replace(" at ", " ")
    s = normalize_spaces(s)

    # --- 0) JS Date string: 'Sat Sep 20 2025 17:00:00 GMT-0400 (Eastern Daylight Time)'
    m = re.match(r"^[A-Za-z]{3}\s+([A-Za-z]{3})\s+(\d{1,2})\s+(\d{4})\s+(\d{2}):(\d{2})(?::(\d{2}))?\s+GMT([+-]\d{4})", s)
    if m:
        mon, da, yr, hh, mi, ss, _gmtoff = m.groups()
        try:
            M = MONTHS.index(mon[:3].upper()) + 1
            H = int(hh); MI = int(mi); SS = int(ss or 0)
            # The JS string shows local time already (e.g., EDT). Keep that time as-is.
            return datetime(int(yr), M, int(da), H, MI, SS)
        except Exception:
            pass

    # --- 1) Excel serial like 45782.5
    if re.fullmatch(r"\d+(\.\d+)?", s) and is_excel_serial(s):
        try:
            return parse_excel_serial(s)
        except Exception:
            pass

    # --- 2) Native ISO parse
    try:
        return datetime.fromisoformat(s)
    except Exception:
        pass

    # --- 3) YYYY-MM-DD HH:MM[:SS] [AM/PM] [TZ letters]
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})[ T](\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM)?\s*([A-Za-z]{1,4})?$", s, re.I)
    if m:
        Y, M, D, hh, mm, ss, ap, _tz = m.groups()
        H = int(hh)
        if ap:
            ap = ap.upper()
            if ap == "PM" and H != 12: H += 12
            if ap == "AM" and H == 12: H = 0
        return datetime(int(Y), int(M), int(D), H, int(mm), int(ss or 0))

    # --- 4) M/D/YYYY [H:MM] [AM/PM]
    m = re.match(r"^(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})(?:\s+(\d{1,2})(?::(\d{2}))?\s*(AM|PM)?)?$", s, re.I)
    if m:
        mo, da, yr, hh, mi, ap = m.groups()
        H = int(hh) if hh else 9
        if ap:
            ap = ap.upper()
            if ap == "PM" and H != 12: H += 12
            if ap == "AM" and H == 12: H = 0
        return datetime(int(yr), int(mo), int(da), H, int(mi or 0), 0)

    # --- 5) Mon D, YYYY [H:MM] [AM/PM]
    m = re.match(r"^([A-Za-z]{3,})\s+(\d{1,2}),\s*(\d{4})(?:\s+(\d{1,2})(?::(\d{2}))?\s*(AM|PM)?)?$", s)
    if m:
        mon, da, yr, hh, mi, ap = m.groups()
        try:
            M = MONTHS.index(mon[:3].upper()) + 1
            H = int(hh) if hh else 9
            if ap:
                ap = ap.upper()
                if ap == "PM" and H != 12: H += 12
                if ap == "AM" and H == 12: H = 0
            return datetime(int(yr), M, int(da), H, int(mi or 0), 0)
        except Exception:
            pass

    # --- 6) Fallback: ISO-ish core like 2025-03-10 or 2025-03-10 9:00
    m = re.search(r"(\d{4}-\d{2}-\d{2})(?:[ T](\d{1,2}):(\d{2}))?", s)
    if m:
        ymd, hh, mi = m.groups()
        H = int(hh) if hh else 9
        return datetime.fromisoformat(f"{ymd} {H:02d}:{(mi or '00')}")

    return None
