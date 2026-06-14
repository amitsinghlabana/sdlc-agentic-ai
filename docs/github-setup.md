# GitHub Setup — real publish (branch + PR)

Turns on the **real** GitHub integration so the pipeline can push generated code
as a Pull Request. Until you do this, the app uses the free offline **mock** — so
it already works; this just makes the PRs real.

> The integration calls the **GitHub REST API** (not local `git`), so there's no
> `git init`/clone needed. The mock fallback is always one env flip away
> (`GITHUB_PROVIDER=mock`).

---

## 1. Create a sandbox repo (1 min)

Use a throwaway repo so demo commits never touch real work.

1. GitHub → **New repository** (https://github.com/new).
2. Name e.g. `sdlc-sandbox`. Visibility: **Private** is fine.
3. ✅ **Check "Add a README"** — this gives the repo a default branch so the
   "branch + PR" path works immediately.
4. **Create repository.** Note the `owner/name` (e.g. `amitsingh7038/sdlc-sandbox`).

---

## 2. Create a token (2 min)

Pick the option that matches how you want to publish:

### Option A — PR into one existing repo (sandbox)
A token scoped to a **single repo**. Cannot create new repos.

1. **Fine-grained tokens** → **Generate new token**
   (https://github.com/settings/personal-access-tokens/new).
2. **Token name:** `sdlc-agent`. **Expiration:** 30 days is fine.
3. **Repository access:** *Only select repositories* → pick your `sdlc-sandbox`.
4. **Permissions** (Repository permissions):
   | Permission | Access |
   |---|---|
   | **Contents** | Read and write |
   | **Pull requests** | Read and write |
   | **Issues** | Read-only *(for `/import`)* |
   *(Metadata: Read-only is added automatically.)*
5. **Generate token** → copy it (starts with `github_pat_…`).

### Option B — Create brand-new repos + push (owner-only mode) ⭐
Needed when `GITHUB_REPO` is empty and the agent **creates a new repo**, or to
push to repos that don't exist yet. Requires **account-level** permissions, so a
single-repo token will **not** work (you'll get `403 Resource not accessible`).

**Fine-grained token:**
1. **Repository access:** **All repositories** *(creation is account-level — a
   "select repositories" token can't create new ones)*.
2. **Permissions:**
   | Permission | Access |
   |---|---|
   | **Administration** | Read and write *(create repos)* |
   | **Contents** | Read and write *(push files)* |
   | **Pull requests** | Read and write *(open PRs)* |
   | **Issues** | Read-only *(for `/import`)* |

**…or a classic token (simplest):** Settings → **Tokens (classic)** →
**Generate new token** → scope **`repo`** (full control of private repos). One
checkbox covers create + push + PR for every repo on your account.

> Already created a sandbox-only token and hitting `403 Resource not accessible
> by personal access token` on create/push? That token is scoped to one repo —
> regenerate it as **Option B** (or use a classic `repo` token), update
> `GITHUB_TOKEN` in `.env.local`, and restart.

---

## 3. Configure env vars

**`.env`** (non-secret — safe to keep):
```dotenv
GITHUB_PROVIDER=cloud
GITHUB_REPO=YOUR-USER/sdlc-sandbox
GITHUB_DEFAULT_BRANCH=main
```

**`.env.local`** (secret — gitignored, never attach):
```dotenv
GITHUB_TOKEN=github_pat_...your token...
```

---

## 4. Restart & verify

```powershell
./start.ps1
```

- **Status:** http://localhost:8000/api/github/status →
  `{"provider":"cloud","is_mock":false,"repo":"YOUR-USER/sdlc-sandbox", ...}`
- **In the UI:** the header badge turns indigo → **GitHub: YOUR-USER/sdlc-sandbox**.
- Run a feature → click **Publish to GitHub** → confirm → it opens a **real PR**
  on your sandbox repo. Open the link to see the generated files as a diff.

### Diagnose the token (when create/push 403s)

```text
http://localhost:8000/api/github/test
```
Returns who the token authenticates as, whether that matches `GITHUB_OWNER`, the
token type, and whether it can create repos — plus actionable `hints`. Example:
```json
{ "ok": true, "authenticated_as": "amitsinghlabana", "owner_matches": true,
  "token_type": "fine-grained", "can_create_repos": null,
  "hints": ["Fine-grained token: creating repos needs … 'Administration: Read and write' …"] }
```

---

## 5. Troubleshooting

| Symptom | Fix |
|---|---|
| Badge still says **Mock** | `GITHUB_PROVIDER` not `cloud`, or `GITHUB_TOKEN`/owner missing → falls back to mock (safe). |
| `401 Bad credentials` | Token wrong/expired, or not in `.env.local`. |
| **`403` on create, even with "All repositories"** | The fine-grained token is **missing the `Administration: Read and write`** permission (it's a *separate* dropdown from Contents — easy to miss). Add it, regenerate, update `.env.local`. **If it still 403s, switch to a classic token with the `repo` scope** — it reliably creates repos. Run `/api/github/test` to confirm. |
| `403` on push/PR | Repo needs **Contents** + **Pull requests** = Read and write, and the token must have access to it. |
| `403` + *owner mismatch* | `/api/github/test` shows `owner_matches: false` → your token's account ≠ `GITHUB_OWNER`. Set `GITHUB_OWNER` to the token's account, or use a token for that org. |
| `404` on the repo | `GITHUB_REPO` typo, or token can't see it (private + not selected). |
| `422 Reference already exists` | A branch name collision — just re-run (branch names are timestamped). |
| `CERTIFICATE_VERIFY_FAILED` | Corporate TLS — set `GITHUB_CA_BUNDLE` or `GITHUB_VERIFY_SSL=false` (OS trust store is used by default). |

> **TL;DR for "create a new repo":** if a fine-grained token gives you any trouble,
> a **classic token with the `repo` scope** is the fastest guaranteed fix.

---

## 6. Safety notes

- The client only ever writes to a **new branch + PR** (never force-pushes `main`).
- The UI shows a **confirm dialog** before any real write.
- Set `GITHUB_DRY_RUN=true` to rehearse with zero writes.
- Rotate/revoke the token in GitHub Settings when the hackathon ends.

