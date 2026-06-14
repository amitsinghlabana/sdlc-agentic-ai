"""Application configuration.

All settings are read from environment variables (optionally via a local
``.env`` file). The defaults are tuned for **free local testing**: the LLM
provider defaults to ``mock`` so the whole pipeline runs end-to-end without an
Azure account or spending a single token.

Flip ``LLM_PROVIDER=azure`` (and set the Azure vars) when you want real model
output for the demo.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Repo root: …/sdlc-agent  (this file is backend/app/config.py)
_ROOT = Path(__file__).resolve().parent.parent.parent

# 1) Non-secret config + placeholders (safe to commit/attach).
load_dotenv(_ROOT / ".env")
# 2) Local SECRETS overrides — gitignored, NEVER commit or attach this file.
#    Put real tokens/keys here (JIRA_API_TOKEN, AZURE_OPENAI_API_KEY, …) so they
#    never need to live in .env. Values here win over .env.
load_dotenv(_ROOT / ".env.local", override=True)


def _get_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    """Strongly-typed view over environment configuration."""

    def __init__(self) -> None:
        # Provider selection: "mock" (default, free) | "azure" | "openai"
        self.llm_provider: str = os.getenv("LLM_PROVIDER", "mock").strip().lower()

        # --- Azure OpenAI ---
        self.azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip()
        self.azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "").strip()
        self.azure_openai_api_version: str = os.getenv(
            "AZURE_OPENAI_API_VERSION", "2024-08-01-preview"
        ).strip()
        # The *deployment* name you created in Azure AI Foundry (not the model name).
        self.azure_openai_deployment: str = os.getenv(
            "AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"
        ).strip()

        # --- Vanilla OpenAI (handy fallback for local dev) ---
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
        self.openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

        # --- LLM TLS handling (corporate HTTPS inspection / MITM proxy) ---
        # Azure/OpenAI calls go over HTTPS too, so the same self-signed-CA issue that
        # affects JIRA can break them. By default verify via the OS trust store
        # (truststore). Optionally point at a custom CA bundle, or disable (insecure).
        self.llm_ca_bundle: str = os.getenv("LLM_CA_BUNDLE", "").strip()
        self.llm_verify_ssl: bool = _get_bool("LLM_VERIFY_SSL", True)

        # --- Generation tuning (cost guardrails) ---
        # General cap for text agents (requirements/architect/reviewer/docs).
        self.max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "3000"))
        # Larger cap for code-emitting agents (developer/tester): a multi-file
        # response is big, and truncation would corrupt the JSON → lost files.
        self.code_max_tokens: int = int(os.getenv("LLM_CODE_MAX_TOKENS", "8000"))
        self.temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.4"))
        self.request_timeout: float = float(os.getenv("LLM_TIMEOUT", "90"))

        # --- Orchestration behaviour ---
        self.max_review_loops: int = int(os.getenv("MAX_REVIEW_LOOPS", "2"))
        # Delay (seconds) between streamed text chunks — purely cosmetic so the
        # UI shows a lively "typing" effect. Set to 0 for fastest runs.
        self.stream_delay: float = float(os.getenv("STREAM_DELAY", "0.015"))

        # --- JIRA integration ---
        # Provider selection: "mock" (default, free, offline) | "cloud" (real JIRA Cloud)
        self.jira_provider: str = os.getenv("JIRA_PROVIDER", "mock").strip().lower()
        self.jira_base_url: str = os.getenv("JIRA_BASE_URL", "").strip().rstrip("/")
        self.jira_email: str = os.getenv("JIRA_EMAIL", "").strip()
        self.jira_api_token: str = os.getenv("JIRA_API_TOKEN", "").strip()
        self.jira_project_key: str = os.getenv("JIRA_PROJECT_KEY", "").strip()
        # Instance-specific custom field id for story points (skip if empty).
        self.jira_story_points_field: str = os.getenv("JIRA_STORY_POINTS_FIELD", "").strip()
        # Default assignee for created stories/sub-tasks. Accepts:
        #   ""            -> leave unassigned (default)
        #   "me"/"self"   -> the API-token owner (resolved via /myself)
        #   "<email>"     -> resolved to an accountId via user search
        #   "<accountId>" -> used directly
        self.jira_default_assignee: str = os.getenv("JIRA_DEFAULT_ASSIGNEE", "").strip()
        # Sub-task issue type name (company-managed: "Sub-task"; some team-managed: "Subtask").
        self.jira_subtask_issue_type: str = os.getenv("JIRA_SUBTASK_ISSUE_TYPE", "Sub-task").strip()
        # When true, the cloud client logs what it *would* create without POSTing.
        self.jira_dry_run: bool = _get_bool("JIRA_DRY_RUN", False)
        # TLS handling for corporate networks that do HTTPS inspection (MITM proxy).
        # By default we verify using the OS trust store (via ``truststore``), which
        # picks up the corporate root CA already trusted by Windows. Optionally point
        # at a custom CA bundle (.pem), or — last resort, insecure — disable verify.
        self.jira_ca_bundle: str = os.getenv("JIRA_CA_BUNDLE", "").strip()
        self.jira_verify_ssl: bool = _get_bool("JIRA_VERIFY_SSL", True)

        # --- Knowledge / grounding (Microsoft Foundry IQ) ---
        # Provider selection: "mock" (default, free, offline) | "foundry" (real Foundry IQ)
        self.knowledge_provider: str = os.getenv("KNOWLEDGE_PROVIDER", "mock").strip().lower()
        # How many grounded sources to inject per run.
        self.knowledge_top_k: int = int(os.getenv("KNOWLEDGE_TOP_K", "4"))
        # Local corpus the mock client grounds against (in-repo standards docs).
        self.knowledge_dir: str = os.getenv(
            "KNOWLEDGE_DIR", str(_ROOT / "docs" / "standards")
        ).strip()
        # Foundry IQ / Azure AI Search agentic retrieval (only needed when provider=foundry).
        self.foundry_search_endpoint: str = os.getenv("FOUNDRY_SEARCH_ENDPOINT", "").strip().rstrip("/")
        self.foundry_knowledge_agent: str = os.getenv("FOUNDRY_KNOWLEDGE_AGENT", "").strip()
        self.foundry_index: str = os.getenv("FOUNDRY_INDEX", "").strip()
        self.foundry_api_version: str = os.getenv("FOUNDRY_API_VERSION", "2025-08-01-preview").strip()
        self.foundry_api_key: str = os.getenv("FOUNDRY_API_KEY", "").strip()
        # TLS reuse for the knowledge endpoint (mirrors LLM_*/JIRA_* handling).
        self.knowledge_ca_bundle: str = os.getenv("KNOWLEDGE_CA_BUNDLE", "").strip()
        self.knowledge_verify_ssl: bool = _get_bool("KNOWLEDGE_VERIFY_SSL", True)

        # --- GitHub integration ---
        # Provider selection: "mock" (default, free, offline) | "cloud" (real GitHub REST)
        self.github_provider: str = os.getenv("GITHUB_PROVIDER", "mock").strip().lower()
        self.github_api_url: str = os.getenv("GITHUB_API_URL", "https://api.github.com").strip().rstrip("/")
        self.github_token: str = os.getenv("GITHUB_TOKEN", "").strip()  # secret → .env.local
        # The account/org that owns repos. Optional if GITHUB_REPO includes the owner.
        self.github_owner: str = os.getenv("GITHUB_OWNER", "").strip().strip("/")
        # Optional default repo. Accepts "owner/name" (work on that repo → PR),
        # just "owner" (no default repo → agent creates a new one), or empty.
        self.github_repo: str = os.getenv("GITHUB_REPO", "").strip().strip("/")
        self.github_default_branch: str = os.getenv("GITHUB_DEFAULT_BRANCH", "main").strip()
        # New repos are created private by default; flip to make them public.
        self.github_private: bool = _get_bool("GITHUB_PRIVATE", True)
        # When true, the cloud client logs what it WOULD do without writing.
        self.github_dry_run: bool = _get_bool("GITHUB_DRY_RUN", False)
        # TLS reuse for the GitHub endpoint (mirrors LLM_*/JIRA_* handling).
        self.github_ca_bundle: str = os.getenv("GITHUB_CA_BUNDLE", "").strip()
        self.github_verify_ssl: bool = _get_bool("GITHUB_VERIFY_SSL", True)

    @property
    def azure_configured(self) -> bool:
        return bool(self.azure_openai_endpoint and self.azure_openai_api_key)

    @property
    def openai_configured(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def jira_configured(self) -> bool:
        """True when enough is set to talk to a real JIRA Cloud instance."""
        return bool(
            self.jira_base_url
            and self.jira_email
            and self.jira_api_token
            and self.jira_project_key
        )

    @property
    def knowledge_configured(self) -> bool:
        """True when enough is set to call real Foundry IQ agentic retrieval."""
        return bool(
            self.foundry_search_endpoint
            and self.foundry_knowledge_agent
            and self.foundry_api_key
        )

    @property
    def github_configured(self) -> bool:
        """True when enough is set to talk to real GitHub (token + an owner).

        The owner may come from ``GITHUB_OWNER`` or the owner part of
        ``GITHUB_REPO``. A repo *name* is optional — without one the agent
        creates a new repository.
        """
        owner = self.github_owner or (self.github_repo.split("/", 1)[0] if self.github_repo else "")
        return bool(self.github_token and owner)


settings = Settings()

# Apply persisted runtime overrides (mock↔live switches set via /api/admin).
# Kept import-light to avoid cycles: runtime_config imports no app modules at top.
from .runtime_config import apply_overrides  # noqa: E402

apply_overrides(settings)

