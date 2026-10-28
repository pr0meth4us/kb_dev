"""
Deploy the EGD wiki MCP server (server.py) to Modal.

    modal deploy mcp_server/modal_app.py

Neo4j credentials come from the Modal secret `egd-neo4j`, created from the
repo's .env (never committed):

    modal secret create egd-neo4j --from-dotenv .env

The two audience tokens come from the Modal secret `egd-mcp-auth`:

    modal secret create egd-mcp-auth \\
        MCP_AUTH_TOKEN_PUBLIC=<random> MCP_AUTH_TOKEN_STAFF=<different random>

The endpoint (streamable HTTP, stateless, JSON responses) is
<printed *.modal.run URL>/mcp. Call it with `Authorization: Bearer <token>`.
The public token sees public pages only; give the staff token only to the
backend path that has verified the user is authorised EGD staff.
"""

from pathlib import Path

import modal

HERE = Path(__file__).parent
MODEL_CACHE = "/models"

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "mcp==1.30.0",
        "neo4j>=5.28,<6",
        "fastembed>=0.4",
        "python-dotenv",
    )
    .env({"FASTEMBED_CACHE_PATH": MODEL_CACHE, "MCP_HOST": "0.0.0.0"})
    # Bake the query-embedding model into the image so cold starts don't download it.
    .run_commands(
        "python -c \"from fastembed import TextEmbedding; "
        "TextEmbedding(model_name='BAAI/bge-small-en-v1.5')\""
    )
    .add_local_file(HERE / "server.py", "/root/server.py")
)

app = modal.App("egd-wiki-mcp", image=image)


@app.function(
    secrets=[modal.Secret.from_name("egd-neo4j"), modal.Secret.from_name("egd-mcp-auth")],
    scaledown_window=15 * 60,
    timeout=10 * 60,
)
@modal.concurrent(max_inputs=50)
@modal.asgi_app()
def web():
    import server  # mcp_server/server.py, copied to /root/server.py

    return server.create_app()
