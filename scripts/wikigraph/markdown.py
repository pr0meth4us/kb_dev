from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .config import WIKI_DIR

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?(.*)\Z", re.DOTALL)
# Inside markdown tables the alias pipe is escaped ([[slug\|Alias]]), so the
# captured target may end in a backslash; clean_target() strips it.
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]+)?\]\]")


def clean_target(raw: str) -> str:
    return raw.strip().rstrip("\\").strip()

# audience (public | internal) lets the chatbot filter [INTERNAL] pages.
STRING_PROPS = ("type", "title", "status", "audience")


@dataclass
class Page:
    path: Path
    slug: str
    type: str | None = None
    title: str | None = None
    status: str | None = None
    audience: str | None = None
    date: str | None = None
    sources: list[str] = field(default_factory=list)
    body: str = ""

    @property
    def links(self) -> list[str]:
        return sorted(set(clean_target(m) for m in WIKILINK_RE.findall(self.body)) - {self.slug})

    @property
    def props(self) -> dict:
        props = {"slug": self.slug, "sources": self.sources, "body": self.body}
        for key in STRING_PROPS + ("date",):
            val = getattr(self, key)
            if val is not None:
                props[key] = val
        return props


def _normalize_date(val) -> str | None:
    if val is None:
        return None
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return str(val)


def parse_page(path: Path) -> Page | None:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None

    raw_meta, body = match.groups()
    meta = yaml.safe_load(raw_meta) or {}
    slug = path.stem

    return Page(
        path=path,
        slug=slug,
        **{key: (str(meta[key]) if meta.get(key) is not None else None) for key in STRING_PROPS},
        date=_normalize_date(meta.get("date")),
        sources=[str(s) for s in (meta.get("sources") or [])],
        body=body,
    )


def iter_pages(wiki_dir: Path = WIKI_DIR) -> list[Page]:
    pages = []
    for path in sorted(wiki_dir.rglob("*.md")):
        if path.name in ("index.md", "log.md"):
            continue
        if "lint-reports" in path.parts:  # maintenance records, not content for the app
            continue
        page = parse_page(path)
        if page is None:
            print(f"  skip (no frontmatter): {path.relative_to(wiki_dir)}", file=sys.stderr)
            continue
        pages.append(page)
    return pages


def build_resolver(pages: list[Page]) -> dict[str, str]:
    """Maps a lowercased slug/title to its page's slug, so a [[wiki-link]]
    can target a page by filename (the normal case here) or by title, and
    unresolvable links can be told apart from real misses."""
    resolver: dict[str, str] = {"index": "index"}  # index.md has no frontmatter and is excluded
    # from iter_pages, but [[index]] is a normal, expected link target.
    for page in pages:
        for key in (page.slug, page.title):
            if key:
                resolver[key.strip().lower()] = page.slug
    return resolver
