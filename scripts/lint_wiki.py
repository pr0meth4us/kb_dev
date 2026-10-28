#!/usr/bin/env python3
"""Mechanical lint of wiki/ against the CLAUDE.md page rules.

Checks frontmatter (required keys, allowed values, sources as strings that
exist in raw/), audience rules (internal/ pages are internal; public pages
never link to internal ones), unique slugs and wikilink targets. Judgement
checks (contradictions, stale claims, figures, Khmer terms) stay manual.

Usage:
  python3 scripts/lint_wiki.py
Exits 1 if any error is found; "missing link targets" are listed separately,
since links to pages planned for a later batch are expected mid-build.
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?(.*)\Z", re.DOTALL)
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]+)?\]\]")
TYPES = {"organisation", "program", "course", "process", "platform", "policy",
         "reference", "query", "lint-report"}
STATUSES = {"draft", "current", "superseded", "pending-decision"}
AUDIENCES = {"public", "internal"}
SKIP = {"index.md", "log.md"}


def main():
    errors, missing = [], defaultdict(set)
    pages, slugs = {}, defaultdict(list)
    for path in sorted(WIKI.rglob("*.md")):
        rel = path.relative_to(ROOT)
        slugs[path.stem].append(rel)
        if path.name in SKIP:
            continue
        m = FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
        if not m:
            errors.append(f"{rel}: no frontmatter")
            continue
        meta, body = yaml.safe_load(m.group(1)) or {}, m.group(2)
        pages[path.stem] = (rel, meta, body)
        is_lint = "lint-reports" in path.parts
        for key in ("title", "type", "audience", "status") + (() if is_lint else ("sources",)):
            if not meta.get(key):
                errors.append(f"{rel}: missing `{key}`")
        if meta.get("type") and meta["type"] not in TYPES:
            errors.append(f"{rel}: bad type {meta['type']!r}")
        if meta.get("status") and meta["status"] not in STATUSES:
            errors.append(f"{rel}: bad status {meta['status']!r}")
        if meta.get("audience") and meta["audience"] not in AUDIENCES:
            errors.append(f"{rel}: bad audience {meta['audience']!r}")
        if "internal" in path.parts and meta.get("audience") != "internal":
            errors.append(f"{rel}: under internal/ but audience is not internal")
        for src in meta.get("sources") or []:
            if not isinstance(src, str):
                errors.append(f"{rel}: source is not a string (quote it): {src!r}")
                continue
            # a source may carry a note after the path: "raw/X.md (read: §1)"
            src_path = re.match(r"(raw/.+?\.[A-Za-z0-9]+)(?:\s|$)", src)
            if not src_path or not (ROOT / src_path.group(1)).exists():
                errors.append(f"{rel}: source not found: {src}")
    for slug, paths in slugs.items():
        if len(paths) > 1:
            errors.append(f"duplicate slug {slug!r}: {', '.join(map(str, paths))}")
    for slug, (rel, meta, body) in pages.items():
        for target in {t.strip().rstrip("\\").strip() for t in WIKILINK_RE.findall(body)}:
            if target not in pages and target not in ("index", "log"):
                missing[target].add(slug)
            elif (meta.get("audience") == "public" and target in pages
                  and pages[target][1].get("audience") == "internal"):
                errors.append(f"{rel}: public page links to internal page [[{target}]]")
    print(f"{len(pages)} pages checked.")
    for e in errors:
        print("ERROR", e)
    if missing:
        print(f"\nMissing link targets ({len(missing)}):")
        for target in sorted(missing):
            print(f"  [[{target}]] <- {', '.join(sorted(missing[target]))}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
