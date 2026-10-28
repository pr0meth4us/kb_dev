#!/usr/bin/env python3
"""Sync wiki/*.md (frontmatter + [[wiki-links]]) into Neo4j.

The markdown wiki is the source of truth. This script derives a graph
mirror from it and is safe to re-run after every ingest: pages no longer
present in wiki/ are deleted and every remaining page's properties and
links are recreated from the current markdown, so Neo4j never drifts
from the wiki (e.g. a link removed from a page won't leave a stale
relationship behind).

This database also hosts sibling wiki graphs (~/Desktop/biz gov as :Page,
the MSME wiki as :MSMEPage). Everything this script writes is scoped under
the distinct base label :EGDPage (see wikigraph/config.py NAMESPACE_LABEL)
so it can never touch, merge into, or delete those graphs, even where a
page slug collides between wikis.

Usage:
    python3 scripts/sync_neo4j.py

Requires a .env file (see .env.example) with NEO4J_URI, NEO4J_USERNAME,
NEO4J_PASSWORD for an Aura (or any Bolt-reachable) instance.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from wikigraph.config import Neo4jConfigError
from wikigraph.embeddings import EmbeddingsUnavailable, get_page_embeddings
from wikigraph.graph import WikiGraph
from wikigraph.markdown import WIKI_DIR, iter_pages


def main():
    pages = iter_pages()
    if not pages:
        sys.exit(f"No wiki pages with frontmatter found under {WIKI_DIR} — nothing to sync.")

    try:
        embeddings = get_page_embeddings(pages)
    except EmbeddingsUnavailable as e:
        print(f"Skipping embeddings ({e}) — syncing graph structure only.", file=sys.stderr)
        embeddings = {}

    try:
        with WikiGraph() as graph:
            report = graph.sync(pages, embeddings=embeddings)
    except Neo4jConfigError as e:
        sys.exit(str(e))

    print(
        f"Synced {report.synced} pages ({report.embedded} with embeddings, "
        f"{report.links} LINKS_TO), deleted {report.deleted} stale :EGDPage nodes."
    )
    if report.unresolved_links:
        print("Unresolved links:", file=sys.stderr)
        for slug, links in report.unresolved_links.items():
            print(f"  {slug}: {', '.join(links)}", file=sys.stderr)


if __name__ == "__main__":
    main()
