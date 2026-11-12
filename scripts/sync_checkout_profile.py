"""Mirror the shared declarative model into the public checkout asset only."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "supabase/functions/_shared/checkout-profile.mjs"
TARGET = ROOT / "docs/assets/checkout-profile.js"

if __name__ == "__main__":
    TARGET.write_text(SOURCE.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    print("Updated one checkout profile asset; no pages or availability rebuilt.")
