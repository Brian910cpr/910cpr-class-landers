"""Re-render named selector HTML only, retaining the published availability data."""
from __future__ import annotations

import argparse
import json

from scripts.block_start_time_selector import ROOT, load_block_schedule_page_configs
from scripts.build_bls_block_schedule_pilot import render_html, selector_availability_path
from scripts.inject_global_theme_assets import inject_html


def main() -> None:
    configs = load_block_schedule_page_configs()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pages", nargs="+", choices=sorted(configs))
    args = parser.parse_args()
    for key in args.pages:
        config = configs[key]
        published = json.loads(selector_availability_path(key).read_text(encoding="utf-8"))
        # Schedule dates are fetched by the existing browser selector. Rendering
        # presentation does not recompute availability or rewrite its JSON.
        payload = {"pageKey": key, "pageConfig": config, "generatedAt": published["generatedAt"], "counts": published.get("counts", {}), "dates": []}
        rendered, _ = inject_html(render_html(payload))
        for relative in [config["output_path"], *config.get("alias_output_paths", [])]:
            (ROOT / relative).write_text(rendered, encoding="utf-8")
            print(relative)


if __name__ == "__main__":
    main()
