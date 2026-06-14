# JIRA Integration — Technical Analysis & Plan

> **Status:** Draft analysis for review — no code will be written until you approve direction.
> **Scope:** Two-way JIRA integration (push generated stories → JIRA; pull a JIRA issue →
> pipeline input) that fits the existing FastAPI + provider/factory/mock architecture and
> stays **100% free by default**.
>
> **Update (Jun 2026):** A free-tier **JIRA Cloud** account has been created → **P2 is unblocked**.
> Connection approach = **direct REST, not MCP** (see §5.5 for the rationale and how an
> `McpJiraClient` can be added later behind the same factory).
>
> **Hosting decision (Jun 2026):** The **final demo is HOSTED (online)** and uses **real
> services** — `LLM_PROVIDER=azure` + `JIRA_PROVIDER=cloud`. The **mock** providers are kept for
> **local testing and repeated dev runs only** (free, offline, deterministic). Same code, just
> different env vars per environment — see **§9.5 Hosting & Environment Strategy**.
>
> **Free hosting note (Jun 2026):** Free non-Azure hosts (Vercel, Render, Fly.io, HF Spaces) are
> on the table. ⚠️ **Vercel is great for the frontend but not for our streaming Python backend**
> (its serverless functions cap request duration, which breaks our long-lived `/api/stream` SSE).
> See **§9.6 Free Hosting Options (Vercel & alternatives)** for the comparison and recommendation.

---

## 1. TL;DR

Mirror the project's existing **`llm/` provider pattern** with a new
**`backend/app/integrations/jira/`** package (`base` → `mock` → `cloud` → `factory`). Add a
structured **`stories.json`** artifact to the Requirements agent so we never parse markdown.
Expose three small endpoints (`status`, `import`, `create-stories`) and two UI affordances
(Import box + "Create N stories in JIRA" button). Default to a **`MockJiraClient`** so the
whole feature is demoable offline with zero JIRA account, exactly like the mock LLM provider.
Real JIRA Cloud is a one-env-var flip (`JIRA_PROVIDER=cloud`).

**Why this shape:** it's the codebase's core idiom already (`get_llm()` in
`backend/app/llm/factory.py`), it keeps cost at $0, and it makes story creation
**human-in-the-loop** (a button, never an automatic write to a real board).

---

## 2. JIRA Cloud REST API v3 Fundamentals

**Base URL:** `https://<your-site>.atlassian.net` → API root `…/rest/api/3`.

| Capability | Method & Path | Notes |
|---|---|---|
| Create issue | `POST /rest/api/3/issue` | Body `{ "fields": { … } }`; returns `{id, key, self}`. |
| Bulk create | `POST /rest/api/3/issue/bulk` | `{ "issueUpdates": [ {fields…}, … ] }` — fewer round-trips. |
| Get issue | `GET /rest/api/3/issue/{key}` | `?fields=summary,description,issuetype,labels,subtasks,parent`. |
| Search (JQL) | `POST /rest/api/3/search/jql` | **New** enhanced endpoint. Classic `/search` is **deprecated** — abstract it. |
| List projects | `GET /rest/api/3/project/search` | Paginated; or `GET /rest/api/3/project`. |
| Create metadata | `GET /rest/api/3/issue/createmeta/{projectKey}/issuetypes` | Discover issue types + field IDs. |

### Atlassian Document Format (ADF) — the v3 gotcha
In API **v3**, rich-text fields (notably `description`) are **not plain strings** — they must be
an **ADF JSON document**. (API v2 accepted plain text; Cloud favors v3/ADF.)

Minimal ADF doc for *"As a user… / Acceptance Criteria: …"*:

```jsonc
{
  "type": "doc", "version": 1,
  "content": [
    { "type": "paragraph",
      "content": [ { "type": "text", "text": "As a user, I can sign in with email/password." } ] },
    { "type": "heading", "attrs": { "level": 3 },
      "content": [ { "type": "text", "text": "Acceptance Criteria" } ] },
    { "type": "bulletList", "content": [
      { "type": "listItem", "content": [ { "type": "paragraph",
        "content": [ { "type": "text", "text": "Email must be valid; password >= 8 chars." } ] } ] },
      { "type": "listItem", "content": [ { "type": "paragraph",
        "content": [ { "type": "text", "text": "Failed login returns 401 with a generic message." } ] } ] }
    ] }
  ]
}
```

We only need a tiny ADF **builder** (paragraph, heading, bulletList) and a **flattener** (walk
`content`, concat `text` nodes) for inbound. Keep it minimal to avoid validation errors.

---

## 3. Authentication — Recommendation: API Token + Basic Auth

| Option | Effort | Hackathon fit |
|---|---|---|
| **API token + email (HTTP Basic)** ✅ | Lowest | **Recommended.** `Authorization: Basic base64(email:token)`. `httpx` does this via `auth=(email, token)`. |
| OAuth 2.0 (3LO) | High | Needs OAuth app, callback, scopes, `cloudid` routing. Overkill. |
| Forge / Connect app | Highest | Full app framework + hosting. Not for a demo. |

- **Get a token:** id.atlassian.com → *Security → API tokens → Create*.
- **Permissions:** a token inherits the **user's** project permissions (use an account that can
  create issues in the target/sandbox project).
- **Secrets:** local `.env` (add to `.env.example`); in Azure use App Settings / **Key Vault**.
  Never commit tokens; redact in logs.

---

## 4. Data Mapping (the crux)

### 4a. Outbound — Requirements output → JIRA issues
**Recommendation:** have the Requirements agent **also emit a structured `stories.json`
artifact** alongside `requirements.md`. This needs **zero model changes** — `Artifact` already
carries arbitrary `content`, and `agents/base.py` already parses an `artifacts[]` array. We just
teach the persona (and the mock builder `_requirements`) to add a second artifact.

Proposed **story schema** (`stories.json`):

```jsonc
{
  "epic": { "summary": "Email/password login", "description": "Authentication feature" },
  "stories": [
    {
      "summary": "Sign in with email and password",     // -> fields.summary (<=255 chars)
      "description": "As a user, I want to sign in...",  // -> fields.description (ADF)
      "acceptance_criteria": ["Valid email required", "401 on bad creds"], // -> ADF section
      "story_points": 3,                                 // -> custom field (instance-specific)
      "labels": ["auth", "sdlc-agent"],                  // -> fields.labels (no spaces!)
      "issue_type": "Story"                              // -> fields.issuetype.name
    }
  ]
}
```

**Field mapping to `POST /issue`:**

| Story field | JIRA `fields.*` | Notes |
|---|---|---|
| `summary` | `summary` | Clamp to 255 chars. |
| `description` + `acceptance_criteria` | `description` (ADF) | AC rendered as heading + bulletList. |
| `issue_type` | `issuetype.name` | Validate against `createmeta`. |
| `labels` | `labels` | Strip spaces; add marker label for idempotency (§7). |
| `story_points` | `customfield_XXXXX` | **Instance-specific** → configurable (`JIRA_STORY_POINTS_FIELD`); skip if unknown. |
| Epic membership | `parent.key` (team-managed/new) **or** `customfield_10014` "Epic Link" (classic) | Create Epic first, then set parent. |

**Flow:** optionally create the Epic → capture its key → create each Story with
`parent.key = <epicKey>` (or bulk-create children).

### 4b. Inbound — JIRA issue → feature-request string
Fetch the issue, **flatten ADF → text**, gather child issues, and assemble the plain string the
pipeline already consumes (`wp.request` in `orchestrator.py`):

```
{summary}

{flattened description}

Acceptance Criteria:
- ...
- ...

Child stories:
- {child summary}
- {child summary}
```

- **Children:** for an Epic, fetch via JQL (`parent = KEY` or `"Epic Link" = KEY`); for a Story,
  read `fields.subtasks`.
- **AC source:** description section or custom field — make configurable; fall back to "whole
  description".

---

## 5. Recommended Design — Mirror the LLM Provider Pattern

New package **`backend/app/integrations/jira/`**, one-to-one with `llm/`:

| `llm/` (existing) | `integrations/jira/` (proposed) | Responsibility |
|---|---|---|
| `base.py` `LLMProvider` | `base.py` `JiraClient` (ABC) | Interface: `get_issue`, `search`, `list_projects`, `create_issue`, `create_epic`, `bulk_create`. |
| `mock.py` `MockProvider` | `mock.py` `MockJiraClient` | In-memory; returns `DEMO-123`; seeds a demo Epic + children. **Default.** |
| `azure_openai.py` | `cloud.py` `CloudJiraClient` | Real v3 calls via `httpx.AsyncClient`, Basic auth, ADF, pagination, retries. |
| `factory.py` `get_llm()` | `factory.py` `get_jira()` | Pick `JIRA_PROVIDER` (`mock`\|`cloud`), default `mock`, fall back to mock; cached singleton + `reset_jira()`. |

Plus two small support files (keep mapping logic testable):
- `models.py` — pydantic `JiraIssue` (key, summary, description_text, issue_type, labels,
  acceptance_criteria, children) and `CreatedIssue` (key, url, summary).
- `mapping.py` — ADF **build**/**flatten**, story→fields mapping, feature-request string builder.

**Interface sketch** (signatures only — analysis, not implementation):

```python
class JiraClient(ABC):
    name: str; label: str
    async def get_issue(self, key: str) -> JiraIssue: ...
    async def search(self, jql: str, *, limit: int = 50) -> list[JiraIssue]: ...
    async def list_projects(self) -> list[dict]: ...
    async def create_issue(self, story: dict, *, parent_key: str | None = None) -> CreatedIssue: ...
    async def create_epic(self, epic: dict) -> CreatedIssue: ...
    async def bulk_create(self, stories: list[dict], *, parent_key: str | None = None) -> list[CreatedIssue]: ...
```

**Dependency:** `httpx` is already present transitively (via `openai` and Starlette's
`TestClient`). Add it **explicitly** to `backend/requirements.txt`.

**New config in `config.py`** (env-driven, defaults safe):

| Setting | Env var | Default |
|---|---|---|
| `jira_provider` | `JIRA_PROVIDER` | `mock` |
| `jira_base_url` | `JIRA_BASE_URL` | `""` |
| `jira_email` | `JIRA_EMAIL` | `""` |
| `jira_api_token` | `JIRA_API_TOKEN` | `""` |
| `jira_project_key` | `JIRA_PROJECT_KEY` | `""` |
| `jira_story_points_field` | `JIRA_STORY_POINTS_FIELD` | `""` (skip if empty) |
| `jira_dry_run` | `JIRA_DRY_RUN` | `false` |
| **property** `jira_configured` | — | `base_url && email && token && project_key` |

---

## 5.5 Connection Approach — Direct REST vs MCP

> **✅ DECISION (locked): use the direct REST "link" as the core integration.** For our
> button-driven, deterministic create/read flow it is **both the easiest and the most correct**
> path (1 API token + 4 env vars; fully mockable for $0). MCP is built for AI *assistants* to call
> tools dynamically and adds a server/OAuth layer we don't need. An optional `McpJiraClient` stays
> available as a **P3 wow-factor stretch** behind the same factory.

**Short answer: the plan does _not_ use MCP. It uses a direct REST client (`httpx` → JIRA
Cloud REST v3).** Here is why, and exactly when MCP would make sense.

**What MCP is:** the **Model Context Protocol** is an open standard for exposing external
tools/data to AI agents through a uniform client–server interface. An *MCP server* for JIRA
exposes tools like `createJiraIssue` / `getJiraIssue`; an app that wants to use them acts as an
*MCP client/host*.

**If we went MCP, the options would be:**

| MCP option | Auth | Offline / mock | Notes |
|---|---|---|---|
| Atlassian **official Remote MCP Server** (hosted) | OAuth 2.1 | ❌ needs a real account, online | Managed by Atlassian; great inside Claude / Cursor / VS Code. |
| Community server (e.g. `mcp-atlassian`, self-hosted) | API token | ⚠️ needs the server process running | Docker/local; also supports Server/DC. |

**Trade-offs vs the planned direct-REST client:**

| Factor | Direct REST (planned) | MCP |
|---|---|---|
| Fits existing `provider/factory/mock` idiom | ✅ exactly | ⚠️ extra moving part (MCP client + a server process/transport) |
| $0 **offline** demo via mock | ✅ trivial (`MockJiraClient`) | ❌/⚠️ official server needs account + OAuth; self-hosted needs a running server |
| Control over exact fields / ADF | ✅ full | ⚠️ limited to the server's tool surface |
| Determinism (create on a **button**, not LLM whim) | ✅ | tool-calling is more dynamic than we need here |
| "Wow factor" / trendiness | neutral | ✅ if judges specifically value MCP |
| Effort | **low** | higher (auth, transport, ops) |

**Recommendation:**
- **Core integration → direct REST.** Simpler, fully mockable for **$0**, deterministic, and it
  matches the codebase's idioms.
- **The door stays open for MCP for free:** because everything sits behind the `JiraClient` ABC +
  `get_jira()` factory, a future **`McpJiraClient`** is *just another provider*
  (`JIRA_PROVIDER=mcp`) — no changes to agents, endpoints, or the UI.
- **If the hackathon rewards MCP specifically,** add the optional `McpJiraClient` as a **P3
  stretch**, or show a separate "Claude / VS Code → Atlassian MCP" demo on top of the same design.

---

## 6. API + Orchestration Changes

**New endpoints** — in a dedicated `backend/app/routers/jira.py` (`APIRouter`) included by
`main.py`, to keep `main.py` lean:

| Endpoint | Purpose | Returns |
|---|---|---|
| `GET /api/jira/status` | JIRA equivalent of `GET /api/config`. | `{configured, provider, base_url_host, project_key, dry_run}` (**token never returned**). |
| `GET /api/jira/import?key=PROJ-123` | Build a feature-request string for Composer prefill. | `{request, issue:{key,summary,type}}`. |
| `POST /api/jira/create-stories` | Push generated stories (HITL action). | `{created:[{key,url,summary}], epic?, skipped:[…]}`. |
| `GET /api/jira/projects` *(stretch)* | Project picker. | `[{key,name}]`. |

**Orchestration decision — recommend (b): post-run button, not a pipeline agent.**

| Option | Pros | Cons |
|---|---|---|
| (a) "JIRA Publisher" agent inside `run_pipeline` | Emits its own SSE/artifact; feels integrated. | **Auto-writes to a real board every run** — dangerous. |
| **(b) Separate post-run action (button) ✅** | **Human-in-the-loop**; never spams a board; stateless. | One extra click (desirable). |

**Surfacing results:** `create-stories` returns the created keys/URLs to the button handler.
Optionally synthesize a small `jira.md` artifact so links also appear in the existing
**ArtifactPanel**. No new SSE event type required for the MVP.

**Statelessness:** the frontend already receives `stories.json` via the `artifact` SSE event, so
it can POST it straight to `create-stories` — **no server-side run persistence needed** for MVP.

---

## 7. Frontend Changes (keep build-free `frontend/main.js`)

Consistent with the existing **htm + React + Tailwind** (no JSX build):

1. **JIRA status badge** — in `Header`, next to the provider badge; fetch `GET /api/jira/status`.
   Show `JIRA: Mock` (amber, free) / `JIRA: <site> (cloud)` (emerald) / `not configured` (slate).
2. **"Import from JIRA"** — small input + button near `Composer` (issue key →
   `GET /api/jira/import` → prefill textarea).
3. **"Create N stories in JIRA"** — appears when a `stories.json` artifact exists (on the
   Requirements `AgentCard` or a results strip). On click → `POST /api/jira/create-stories` →
   render returned issue links (reuse the existing `toast`/`notify`); spinner while in flight.
4. **Confirmation guard** — when provider = `cloud`, confirm before creating (mock = no confirm).

New small components: `JiraBadge`, `JiraImport`, `JiraPublish`; a `useJira` hook. Mirror
optionally in the `web/` TS app if the production build is used.

---

## 8. Security & Safety

- **No auto-create on real boards** — only via explicit button + confirm for `cloud`.
- **Redact secrets** — never log/return the token; `status` returns host only.
- **Rate limits** — handle HTTP **429**; honor `Retry-After`; exponential backoff in `cloud.py`.
- **Idempotency** — avoid duplicates on re-run via a marker label (e.g., `sdlc-agent` +
  deterministic `sdlcrun-<hash>`); optionally JQL-search before creating. Pair with dry-run.
- **Dry-run mode** (`JIRA_DRY_RUN=true`) — `cloud.py` returns what it *would* create.
- **Sandbox project** — demo against a dedicated test project; never real work.
- **Validation** — strip spaces from labels, clamp summary to 255, validate issue type via
  `createmeta`, keep ADF minimal.

---

## 9. Cost & Accounts

- **JIRA Cloud free tier:** up to **10 users, free forever** — sufficient for the demo.
- **API token:** free.
- **Mock mode:** **$0**, no account, fully offline — preserves the project's cost philosophy.
- **No Azure impact:** JIRA is independent of Azure OpenAI credits.

---

## 9.5 Hosting & Environment Strategy

The **final demo is hosted** and runs against **real** services; **mock** is for local testing and
repeated dev runs. The provider/factory pattern makes this purely a matter of env vars — **the
code is identical** across environments.

| Aspect | Local testing / dev | **Hosted final demo** |
|---|---|---|
| LLM provider | `LLM_PROVIDER=mock` (free, offline, deterministic) | `LLM_PROVIDER=azure` (real Azure OpenAI) |
| JIRA provider | `JIRA_PROVIDER=mock` (in-memory, `DEMO-123`) | `JIRA_PROVIDER=cloud` (real JIRA Cloud) |
| Frontend | build-free `frontend/` (React/Tailwind via CDN) | **built `web/dist`** (self-hosted assets, no CDN runtime dependency) |
| Secrets | local `.env` (gitignored) | **Azure App Settings / Key Vault** |
| Cost | **$0** | Azure OpenAI tokens + JIRA free tier |

### Why build `web/dist` for the hosted demo
The build-free `frontend/` loads React + Tailwind from public CDNs at runtime — perfect for local
dev, but a **live-demo risk** (if a CDN is slow/blocked, the UI won't paint). For the hosted demo,
**build the Vite app once** (`cd web && npm install && npm run build`); FastAPI already prefers
`web/dist`, so assets become **same-origin and self-contained** — no third-party runtime dependency.
*(Our earlier npm install was flaky on the dev box; do this build step on the deploy host or in CI
where the network is reliable.)*

### Deployment target (consistent with `docs/plan.md`)
- **Backend (API + SSE):** **Azure Container Apps** or **App Service** — both support long-lived
  **SSE** streams (our `/api/stream`). Avoid Functions Consumption for the stream (timeout/buffering).
- **Frontend:** served by the **same FastAPI origin** from `web/dist` → **no CORS** to configure,
  one URL to share with judges.
- **Secrets:** `AZURE_OPENAI_*` and `JIRA_*` as **App Settings** (or Key Vault refs); never in the image.
- **HTTPS note:** the JIRA token leaves only via server→JIRA REST calls over TLS; it is **never**
  sent to the browser (`/api/jira/status` returns host only).

### Demo-day reliability (hosted, but keep a safety net)
Even with real services, keep the mock as an **emergency fallback**: a single env flip
(`LLM_PROVIDER=mock` / `JIRA_PROVIDER=mock`) restores a deterministic, offline run if the venue
network, Azure, or JIRA misbehaves mid-demo. Also: pre-create the sandbox project, pre-warm one
run, and set an **Azure budget alert**.

---

## 9.6 Free Hosting Options (Vercel & alternatives)

**Yes, free non-Azure hosting is possible — but mind one hard constraint: our backend streams
Server-Sent Events (`/api/stream`) and a full pipeline run can take ~30–90s with real Azure
OpenAI. It needs an _always-on / long-request_ host, not short-lived serverless functions.**

### The Vercel caveat (important)
Vercel is **excellent for the frontend** (it can host our built `web/dist` for free on a fast
CDN). But Vercel runs backends as **serverless functions with a max execution duration**
(short on the Hobby/free plan). A long-lived SSE stream and a multi-second agent run will be
**cut off or buffered** there. So: **Vercel = frontend yes, streaming Python backend no.**

### Comparison of free/cheap hosts

| Host | Free tier | Long SSE / long requests | One URL (FE+BE)? | Notes |
|---|---|---|---|---|
| **Azure Container Apps** ✅ *(recommended)* | Monthly free grant + your **$200** credit | ✅ persistent process | ✅ | Best Azure story; scales to zero; serves `web/dist` from the same origin. |
| **Render** (Web Service) | ✅ free | ✅ (⚠️ idles after ~15 min → cold start) | ✅ | Dead-simple Python deploy; great for a demo. |
| **Fly.io** | ✅ small free allowance | ✅ containers | ✅ | Docker-based; can keep a machine warm. |
| **Hugging Face Spaces** (Docker) | ✅ free | ✅ | ✅ | Super easy public URL; nice for hackathon sharing. |
| **Railway** | trial credits | ✅ | ✅ | Easy, but free is time-limited credits. |
| **Vercel** | ✅ free | ❌ for our SSE backend | ⚠️ FE only | Use for **frontend only**, paired with one of the above. |

### Two viable shapes

- **A) Single host (recommended):** put **frontend + backend together** on a container host
  (Container Apps / Render / Fly / HF Spaces). FastAPI already serves `web/dist`, so it's **one
  URL, no CORS, fewer moving parts** — ideal for a live demo.
- **B) Split:** **frontend on Vercel** (free CDN) + **backend on a container host**. Two URLs;
  relies on our existing permissive CORS middleware. Only worth it if you specifically want
  Vercel's frontend hosting; it adds complexity for no demo benefit.

### Recommendation
- If you'll use your **Azure credit** → **Azure Container Apps (Shape A)**: best fit, SSE-friendly,
  single origin, and consistent with `docs/plan.md`.
- If you want a **truly free, no-Azure** option → **Render or Hugging Face Spaces (Shape A)**:
  both run the whole app on one free URL and support our SSE stream.
- **Vercel** is a fine choice **only for the frontend** in a split setup — not for the backend.

> The provider/factory design means **none of this changes the code** — only env vars and the
> chosen host differ. We can decide the host at deploy time without blocking development.

---

## 10. Phased Roadmap & Effort

| Phase | Deliverables | Cost | Est. |
|---|---|---|---|
| **P1 — MVP (mock-only, free)** | `stories.json` from Requirements (persona + mock `_requirements`); `integrations/jira/{base,mock,factory,models,mapping}.py`; config fields; `GET /api/jira/status` + `POST /api/jira/create-stories`; UI badge + "Create N stories" button; tests in mock mode. | $0 | **0.5–1.5 d** |
| **P2 — Real Cloud + inbound** | `cloud.py` (httpx, Basic auth, ADF build/flatten, get/create); `GET /api/jira/import` + Composer "Import from JIRA"; `.env.example` + README/docs update. | Free tier | **1–2 d** |
| **P3 — Stretch** | Epic creation + `parent` linking; story-points field discovery; idempotency (marker label + JQL dedupe); JQL search + projects picker; `bulk` create; dry-run. | Free tier | **1–3 d** |

---

## 11. Demo Script

### A) Hosted final demo (primary — real services)
Env on the host: `LLM_PROVIDER=azure`, `JIRA_PROVIDER=cloud`, frontend served from `web/dist`.

1. Open the hosted URL. Header shows **`Azure OpenAI`** and **`JIRA: <your-site> (cloud)`** badges.
2. **Inbound:** paste a real key (e.g. `SDLC-1`) into *Import from JIRA* → Composer prefills from
   the live issue (summary + flattened ADF description + acceptance criteria + child stories).
3. **Run team** → pipeline streams live and produces `requirements.md`, **`stories.json`**,
   design / code / tests / docs.
4. **Outbound:** click **"Create N stories in JIRA"** → confirm dialog (shown for `cloud`) →
   real issues created → click the returned links to open them **in your live JIRA board**. 🎉
5. Results also appear as a `jira.md` artifact in the ArtifactPanel.

### B) Local testing / fallback (mock — free & offline)
Env: `LLM_PROVIDER=mock`, `JIRA_PROVIDER=mock`. Same UI, same code path.

1. Header shows **`Mock (free)`** and **`JIRA: Mock (free)`** — $0, no account, no network.
2. *Import from JIRA* with seeded key `DEMO-1` → Composer prefills from the in-memory epic.
3. **Run team** → produces the same artifacts deterministically.
4. **"Create 3 stories in JIRA"** → mock returns `DEMO-101..103` with URLs (no confirm needed).
5. Use this for fast repeated runs, CI, and as the **emergency fallback** during the live demo.

---

## 12. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Custom field IDs (story points, Epic Link) vary per instance | Discover via `createmeta`; configurable; **skip** if unknown. |
| ADF validation errors | Minimal builder (paragraph/heading/bulletList) + unit tests. |
| `/rest/api/3/search` deprecation | Use `/search/jql`; hide behind `JiraClient.search`. |
| team-managed vs company-managed (parent vs Epic Link) | Support both; default to `parent`; config switch. |
| 429 rate limits | Backoff + honor `Retry-After`. |
| Duplicate issues on re-run | Marker label + JQL dedupe + dry-run. |
| LLM emits invalid `stories.json` | Validate with pydantic; fall back to parsing `requirements.md` or skip publish. |

---

## 13. Open Questions (please confirm)

1. **JIRA flavor:** ✅ **Cloud confirmed** (free-tier Cloud account created) → REST **v3 + ADF**.
2. **Account ready? ✅ Free-tier JIRA Cloud account created.** To wire P2 I'll need four values in
   `.env`: `JIRA_BASE_URL` (your `https://<site>.atlassian.net`), `JIRA_EMAIL`, a `JIRA_API_TOKEN`
   (create at id.atlassian.com → *Security → API tokens*), and a **sandbox** `JIRA_PROJECT_KEY`
   (e.g. `SDLC`).
3. **Epic linking** required for the demo, or are **flat Stories** enough for MVP?
   *Recommend flat for P1, Epic in P3.*
4. **Issue types** available (Story/Task/Bug) and project type (team- vs company-managed)?
5. **Story points** needed (and the custom field id), or omit?
6. **Acceptance criteria** target: a **description section** (simplest) or a **custom field**?
7. **Frontend target:** build-free `frontend/main.js` only, or also wire the `web/` TS app?
8. **Connection approach:** direct **REST** (recommended default) or **MCP** (optional
   `McpJiraClient`, P3 stretch)? *See §5.5.*
9. **Hosting target (final demo):** ✅ **Hosted online with real services** confirmed. Pick the
   host: **Azure Container Apps** (recommended; uses your credit) **or** a **free** container host
   (**Render** / **Hugging Face Spaces**). **Vercel** is fine for the **frontend only** (its
   serverless backend can't hold our SSE stream) — see **§9.6**. All options run the *same code*.

