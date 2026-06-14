# 📋 Plan: SDLC Agentic AI — Hackathon Specification & Build Plan

> **Status:** Draft for review. This is a planning deliverable only — no implementation yet.
> Review, comment, and we'll refine before any code is written.

---

## 1. Vision & Problem Statement

### What it is
**SDLC Agentic AI** is a multi-agent system where specialized AI agents collaborate — like a
virtual software team — to take a feature request from **idea → requirements → design → code →
tests → review → docs → deployment**, with humans approving at key checkpoints.

### The problem
Modern software delivery is slow and fragmented across many specialist roles (BA, architect, dev,
QA, reviewer, DevOps, tech writer). Context is lost in handoffs, boilerplate is repetitive, and
small features still need a whole team. Solo developers and small teams can't cover every role well.

### The solution
An **Orchestrator agent** that decomposes a request and delegates to role-specialized agents, each
an expert in one SDLC phase, sharing a common memory and producing real artifacts (Markdown specs,
code files, test files, a PR).

### Hackathon framing (why it wins)
| Criterion | How we hit it |
|-----------|---------------|
| **Wow-factor** | Watch a "team" of agents work live, streaming their thoughts and handing off to each other |
| **Achievable** | MVP = orchestrator + 3–4 agents producing artifacts for one demo scenario |
| **Tangible output** | Generates a real GitHub PR with code, tests, and docs |
| **Azure story** | Showcases Azure OpenAI + AI Foundry agent orchestration end-to-end |
| **Relatable** | Every judge understands "build me a login page" |

---

## 2. Capabilities & Features

### Agent roster (the "virtual team")

| Agent | Role | Inputs → Outputs | Key tools |
|-------|------|------------------|-----------|
| 🧭 **Orchestrator / PM** | Plans, decomposes, routes, tracks state, manages human approvals | User request → task graph + final assembled result | State store, agent registry |
| 📝 **Requirements Analyst** | Turns vague request into structured user stories + acceptance criteria | Request → `requirements.md` | RAG over project context |
| 🏛️ **Architect** | Proposes design, tech choices, file/component structure | Requirements → `design.md` + scaffolding plan | Diagram/Markdown gen |
| 💻 **Developer / Coder** | Writes implementation code from the design | Design → source files | Code-gen, file writer |
| 🧪 **Tester / QA** | Generates unit/integration tests + test plan | Code + requirements → test files | Code-gen, (optional) test runner |
| 🔍 **Code Reviewer** | Reviews code for bugs, style, security; requests changes | Code → review comments + verdict | Static analysis, lint |
| 🚀 **DevOps** | Generates CI/CD workflow, Dockerfile, deploy config | Repo → `.github/workflows`, IaC | GitHub API |
| 📚 **Documentation** | Produces README, API docs, changelog | All artifacts → `README.md` etc. | Markdown gen |

**Handoff model:** the Orchestrator passes a shared **"work package"** (request + accumulated
artifacts + state) down a pipeline; each agent appends its artifact. The Reviewer can send work
**back** to the Developer (feedback loop, capped at N iterations).

### MVP vs. Stretch (prioritized)

#### 🟢 MVP — must-have for the demo
1. Orchestrator that decomposes a request and runs a **sequential pipeline**.
2. **Requirements Analyst**, **Architect**, **Developer**, **Tester** agents producing real artifacts.
3. Shared state/memory passed between agents.
4. **Web UI** showing each agent's output streaming in real time.
5. One polished end-to-end scenario ("Add a login page").
6. Artifacts downloadable / viewable (Markdown + code files).

#### 🟡 Should-have (if time allows)
7. **Code Reviewer** agent with a Developer↔Reviewer feedback loop.
8. **Human-in-the-loop** approval gates (approve requirements before coding).
9. **Documentation** agent (auto README).
10. Persist runs to a database; re-open past runs.

#### 🔵 Stretch — wow extras
11. **DevOps** agent that opens a **real GitHub PR** via the GitHub API.
12. **RAG** over an existing codebase (Azure AI Search) so agents respect existing patterns.
13. Live **test execution** in a sandbox; loop until tests pass.
14. Agent "chat" view showing inter-agent messages.
15. Voice or diagram (Mermaid) output from the Architect.

---

## 3. Architecture

### Orchestration pattern
**Orchestrator-Worker + Sequential Pipeline with feedback loops.** The Orchestrator owns the plan;
worker agents execute phases in order; the Reviewer can loop back to the Developer. This is the most
demo-legible and reliable pattern for a hackathon (vs. fully autonomous graph chaos).

### Component diagram (described)
```
┌──────────────────────────────────────────────────────────────┐
│  FRONTEND  (Azure Static Web Apps)                            │
│  React/Next chat UI · live agent stream · artifact viewer     │
└───────────────▲───────────────────────────┬──────────────────┘
                │ WebSocket/SSE (stream)     │ REST (start run)
┌───────────────┴───────────────────────────▼──────────────────┐
│  BACKEND / API  (Azure Container Apps or Functions)           │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  AGENT ORCHESTRATION LAYER                              │  │
│  │  Orchestrator → [Req][Arch][Dev][Test][Review][Docs]   │  │
│  │  shared "work package" state · human-in-loop gates     │  │
│  └───────┬───────────────┬────────────────┬───────────────┘  │
│          │               │                │                   │
│   ┌──────▼─────┐  ┌───────▼──────┐  ┌──────▼───────┐          │
│   │ Azure      │  │ Azure AI     │  │ State store  │          │
│   │ OpenAI     │  │ Search       │  │ Cosmos DB /  │          │
│   │ (LLM)      │  │ (vector RAG) │  │ Table Storage│          │
│   └────────────┘  └──────────────┘  └──────────────┘          │
│          │                                                     │
│   ┌──────▼──────┐   ┌──────────────┐                          │
│   │ Key Vault   │   │ GitHub API   │ (DevOps agent → PR)      │
│   └─────────────┘   └──────────────┘                          │
└───────────────────────────────────────────────────────────────┘
```

### Key design decisions
- **Communication:** agents exchange a structured JSON **work package**; the Orchestrator validates
  each step's output schema before proceeding.
- **Shared memory:** short-term = in-run state object; long-term = Cosmos DB (run history) +
  Azure AI Search (codebase/context RAG).
- **Tool usage:** agents call typed tools (file writer, GitHub client, web/RAG search, optional code
  runner) via the framework's function-calling.
- **Human-in-the-loop:** approval gate after Requirements and before PR creation; UI shows
  "Approve / Edit / Reject".
- **Streaming:** token streaming + per-agent status events over SSE/WebSocket for the live
  "team at work" effect.

---

## 4. Azure-Centric Tech Stack

### Service mapping & free-tier notes
| Layer | Recommended Azure service | Free-trial / cost notes |
|-------|---------------------------|--------------------------|
| **LLM** | **Azure OpenAI** (GPT-4o / GPT-4o-mini) via **Azure AI Foundry** | Pay-as-you-go; covered by **$200 trial credit**. Use `gpt-4o-mini` for cheap agents, `gpt-4o` for hard reasoning. ⚠️ biggest cost driver |
| **Agent orchestration** | **Azure AI Foundry Agent Service** *or* self-hosted framework (see below) | Foundry Agent Service is managed; self-hosting on Container Apps is cheaper/portable |
| **Vector store / RAG** | **Azure AI Search** | **Free tier** exists (50 MB, 3 indexes) and supports vector search — fine for demo. Basic tier if you outgrow it |
| **Backend/API** | **Azure Container Apps** (preferred) or **Azure Functions** | Container Apps: generous monthly **free grant**. Functions Consumption: **1M free executions/mo**. Container Apps better for long-running agent runs |
| **State / history** | **Azure Cosmos DB** (free tier) or **Table Storage** | Cosmos free tier: **1000 RU/s + 25 GB free**. Table Storage = pennies. Table Storage is simplest for MVP |
| **Secrets** | **Azure Key Vault** | Effectively free at low usage |
| **Frontend hosting** | **Azure Static Web Apps** | **Free tier** (perfect for hackathon) |
| **CI/CD** | **GitHub Actions** | Free for public repos; also the DevOps agent's integration target |
| **Observability (opt.)** | **Application Insights** | Free quota sufficient for demo |

### Agent framework recommendation
| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **Microsoft Agent Framework** (unifies Semantic Kernel + AutoGen) | Native Azure OpenAI/Foundry integration, multi-agent + workflows, MS-supported | Newer API surface | ✅ **Recommended** — best Azure alignment |
| **Semantic Kernel** | Mature, great Azure + .NET/Python, plugins | Multi-agent is evolving | ✅ Strong fallback |
| **AutoGen** | Excellent multi-agent conversations, fast prototyping | Less "production" structure | ✅ Great for the demo loop |
| **LangGraph** | Best-in-class explicit graph control + checkpoints | Less Azure-native, more glue code | ⚠️ Use if you want graph control |
| **Azure AI Foundry Agent Service** | Fully managed, threads/tools built in | Less control, evolving | ⚠️ Consider for stretch |

> **Recommendation:** **Python + Microsoft Agent Framework (or Semantic Kernel)** targeting
> **Azure OpenAI** via **Azure AI Foundry**. Python maximizes hackathon velocity and AI ecosystem support.

---

## 5. Requirements

### Accounts & access
- **Azure account** with active **free-trial ($200) credit**; create one **Resource Group** for easy cleanup.
- **Azure OpenAI / AI Foundry** access enabled in the subscription; deploy `gpt-4o` and `gpt-4o-mini`.
- **GitHub account** + a **Personal Access Token** (repo scope) for the DevOps agent.

### Keys / secrets (store in Key Vault or local `.env`)
- Azure OpenAI endpoint + key (or Entra ID auth), deployment names.
- Azure AI Search endpoint + key (if RAG used).
- Cosmos/Table Storage connection string.
- GitHub PAT.

### SDKs & dev tools
| Need | Tool |
|------|------|
| Language | **Python 3.11+** (recommended) |
| Agent framework | `agent-framework` / `semantic-kernel` |
| Azure SDKs | `openai`, `azure-search-documents`, `azure-data-tables`/`azure-cosmos`, `azure-identity`, `azure-keyvault-secrets` |
| API | **FastAPI** + Uvicorn (SSE/WebSocket streaming) |
| Frontend | **React/Next.js** (or Vite) |
| GitHub | `PyGithub` or REST |
| Infra | **Azure CLI**, optional **Bicep**, **Docker** |

### Team skills
- 1× Python/backend + agent orchestration (lead).
- 1× frontend (React + streaming UI).
- 1× Azure/DevOps (provisioning, deploy, GitHub integration).
- Shared: prompt engineering for agent personas.

### 💰 Cost / credit budget (watch closely)
| Item | Est. trial impact |
|------|-------------------|
| LLM tokens (dev + demo) | Largest cost — **use `gpt-4o-mini` by default**, cap output tokens, cache results |
| AI Search | Free tier = $0 |
| Container Apps / Functions | Within free grant |
| Cosmos free tier / Table | ~$0 |
| Static Web Apps | Free |
| **Guardrails** | Set a **budget alert** at ~$50, mock LLM calls during UI dev, pre-record a demo run as fallback |

---

## 6. Phased Implementation Roadmap

Assumes a **~2-day (24-working-hour) hackathon**; compresses to 1 day by cutting to 3 agents + no DB.

### Day 0 — Pre-hack prep (before clock starts, if allowed)
- Create Azure account, resource group, deploy OpenAI models.
- Init repo, scaffold backend/frontend, confirm "hello LLM" call works.

### Day 1 — Core engine
| Block | Milestone |
|-------|-----------|
| **H1–2** | Provision Azure (OpenAI, Search, storage, Key Vault); secrets wired |
| **H3–4** | Single-agent loop: prompt → Azure OpenAI → structured output |
| **H5–6** | **Orchestrator** + shared work-package state object |
| **H7–8** | **Requirements** & **Architect** agents producing `requirements.md` / `design.md` |
| **H9–10** | **Developer** & **Tester** agents producing code + test files |
| **H11–12** | End-to-end pipeline runs from CLI for the demo scenario ✅ *MVP backbone done* |

### Day 2 — UI, polish, stretch
| Block | Milestone |
|-------|-----------|
| **H13–14** | FastAPI endpoint + **SSE/WebSocket streaming** of agent events |
| **H15–17** | **Frontend**: chat input, live per-agent panels, artifact viewer |
| **H18** | **Human-in-the-loop** approval gate after Requirements |
| **H19–20** | Stretch: **Code Reviewer loop** and/or **GitHub PR** creation |
| **H21** | Persist runs (Table/Cosmos); deploy to Container Apps + Static Web Apps |
| **H22–23** | **Demo polish**: scripted scenario, error handling, pre-recorded fallback |
| **H24** | Final rehearsal + pitch |

### Minimal end-to-end demo flow (the "definition of done" for MVP)
`User types request → Orchestrator plans → Requirements → Architect → Developer → Tester → UI shows
all artifacts streaming → user downloads result.`

---

## 7. Demo Scenario — "Add a login page"

| Step | Agent | What the audience sees |
|------|-------|------------------------|
| 1 | **User** | Types: *"Add a login page with email/password to my web app."* |
| 2 | 🧭 **Orchestrator** | Streams a plan: "I'll engage Requirements → Architect → Developer → Tester → Reviewer." |
| 3 | 📝 **Requirements** | Produces user stories + acceptance criteria (validation, error states, "remember me"). **→ Human approves.** |
| 4 | 🏛️ **Architect** | Proposes components (`LoginForm`, `AuthService`, `/api/login`), tech choices, file layout, optional Mermaid diagram. |
| 5 | 💻 **Developer** | Generates real code files (component + API handler + validation). |
| 6 | 🧪 **Tester** | Generates unit tests for validation and auth flow + a test plan. |
| 7 | 🔍 **Reviewer** *(stretch)* | Flags "password not hashed"; **loops back**; Developer fixes; Reviewer approves. |
| 8 | 🚀 **DevOps** *(stretch)* | Opens a **GitHub PR** with all files + a CI workflow. |
| 9 | 📚 **Docs** *(stretch)* | Adds README section + changelog. |
| 10 | **Finale** | UI shows the full artifact set; judges click the live PR link. 🎉 |

---

## 8. Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| **LLM cost overrun** burns trial credit | High | Default to `gpt-4o-mini`, cap tokens, cache, budget alert at $50, mock during UI dev |
| **API rate limits / throttling** | Med | Request quota early, add retry/backoff, sequential (not parallel) agent calls |
| **Agent hallucination / bad output** | High | Strict output schemas + validation, constrained prompts, human approval gates, scoped scenario |
| **Reviewer↔Dev infinite loop** | Med | Hard cap iterations (e.g., 2), then escalate to human |
| **Time runs out** | High | Strict MVP-first; stretch goals are independent toggles; pre-record fallback demo |
| **Azure provisioning friction** (OpenAI access, regions) | Med | Provision Day 0; pick a region with model availability; keep keys in Key Vault/`.env` |
| **Live-demo failure** (network/API) | Med | Pre-recorded run + cached artifacts as backup |
| **Integration complexity** (GitHub, deploy) | Med | Keep GitHub/PR as **stretch**; CLI/local works without them |

---

## 9. Suggested Repo / Project Structure

```
sdlc-agent/
├── README.md
├── docs/
│   ├── architecture.md
│   ├── demo-script.md
│   └── plan.md                  # this plan
├── infra/                       # Azure provisioning
│   ├── main.bicep
│   └── deploy.ps1
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI + streaming endpoints
│   │   ├── orchestrator.py      # plan + route + state
│   │   ├── agents/
│   │   │   ├── base.py          # shared agent contract
│   │   │   ├── requirements.py
│   │   │   ├── architect.py
│   │   │   ├── developer.py
│   │   │   ├── tester.py
│   │   │   ├── reviewer.py
│   │   │   ├── devops.py
│   │   │   └── docs.py
│   │   ├── tools/               # file writer, github, rag search
│   │   ├── prompts/             # per-agent persona prompts
│   │   ├── memory/              # state store + AI Search client
│   │   └── models/              # work-package schemas (pydantic)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/          # AgentPanel, ArtifactViewer, ChatInput
│   │   ├── hooks/               # useAgentStream (SSE/WS)
│   │   └── App.tsx
│   └── package.json
├── samples/                     # example outputs for fallback demo
├── .env.example
└── .github/workflows/ci.yml
```

---

## ❓ Open Questions to Finalize Before Implementation

1. **Hackathon duration?** 24h / 48h / 1-week — re-times the roadmap. *(Currently assumes ~2 days.)*
2. **Language preference?** **Python** (recommended, fastest) vs. **.NET/TypeScript**.
3. **Framework choice?** **Microsoft Agent Framework / Semantic Kernel** (Azure-native) vs. **AutoGen** (fastest multi-agent) vs. **LangGraph** (graph control).
4. **Output ambition:** is a **real GitHub PR** a must-have, or are downloadable artifacts enough?
5. **Team size & skills?** Determines how many stretch goals are realistic.
6. **Codebase RAG:** demo on a **greenfield** request only, or also operate on an **existing repo**?

