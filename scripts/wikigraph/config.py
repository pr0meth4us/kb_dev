from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
WIKI_DIR = ROOT / "wiki"

# This wiki shares a Neo4j database with sibling wiki graphs: the MSME wiki
# (~/Desktop/KB/MSME Bots, label :MSMEPage) and biz gov (label :Page). To
# sync into the same database without colliding with, or deleting, those
# graphs, every node/index/constraint here is namespaced under a distinct
# base label, NAMESPACE_LABEL. Sync deletes any NAMESPACE_LABEL node whose
# slug isn't in this wiki, so a shared label would wipe the other wikis.
NAMESPACE_LABEL = "EGDPage"

TYPE_LABELS = {
    "organisation": "Organisation",
    "program": "Program",
    "course": "Course",
    "process": "Process",
    "platform": "Platform",
    "policy": "Policy",
    "reference": "Reference",
    "query": "Query",
}
ALL_TYPE_LABELS = ":".join(sorted(set(TYPE_LABELS.values())))


class Neo4jConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Neo4jConfig:
    uri: str
    username: str
    password: str
    database: str | None = None

    @classmethod
    def from_env(cls) -> "Neo4jConfig":
        try:
            from dotenv import load_dotenv
        except ImportError as e:
            raise Neo4jConfigError(
                "python-dotenv is not installed. Run "
                "`pip install neo4j pyyaml python-dotenv` to enable Neo4j sync."
            ) from e
        load_dotenv(ROOT / ".env")

        uri = os.environ.get("NEO4J_URI")
        username = os.environ.get("NEO4J_USERNAME")
        password = os.environ.get("NEO4J_PASSWORD")
        database = os.environ.get("NEO4J_DATABASE") or None
        missing = [
            name
            for name, val in [
                ("NEO4J_URI", uri),
                ("NEO4J_USERNAME", username),
                ("NEO4J_PASSWORD", password),
            ]
            if not val
        ]
        if missing:
            raise Neo4jConfigError(
                f"Missing env vars: {', '.join(missing)}. "
                f"Copy .env.example to .env and fill in your Neo4j Aura credentials."
            )
        return cls(uri=uri, username=username, password=password, database=database)
