from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PUBLIC_EXCLUDED_DIRECTORIES = {"admin", "control-center"}
LANDER_REFERENCE = re.compile(r"(?:href\s*=\s*[\"']|[\"'])([^\"']*css/lander\.css(?:\?[^\"']*)?)[\"']", re.IGNORECASE)


def public_html_files() -> list[Path]:
    return [
        path
        for path in sorted(DOCS.rglob("*.html"))
        if not PUBLIC_EXCLUDED_DIRECTORIES.intersection(path.relative_to(DOCS).parts)
    ]


class PublicCssReferenceTests(unittest.TestCase):
    def test_shared_stylesheet_exists(self) -> None:
        self.assertTrue((DOCS / "css" / "lander.css").is_file())

    def test_all_public_html_lander_references_are_root_relative(self) -> None:
        references: list[tuple[Path, str]] = []
        for path in public_html_files():
            for match in LANDER_REFERENCE.finditer(path.read_text(encoding="utf-8", errors="replace")):
                references.append((path, match.group(1)))
        self.assertGreater(len(references), 0)
        failures = [f"{path.relative_to(ROOT)} -> {reference}" for path, reference in references if reference != "/css/lander.css"]
        self.assertEqual([], failures, "Nonstandard public stylesheet references:\n" + "\n".join(failures))

    def test_generators_never_emit_relative_lander_reference(self) -> None:
        failures: list[str] = []
        for path in sorted((ROOT / "scripts").rglob("*.py")):
            for match in LANDER_REFERENCE.finditer(path.read_text(encoding="utf-8", errors="replace")):
                if match.group(1) != "/css/lander.css":
                    failures.append(f"{path.relative_to(ROOT)} -> {match.group(1)}")
        self.assertEqual([], failures, "Generators emitting nonstandard stylesheet references:\n" + "\n".join(failures))

    def test_group_pages_keep_shared_stylesheet(self) -> None:
        for relative in ("group.html", "group-training.html"):
            with self.subTest(page=relative):
                html = (DOCS / relative).read_text(encoding="utf-8")
                self.assertEqual(1, html.count('href="/css/lander.css"'))


if __name__ == "__main__":
    unittest.main()
