from __future__ import annotations

from dataclasses import dataclass, field

from .config import ALL_TYPE_LABELS, NAMESPACE_LABEL, Neo4jConfig, Neo4jConfigError, TYPE_LABELS
from .embeddings import EMBEDDING_DIMENSIONS
from .markdown import WIKILINK_RE, Page, build_resolver, clean_target


@dataclass
class SyncReport:
    synced: int
    deleted: int
    embedded: int
    links: int
    unresolved_links: dict[str, list[str]] = field(default_factory=dict)


class WikiGraph:
    """Pushes wiki/*.md into Neo4j. Markdown stays the source of truth —
    this is a rebuildable mirror, never hand-edited.

    This database also hosts sibling wiki graphs (~/Desktop/biz gov as
    :Page, the MSME wiki as :MSMEPage) — every node/relationship/index here
    is scoped under :NAMESPACE_LABEL ("EGDPage"), so this sync can never
    read, merge into, or delete those graphs' nodes, even where a page slug
    collides between wikis.
    """

    def __init__(self, config: Neo4jConfig | None = None):
        try:
            from neo4j import GraphDatabase
        except ImportError as e:
            raise Neo4jConfigError(
                "neo4j driver is not installed. Run "
                "`pip install neo4j pyyaml python-dotenv` to enable Neo4j sync."
            ) from e
        self.config = config or Neo4jConfig.from_env()
        self.driver = GraphDatabase.driver(
            self.config.uri, auth=(self.config.username, self.config.password)
        )

    def close(self):
        self.driver.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _session(self):
        return self.driver.session(database=self.config.database)

    def ensure_constraints(self, embedding_dimensions: int = EMBEDDING_DIMENSIONS):
        with self._session() as session:
            session.run(
                f"CREATE CONSTRAINT egd_page_slug IF NOT EXISTS "
                f"FOR (p:{NAMESPACE_LABEL}) REQUIRE p.slug IS UNIQUE"
            )
            session.run(
                f"CREATE FULLTEXT INDEX egdPageFulltext IF NOT EXISTS "
                f"FOR (p:{NAMESPACE_LABEL}) ON EACH [p.title, p.body]"
            )
            session.run(
                f"""
                CREATE VECTOR INDEX egdPageEmbedding IF NOT EXISTS
                FOR (p:{NAMESPACE_LABEL}) ON p.embedding
                OPTIONS {{indexConfig: {{
                    `vector.dimensions`: {embedding_dimensions},
                    `vector.similarity_function`: 'cosine'
                }}}}
                """
            )

    def sync(
        self, pages: list[Page], embeddings: dict[str, list[float]] | None = None
    ) -> SyncReport:
        embeddings = embeddings or {}
        self.ensure_constraints()
        resolver = build_resolver(pages)
        current_slugs = {p.slug for p in pages}
        unresolved: dict[str, list[str]] = {}

        link_count = 0

        deleted = self._write_with_retry(self._delete_stale, current_slugs)
        for page in pages:
            targets = []
            misses = []
            for raw in WIKILINK_RE.findall(page.body):
                key = clean_target(raw).lower()
                target_slug = resolver.get(key)
                if target_slug in current_slugs and target_slug != page.slug:
                    targets.append(target_slug)
                elif not target_slug:
                    misses.append(clean_target(raw))
                # A target that resolves to a file outside the graph (index.md
                # has no frontmatter) is skipped; MERGE would create a stub node.
            if misses:
                unresolved[page.slug] = misses
            link_count += len(set(targets))

            self._write_with_retry(
                self._upsert_page, page, targets, embeddings.get(page.slug)
            )

        return SyncReport(
            synced=len(pages),
            deleted=deleted,
            embedded=len(embeddings),
            links=link_count,
            unresolved_links=unresolved,
        )

    def _write_with_retry(self, work, *args, attempts: int = 4):
        """Run one write transaction in a fresh session, retrying when the
        connection drops (ServiceUnavailable, SessionExpired, IncompleteCommit).

        Safe to repeat: every write here is an idempotent MERGE/SET/DELETE, so
        retrying an IncompleteCommit that did land changes nothing.
        """
        import time

        from neo4j.exceptions import IncompleteCommit, ServiceUnavailable, SessionExpired

        for attempt in range(1, attempts + 1):
            try:
                with self._session() as session:
                    return session.execute_write(work, *args)
            except (ServiceUnavailable, SessionExpired, IncompleteCommit):
                if attempt == attempts:
                    raise
                time.sleep(2 * attempt)

    @staticmethod
    def _delete_stale(tx, current_slugs: set[str]) -> int:
        result = tx.run(
            f"MATCH (p:{NAMESPACE_LABEL}) WHERE NOT p.slug IN $slugs "
            f"DETACH DELETE p RETURN count(p) AS n",
            slugs=list(current_slugs),
        )
        return result.single()["n"]

    @staticmethod
    def _upsert_page(tx, page: Page, link_target_slugs: list[str], embedding: list[float] | None):
        type_label = TYPE_LABELS.get(page.type)
        labels = f"{NAMESPACE_LABEL}:{type_label}" if type_label else NAMESPACE_LABEL
        tx.run(
            f"""
            MERGE (p:{NAMESPACE_LABEL} {{slug: $slug}})
            REMOVE p:{ALL_TYPE_LABELS}
            SET p:{labels}, p += $props
            """,
            slug=page.slug,
            props=page.props,
        )

        if embedding is not None:
            tx.run(
                f"MATCH (p:{NAMESPACE_LABEL} {{slug: $slug}}) SET p.embedding = $embedding",
                slug=page.slug,
                embedding=embedding,
            )

        tx.run(
            f"MATCH (p:{NAMESPACE_LABEL} {{slug: $slug}})-[r:LINKS_TO]->() DELETE r",
            slug=page.slug,
        )
        # One round trip for all of a page's links (the database is remote;
        # one query per link made a full sync take over 10 minutes).
        tx.run(
            f"""
            MATCH (p:{NAMESPACE_LABEL} {{slug: $slug}})
            UNWIND $targets AS target_slug
            MERGE (q:{NAMESPACE_LABEL} {{slug: target_slug}})
            MERGE (p)-[:LINKS_TO]->(q)
            """,
            slug=page.slug,
            targets=sorted(set(link_target_slugs)),
        )

    def search_fulltext(self, query: str, limit: int = 10) -> list[dict]:
        with self._session() as session:
            result = session.run(
                """
                CALL db.index.fulltext.queryNodes('egdPageFulltext', $search_query)
                YIELD node, score
                RETURN node.slug AS slug, node.title AS title, node.type AS type, score
                ORDER BY score DESC
                LIMIT $limit
                """,
                search_query=query,
                limit=limit,
            )
            return [dict(r) for r in result]

    def search_vector(self, query_vector: list[float], limit: int = 10) -> list[dict]:
        """Nearest pages by embedding cosine similarity (semantic, not link-based)."""
        with self._session() as session:
            result = session.run(
                f"""
                MATCH (p:{NAMESPACE_LABEL})
                SEARCH p IN (VECTOR INDEX egdPageEmbedding FOR $vector LIMIT $limit) SCORE AS score
                RETURN p.slug AS slug, p.title AS title, p.type AS type, score
                ORDER BY score DESC
                """,
                vector=query_vector,
                limit=limit,
            )
            return [dict(r) for r in result]

    def similar_to(self, slug: str, limit: int = 10) -> list[dict]:
        """Pages with embeddings nearest to the given page's own embedding."""
        with self._session() as session:
            row = session.run(
                f"MATCH (p:{NAMESPACE_LABEL} {{slug: $slug}}) RETURN p.embedding AS embedding",
                slug=slug,
            ).single()
            if row is None or row["embedding"] is None:
                return []
            hits = self.search_vector(row["embedding"], limit=limit + 1)
            return [h for h in hits if h["slug"] != slug][:limit]

    def stats(self) -> dict:
        with self._session() as session:
            by_type = session.run(
                f"MATCH (p:{NAMESPACE_LABEL}) RETURN p.type AS type, count(*) AS n ORDER BY n DESC"
            ).data()
            rel_counts = session.run(
                f"MATCH (p:{NAMESPACE_LABEL})-[r]->(:{NAMESPACE_LABEL}) "
                f"RETURN type(r) AS rel, count(*) AS n ORDER BY n DESC"
            ).data()
            orphans = session.run(
                f"MATCH (p:{NAMESPACE_LABEL}) WHERE NOT (p)--() "
                f"RETURN p.slug AS slug, p.title AS title ORDER BY p.slug"
            ).data()
            hubs = session.run(
                f"""
                MATCH (p:{NAMESPACE_LABEL})
                OPTIONAL MATCH (p)-[r:LINKS_TO]-(:{NAMESPACE_LABEL})
                WITH p, count(r) AS degree
                RETURN p.slug AS slug, p.title AS title, degree
                ORDER BY degree DESC
                LIMIT 10
                """
            ).data()
            embedded = session.run(
                f"MATCH (p:{NAMESPACE_LABEL}) WHERE p.embedding IS NOT NULL RETURN count(p) AS n"
            ).single()["n"]
            return {
                "by_type": by_type,
                "relationships": rel_counts,
                "orphans": orphans,
                "hubs": hubs,
                "embedded": embedded,
            }
