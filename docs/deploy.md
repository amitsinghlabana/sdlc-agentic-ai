# 🚀 Deploy — hosted demo

One container serves **both** the API and the built React UI from the same
origin (no CORS, no separate frontend host). The image **rebuilds `web/dist`
fresh** on every build, so the hosted demo always ships the latest UI.

> Local dev doesn't need any of this — `./start.ps1` runs everything and now
> rebuilds `web/dist` automatically when web deps are installed.

---

## What the image does

`Dockerfile` (repo root) is multi-stage:

1. **`node:22-alpine`** → `npm ci && npm run build` → produces `web/dist`.
2. **`python:3.13-slim`** → installs `backend/requirements.txt`, copies the app +
   the built `web/dist`, and runs `uvicorn`.

FastAPI prefers `web/dist` when present (else the zero-build `frontend/`), so the
**React app is what gets served** in production. It respects `$PORT` if the host
injects one (Container Apps / Render / Fly / HF Spaces).

---

## Build & run locally (Docker)

```bash
docker build -t sdlc-agent .
docker run --rm -p 8000:8000 --env-file .env.local -e LLM_PROVIDER=azure sdlc-agent
# open http://localhost:8000
```

> `.env` / `.env.local` are **git- and docker-ignored** — secrets are passed at
> **runtime** (`--env-file` / platform secrets), never baked into the image.

---

## Azure Container Apps (recommended)

```bash
# 1) One-time: resource group + environment
az group create -n sdlc-rg -l centralus
az containerapp env create -n sdlc-env -g sdlc-rg -l centralus

# 2) Build the image in the cloud (works off the locked-down network)
az acr create -n sdlcacr$RANDOM -g sdlc-rg --sku Basic --admin-enabled true
az acr build -r <yourAcr> -t sdlc-agent:latest .

# 3) Deploy (ingress on 8000); add secrets as env vars
az containerapp create -n sdlc-app -g sdlc-rg --environment sdlc-env \
  --image <yourAcr>.azurecr.io/sdlc-agent:latest \
  --target-port 8000 --ingress external \
  --env-vars LLM_PROVIDER=azure KNOWLEDGE_PROVIDER=foundry \
             JIRA_PROVIDER=cloud GITHUB_PROVIDER=cloud
# then set secrets (AZURE_OPENAI_API_KEY, JIRA_API_TOKEN, GITHUB_TOKEN, …)
# via `az containerapp secret set` + reference them in --env-vars.
```

Scales to zero, uses the monthly free grant + your credit, single origin.

---

## Runtime environment variables

Set these on the host (secrets via the platform's secret store):

| Group | Keys |
|---|---|
| LLM | `LLM_PROVIDER=azure`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT` |
| Foundry IQ | `KNOWLEDGE_PROVIDER=foundry`, `FOUNDRY_SEARCH_ENDPOINT`, `FOUNDRY_API_KEY`, `FOUNDRY_INDEX`, `FOUNDRY_KNOWLEDGE_AGENT` |
| JIRA | `JIRA_PROVIDER=cloud`, `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_PROJECT_KEY` |
| GitHub | `GITHUB_PROVIDER=cloud`, `GITHUB_OWNER`, `GITHUB_TOKEN` |

Any provider left unset/misconfigured **falls back to its free mock** — the demo
never hard-fails. Flip providers live from the in-app **gear → mock/live**.

---

## Frontend-only on Vercel (optional)

Vercel can host the built UI (`web/`) for a fast CDN demo, pointing at a hosted
API. For judging, the **single-container** option above is simpler (one URL, no
CORS) and is the recommended path.

