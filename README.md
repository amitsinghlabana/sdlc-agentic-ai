# 🧩 SDLC Agentic AI

A multi-agent system that acts like a **virtual software team**. Give it a feature
request and a pipeline of specialized AI agents collaborates to produce
**requirements → design → code → tests → review → docs** — streamed live to a
modern web UI, then optionally pushed to **GitHub** and **JIRA**.

Runs **100% free locally** thanks to built-in **mock providers** (the default).
Flip a single env var — or click the in-app toggle — to switch any integration to
its **live** provider (Azure OpenAI, JIRA Cloud, GitHub, Foundry IQ).

> 📄 Full specification & roadmap: [`docs/plan.md`](docs/plan.md) ·
> 🚀 Deployment: [`docs/deploy.md`](docs/deploy.md)

---

## 🤖 How the AI works

The heart of the product is an **Orchestrator** that runs a team of specialized
LLM agents as a **sequential pipeline**, passing a shared **work package** from one
to the next. Each agent has a focused persona, reads the artifacts produced
upstream, and contributes its own.

| Agent | Role |
|-------|------|
| 📝 Requirements Analyst | Turns the request into user stories + acceptance criteria (and a structured `stories.json`) |
| 🏛️ Architect | Picks a stack, defines the API contract & component design |
| 💻 Developer | Implements the design as runnable, multi-file code |
| 🧪 Tester / QA | Writes unit tests (happy + failure paths) |
| 🔍 Code Reviewer | Reviews for bugs/security; can **loop back** to the Developer |
| 📚 Documentation | Generates a feature README |

### The agentic feedback loop
The Reviewer isn't just a final stamp — it can **send work back**. A capped
**Reviewer → Developer loop** lets the team self-correct: e.g. the Reviewer catches
a plaintext-password bug, returns it with comments, and the Developer fixes it with
bcrypt before the Reviewer approves. The loop count is bounded
(`MAX_REVIEW_LOOPS`) so a run always terminates.

### Grounded in your standards (RAG)
Before the agents start, the run is **grounded** against a knowledge base
(coding standards, security checklist, SDLC policy). Requirements and reviews can
**cite sources**, so the output reflects *your* conventions — not just generic
model knowledge. Locally this grounds against `docs/standards/*.md`; in the cloud
it can use **Microsoft Foundry IQ** agentic retrieval.

### Live streaming
The backend emits **Server-Sent Events** (`agent_start`, `delta`, `artifact`,
`agent_done`, `loop`, `run_complete`). The UI renders them in real time — you watch
each agent think, emit files, and hand off, token by token.

### Provider abstraction
Every external dependency is behind a small interface with a **mock** and a
**live** implementation. Swap them per-integration via env vars **or** the in-app
**gear → mock / live** toggle (persisted, hot-reloaded, **no restart**). Anything
left unconfigured **safely falls back to its mock**, so the app never hard-fails.

---

## 🔗 Integrations

### 🎫 JIRA (two-way)
- **Import:** enter an issue/epic key → the app fetches it and prefills the
  feature request, then run the team as usual.
- **Create stories:** the Requirements agent emits `stories.json`; a
  **"Create N stories in JIRA"** button pushes them as issues —
  **human-in-the-loop** (you click; it never writes automatically).

### 🐙 GitHub (two-way)
- **Repo context:** point a run at an existing repo and the agents load it as
  context so they edit the *real* codebase.
- **Publish:** select which generated files to ship, then either **open a branch +
  pull request** against an existing repo or **create a brand-new repo** — with an
  **AI-generated commit message**. Always explicit, never automatic.

### 📚 Knowledge / Foundry IQ
Grounds runs against your standards corpus for citable, on-brand output.

> All three default to **free, offline mocks** (no account, no tokens). Flip any
> one to live independently — same code, same UI.

---

## 🖥️ The web app

A multi-page **React 18 + TypeScript + Tailwind + Vite** SaaS UI:

- **Workspace** — the requirement composer, the live agent pipeline, and a
  VS Code–style artifact explorer with per-file selection → publish drawer.
- **Dashboard** — run stats and recent activity.
- **Runs** — history of past runs.
- **Settings** — provider mock/live switches.
- A unified, **collapsible** side navigation shared across every screen.

---

## 🚀 Quick start (local, free)

### Option A — one command (Windows / PowerShell)
```powershell
./start.ps1
```
Builds the web UI (if Node deps are present), then serves everything at
<http://localhost:8000>. Defaults to **mock** mode → no account or API key, **$0**.

### Option B — manual (backend only, zero-build UI)
```powershell
cd backend
python -m venv ../.venv
../.venv/Scripts/Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Open <http://localhost:8000>, type a feature request, and hit **Run**.

### Option C — web UI dev server (hot reload)
```powershell
cd web
npm install
npm run dev      # http://localhost:5173, proxies /api → :8000
npm run build    # outputs web/dist, which FastAPI then serves at :8000
```

---

## ⚙️ Configuration

Copy the template and edit it — **secrets live only in `.env`** (git-ignored,
never committed, never sent to the browser):

```powershell
Copy-Item .env.example .env
```

Each integration is selected by a `*_PROVIDER` variable and defaults to `mock`.
Set it to the live value and fill in that group's credentials:

| Integration | Switch | Live credentials (placeholders) |
|---|---|---|
| LLM | `LLM_PROVIDER=azure` | `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT` |
| LLM (alt) | `LLM_PROVIDER=openai` | `OPENAI_API_KEY` |
| JIRA | `JIRA_PROVIDER=cloud` | `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_PROJECT_KEY` |
| GitHub | `GITHUB_PROVIDER=cloud` | `GITHUB_OWNER`, `GITHUB_TOKEN` |
| Knowledge | `KNOWLEDGE_PROVIDER=foundry` | `FOUNDRY_SEARCH_ENDPOINT`, `FOUNDRY_KNOWLEDGE_AGENT`, `FOUNDRY_INDEX` |

See [`.env.example`](.env.example) for the full list with inline notes. You can
also flip providers at runtime from the in-app **gear** menu — no restart.

> 💡 **Cost control:** LLM defaults use a small model, cap output tokens, and run
> agents sequentially — a full run is a handful of small calls. Set a budget alert
> on your cloud account.

> 🔒 Tokens are used **server → service over HTTPS only**; they are never sent to
> the browser. See [`docs/jira-integration.md`](docs/jira-integration.md) and
> [`docs/github-setup.md`](docs/github-setup.md) for the integration designs.

---

## 🧪 Run the tests
```powershell
cd backend
pytest
```
Tests exercise the whole pipeline in mock mode (free & deterministic), including
the reviewer feedback loop, knowledge grounding, and the JIRA/GitHub integrations
(status, import, create-stories, publish).

---

## 🧱 Architecture

```
React UI (web/, Vite + TS)  ──SSE──►  FastAPI  ──►  Orchestrator
  live agent pipeline                /api/stream     │ sequential pipeline + review loop
  artifact explorer + publish                        ▼
                                            Agents ──► LLM Provider   (mock | azure | openai)
                                                  └──► Knowledge       (mock | foundry)
                                                  └──► JIRA            (mock | cloud)
                                                  └──► GitHub          (mock | cloud)
```

* **Frontend:** a multi-page **React 18 + TypeScript + Tailwind** app in `web/`,
  built with Vite to `web/dist`. A tiny **zero-build** UI in `frontend/` is kept as
  a no-tooling fallback; FastAPI serves `web/dist` when present, else `frontend/`.
* **Streaming:** Server-Sent Events render the run live, token by token.
* **Work package:** a shared state object accumulates artifacts as it flows
  through the agents.
* **Provider abstraction:** mock/live per integration, switchable via env var or
  the in-app toggle (persisted, hot-reloaded).

---

## 📁 Project structure

```
sdlc-agent/
├── README.md
├── start.ps1                 # one-command local launcher (Windows)
├── Dockerfile                # multi-stage: build web UI → serve with the API
├── .env.example              # all config, with placeholders (no secrets)
├── docs/
│   ├── plan.md               # full spec & roadmap
│   ├── deploy.md             # deployment guide (single-container)
│   ├── jira-integration.md   # JIRA integration design
│   ├── github-setup.md       # GitHub setup
│   ├── foundry-iq-setup.md   # Foundry IQ (knowledge) setup
│   └── standards/            # grounding corpus (coding/security/SDLC standards)
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py           # FastAPI + SSE + static hosting
│   │   ├── orchestrator.py   # pipeline + review loop (event stream)
│   │   ├── config.py         # env settings + provider selection
│   │   ├── runtime_config.py # persisted mock↔live overrides
│   │   ├── models.py         # Artifact / AgentResult / WorkPackage
│   │   ├── agents/           # requirements, architect, developer, tester, reviewer, docs
│   │   ├── llm/              # base, mock, azure_openai, openai, factory
│   │   ├── integrations/     # github/, jira/, knowledge/ (each: base, mock, cloud, factory)
│   │   ├── routers/          # admin (provider switch), github, jira
│   │   └── prompts/          # agent personas
│   └── tests/                # pipeline, jira, github, knowledge, admin, …
├── frontend/                 # zero-build fallback UI (served if web/dist is absent)
└── web/                      # primary UI — Vite + React + TypeScript
    ├── package.json
    └── src/                  # pages/, components/, hooks/, store/, lib/
```

---

## 🚢 Deploy

One container builds the React UI and serves it together with the API from a
**single origin** (no CORS, no separate frontend host). See
[`docs/deploy.md`](docs/deploy.md) for the Docker build and cloud steps. Secrets
are provided at **runtime** via the platform's secret store — never baked into the
image.

---

## 🗺️ Roadmap / stretch goals
See [`docs/plan.md`](docs/plan.md). Highlights: deeper human-in-the-loop approval
gates, richer codebase RAG, live test execution, and persisted server-side run
history.

