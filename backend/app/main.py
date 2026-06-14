"""FastAPI app: SSE streaming endpoint + static frontend + JSON run endpoint."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .agents import team_roster
from .config import settings
from .integrations.github import get_github
from .integrations.knowledge import get_knowledge
from .llm.factory import get_llm
from .orchestrator import run_pipeline
from .routers import admin as admin_router
from .routers import github as github_router
from .routers import jira as jira_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("sdlc")

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WEB_DIST = _REPO_ROOT / "web" / "dist"          # built React UI (preferred)
FRONTEND_DIR = _REPO_ROOT / "frontend"          # legacy zero-build fallback

app = FastAPI(title="SDLC Agentic AI", version="0.1.0")

# Permissive CORS for local dev / separate frontend hosting.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    request: str


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/api/config")
async def get_config() -> dict:
    llm = get_llm()
    return {
        "provider": llm.name,
        "provider_label": getattr(llm, "label", llm.name),
        "is_mock": llm.name == "mock",
        "max_review_loops": settings.max_review_loops,
    }


@app.get("/api/llm/test")
async def test_llm() -> dict:
    """Tiny real completion to verify provider connectivity (and the TLS fix).

    Cheap (a handful of tokens). Returns a clean error instead of a stack trace so
    the UI / curl can show exactly what's wrong (auth, deployment name, SSL, …).
    """
    llm = get_llm()
    try:
        reply = await llm.complete(
            "You are a health check. Reply with a short confirmation.",
            'Reply with exactly: {"ok": true}',
            tag="",
            json_mode=False,
            max_tokens=16,
        )
        return {"ok": True, "provider": llm.name, "label": getattr(llm, "label", llm.name),
                "sample": (reply or "").strip()[:120]}
    except Exception as exc:  # noqa: BLE001 — surface a readable reason
        logger.exception("LLM connectivity test failed")
        return {"ok": False, "provider": llm.name, "label": getattr(llm, "label", llm.name),
                "error": f"{type(exc).__name__}: {exc}"[:300]}


@app.get("/api/team")
async def get_team() -> dict:
    return {"team": team_roster()}


@app.get("/api/knowledge/status")
async def knowledge_status() -> dict:
    """Foundry IQ grounding status (never returns the key)."""
    client = get_knowledge()
    return {
        "provider": client.name,
        "label": getattr(client, "label", client.name),
        "is_mock": client.name == "mock",
        "configured": settings.knowledge_configured,
        "top_k": settings.knowledge_top_k,
        "sources": getattr(client, "sources_count", None),
    }


@app.get("/api/knowledge/test")
async def knowledge_test(q: str = "secure login with email and password") -> dict:
    """Run a sample agentic retrieval to verify grounding (and connectivity)."""
    client = get_knowledge()
    try:
        result = await client.retrieve(q, top=settings.knowledge_top_k)
        return {
            "ok": True,
            "provider": result.provider,
            "label": getattr(client, "label", result.provider),
            "count": len(result.citations),
            "subqueries": result.subqueries,
            "citations": [c.model_dump() for c in result.citations],
        }
    except Exception as exc:  # noqa: BLE001 — surface a readable reason
        logger.exception("Knowledge connectivity test failed")
        return {"ok": False, "provider": client.name,
                "error": f"{type(exc).__name__}: {exc}"[:300]}


# JIRA endpoints (status, import, create-stories).
app.include_router(jira_router.router)

# GitHub endpoints (status, import, publish).
app.include_router(github_router.router)

# Admin endpoints (runtime mock↔live provider switching).
app.include_router(admin_router.router)


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


@app.get("/api/stream")
async def stream(request: str, repo: str | None = None):
    """Stream the pipeline as Server-Sent Events (consumed by EventSource).

    When ``repo`` (owner/name) is supplied, the existing repository is loaded as
    context so the agents edit the real codebase and target it for a branch + PR.
    """

    async def generator():
        seed_files = []
        if repo:
            try:
                seed_files = await get_github().fetch_repo_context(repo)
            except Exception as exc:  # surface, but still run from scratch
                logger.exception("repo context fetch failed for %s", repo)
                yield _sse({"type": "repo_context", "repo": repo, "count": 0,
                            "files": [], "error": f"{type(exc).__name__}: {exc}"})
        try:
            async for event in run_pipeline(request, get_llm(), seed_files=seed_files, repo=repo):
                yield _sse(event)
        except Exception as exc:  # last-resort guard
            logger.exception("pipeline failed")
            yield _sse({"type": "error", "message": str(exc)})

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable proxy buffering (nginx/Azure)
        },
    )


@app.post("/api/run")
async def run(body: RunRequest) -> dict:
    """Non-streaming run — returns all events + final artifacts (handy for testing)."""
    events: list[dict] = []
    artifacts: dict[str, dict] = {}
    async for event in run_pipeline(body.request, get_llm()):
        events.append(event)
        if event["type"] == "artifact":
            art = event["artifact"]
            artifacts[art["name"]] = art
    return {"events": events, "artifacts": list(artifacts.values())}


# Mount the static frontend LAST so /api/* routes take precedence.
# Prefer the built React UI (web/dist); fall back to the zero-build vanilla UI.
_serving_react = WEB_DIST.exists()
_static_dir = WEB_DIST if _serving_react else FRONTEND_DIR


# Zero-build frontend: serve the marketing landing at "/" and the app at "/app".
# (The React build handles its own routing via React Router, so we skip this then.)
if not _serving_react and (FRONTEND_DIR / "landing.html").exists():
    from fastapi.responses import FileResponse

    @app.get("/", include_in_schema=False)
    async def _landing():
        return FileResponse(str(FRONTEND_DIR / "landing.html"))

    @app.get("/app", include_in_schema=False)
    async def _app_page():
        return FileResponse(str(FRONTEND_DIR / "index.html"))


class SPAStaticFiles(StaticFiles):
    """StaticFiles that serves index.html for unknown paths (client-side routing).

    Real asset requests resolve normally; an unknown *page* path (e.g. /app,
    /dashboard) falls back to index.html so a refresh / deep-link doesn't 404.
    Paths under /api/ and obvious asset requests keep their real 404 so missing
    endpoints/files never masquerade as the app shell.
    """

    async def get_response(self, path: str, scope):  # type: ignore[override]
        from starlette.exceptions import HTTPException as StarletteHTTPException

        try:
            resp = await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            # Use the URL path (forward slashes) — ``path`` is OS-normalized and
            # uses backslashes on Windows, which would break these prefix checks.
            url_path = scope.get("path", "").lstrip("/")
            is_api = url_path.startswith("api/") or url_path == "api"
            # A dotted last segment (e.g. foo.js, app.css) is an asset, not a route.
            is_asset = "." in url_path.rsplit("/", 1)[-1]
            if exc.status_code == 404 and not is_api and not is_asset:
                resp = await super().get_response("index.html", scope)
            else:
                raise
        # Never let the HTML shell be cached — otherwise a browser can keep
        # showing a stale build (e.g. an old landing page) after a redeploy.
        # Content-hashed assets under /assets/ stay cacheable.
        if resp.media_type == "text/html" or str(getattr(resp, "path", "")).endswith("index.html"):
            resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return resp


if _static_dir.exists():
    logger.info("Serving frontend from %s", _static_dir)
    app.mount("/", SPAStaticFiles(directory=str(_static_dir), html=True), name="frontend")
else:  # pragma: no cover
    logger.warning(
        "No frontend found. Build the React app (cd web && npm install && npm run build) "
        "or keep the legacy files in %s",
        FRONTEND_DIR,
    )

