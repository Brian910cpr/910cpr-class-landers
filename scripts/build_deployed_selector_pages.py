from __future__ import annotations

from scripts.build_bls_block_schedule_pilot import run_page


DEPLOYED_SELECTOR_PAGE_KEYS = ("bls", "heartsaver", "uscg_first_aid_cpr_aed")


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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
