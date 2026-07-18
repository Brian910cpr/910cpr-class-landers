from __future__ import annotations

from pathlib import Path

from scripts.build_bls_block_schedule_pilot import ROOT, render_redirect_html, run_page


DEPLOYED_SELECTOR_PAGE_KEYS = ("bls", "heartsaver", "acls", "pals", "arc", "uscg_first_aid_cpr_aed", "hsi", "family_cpr")


def main() -> int:
    print("Building deployed selector pages and resolved availability artifacts.")
    for page_key in DEPLOYED_SELECTOR_PAGE_KEYS:
        result = run_page(page_key)
        counts = result["counts"]
        print(
            f"{page_key}: offers={counts.get('publicSelectableOfferCount', 0)} "
            f"dates={counts.get('publicSelectableDateCount', 0)} "
            f"starts={counts.get('publicSelectableStartTimeCount', 0)}"
        )
        for path in result["output_paths"]:
            print(f"- {path}")
    arc_redirect = ROOT / "docs" / "arc-schedule.html"
    arc_target = ROOT / "docs" / "arc.html"
    arc_redirect.write_text(render_redirect_html(arc_redirect, arc_target, "Red Cross Schedule"), encoding="utf-8")
    print(f"arc selector: {arc_target}; legacy redirect: {arc_redirect}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
