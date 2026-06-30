from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ResolvedPath:
    path: Path
    source: str
    label: str
    env_var: str | None = None


def _abs_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def resolve_live_input_path(
    repo_root: Path,
    *,
    label: str,
    cli_path: str | None,
    env_var: str | None,
    private_path: str,
    legacy_paths: Iterable[str],
) -> ResolvedPath:
    """Resolve a local live-data input without requiring live exports in git.

    Resolution order:
    1. Explicit CLI path.
    2. Environment variable.
    3. Private local path under data/private.
    4. Legacy tracked path during transition.

    The returned path may not exist only when all candidates are missing; callers
    should use missing_live_input_message for a helpful operator-facing error.
    """

    if cli_path:
        return ResolvedPath(_abs_path(repo_root, cli_path), "cli", label)

    if env_var:
        env_value = os.environ.get(env_var)
        if env_value:
            return ResolvedPath(_abs_path(repo_root, env_value), "env", label, env_var=env_var)

    private_candidate = _abs_path(repo_root, private_path)
    if private_candidate.exists():
        return ResolvedPath(private_candidate, "private", label)

    for legacy_path in legacy_paths:
        legacy_candidate = _abs_path(repo_root, legacy_path)
        if legacy_candidate.exists():
            return ResolvedPath(legacy_candidate, "legacy", label)

    return ResolvedPath(private_candidate, "missing", label)


def resolve_live_output_dir(
    repo_root: Path,
    *,
    label: str,
    cli_path: str | None,
    env_var: str | None,
    private_path: str,
    legacy_path: str,
) -> ResolvedPath:
    """Resolve a local live-data output directory.

    New runtime outputs should prefer data/private during normal operation. A CLI
    path still wins so existing operator commands remain compatible.
    """

    if cli_path:
        return ResolvedPath(_abs_path(repo_root, cli_path), "cli", label)

    if env_var:
        env_value = os.environ.get(env_var)
        if env_value:
            return ResolvedPath(_abs_path(repo_root, env_value), "env", label, env_var=env_var)

    return ResolvedPath(_abs_path(repo_root, private_path), "private", label)


def print_resolved_path(resolved: ResolvedPath) -> None:
    print(f"{resolved.label}: {resolved.path} ({resolved.source})")


def runtime_audit_preview_dir(repo_root: Path) -> Path:
    return repo_root / "data" / "runtime" / "audit_previews"


def dynamic_offers_preview_path(repo_root: Path) -> Path:
    return runtime_audit_preview_dir(repo_root) / "dynamic_offers_preview.json"


def public_sellable_offers_preview_path(repo_root: Path) -> Path:
    return runtime_audit_preview_dir(repo_root) / "public_sellable_offers_preview.json"


def dynamic_offers_preview_summary_json_path(repo_root: Path) -> Path:
    return repo_root / "data" / "audit" / "dynamic_offers_preview_summary.json"


def public_sellable_offers_preview_summary_json_path(repo_root: Path) -> Path:
    return repo_root / "data" / "audit" / "public_sellable_offers_preview_summary.json"


def dynamic_offers_preview_summary_md_path(repo_root: Path) -> Path:
    return repo_root / "data" / "audit" / "dynamic_offers_preview_summary.md"


def public_sellable_offers_preview_summary_md_path(repo_root: Path) -> Path:
    return repo_root / "data" / "audit" / "public_sellable_offers_preview_summary.md"


def missing_live_input_message(
    resolved: ResolvedPath,
    *,
    private_path: str,
    env_var: str | None,
    cli_flag: str | None,
    legacy_paths: Iterable[str] = (),
) -> str:
    lines = [
        f"Missing required live data file for {resolved.label}: {resolved.path}",
        "",
        "Real Enrollware/student exports are not required from git. Provide one of:",
    ]
    if cli_flag:
        lines.append(f"- {cli_flag} <path>")
    if env_var:
        lines.append(f"- {env_var}=<path>")
    lines.append(f"- {private_path}")
    legacy_list = list(legacy_paths)
    if legacy_list:
        lines.append("")
        lines.append("Legacy transition paths still supported if present:")
        lines.extend(f"- {path}" for path in legacy_list)
    lines.append("")
    lines.append("Place private live exports under data/private/... or pass an explicit path.")
    return "\n".join(lines)
