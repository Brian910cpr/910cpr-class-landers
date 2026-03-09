from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, unquote

import requests


IMG_SRC_RE = re.compile(r"""src\s*=\s*["']([^"']+)["']""", re.IGNORECASE)


def log(msg: str) -> None:
    print(f"[INFO] {msg}")


def warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def safe_slug(value: str) -> str:
    value = value.lower()
    value = value.replace("%20", "-")
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-") or "file"


def short_hash(value: str, length: int = 12) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def extract_img_urls(html: str | None) -> list[str]:
    if not html:
        return []
    urls = []
    for match in IMG_SRC_RE.findall(html):
        if match.lower().startswith(("http://", "https://")):
            urls.append(match)
    return urls


def infer_extension(url: str, content_type: str | None = None) -> str:
    parsed = urlparse(url)
    path = unquote(parsed.path)
    ext = Path(path).suffix.lower()

    if ext in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}:
        return ext

    if content_type:
        ct = content_type.lower().split(";")[0].strip()
        mapping = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "image/svg+xml": ".svg",
        }
        if ct in mapping:
            return mapping[ct]

    return ".bin"


def build_local_filename(
    course_id: str,
    field_name: str,
    url: str,
    content_type: str | None = None,
) -> str:
    parsed = urlparse(url)
    original_name = Path(unquote(parsed.path)).name or "image"
    original_stem = Path(original_name).stem or "image"
    ext = infer_extension(url, content_type=content_type)
    hashed = short_hash(url)
    raw_name = f"course-{course_id}-{field_name}-{original_stem}-{hashed}{ext}"
    return safe_slug(raw_name)


def download_file(
    url: str,
    destination: Path,
    timeout: int = 30,
    retries: int = 3,
    skip_existing: bool = False,
) -> tuple[str, str | None]:
    if skip_existing and destination.exists():
        return "skipped-existing", None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) course-archive-mirror/1.0"
    }

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout, stream=True)
            response.raise_for_status()

            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            return "downloaded", response.headers.get("Content-Type")
        except Exception as exc:
            last_error = str(exc)
            if attempt < retries:
                time.sleep(1)

    raise RuntimeError(f"Failed after {retries} attempts: {url} :: {last_error}")


def replace_src_urls(html: str | None, replacements: dict[str, str]) -> str | None:
    if not html:
        return html

    updated = html
    for old_url, new_src in replacements.items():
        pattern = re.compile(
            r"""src\s*=\s*["']""" + re.escape(old_url) + r"""["']""",
            re.IGNORECASE,
        )
        updated = pattern.sub(f'src="{new_src}"', updated)

    return updated


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mirror course archive HTML images locally and rewrite image paths in JSON."
    )
    parser.add_argument(
        "--archive-json",
        required=True,
        help="Path to the source course archive JSON, e.g. raw/course_archive_v2.json",
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Path to repo root, e.g. D:/Users/.../910cpr-class-landers",
    )
    parser.add_argument(
        "--images-dir",
        default="docs/images/course-archive",
        help="Repo-relative folder where mirrored images should be stored.",
    )
    parser.add_argument(
        "--updated-archive",
        default="docs/data/course_archive_mirrored.json",
        help="Repo-relative output path for the updated archive JSON.",
    )
    parser.add_argument(
        "--manifest",
        default="docs/data/course_image_manifest.json",
        help="Repo-relative output path for the image manifest JSON.",
    )
    parser.add_argument(
        "--relative-prefix",
        default="../images/course-archive",
        help="HTML-relative src prefix to write into course HTML fields.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip downloading files that already exist locally.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    archive_json = Path(args.archive_json).resolve()
    images_dir = (repo_root / args.images_dir).resolve()
    updated_archive_path = (repo_root / args.updated_archive).resolve()
    manifest_path = (repo_root / args.manifest).resolve()

    if not archive_json.exists():
        raise FileNotFoundError(f"Archive JSON not found: {archive_json}")

    log(f"Loading archive: {archive_json}")
    archive = load_json(archive_json)

    courses = archive.get("courses")
    if not isinstance(courses, list):
        raise ValueError("Archive JSON must contain a top-level 'courses' list.")

    images_dir.mkdir(parents=True, exist_ok=True)
    updated_archive_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    global_registry: dict[str, dict[str, Any]] = {}
    manifest_items: list[dict[str, Any]] = []

    for course in courses:
        course_id = str(course.get("course_id", "unknown"))
        log(f"Scanning course {course_id}")

        for field_name in ("original_html", "lander_html"):
            html = course.get(field_name)
            urls = extract_img_urls(html)

            if not urls:
                continue

            replacements: dict[str, str] = {}

            for url in urls:
                if url not in global_registry:
                    try:
                        temp_name = build_local_filename(course_id, field_name, url, None)
                        temp_path = images_dir / temp_name
                        status, content_type = download_file(
                            url=url,
                            destination=temp_path,
                            skip_existing=args.skip_existing,
                        )

                        final_name = build_local_filename(course_id, field_name, url, content_type)
                        final_path = images_dir / final_name

                        if temp_path != final_path:
                            if final_path.exists():
                                temp_path.unlink(missing_ok=True)
                            else:
                                temp_path.rename(final_path)

                        repo_rel_path = Path(args.images_dir.replace("\\", "/")) / final_name
                        relative_src = f"{args.relative_prefix.rstrip('/')}/{final_name}"

                        global_registry[url] = {
                            "original_url": url,
                            "local_filename": final_name,
                            "repo_path": str(repo_rel_path).replace("\\", "/"),
                            "relative_src": relative_src,
                            "status": status,
                            "content_type": content_type,
                        }
                    except Exception as exc:
                        warn(f"Failed to download {url} :: {exc}")
                        global_registry[url] = {
                            "original_url": url,
                            "local_filename": None,
                            "repo_path": None,
                            "relative_src": url,
                            "status": "failed",
                            "content_type": None,
                            "error": str(exc),
                        }

                mapped = global_registry[url]
                replacements[url] = mapped["relative_src"]

                manifest_items.append(
                    {
                        "course_id": course_id,
                        "field": field_name,
                        "original_url": url,
                        "local_filename": mapped.get("local_filename"),
                        "repo_path": mapped.get("repo_path"),
                        "relative_src": mapped.get("relative_src"),
                        "status": mapped.get("status"),
                    }
                )

            course[field_name] = replace_src_urls(html, replacements)

    old_version = archive.get("version")
    if isinstance(old_version, int):
        archive["version"] = old_version + 1
    else:
        archive["version"] = 1

    archive["image_mirror"] = {
        "source_archive": str(archive_json),
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "images_dir": args.images_dir,
        "relative_prefix": args.relative_prefix,
        "unique_image_count": len(global_registry),
    }

    manifest = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_archive": str(archive_json),
        "updated_archive": str(updated_archive_path),
        "images_dir": args.images_dir,
        "unique_image_count": len(global_registry),
        "items": manifest_items,
    }

    save_json(updated_archive_path, archive)
    save_json(manifest_path, manifest)

    log(f"Updated archive written to: {updated_archive_path}")
    log(f"Manifest written to: {manifest_path}")
    log(f"Unique images found: {len(global_registry)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())