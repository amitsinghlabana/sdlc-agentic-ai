# Foundry IQ Setup — Azure AI Search (agentic retrieval)

This guide turns on the **real** Foundry IQ grounding (the "librarian" 📚 that
remembers your docs), wired to your **existing Azure OpenAI** (the "writer" 🧠).
Until you do this, the app uses the free offline **mock** — so it already works;
this just makes the grounding *real* for the hosted demo.

> **Cost note:** delete the search service after the hackathon (last step). The
> mock fallback is always one env flip away (`KNOWLEDGE_PROVIDER=mock`).

---

## 1. Create an Azure AI Search service (one-time, portal)

1. Azure Portal → **Create a resource** → **Azure AI Search**.
2. Resource group: reuse **sdlc-agent-rg**. Name: e.g. `sdlc-search-<initials>`.
3. **Pricing tier: Basic** (recommended — agentic retrieval / *knowledge agents*
   may not be available on Free). Create.
4. Open the resource → **Settings → Keys** → copy a **Primary admin key**.
5. Overview → copy the **Url** → `https://<your-search>.search.windows.net`.

You keep your existing **Azure OpenAI** resource — AI Search *calls* it; you do
**not** create a second OpenAI.

---

## 2. Configure env vars

**`.env`** (non-secret — already has placeholders):

```dotenv
KNOWLEDGE_PROVIDER=mock          # leave as mock until step 4 succeeds
FOUNDRY_SEARCH_ENDPOINT=https://<your-search>.search.windows.net
FOUNDRY_INDEX=sdlc-standards
FOUNDRY_KNOWLEDGE_AGENT=sdlc-knowledge-agent
FOUNDRY_API_VERSION=2025-08-01-preview   # match what your portal shows
```

**`.env.local`** (secret — gitignored, never attach):

```dotenv
FOUNDRY_API_KEY=<Search ADMIN key from step 1.4>
```

> Your `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT` (e.g. `gpt-4o-mini`),
> and `AZURE_OPENAI_API_KEY` must also be set — the setup script binds the
> knowledge agent to that deployment.

---

## 3. Run the one-command setup

From the repo root:

```powershell
python scripts/setup_foundry_iq.py all
```

This runs four steps and prints a ✓ for each:

| Step | What it does | Analogy |
|---|---|---|
| `index`  | Creates the search index (text + semantic config) | builds the library shelves |
| `upload` | Uploads `docs/standards/*.md` as citable chunks | puts your books on the shelves |
| `agent`  | Creates the **knowledge agent** bound to your Azure OpenAI | hires the librarian + gives them a brain |
| `test`   | Runs a sample retrieval and prints the cited sources | asks a test question |

Re-run any single step, e.g. after editing docs: `python scripts/setup_foundry_iq.py upload`.

---

## 4. Flip the app to real Foundry IQ

In `.env`, set:

```dotenv
KNOWLEDGE_PROVIDER=foundry
```

Restart (`./start.ps1`) and verify:

```
http://localhost:8000/api/knowledge/status   →  provider: "foundry"
http://localhost:8000/api/knowledge/test      →  ok: true, count >= 1, real citations
```

Run a feature (e.g. *"Add secure email/password login"*). The **Grounding**
panel now shows sources retrieved live from Azure AI Search, and the
Requirements/Architect output cites them inline as `[S1]`.

---

## 5. Troubleshooting

| Symptom | Fix |
|---|---|
| `403` on setup | Wrong key — use the **admin** key in `.env.local`. |
| `Feature not supported` / agent step fails | Search tier too low → use **Basic+**; or bump `FOUNDRY_API_VERSION` to the value your portal lists. |
| `test` returns 0 references | Index empty (run `upload`) or semantic config missing (re-run `index`). |
| `CERTIFICATE_VERIFY_FAILED` | Corporate TLS — set `KNOWLEDGE_CA_BUNDLE` or `KNOWLEDGE_VERIFY_SSL=false` (the OS trust store is used by default). |
| App still says "Mock" | `KNOWLEDGE_PROVIDER` not `foundry`, or `FOUNDRY_*` incomplete (it safely falls back to mock). |

---

## 6. Tear down (cost cleanup)

```powershell
python scripts/setup_foundry_iq.py delete   # removes the agent + index
```

Then delete the **Azure AI Search** resource in the portal (or delete the whole
**sdlc-agent-rg** resource group to remove everything at once).

