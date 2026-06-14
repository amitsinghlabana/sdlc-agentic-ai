"""Mock LLM provider — the zero-cost engine for local testing & internal demos.

It returns realistic, schema-valid JSON for each agent so the *entire* multi-agent
pipeline (and the live streaming UI) works end-to-end without an Azure account or
spending any tokens. It is also deterministic, which makes it perfect for the
reviewer ↔ developer feedback-loop demo:

* First developer pass stores passwords in plaintext (an intentional "bug").
* The reviewer spots it and requests changes.
* The developer's revised pass uses bcrypt; the reviewer then approves.

The branch is detected purely from the prompt text (presence of "reviewer
feedback to address" / "bcrypt"), so no hidden state is needed.
"""
from __future__ import annotations

import json

from .base import LLMProvider


def _title(request: str) -> str:
    t = (request or "the requested feature").strip().splitlines()[0]
    return (t[:70] + "…") if len(t) > 70 else t


class MockProvider(LLMProvider):
    name = "mock"
    label = "Mock (free)"

    async def complete(
        self,
        system: str,
        user: str,
        *,
        tag: str = "",
        json_mode: bool = True,
        max_tokens: int | None = None,
    ) -> str:
        title = _title(user.split("Feature request:", 1)[-1] if "Feature request:" in user else user)
        builder = {
            "requirements": self._requirements,
            "architect": self._architect,
            "developer": self._developer,
            "tester": self._tester,
            "reviewer": self._reviewer,
            "docs": self._docs,
            "committer": self._committer,
        }.get(tag, self._generic)
        return json.dumps(builder(title, user))

    # ------------------------------------------------------------------ #
    def _requirements(self, title: str, user: str) -> dict:
        grounded = "Grounded knowledge" in user
        cite = " [S1]" if grounded else ""
        details = (
            f"## Requirements for: {title}\n\n"
            "I broke the request into user stories with testable acceptance criteria "
            "and called out non-functional needs (security, validation, accessibility)."
            + (
                "\n\nGrounded in company standards via **Foundry IQ** — security and "
                "story conventions are cited inline as [S#]."
                if grounded
                else ""
            )
        )
        content = (
            f"# Requirements — {title}\n\n"
            "## User Stories\n"
            "- **US-1:** As a user, I can sign in with my email and password so I can access my account.\n"
            "- **US-2:** As a user, I see clear validation errors when my input is invalid.\n"
            "- **US-3:** As a user, I am told when my credentials are wrong without leaking which field failed.\n\n"
            "## Acceptance Criteria\n"
            "- Email must be a valid format; password is required (min 8 chars).\n"
            "- Successful login returns a 200 and a session indicator.\n"
            f"- Failed login returns 401 with a generic message.{cite}\n"
            "- All inputs are validated server-side.\n\n"
            "## Non-Functional\n"
            f"- **Security:** passwords must never be stored or compared in plaintext.{cite}\n"
            "- **Accessibility:** form fields have labels; errors are announced.\n"
            "- **Performance:** auth response < 300ms under demo load.\n"
        )
        stories_json = json.dumps(
            {
                "epic": {"summary": title, "description": f"Feature: {title}"},
                "stories": [
                    {
                        "summary": "Sign in with email and password",
                        "description": "As a user, I can sign in with my email and password so I can access my account.",
                        "acceptance_criteria": [
                            "Email must be a valid format; password is required (min 8 chars).",
                            "Successful login returns 200 and a session indicator.",
                            "Failed login returns 401 with a generic message.",
                        ],
                        "story_points": 3,
                        "labels": ["auth", "sdlc-agent"],
                        "issue_type": "Story",
                        "subtasks": [
                            {"summary": "Build the login form UI"},
                            {"summary": "Implement POST /api/login endpoint"},
                            {"summary": "Write unit tests for auth flow"},
                        ],
                    },
                    {
                        "summary": "Show clear validation errors",
                        "description": "As a user, I see clear validation errors when my input is invalid.",
                        "acceptance_criteria": [
                            "Inline error messages for each field.",
                            "Errors are announced for screen readers.",
                        ],
                        "story_points": 2,
                        "labels": ["validation", "sdlc-agent"],
                        "issue_type": "Story",
                        "subtasks": [
                            {"summary": "Add client-side field validation"},
                            {"summary": "Add ARIA live region for error announcements"},
                        ],
                    },
                ],
            },
            indent=2,
        )
        return {
            "summary": "Authored user stories + acceptance criteria with security & accessibility constraints.",
            "details": details,
            "artifacts": [
                {"name": "requirements.md", "type": "markdown", "language": "markdown", "content": content},
                {"name": "stories.json", "type": "config", "language": "json", "content": stories_json},
            ],
        }

    def _architect(self, title: str, user: str) -> dict:
        details = (
            f"## Technical Design for: {title}\n\n"
            "Chose a small **FastAPI** backend + a static HTML form. Defined the API "
            "contract, component breakdown, and a sequence diagram."
        )
        content = (
            f"# Design — {title}\n\n"
            "## Stack\n"
            "- **Backend:** Python + FastAPI (Pydantic validation).\n"
            "- **Frontend:** static HTML form posting JSON.\n"
            "- **Password hashing:** bcrypt.\n\n"
            "## Components\n"
            "| Component | Responsibility |\n"
            "|-----------|----------------|\n"
            "| `login.html` | Renders the email/password form |\n"
            "| `auth.py` (`/api/login`) | Validates input, verifies credentials |\n"
            "| `verify_password` | Compares password against stored bcrypt hash |\n\n"
            "## API Contract\n"
            "`POST /api/login` → `{ email, password }` → `200 {status, message}` | `401`.\n\n"
            "## Sequence\n"
            "```mermaid\n"
            "sequenceDiagram\n"
            "  User->>login.html: enter email/password\n"
            "  login.html->>auth.py: POST /api/login\n"
            "  auth.py->>auth.py: validate + verify_password\n"
            "  auth.py-->>login.html: 200 / 401\n"
            "```\n"
        )
        return {
            "summary": "Selected FastAPI + bcrypt, defined the API contract and component breakdown.",
            "details": details,
            "artifacts": [
                {"name": "design.md", "type": "markdown", "language": "markdown", "content": content}
            ],
        }

    def _developer(self, title: str, user: str) -> dict:
        revising = "reviewer feedback to address" in user.lower()
        if revising:
            details = (
                "## Revised implementation\n\n"
                "Addressed the review: passwords are now hashed and verified with **bcrypt** "
                "via a dedicated `verify_password` helper."
            )
            auth_py = (
                "from fastapi import APIRouter, HTTPException\n"
                "from pydantic import BaseModel, EmailStr\n"
                "import bcrypt\n\n"
                "router = APIRouter()\n\n"
                "# Demo store now holds bcrypt password *hashes* (never plaintext).\n"
                "USERS = {\n"
                '    "user@example.com": bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()\n'
                "}\n\n\n"
                "class LoginRequest(BaseModel):\n"
                "    email: EmailStr\n"
                "    password: str\n\n\n"
                "def verify_password(password: str, password_hash: str) -> bool:\n"
                "    return bcrypt.checkpw(password.encode(), password_hash.encode())\n\n\n"
                '@router.post("/api/login")\n'
                "def login(payload: LoginRequest):\n"
                "    stored_hash = USERS.get(payload.email)\n"
                "    if stored_hash is None or not verify_password(payload.password, stored_hash):\n"
                '        raise HTTPException(status_code=401, detail="Invalid email or password")\n'
                '    return {"status": "ok", "message": "Logged in"}\n'
            )
            summary = "Revised: passwords now hashed & verified with bcrypt."
        else:
            details = (
                "## Initial implementation\n\n"
                "Built the `/api/login` route with Pydantic validation and a simple in-memory "
                "user store for the demo."
            )
            auth_py = (
                "from fastapi import APIRouter, HTTPException\n"
                "from pydantic import BaseModel, EmailStr\n\n"
                "router = APIRouter()\n\n"
                "# Demo in-memory user store (replace with a real database).\n"
                'USERS = {"user@example.com": "password123"}\n\n\n'
                "class LoginRequest(BaseModel):\n"
                "    email: EmailStr\n"
                "    password: str\n\n\n"
                '@router.post("/api/login")\n'
                "def login(payload: LoginRequest):\n"
                "    stored = USERS.get(payload.email)\n"
                "    if stored is None or stored != payload.password:\n"
                '        raise HTTPException(status_code=401, detail="Invalid email or password")\n'
                '    return {"status": "ok", "message": "Logged in"}\n'
            )
            summary = "Implemented /api/login with validation (in-memory user store)."

        login_html = (
            "<!doctype html>\n"
            '<html lang="en">\n<head>\n  <meta charset="utf-8" />\n'
            f"  <title>Login — {title}</title>\n</head>\n<body>\n"
            '  <form id="login-form">\n'
            '    <label>Email <input type="email" name="email" required /></label>\n'
            '    <label>Password <input type="password" name="password" required minlength="8" /></label>\n'
            '    <button type="submit">Sign in</button>\n'
            '    <p id="msg" role="status"></p>\n'
            "  </form>\n"
            "  <script>\n"
            "    const f = document.getElementById('login-form');\n"
            "    f.addEventListener('submit', async (e) => {\n"
            "      e.preventDefault();\n"
            "      const body = { email: f.email.value, password: f.password.value };\n"
            "      const r = await fetch('/api/login', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});\n"
            "      document.getElementById('msg').textContent = r.ok ? 'Welcome!' : 'Invalid email or password';\n"
            "    });\n"
            "  </script>\n"
            "</body>\n</html>\n"
        )
        return {
            "summary": summary,
            "details": details,
            "artifacts": [
                {"name": "app/auth.py", "type": "code", "language": "python", "content": auth_py},
                {"name": "templates/login.html", "type": "code", "language": "html", "content": login_html},
            ],
        }

    def _tester(self, title: str, user: str) -> dict:
        details = (
            "## Test plan\n\n"
            "Added unit tests covering the happy path and a wrong-password case using "
            "FastAPI's `TestClient`."
        )
        test_py = (
            "from fastapi import FastAPI\n"
            "from fastapi.testclient import TestClient\n"
            "from app.auth import router\n\n"
            "app = FastAPI()\n"
            "app.include_router(router)\n"
            "client = TestClient(app)\n\n\n"
            "def test_login_success():\n"
            '    r = client.post("/api/login", json={"email": "user@example.com", "password": "password123"})\n'
            "    assert r.status_code == 200\n\n\n"
            "def test_login_wrong_password():\n"
            '    r = client.post("/api/login", json={"email": "user@example.com", "password": "nope"})\n'
            "    assert r.status_code == 401\n"
        )
        return {
            "summary": "Wrote unit tests for the success and wrong-password paths.",
            "details": details,
            "artifacts": [
                {"name": "tests/test_auth.py", "type": "test", "language": "python", "content": test_py}
            ],
        }

    def _reviewer(self, title: str, user: str) -> dict:
        secure = ("bcrypt" in user.lower()) or ("verify_password" in user.lower())
        if secure:
            return {
                "summary": "Approved — passwords are hashed with bcrypt and inputs validated.",
                "details": (
                    "## Review — ✅ Approved\n\n"
                    "- Passwords are now hashed & verified with bcrypt. 👍\n"
                    "- Input validation via Pydantic looks good.\n"
                    "- Follow-up (non-blocking): add rate limiting / account lockout.\n"
                ),
                "verdict": "approve",
                "comments": [
                    "Passwords now hashed with bcrypt — good.",
                    "Consider adding rate limiting and account lockout as a follow-up.",
                ],
                "artifacts": [],
            }
        return {
            "summary": "Requested changes — passwords are compared in plaintext.",
            "details": (
                "## Review — 🔁 Changes requested\n\n"
                "- **Security (blocking):** passwords are stored and compared in plaintext. "
                "Store a bcrypt hash and verify with `bcrypt.checkpw`.\n"
                "- Otherwise the structure and validation look fine.\n"
            ),
            "verdict": "request_changes",
            "comments": [
                "Passwords are compared in plaintext — store and verify bcrypt hashes instead.",
                "Add rate limiting to mitigate brute-force attempts (follow-up).",
            ],
            "artifacts": [],
        }

    def _docs(self, title: str, user: str) -> dict:
        content = (
            f"# {title}\n\n"
            "## Overview\n"
            "Adds email/password login backed by a FastAPI endpoint with bcrypt-hashed credentials.\n\n"
            "## Run\n"
            "```bash\n"
            "uvicorn app.main:app --reload\n"
            "```\n\n"
            "## API\n"
            "`POST /api/login` — body `{ email, password }` → `200` on success, `401` otherwise.\n\n"
            "## Tests\n"
            "```bash\n"
            "pytest\n"
            "```\n"
        )
        return {
            "summary": "Generated a feature README with run, API, and test instructions.",
            "details": "## Documentation\n\nProduced a README section covering setup, the API, and tests.",
            "artifacts": [
                {"name": "README_feature.md", "type": "doc", "language": "markdown", "content": content}
            ],
        }

    def _generic(self, title: str, user: str) -> dict:
        return {
            "summary": f"Processed: {title}",
            "details": f"Mock output for: {title}",
            "artifacts": [],
        }

    def _committer(self, title: str, user: str) -> dict:
        # Derive the feature from the "Feature:" line if present.
        feature = title
        files: list[str] = []
        for line in user.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("feature:"):
                feature = stripped.split(":", 1)[1].strip() or title
            elif stripped.startswith("- "):
                files.append(stripped[2:].strip())
        subject = f"feat: {feature}"[:72]
        listing = "\n".join(f"- `{f}`" for f in files) or "- (generated files)"
        body = (
            "Implements the requested change.\n\n"
            f"Files:\n{listing}\n\n"
            "Authored by the SDLC Agentic AI committer."
        )
        return {
            "subject": subject,
            "body": body,
            "pr_title": subject,
            "pr_body": f"## {feature}\n\nAutomated change from the SDLC pipeline.\n\n{listing}",
        }

