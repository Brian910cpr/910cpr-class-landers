from __future__ import annotations

from collections import Counter

from scripts.audit_sitewide_links import audit, public_html_files, write_csv, write_markdown


def main() -> int:
    """Run the sitewide link audit and fail when any BROKEN rows exist.

    The underlying audit module remains usable as an advisory/reporting tool.
    Canonical publication should call this strict wrapper so a positive broken-link
    finding cannot be followed by a green publish.
    """
    rows = audit()
    write_csv(rows)
    write_markdown(rows)

    counts = Counter(row.status for row in rows)
    broken = counts.get("BROKEN", 0)
    suspicious = counts.get("SUSPICIOUS", 0)
    low_confidence = sum(1 for row in rows if row.confidence == "LOW" and row.status != "OK")

    print(f"Public files scanned: {len(public_html_files())}")
    print(f"Links/buttons scanned: {len(rows)}")
    print(f"Broken: {broken}")
    print(f"Suspicious: {suspicious}")
    print(f"Low confidence needing review: {low_confidence}")
    print("Wrote: debug/sitewide_link_button_audit.csv")
    print("Wrote: debug/sitewide_link_button_audit.md")

    if broken:
        print(f"FAIL-CLOSED: refusing publication because the sitewide audit found {broken} broken link(s)/button target(s).")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
