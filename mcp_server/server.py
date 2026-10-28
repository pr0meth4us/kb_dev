"""
MCP server for the EGD Chatbot wiki's Neo4j mirror.

Serves the EGD wiki (nodes labelled :EGDPage, synced by scripts/sync_neo4j.py)
to the EGD Chatbot's generation layer over streamable HTTP (endpoint: /mcp).

Tools (all read-only, all scoped to :EGDPage):
  - search_wiki:  semantic search (BAAI/bge-small-en-v1.5 vector index),
                  expanded one hop through LINKS_TO for related pages
  - keyword_search: substring search over title/body, Khmer-normalised
  - get_page:     one page in full, by slug
  - list_pages:   the page catalogue, optionally filtered by type

Access control (CLAUDE.md, app-integration/egd-chatbot-instruction.md §3):
  The bearer token decides the audience, not a tool argument, so the model
  can never widen its own access.
    MCP_AUTH_TOKEN_PUBLIC -> only pages with audience "public"
    MCP_AUTH_TOKEN_STAFF  -> public and internal pages
  The chatbot backend checks on every message whether the user is
  authorised EGD staff and connects with the matching token. Internal pages
  are invisible to the public token: they are never returned, listed or
  shown as related, and get_page reports them as not found.

There is deliberately no raw-Cypher tool: it would bypass the audience
filter and could read other wikis sharing the database (:MSMEPage, :Page).

Tool schemas stay Gemini-safe: plain string/integer arguments, plain-text
output, no anyOf/null/additionalProperties.

Connection: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE from the
repo's .env locally, or the Modal secret `egd-neo4j` (see modal_app.py).

Run locally:  python mcp_server/server.py   (serves http://127.0.0.1:8000/mcp)
Without any token configured the server only starts on localhost, and then
serves the public audience only.
"""

from __future__ import annotations

import hmac
import os
import re
import threading

from dotenv import load_dotenv
from mcp.server.fastmcp import Context, FastMCP
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE") or None
LABEL = "EGDPage"  # must match scripts/wikigraph/config.py NAMESPACE_LABEL
VECTOR_INDEX_NAME = "egdPageEmbedding"
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"  # same model the sync embeds with
PAGE_TYPES = ("organisation", "program", "course", "process", "platform",
              "policy", "reference", "query")

mcp = FastMCP(
    "egd-wiki",
    host=os.getenv("MCP_HOST", "127.0.0.1"),
    port=int(os.getenv("MCP_PORT", "8000")),
    stateless_http=True,
    json_response=True,
)

# --------------------------------------------------------------------------
# Audience (set per request by the auth middleware)
# --------------------------------------------------------------------------

PUBLIC_ONLY = ("public",)
ALL_AUDIENCES = ("public", "internal")
_STATE_KEY = "egd_audience"


def _audience(ctx: Context) -> tuple:
    """The audience the middleware attached to this HTTP request.

    Read from the request scope (tool calls run outside the request's task,
    so a context variable would not reach them). Anything unexpected falls
    back to public, never to staff.
    """
    request = getattr(ctx.request_context, "request", None)
    state = request.scope.get("state", {}) if request is not None else {}
    audience = state.get(_STATE_KEY, PUBLIC_ONLY)
    return audience if audience in (PUBLIC_ONLY, ALL_AUDIENCES) else PUBLIC_ONLY


# --------------------------------------------------------------------------
# Neo4j and embeddings
# --------------------------------------------------------------------------

_driver = None
_driver_lock = threading.Lock()


def _get_driver():
    global _driver
    if _driver is None:
        with _driver_lock:
            if _driver is None:
                if not (NEO4J_URI and NEO4J_USERNAME and NEO4J_PASSWORD):
                    raise ValueError(
                        "Neo4j connection is not configured. Set NEO4J_URI, "
                        "NEO4J_USERNAME and NEO4J_PASSWORD."
                    )
                _driver = GraphDatabase.driver(
                    NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
                )
    return _driver


_embedder = None
_embedder_lock = threading.Lock()


def _embed_query(text: str) -> list[float]:
    global _embedder
    if _embedder is None:
        with _embedder_lock:
            if _embedder is None:
                from fastembed import TextEmbedding

                _embedder = TextEmbedding(model_name=EMBEDDING_MODEL_NAME)
    return next(iter(_embedder.query_embed([text]))).tolist()


def _read(query: str, parameters: dict) -> list[dict]:
    def _work(tx):
        return [record.data() for record in tx.run(query, parameters)]

    with _get_driver().session(database=NEO4J_DATABASE) as session:
        return session.execute_read(_work)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

# Khmer spellings that look alike but differ as strings (wiki/glossary.md):
# subscript TA (U+17D2 U+178F) vs subscript DA (U+17D2 U+178A), and quote styles.
_KHMER_FOLD = (("្ដ", "្ត"), ("“", '"'), ("”", '"'),
               ("«", '"'), ("»", '"'))


def _fold(text: str) -> str:
    for a, b in _KHMER_FOLD:
        text = text.replace(a, b)
    return text.lower()


def _cypher_fold(expr: str) -> str:
    for a, b in _KHMER_FOLD:
        expr = f"replace({expr}, '{a}', '{b.replace(chr(39), chr(92) + chr(39))}')"
    return f"toLower({expr})"


def _to_int(value, name: str, minimum: int, maximum: int) -> int:
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a whole number")
    return max(minimum, min(maximum, value))


_SUMMARY_RE = re.compile(r"^\s*([^#\-|>*`\s].*)$", re.MULTILINE)


def _summary(body: str | None) -> str:
    """The page's one-line summary: its first plain paragraph line."""
    match = _SUMMARY_RE.search(body or "")
    return match.group(1).strip() if match else ""


def _block(index: int, page: dict, staff: bool, score: float | None = None,
           related: list[dict] | None = None, full: bool = True) -> str:
    header = f"[{index}] {page.get('title') or page.get('slug')}"
    if score is not None:
        header += f"  (relevance {score:.3f})"
    lines = [header, f"Slug: {page.get('slug')}", f"Type: {page.get('type')}"]
    if page.get("status"):
        lines.append(f"Status: {page['status']}")
    if staff:
        lines.append(f"Audience: {page.get('audience')}")
        if page.get("sources"):
            lines.append(f"Sources (maintainers only): {'; '.join(page['sources'])}")
    lines.append("")
    lines.append((page.get("body") or "").strip() if full else _summary(page.get("body")))
    if related:
        names = [f"{r['title']} [{r['slug']}]" for r in related if r.get("slug")]
        if names:
            lines += ["", "Related pages: " + ", ".join(names)]
    return "\n".join(lines)


def _join(blocks: list[str]) -> str:
    return "\n\n---\n\n".join(blocks) if blocks else "No results found."


_PAGE_FIELDS = (
    "p {.slug, .title, .type, .status, .audience, .body, .sources} AS page"
)


# --------------------------------------------------------------------------
# Tools
# --------------------------------------------------------------------------

@mcp.tool(structured_output=False)
def search_wiki(query: str, ctx: Context, top_k: int = 5) -> str:
    """Semantic search over the EGD Program knowledge base. Use this first.

    Finds the wiki pages most relevant to a question about the Enterprises Go
    Digital (EGD) Program: the DAA, DA Training courses, the DA Grant, Digital
    Solution Providers, the EGD Platform, contacts and official figures.
    Each result is a full page plus the titles of directly linked pages.

    The pages are written in English. If the user writes in Khmer, put the
    query in English (Khmer official terms are on the page "glossary").
    Quote figures exactly as the pages state them.

    Args:
        query: The question or topic, in English.
        top_k: How many pages to return (1-10).

    Returns:
        Numbered page blocks (title, slug, type, status, full text, related
        pages), most relevant first, or "No results found."
    """
    if not query or not query.strip():
        raise ValueError("query must not be empty")
    top_k = _to_int(top_k, "top_k", 1, 10)
    audience = _audience(ctx)
    rows = _read(
        f"""
        CALL db.index.vector.queryNodes($index, $fetch, $embedding) YIELD node AS p, score
        WITH p, score
        WHERE p:{LABEL} AND p.audience IN $allowed
        ORDER BY score DESC
        LIMIT $top_k
        CALL (p) {{
          OPTIONAL MATCH (p)-[:LINKS_TO]-(n:{LABEL})
          WHERE n.audience IN $allowed
          RETURN collect(DISTINCT {{slug: n.slug, title: n.title}})[0..12] AS related
        }}
        RETURN {_PAGE_FIELDS}, score, related
        """,
        {
            "index": VECTOR_INDEX_NAME,
            "fetch": top_k * 4,  # over-fetch so audience filtering still leaves top_k
            "embedding": _embed_query(query),
            "allowed": list(audience),
            "top_k": top_k,
        },
    )
    return _join([
        _block(i, r["page"], "internal" in audience, score=r["score"], related=r["related"])
        for i, r in enumerate(rows, 1)
    ])


@mcp.tool(structured_output=False)
def keyword_search(keyword: str, ctx: Context, limit: int = 10) -> str:
    """Find EGD wiki pages containing an exact word or phrase.

    Case-insensitive substring match over page titles and text. Works for
    English and Khmer; Khmer spelling variants (subscript ត/ដ, «»/“” quotes)
    are treated as equal. Use it for names, codes and figures, e.g. "DA6",
    "CamDigiKey", "1,600,000" or a Khmer term. Prefer search_wiki for
    questions.

    Args:
        keyword: The word or phrase to find.
        limit: Maximum number of pages (1-20).

    Returns:
        Numbered blocks with each matching page's title, slug and one-line
        summary (call get_page for the full text), or "No results found."
    """
    if not keyword or not keyword.strip():
        raise ValueError("keyword must not be empty")
    limit = _to_int(limit, "limit", 1, 20)
    audience = _audience(ctx)
    rows = _read(
        f"""
        MATCH (p:{LABEL})
        WHERE p.audience IN $allowed
          AND ({_cypher_fold("coalesce(p.title, '')")} CONTAINS $kw
               OR {_cypher_fold("coalesce(p.body, '')")} CONTAINS $kw)
        RETURN {_PAGE_FIELDS}
        ORDER BY p.slug
        LIMIT $limit
        """,
        {"kw": _fold(keyword.strip()), "allowed": list(audience), "limit": limit},
    )
    return _join([_block(i, r["page"], "internal" in audience, full=False) for i, r in enumerate(rows, 1)])


@mcp.tool(structured_output=False)
def get_page(slug: str, ctx: Context) -> str:
    """Return one EGD wiki page in full, by its slug.

    Useful pages: "official-figures" (every amount and time limit, exact
    wording), "contacts" (hotline, Telegram, hours, fallback),
    "glossary" (official English-Khmer terms), "overview".

    Args:
        slug: The page slug, e.g. "da-grant" or "contacts".

    Returns:
        The page block (title, slug, type, status, full text, related
        pages), or "No page found with that slug."
    """
    if not slug or not slug.strip():
        raise ValueError("slug must not be empty")
    audience = _audience(ctx)
    rows = _read(
        f"""
        MATCH (p:{LABEL} {{slug: $slug}})
        WHERE p.audience IN $allowed
        CALL (p) {{
          OPTIONAL MATCH (p)-[:LINKS_TO]-(n:{LABEL})
          WHERE n.audience IN $allowed
          RETURN collect(DISTINCT {{slug: n.slug, title: n.title}})[0..20] AS related
        }}
        RETURN {_PAGE_FIELDS}, related
        """,
        {"slug": slug.strip().lower(), "allowed": list(audience)},
    )
    if not rows:
        return "No page found with that slug."
    return _block(1, rows[0]["page"], "internal" in audience, related=rows[0]["related"])


@mcp.tool(structured_output=False)
def list_pages(ctx: Context, page_type: str = "") -> str:
    """List the EGD wiki's pages with a one-line summary each.

    Args:
        page_type: Optional filter, one of: organisation, program, course,
            process, platform, policy, reference, query. Leave empty for all.

    Returns:
        One line per page: slug, type, title and summary.
    """
    page_type = (page_type or "").strip().lower()
    if page_type and page_type not in PAGE_TYPES:
        raise ValueError(f"page_type must be one of: {', '.join(PAGE_TYPES)}")
    audience = _audience(ctx)
    rows = _read(
        f"""
        MATCH (p:{LABEL})
        WHERE p.audience IN $allowed AND ($type = '' OR p.type = $type)
        RETURN p.slug AS slug, p.type AS type, p.title AS title, p.body AS body
        ORDER BY p.type, p.slug
        """,
        {"allowed": list(audience), "type": page_type},
    )
    if not rows:
        return "No results found."
    return "\n".join(
        f"- {r['slug']} ({r['type']}): {r['title']} — {_summary(r['body'])}" for r in rows
    )


# --------------------------------------------------------------------------
# Bearer-token auth -> audience
# --------------------------------------------------------------------------

PUBLIC_TOKEN = os.getenv("MCP_AUTH_TOKEN_PUBLIC") or None
STAFF_TOKEN = os.getenv("MCP_AUTH_TOKEN_STAFF") or None
_LOCAL_HOSTS = ("127.0.0.1", "localhost", "::1")


class AudienceTokenMiddleware:
    """Map the presented token to an audience; reject anything else.

    Accepted as `Authorization: Bearer <token>`, or as `?token=<token>` for
    MCP clients that can only be given a URL. With no tokens configured
    (localhost only) every request is public.
    """

    def __init__(self, app, tokens: dict[bytes, tuple]):
        self.app = app
        self.tokens = tokens

    @staticmethod
    def _presented(scope) -> bytes | None:
        for name, value in scope.get("headers", []):
            if name == b"authorization":
                scheme, _, credential = value.partition(b" ")
                if scheme.lower() == b"bearer" and credential:
                    return credential.strip()
        from urllib.parse import parse_qs

        values = parse_qs(scope.get("query_string", b"").decode()).get("token")
        return values[0].encode() if values else None

    def _audience_for(self, presented: bytes | None):
        if not self.tokens:
            return PUBLIC_ONLY
        if presented is None:
            return None
        for token, audience in self.tokens.items():
            if hmac.compare_digest(presented, token):
                return audience
        return None

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        if scope.get("path", "").startswith("/.well-known/"):
            # No OAuth here: a 404 tells clients to use the token as given.
            return await self._send(send, 404, b'{"error": "not found"}')
        audience = self._audience_for(self._presented(scope))
        if audience is None:
            return await self._send(
                send, 401,
                b'{"error": "unauthorized", "detail": "missing or invalid bearer token"}',
                [(b"www-authenticate", b'Bearer realm="egd-wiki-mcp"')],
            )
        scope.setdefault("state", {})[_STATE_KEY] = audience
        await self.app(scope, receive, send)

    @staticmethod
    async def _send(send, status: int, body: bytes, extra_headers=()):
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
                *extra_headers,
            ],
        })
        await send({"type": "http.response.body", "body": body})


def create_app():
    """The streamable-HTTP MCP app behind the audience tokens.

    Refuses to start on a non-local host unless both tokens are set, and
    refuses identical tokens (the staff token must differ from the public one).
    """
    tokens: dict[bytes, tuple] = {}
    if PUBLIC_TOKEN:
        tokens[PUBLIC_TOKEN.encode()] = PUBLIC_ONLY
    if STAFF_TOKEN:
        if STAFF_TOKEN == PUBLIC_TOKEN:
            raise RuntimeError("MCP_AUTH_TOKEN_STAFF must differ from MCP_AUTH_TOKEN_PUBLIC")
        tokens[STAFF_TOKEN.encode()] = ALL_AUDIENCES
    if not (PUBLIC_TOKEN and STAFF_TOKEN) and mcp.settings.host not in _LOCAL_HOSTS:
        raise RuntimeError(
            "Set both MCP_AUTH_TOKEN_PUBLIC and MCP_AUTH_TOKEN_STAFF when serving "
            "on a non-local host"
        )
    return AudienceTokenMiddleware(mcp.streamable_http_app(), tokens)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(create_app(), host=mcp.settings.host, port=mcp.settings.port)
