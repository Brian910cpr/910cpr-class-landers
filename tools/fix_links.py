import sys, os, io, re
from pathlib import Path

MAPPING = {
"/courses/bls/": "/courses/bls/index.html",
"/courses/fa/": "/courses/fa/index.html",
"/courses/pals/": "/courses/pals/index.html",
"/courses/acls/": "/courses/acls/index.html",
"/": "/index.html",
"/uscg/": "/uscg/index.html",
"/caregivers/": "/caregivers/index.html",
"/parents/": "/parents/index.html",
"/workplaces/": "/workplaces/index.html",
"/industry/": "/industry/index.html",
"/medical/": "/medical/index.html",
}

def fix_file(p):
try:
txt = p.read_text(encoding="utf-8", errors="ignore")
except Exception:
return 0
orig = txt
for old, new in MAPPING.items():
# replace only when old looks like a full href value or path segment
txt = txt.replace(f'href="{old}"', f'href="{new}"')
txt = txt.replace(f"href='{old}'", f"href='{new}'")
if txt != orig:
p.write_text(txt, encoding="utf-8")
return 1
return 0

def main(root):
root = Path(root)
changed = 0
for p in root.rglob(".htm"):
changed += fix_file(p)
print(f"Updated files: {changed}")

if name == "main":
if len(sys.argv) < 2:
print("Usage: python fix_links.py <site_root>")
sys.exit(1)
main(sys.argv[1])