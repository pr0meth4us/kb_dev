"""
Smoke test for the EGD wiki MCP server, including audience isolation.

Start the server with both tokens set, then run:

    MCP_URL=http://127.0.0.1:8000/mcp \\
    MCP_AUTH_TOKEN_PUBLIC=... MCP_AUTH_TOKEN_STAFF=... \\
    python mcp_server/smoke_test.py

Exits non-zero if any check fails. The key checks: the public token can
never see an internal page (by search, keyword, slug or listing), and the
staff token can.
"""

import asyncio
import os
import sys

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

URL = os.environ.get("MCP_URL", "http://127.0.0.1:8000/mcp")
PUBLIC = os.environ["MCP_AUTH_TOKEN_PUBLIC"]
STAFF = os.environ["MCP_AUTH_TOKEN_STAFF"]
INTERNAL_SLUGS = ["platform-approval-workflow", "policy-research-office",
                  "egd-implementation-progress", "pending-decisions",
                  "chatbot-qa-test-set"]

failures = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        failures.append(name)


async def call(token, tool, args):
    async with streamablehttp_client(URL, headers={"Authorization": f"Bearer {token}"}) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            res = await s.call_tool(tool, args)
            return "\n".join(c.text for c in res.content if hasattr(c, "text"))


async def tools_list(token):
    async with streamablehttp_client(URL, headers={"Authorization": f"Bearer {token}"}) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            return (await s.list_tools()).tools


async def main():
    # Auth
    status = httpx.post(URL, json={}).status_code
    check("no token -> 401", status == 401, str(status))
    status = httpx.post(URL, json={}, headers={"Authorization": "Bearer wrong"}).status_code
    check("bad token -> 401", status == 401, str(status))

    # Schemas are Gemini-safe and hide ctx
    tools = await tools_list(PUBLIC)
    names = sorted(t.name for t in tools)
    check("four tools", names == ["get_page", "keyword_search", "list_pages", "search_wiki"], str(names))
    bad = [t.name for t in tools
           if any(k in str(t.inputSchema) for k in ("anyOf", "additionalProperties", "'null'", "ctx"))]
    check("schemas Gemini-safe (no anyOf/null/additionalProperties/ctx)", not bad, str(bad))

    # Public content works
    out = await call(PUBLIC, "search_wiki", {"query": "How much is the grant for an informal business?", "top_k": 3})
    check("search_wiki finds the grant page", "Slug: da-grant" in out, out[:200])
    check("grant figure present verbatim", "$250 (or 1,000,000 Riels)" in out)
    out = await call(PUBLIC, "keyword_search", {"keyword": "DA6"})
    check("keyword_search DA6", "da6-digital-adoption-for-the-informal-economy" in out, out[:200])
    out = await call(PUBLIC, "keyword_search", {"keyword": "មជ្ឈមណ្ឌលបណ្ដុះធុរកិច្ចថ្មី"})  # FAQ spelling with subscript DA
    check("Khmer ្ដ/្ត folding matches Glossary spelling", "Slug: glossary" in out or "Slug: techo-startup-center" in out, out[:200])
    out = await call(PUBLIC, "get_page", {"slug": "official-figures"})
    check("get_page official-figures", "maximum 2 working days" in out)

    # Public isolation
    for slug in INTERNAL_SLUGS:
        out = await call(PUBLIC, "get_page", {"slug": slug})
        check(f"public cannot get {slug}", out == "No page found with that slug.", out[:80])
    out = await call(PUBLIC, "list_pages", {})
    check("public listing hides internal pages", not any(s in out for s in INTERNAL_SLUGS))
    out = await call(PUBLIC, "search_wiki", {"query": "approval workflow Director Review Finance Review authority levels", "top_k": 10})
    check("public search hides internal pages", not any(f"Slug: {s}" in out for s in INTERNAL_SLUGS))
    check("public search hides internal related links", not any(f"[{s}]" in out for s in INTERNAL_SLUGS))
    check("public output has no Sources/Audience lines", "Sources (maintainers only)" not in out and "Audience:" not in out)
    out = await call(PUBLIC, "keyword_search", {"keyword": "Director Review"})
    check("public keyword hides internal pages", not any(f"Slug: {s}" in out for s in INTERNAL_SLUGS), out[:200])

    # Staff access
    out = await call(STAFF, "get_page", {"slug": "platform-approval-workflow"})
    check("staff can get internal page", "Director Review" in out, out[:120])
    out = await call(STAFF, "list_pages", {})
    check("staff listing includes internal pages", "policy-research-office" in out)

    # Other wikis never leak
    out = await call(STAFF, "keyword_search", {"keyword": "CSIC"})
    check("no MSME pages via keyword (CSIC)", "No results found." in out or "msme" not in out.lower(), out[:200])

    print(f"\n{len(failures)} failure(s)")
    sys.exit(1 if failures else 0)


asyncio.run(main())
