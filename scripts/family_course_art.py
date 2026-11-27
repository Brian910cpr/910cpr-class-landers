"""Approved family artwork, discovered locally at build time (no URL probing)."""
from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CHARACTERS = DOCS / "images" / "characters"


def asset_url(url: str) -> str:
    path = DOCS / url.lstrip("/")
    if not path.is_file():
        raise FileNotFoundError(f"Missing approved artwork asset: {path}")
    return f"{url}?v={hashlib.sha256(path.read_bytes()).hexdigest()[:12]}"


def hero_candidates(config: dict) -> list[dict[str, str]]:
    hero = config.get("hero_image") or {}
    prefix = hero.get("rotation_prefix")
    directory = hero.get("rotation_directory")
    if directory and not re.fullmatch(r"[a-z][a-z0-9-]*", directory):
        raise ValueError("Invalid approved family artwork directory")
    artwork_dir = CHARACTERS / directory if directory else CHARACTERS
    paths = []
    if prefix:
        pattern = re.compile(rf"{re.escape(prefix)}-(\d+)\.webp", re.IGNORECASE)
        paths = sorted(
            (p for p in artwork_dir.glob("*.webp") if pattern.fullmatch(p.name)),
            key=lambda p: int(pattern.fullmatch(p.name).group(1)),
        )
    if not paths and hero.get("url"):
        paths = [DOCS / hero["url"].lstrip("/")]
    candidates = []
    for path in paths:
        if not path.is_file():
            continue
        url = "/" + path.relative_to(DOCS).as_posix()
        item = {"url": asset_url(url), "alt": hero.get("rotation_alts", {}).get(path.stem) or hero.get("alt") or config.get("title", "")}
        small = path.with_name(path.stem + "-480" + path.suffix)
        if small.is_file():
            item["srcset"] = f'{asset_url("/" + small.relative_to(DOCS).as_posix())} 480w, {item["url"]} 960w'
        candidates.append(item)
    return candidates


def hero_markup(config: dict) -> str:
    candidates = hero_candidates(config)
    if not candidates:
        return ""
    hero = config["hero_image"]
    first = candidates[0]
    escape = lambda value: html.escape(str(value), quote=True)
    sizes = ' sizes="(max-width: 820px) 300px, 420px"'
    responsive = f' srcset="{escape(first["srcset"])}"{sizes}' if first.get("srcset") else ""
    fallback = (f'<img src="{escape(first["url"])}"{responsive} alt="{escape(first["alt"])}"'
                ' loading="eager" fetchpriority="high">')
    rotating = bool(hero.get("rotation_prefix") and len(candidates) > 1)
    if rotating:
        # Do not preload #1 while the script picks a different initial hero.
        rotation = f' data-family-hero="{escape(config.get("page_key", "selector"))}" data-hero-images="{escape(json.dumps(candidates))}"'
        markup = f'<img{rotation}{sizes} alt="" fetchpriority="high"><noscript>{fallback}</noscript>'
    else:
        markup = fallback
    return f'''\n      <div class="family-hero-media is-{escape(hero.get("variant", "course-art"))}{' is-rotating' if rotating else ''}">
        {markup}
      </div>'''
