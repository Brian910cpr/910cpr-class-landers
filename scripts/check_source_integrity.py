from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THIS = Path(__file__).resolve()
TEMP_REPAIR_WORKFLOW = (ROOT / '.github' / 'workflows' / 'repair-issue160.yml').resolve()
SCAN_ROOTS = [ROOT / '.github', ROOT / 'scripts', ROOT / 'supabase', ROOT / 'tests']
EXTENSIONS = {'.py', '.js', '.ts', '.tsx', '.json', '.yml', '.yaml', '.md', '.html', '.css', '.sql', '.bat', '.ps1', '.sh'}
MARKERS = (
    'Warning: truncated output (original token count:',
    'tokens truncated',
)

failures = []
for scan_root in SCAN_ROOTS:
    if not scan_root.exists():
        continue
    for path in scan_root.rglob('*'):
        resolved = path.resolve()
        if not path.is_file() or resolved in {THIS, TEMP_REPAIR_WORKFLOW}:
            continue
        if path.suffix.lower() not in EXTENSIONS:
            continue
        if any(part in {'.git', 'node_modules', '__pycache__'} for part in path.parts):
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue
        for marker in MARKERS:
            if marker in text:
                failures.append(f'{path.relative_to(ROOT)}: {marker}')

if failures:
    print('Source-integrity failure: tool truncation marker(s) detected:')
    for failure in failures:
        print(f'- {failure}')
    raise SystemExit(1)

print('Source integrity OK: no tool-truncation markers detected.')
