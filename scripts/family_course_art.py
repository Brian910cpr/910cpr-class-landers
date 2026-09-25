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
    paths = []
    if prefix:
        pattern = re.compile(rf"{re.escape(prefix)}-(\d+)\.webp", re.IGNORECASE)
        paths = sorted(
            (p for p in CHARACTERS.glob("*.webp") if pattern.fullmatch(p.name)),
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
    responsive = f' srcset="{escape(first["srcset"])}" sizes="(max-width: 820px) 300px, 420px"' if first.get("srcset") else ""
    rotation = f' data-family-hero="{escape(config.get("page_key", "selector"))}" data-hero-images="{escape(json.dumps(candidates))}"' if hero.get("rotation_prefix") else ""
    return f'''\n      <div class="family-hero-media is-{escape(hero.get("variant", "course-art"))}">
        <img src="{escape(first['url'])}"{responsive}{rotation} alt="{escape(first['alt'])}" loading="eager" fetchpriority="high">
      </div>'''
