@'
"""
Smoke test:
- Opens https://www.hovn.app/admin/910cpr/sessions
- Waits for the "Export" button
- Holds Ctrl and clicks it (should trigger "Export All")
- Confirms a CSV download occurred and prints the saved path
Nothing else (no rebuilds, no git).
"""

import sys
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeoutError

TARGET_URL = "https://www.hovn.app/admin/910cpr/sessions"

# Keep a persistent browser profile so you only need to log in once.
PROFILE_DIR = Path(__file__).resolve().parent / "playwright_profile_quickcheck"
PROFILE_DIR.mkdir(parents=True, exist_ok=True)

# Where to drop the downloaded CSV (does not touch your real data/sessions.csv)
OUT_DIR = Path(__file__).resolve().parents[1] / "_diagnostics"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def main():
    import os
    headless = os.environ.get("PW_HEADLESS") in ("1", "true", "True")

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=headless,
            accept_downloads=True,
            args=["--disable-dev-shm-usage"],
        )
        page = ctx.new_page()
        page.goto(TARGET_URL, wait_until="domcontentloaded")

        try:
            export_btn = page.get_by_role("button", name="Export")
            export_btn.wait_for(timeout=60_000)
        except PwTimeoutError:
            print("ERROR: Could not find an 'Export' button. Are you logged in and on the Sessions page?")
            ctx.close()
            sys.exit(2)

        # Ctrl+Click to trigger "Export All"
        with page.expect_download() as dl_info:
            page.keyboard.down("Control")
            export_btn.click()
            page.keyboard.up("Control")
        download = dl_info.value

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = OUT_DIR / f"hovn_export_all_{ts}.csv"
        download.save_as(str(out_path))

        print(f"OK: Downloaded CSV -> {out_path}")
        try:
            head = out_path.read_text(encoding="utf-8", errors="ignore").splitlines()[:3]
            print("CSV head:")
            for line in head:
                print("  " + line[:200])
        except Exception as e:
            print(f"Note: could not preview file text ({e})")

        ctx.close()

if __name__ == "__main__":
    main()
'@ | Set-Content -Encoding UTF8 .\tools\quickcheck_export_hovn.py
