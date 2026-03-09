from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import requests


TIMEOUT = 20
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


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def extract_remote_img_urls(html: str | None) -> list[str]:
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
    timeout: int = TIMEOUT,
    retries: int = 3,
    skip_existing: bool = False,
) -> tuple[str, str | None]:
    if skip_existing and destination.exists():
        return "skipped-existing", None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) 910cpr-image-mirror/1.0"
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


def mirror_course_archive_images(
    repo_root: Path,
    archive_json: Path,
    images_dir_rel: str = "docs/images/course-archive",
    updated_archive_rel: str = "docs/data/course_archive_mirrored.json",
    manifest_rel: str = "docs/data/course_image_manifest.json",
    relative_prefix: str = "../images/course-archive",
    skip_existing: bool = False,
) -> tuple[Path, Path, int]:
    log(f"Loading archive: {archive_json}")
    archive = load_json(archive_json)

    courses = archive.get("courses")
    if not isinstance(courses, list):
        raise ValueError("Archive JSON must contain a top-level 'courses' list.")

    images_dir = (repo_root / images_dir_rel).resolve()
    updated_archive_path = (repo_root / updated_archive_rel).resolve()
    manifest_path = (repo_root / manifest_rel).resolve()

    images_dir.mkdir(parents=True, exist_ok=True)
    updated_archive_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    global_registry: dict[str, dict[str, Any]] = {}
    manifest_items: list[dict[str, Any]] = []

    for course in courses:
        course_id = str(course.get("course_id", "unknown"))
        log(f"Scanning archive course {course_id}")

        for field_name in ("raw_enrollware_html", "original_html", "lander_html"):
            html = course.get(field_name)
            urls = extract_remote_img_urls(html)

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
                            skip_existing=skip_existing,
                        )

                        final_name = build_local_filename(course_id, field_name, url, content_type)
                        final_path = images_dir / final_name

                        if temp_path != final_path:
                            if final_path.exists():
                                temp_path.unlink(missing_ok=True)
                            else:
                                temp_path.rename(final_path)

                        repo_rel_path = Path(images_dir_rel.replace("\\", "/")) / final_name
                        relative_src = f"{relative_prefix.rstrip('/')}/{final_name}"

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
    archive["version"] = old_version + 1 if isinstance(old_version, int) else 1
    archive["image_mirror"] = {
        "source_archive": str(archive_json),
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "images_dir": images_dir_rel,
        "relative_prefix": relative_prefix,
        "unique_image_count": len(global_registry),
    }

    manifest = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_archive": str(archive_json),
        "updated_archive": str(updated_archive_path),
        "images_dir": images_dir_rel,
        "unique_image_count": len(global_registry),
        "items": manifest_items,
    }

    save_json(updated_archive_path, archive)
    save_json(manifest_path, manifest)

    log(f"Updated archive written to: {updated_archive_path}")
    log(f"Manifest written to: {manifest_path}")
    log(f"Unique course-archive images found: {len(global_registry)}")

    return updated_archive_path, manifest_path, len(global_registry)


def download_html_image(url: str, image_dir: Path, skip_existing: bool = False) -> str:
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path) or f"image-{short_hash(url)}.jpg"
    filename = safe_slug(filename)
    destination = image_dir / filename

    if skip_existing and destination.exists():
        return f"/images/{filename}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) 910cpr-image-mirror/1.0"
    }

    response = requests.get(url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()

    with destination.open("wb") as f:
        f.write(response.content)

    log(f"Downloaded page image: {filename}")
    return f"/images/{filename}"


def process_html_file(path: Path, image_dir: Path, skip_existing: bool = False) -> None:
    html = path.read_text(encoding="utf-8")
    changed = False

    matches = IMG_SRC_RE.findall(html)
    for url in matches:
        if not url.lower().startswith(("http://", "https://")):
            continue

        try:
            local = download_html_image(url, image_dir, skip_existing=skip_existing)
            if local != url:
                html = html.replace(url, local)
                changed = True
        except Exception as exc:
            warn(f"Failed page image {url} in {path}: {exc}")

    if changed:
        path.write_text(html, encoding="utf-8")
        log(f"Updated HTML page: {path}")


def mirror_existing_html_pages(repo_root: Path, skip_existing: bool = False) -> None:
    docs_dir = repo_root / "docs"
    image_dir = docs_dir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)

    log("Scanning built HTML pages under docs/")
    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith(".html"):
                process_html_file(Path(root) / file, image_dir, skip_existing=skip_existing)
    log("Finished scanning built HTML pages.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mirror images from course archive JSON and/or built HTML pages."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repo root path. Default: current directory",
    )
    parser.add_argument(
        "--archive-json",
        default="raw/course_archive_v3.json",
        help="Path to source course archive JSON. Default: raw/course_archive_v3.json",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip images that already exist locally.",
    )
    parser.add_argument(
        "--pages-only",
        action="store_true",
        help="Only mirror existing built HTML pages under docs/.",
    )
    parser.add_argument(
        "--archive-only",
        action="store_true",
        help="Only mirror images from the course archive JSON.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    archive_json = (repo_root / args.archive_json).resolve() if not Path(args.archive_json).is_absolute() else Path(args.archive_json).resolve()

    if not args.pages_only:
        mirror_course_archive_images(
            repo_root=repo_root,
            archive_json=archive_json,
            skip_existing=args.skip_existing,
        )

    if not args.archive_only:
        mirror_existing_html_pages(
            repo_root=repo_root,
            skip_existing=args.skip_existing,
        )

    log("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())