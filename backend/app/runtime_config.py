"""Runtime provider overrides — switch mock↔live WITHOUT code changes or restart.

Provider selection normally comes from env vars (``.env``), read once at startup.
This module adds a thin, **persistent override layer** on top: a small JSON file
(gitignored) whose values win over the env vars. Change it via the ``/api/admin``
endpoints and the matching factory singleton is rebuilt immediately — no commit,
no push, no restart.

Why a JSON file (not a DB)? Zero infra, matches the project's simple philosophy,
and survives restarts. To use a database instead, swap ``_read``/``_write`` for
your store (e.g. a single ``settings`` row) — nothing else changes.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger("sdlc.runtime")

# Only these settings may be overridden at runtime, with their allowed values.
ALLOWED: dict[str, set[str]] = {
    "llm_provider": {"mock", "azure", "openai"},
    "jira_provider": {"mock", "cloud"},
    "knowledge_provider": {"mock", "foundry"},
    "github_provider": {"mock", "cloud"},
}

_ROOT = Path(__file__).resolve().parent.parent.parent
# Overridable path so tests (and prod) can point elsewhere.
CONFIG_PATH = Path(os.getenv("RUNTIME_CONFIG_PATH", str(_ROOT / "runtime-config.json")))


# --- storage backend (swap these two for a DB if ever needed) -------------- #
def _read() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except Exception:  # noqa: BLE001 — a corrupt file must never crash startup
        logger.warning("runtime-config unreadable (%s); ignoring.", CONFIG_PATH, exc_info=True)
        return {}


def _write(data: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


# --- public API ------------------------------------------------------------ #
def load() -> dict:
    """Return persisted overrides, filtered to the allowlist."""
    return {k: v for k, v in _read().items() if k in ALLOWED and v in ALLOWED[k]}


def apply_overrides(settings) -> dict:
    """Apply persisted overrides onto ``settings`` (call once at startup).

    Also snapshots the env-derived provider values so ``clear_overrides`` can
    revert exactly, regardless of how env was loaded.
    """
    if not hasattr(settings, "_env_providers"):
        settings._env_providers = {k: getattr(settings, k) for k in ALLOWED}
    overrides = load()
    for key, value in overrides.items():
        setattr(settings, key, value)
    if overrides:
        logger.info("Applied runtime provider overrides: %s", overrides)
    return overrides


def _reset_factory(key: str) -> None:
    """Rebuild the cached singleton affected by a provider key (lazy import)."""
    if key == "llm_provider":
        from .llm.factory import reset_llm
        reset_llm()
    elif key == "jira_provider":
        from .integrations.jira import reset_jira
        reset_jira()
    elif key == "knowledge_provider":
        from .integrations.knowledge import reset_knowledge
        reset_knowledge()
    elif key == "github_provider":
        from .integrations.github import reset_github
        reset_github()


def set_overrides(settings, updates: dict) -> dict:
    """Validate, persist, apply, and hot-reload the affected providers.

    Raises ``ValueError`` on an unknown key or invalid value.
    """
    clean: dict = {}
    for key, value in updates.items():
        if key not in ALLOWED:
            raise ValueError(f"Unknown setting '{key}'.")
        if value not in ALLOWED[key]:
            raise ValueError(
                f"Invalid value '{value}' for '{key}' (allowed: {sorted(ALLOWED[key])})."
            )
        clean[key] = value

    data = {k: v for k, v in _read().items() if k in ALLOWED}
    data.update(clean)
    _write(data)

    for key, value in clean.items():
        setattr(settings, key, value)
        _reset_factory(key)
    logger.info("Runtime provider overrides updated: %s", clean)
    return clean


def clear_overrides(settings) -> None:
    """Delete the overrides file and revert ``settings`` to env-derived values."""
    try:
        CONFIG_PATH.unlink()
    except FileNotFoundError:
        pass
    for key, value in getattr(settings, "_env_providers", {}).items():
        setattr(settings, key, value)
        _reset_factory(key)
    logger.info("Runtime provider overrides cleared (reverted to env values).")

