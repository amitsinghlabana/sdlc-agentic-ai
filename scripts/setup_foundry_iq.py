"""Turnkey setup for **Foundry IQ** (Azure AI Search agentic retrieval).

This is the P2 step that makes the *real* knowledge layer work. It:
  1. creates the search **index** (text + semantic config),
  2. **uploads** docs/standards/*.md as searchable, citable chunks,
  3. creates the **knowledge agent** bound to your existing Azure OpenAI
     deployment (the "agentic" planner), and
  4. runs a **test** retrieval to prove it works.

It reuses the app's settings (.env + .env.local) and the shared TLS helper, so
it behaves the same on corporate HTTPS-inspection networks. No new dependencies
— just httpx (already installed).

Prerequisites (one-time, in the Azure portal):
  • An **Azure AI Search** service (Basic tier recommended — agentic retrieval /
    knowledge agents may not be available on Free).
  • Your existing **Azure OpenAI** resource + a chat deployment (e.g. gpt-4o-mini).

Configure (.env, with the secret in .env.local):
  FOUNDRY_SEARCH_ENDPOINT = https://<your-search>.search.windows.net
  FOUNDRY_INDEX           = sdlc-standards
  FOUNDRY_KNOWLEDGE_AGENT = sdlc-knowledge-agent
  FOUNDRY_API_VERSION     = 2025-08-01-preview   (or whatever your portal shows)
  FOUNDRY_API_KEY         = <Search ADMIN key>   → put in .env.local
  AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_DEPLOYMENT / AZURE_OPENAI_API_KEY

Usage (from the repo root):
  python scripts/setup_foundry_iq.py all       # index -> upload -> agent -> test
  python scripts/setup_foundry_iq.py index
  python scripts/setup_foundry_iq.py upload
  python scripts/setup_foundry_iq.py refresh   # clean content update (clears + re-uploads)
  python scripts/setup_foundry_iq.py agent
  python scripts/setup_foundry_iq.py test
  python scripts/setup_foundry_iq.py delete    # tear down (cost cleanup)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

import httpx

# Make the app package importable so we reuse settings (.env/.env.local) + TLS.
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "backend"))

from app.config import settings  # noqa: E402
from app.net import build_ssl_verify  # noqa: E402


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _client() -> httpx.Client:
    if not settings.foundry_search_endpoint:
        sys.exit("ERROR: FOUNDRY_SEARCH_ENDPOINT is not set (see .env).")
    if not settings.foundry_api_key:
        sys.exit("ERROR: FOUNDRY_API_KEY (Search ADMIN key) is not set (see .env.local).")
    return httpx.Client(
        base_url=settings.foundry_search_endpoint,
        headers={"api-key": settings.foundry_api_key, "Content-Type": "application/json"},
        params={"api-version": settings.foundry_api_version},
        verify=build_ssl_verify(settings.knowledge_ca_bundle, settings.knowledge_verify_ssl),
        timeout=60.0,
    )


def _ok(resp: httpx.Response, action: str) -> dict:
    if resp.status_code >= 400:
        sys.exit(f"ERROR during {action}: {resp.status_code}\n{resp.text[:800]}")
    print(f"  ✓ {action} ({resp.status_code})")
    return resp.json() if resp.content else {}


def _slug(*parts: str) -> str:
    raw = "--".join(parts).lower()
    return re.sub(r"[^a-z0-9_=-]+", "-", raw).strip("-")[:128] or "doc"


def _read_sections(docs_dir: Path) -> List[Tuple[str, str, str]]:
    """Return (title, source_filename, body) for each '##' section in the docs."""
    sections: List[Tuple[str, str, str]] = []
    if not docs_dir.exists():
        sys.exit(f"ERROR: knowledge dir not found: {docs_dir}")
    for md in sorted(docs_dir.glob("*.md")):
        text = md.read_text(encoding="utf-8", errors="ignore")
        for part in re.split(r"^##\s+", text, flags=re.M):
            part = part.strip()
            if not part:
                continue
            heading, _, body = part.partition("\n")
            body = " ".join(body.split())
            if heading.strip() and body:
                sections.append((heading.strip(), md.name, body))
    if not sections:
        sys.exit(f"ERROR: no '##' sections found under {docs_dir}")
    return sections


# --------------------------------------------------------------------------- #
# Steps
# --------------------------------------------------------------------------- #
def create_index() -> None:
    name = settings.foundry_index or "sdlc-standards"
    print(f"Creating index '{name}' …")
    _STR = "Edm.String"
    body = {
        "name": name,
        "fields": [
            {"name": "id", "type": _STR, "key": True, "filterable": True},
            {"name": "title", "type": _STR, "searchable": True, "analyzer": "en.microsoft"},
            {"name": "content", "type": _STR, "searchable": True, "analyzer": "en.microsoft"},
            {"name": "source", "type": _STR, "filterable": True, "facetable": True},
            {"name": "url", "type": _STR},
        ],
        "semantic": {
            "defaultConfiguration": "default",
            "configurations": [
                {
                    "name": "default",
                    "prioritizedFields": {
                        "titleField": {"fieldName": "title"},
                        "prioritizedContentFields": [{"fieldName": "content"}],
                        "prioritizedKeywordsFields": [{"fieldName": "source"}],
                    },
                }
            ],
        },
    }
    with _client() as c:
        _ok(c.put(f"/indexes/{name}", json=body), f"create/update index '{name}'")


def upload_docs() -> None:
    name = settings.foundry_index or "sdlc-standards"
    docs_dir = Path(settings.knowledge_dir or (_ROOT / "docs" / "standards"))
    sections = _read_sections(docs_dir)
    docs = [
        {
            "@search.action": "mergeOrUpload",
            "id": _slug(src, title),
            "title": title,
            "content": body,
            "source": src,
            "url": "",
        }
        for (title, src, body) in sections
    ]
    print(f"Uploading {len(docs)} section(s) from {docs_dir} to '{name}' …")
    with _client() as c:
        _ok(c.post(f"/indexes/{name}/docs/index", json={"value": docs}), "upload documents")


def create_agent() -> None:
    agent = settings.foundry_knowledge_agent or "sdlc-knowledge-agent"
    index = settings.foundry_index or "sdlc-standards"
    if not settings.azure_openai_endpoint or not settings.azure_openai_api_key:
        sys.exit("ERROR: AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_API_KEY must be set to bind the agent.")
    if "YOUR-RESOURCE" in settings.azure_openai_endpoint:
        sys.exit(
            "ERROR: AZURE_OPENAI_ENDPOINT is still the placeholder "
            f"({settings.azure_openai_endpoint}). Set your REAL endpoint in .env "
            "(Azure portal → your OpenAI resource → Keys and Endpoint)."
        )
    model_name = os.getenv("AZURE_OPENAI_MODEL_NAME", settings.azure_openai_deployment)
    print(f"Creating knowledge agent '{agent}' bound to deployment "
          f"'{settings.azure_openai_deployment}' over index '{index}' …")
    body = {
        "name": agent,
        "targetIndexes": [{"indexName": index, "defaultRerankerThreshold": 1.5}],
        "models": [
            {
                "kind": "azureOpenAI",
                "azureOpenAIParameters": {
                    "resourceUri": settings.azure_openai_endpoint.rstrip("/"),
                    "deploymentId": settings.azure_openai_deployment,
                    "modelName": model_name,
                    "apiKey": settings.azure_openai_api_key,
                },
            }
        ],
    }
    with _client() as c:
        _ok(c.put(f"/agents/{agent}", json=body), f"create/update knowledge agent '{agent}'")


def test_retrieve() -> None:
    agent = settings.foundry_knowledge_agent or "sdlc-knowledge-agent"
    index = settings.foundry_index or "sdlc-standards"
    query = "secure login with email and password"
    print(f"Test retrieve via agent '{agent}' …\n  query: {query!r}")
    body = {
        "messages": [{"role": "user", "content": [{"type": "text", "text": query}]}],
        "targetIndexParams": [{"indexName": index, "maxDocsForReranker": 200}],
    }
    with _client() as c:
        data = _ok(c.post(f"/agents/{agent}/retrieve", json=body), "retrieve")

    # Real shape: response[0].content[0].text is a JSON array of {title, terms, content}.
    cites = []
    for item in data.get("response") or []:
        for part in item.get("content") or []:
            if isinstance(part, dict) and part.get("text"):
                try:
                    parsed = json.loads(part["text"])
                    if isinstance(parsed, list):
                        cites = parsed
                except (ValueError, TypeError):
                    pass
    if cites:
        print(f"\n  → {len(cites)} grounded source(s):")
        for i, e in enumerate(cites[:5], start=1):
            print(f"    [S{i}] {e.get('title', '?')}  <- {e.get('terms', e.get('source', '?'))}")
    else:
        refs = data.get("references") or []
        print(f"\n  → {len(refs)} reference(s):")
        for i, ref in enumerate(refs[:5], start=1):
            sd = ref.get("sourceData") or {}
            print(f"    [S{i}] {sd.get('title', '?')}  <- {sd.get('source', '?')}")
        if not refs:
            print("  (no references — check tier/semantic config; see the response above)")


def refresh_docs() -> None:
    """Clean content update: delete all existing docs, then re-upload.

    Unlike plain ``upload`` (mergeOrUpload), this removes orphans left behind
    when you rename or delete a '##' section. Leaves the index schema and the
    knowledge agent untouched, so it's the fast, safe way to push doc edits.
    """
    name = settings.foundry_index or "sdlc-standards"
    with _client() as c:
        # 1) Collect existing doc keys.
        resp = c.post(f"/indexes/{name}/docs/search", json={"search": "*", "select": "id", "top": 1000})
        existing = [d["id"] for d in (_ok(resp, "list existing docs").get("value") or [])]
        # 2) Delete them.
        if existing:
            payload = {"value": [{"@search.action": "delete", "id": i} for i in existing]}
            _ok(c.post(f"/indexes/{name}/docs/index", json=payload), f"delete {len(existing)} old doc(s)")
        else:
            print("  (index empty — nothing to delete)")
    # 3) Re-upload current sections.
    upload_docs()


def delete_all() -> None:
    agent = settings.foundry_knowledge_agent or "sdlc-knowledge-agent"
    index = settings.foundry_index or "sdlc-standards"
    print(f"Deleting agent '{agent}' and index '{index}' …")
    with _client() as c:
        r1 = c.delete(f"/agents/{agent}")
        print(f"  agent delete -> {r1.status_code}")
        r2 = c.delete(f"/indexes/{index}")
        print(f"  index delete -> {r2.status_code}")


STEPS = {
    "index": create_index,
    "upload": upload_docs,
    "refresh": refresh_docs,
    "agent": create_agent,
    "test": test_retrieve,
    "delete": delete_all,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Set up Foundry IQ (Azure AI Search agentic retrieval).")
    parser.add_argument(
        "step", nargs="?", default="all",
        choices=["all", *STEPS.keys()],
        help="Which step to run (default: all = index, upload, agent, test).",
    )
    args = parser.parse_args()

    print(f"Endpoint : {settings.foundry_search_endpoint or '(unset)'}")
    print(f"Index    : {settings.foundry_index or 'sdlc-standards'}")
    print(f"Agent    : {settings.foundry_knowledge_agent or 'sdlc-knowledge-agent'}")
    print(f"API ver  : {settings.foundry_api_version}\n")

    if args.step == "all":
        for step in ("index", "upload", "agent", "test"):
            STEPS[step]()
            print()
        print("Done. Set KNOWLEDGE_PROVIDER=foundry in .env, restart, and check /api/knowledge/test.")
    else:
        STEPS[args.step]()


if __name__ == "__main__":
    main()


