"""Fail closed when a static Pages output violates Cloudflare upload limits."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


MIB = 1024 * 1024
DEFAULT_MAX_FILES = 20_000
DEFAULT_MAX_FILE_SIZE = 25 * MIB
MAX_HEADER_RULES = 100
MAX_HEADER_LINE_LENGTH = 2_000
MAX_REDIRECT_STATIC = 2_000
MAX_REDIRECT_DYNAMIC = 100
MAX_REDIRECT_TOTAL = 2_100
MAX_REDIRECT_LINE_LENGTH = 1_000


def meaningful_lines(path: Path) -> list[str]:
    return [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def validate_special_files(root: Path) -> list[str]:
    errors: list[str] = []
    headers = root / "_headers"
    if headers.is_file():
        lines = meaningful_lines(headers)
        rules = sum(not line[:1].isspace() for line in lines)
        if rules > MAX_HEADER_RULES:
            errors.append(f"_headers has {rules} rules; limit is {MAX_HEADER_RULES}")
        for number, line in enumerate(lines, 1):
            if len(line) > MAX_HEADER_LINE_LENGTH:
                errors.append(
                    f"_headers line {number} has {len(line)} characters; "
                    f"limit is {MAX_HEADER_LINE_LENGTH}"
                )

    redirects = root / "_redirects"
    if redirects.is_file():
        lines = meaningful_lines(redirects)
        dynamic = sum(":" in line.split(maxsplit=1)[0] or "*" in line.split(maxsplit=1)[0] for line in lines)
        static = len(lines) - dynamic
        if static > MAX_REDIRECT_STATIC:
            errors.append(f"_redirects has {static} static rules; limit is {MAX_REDIRECT_STATIC}")
        if dynamic > MAX_REDIRECT_DYNAMIC:
            errors.append(f"_redirects has {dynamic} dynamic rules; limit is {MAX_REDIRECT_DYNAMIC}")
        if len(lines) > MAX_REDIRECT_TOTAL:
            errors.append(f"_redirects has {len(lines)} rules; limit is {MAX_REDIRECT_TOTAL}")
        for number, line in enumerate(lines, 1):
            if len(line) > MAX_REDIRECT_LINE_LENGTH:
                errors.append(
                    f"_redirects line {number} has {len(line)} characters; "
                    f"limit is {MAX_REDIRECT_LINE_LENGTH}"
                )
    return errors


def validate_tree(root: Path, max_files: int, max_file_size: int) -> tuple[list[str], int]:
    errors: list[str] = []
    files: list[Path] = []

    if not root.is_dir():
        return [f"output directory does not exist: {root}"], 0

    for current, directories, names in os.walk(root, followlinks=False):
        current_path = Path(current)
        for name in list(directories):
            candidate = current_path / name
            if candidate.is_symlink():
                errors.append(f"symlinked directory is not deployable: {candidate.relative_to(root).as_posix()}")
                directories.remove(name)
        for name in names:
            candidate = current_path / name
            relative = candidate.relative_to(root).as_posix()
            if candidate.is_symlink():
                errors.append(f"symlinked file is not deployable: {relative}")
                continue
            if not candidate.is_file():
                errors.append(f"non-regular asset is not deployable: {relative}")
                continue
            files.append(candidate)
            size = candidate.stat().st_size
            if size > max_file_size:
                errors.append(f"asset exceeds {max_file_size} bytes: {relative} ({size} bytes)")
            if any(ord(character) < 32 or ord(character) == 127 for character in relative):
                errors.append(f"asset path contains a control character: {relative!r}")
    if len(files) > max_files:
        errors.append(f"tree has {len(files)} files; limit is {max_files}")
    errors.extend(validate_special_files(root))
    return errors, len(files)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, default=Path("docs"))
    parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    parser.add_argument("--max-file-size", type=int, default=DEFAULT_MAX_FILE_SIZE)
    args = parser.parse_args(argv)

    errors, count = validate_tree(args.directory, args.max_files, args.max_file_size)
    if errors:
        print(f"Cloudflare Pages preflight failed with {len(errors)} error(s):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        f"Cloudflare Pages preflight passed: {count} files; "
        f"maximum asset size {args.max_file_size} bytes."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
