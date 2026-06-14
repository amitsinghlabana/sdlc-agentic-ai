"""Tests for the 'edit an existing repo' capability (context loading + editing).

Offline/free: uses the mock GitHub client's seeded fake codebase and the mock
LLM, so the whole edit→branch→PR flow is verified without a network.
"""
from __future__ import annotations

import asyncio

from app.config import settings
from app.integrations.github.mock import MockGitHubClient
from app.llm.mock import MockProvider
from app.models import WorkPackage, infer_artifact
from app.orchestrator import run_pipeline


# --------------------------------------------------------------------------- #
# infer_artifact — extension → type/language
# --------------------------------------------------------------------------- #
def test_infer_artifact_python_is_code():
    a = infer_artifact("app/main.py", "x = 1")
    assert a.type == "code" and a.language == "python"


def test_infer_artifact_detects_tests():
    assert infer_artifact("tests/test_x.py").type == "test"
    assert infer_artifact("src/foo.test.ts").type == "test"
    assert infer_artifact("pkg/__tests__/a.js").type == "test"


def test_infer_artifact_config_and_docs():
    assert infer_artifact("pkg.json", "{}").type == "config"
    assert infer_artifact("README.md", "# hi").type == "doc"
    assert infer_artifact("config.yaml", "a: 1").language == "yaml"


# --------------------------------------------------------------------------- #
# WorkPackage context overlay
# --------------------------------------------------------------------------- #
def test_context_files_appear_in_code_block():
    wp = WorkPackage("Add logout")
    wp.add_context_file(infer_artifact("app/auth.py", "def login(): ..."))
    assert wp.has_context
    assert "app/auth.py" in wp.code_block()


def test_produced_artifact_overrides_context_same_path():
    wp = WorkPackage("Edit auth")
    wp.add_context_file(infer_artifact("app/auth.py", "OLD"))
    wp.add_artifact(infer_artifact("app/auth.py", "NEW"))
    paths = [a.name for a in wp.code_artifacts()]
    assert paths.count("app/auth.py") == 1  # de-duplicated
    assert "NEW" in wp.code_block() and "OLD" not in wp.code_block()


# --------------------------------------------------------------------------- #
# Mock client: tree + file + capped context
# --------------------------------------------------------------------------- #
def test_mock_get_repo_tree_and_file():
    gh = MockGitHubClient(repo="me/app", exists=True)
    tree = asyncio.run(gh.get_repo_tree("me/app"))
    assert "app/auth.py" in tree
    f = asyncio.run(gh.get_file("me/app", "app/auth.py"))
    assert "login" in f.content


def test_fetch_repo_context_skips_noise_and_caps(monkeypatch):
    gh = MockGitHubClient(repo="me/app", exists=True)
    # Inject noise that must be skipped.
    gh._tree["package-lock.json"] = "{}"
    gh._tree["node_modules/dep/index.js"] = "x"
    gh._tree["logo.png"] = "binarydata"
    files = asyncio.run(gh.fetch_repo_context("me/app", max_files=3))
    paths = [f.path for f in files]
    assert len(files) <= 3
    assert "package-lock.json" not in paths
    assert not any("node_modules" in p for p in paths)
    assert not any(p.endswith(".png") for p in paths)


def test_fetch_repo_context_requires_owner_name():
    gh = MockGitHubClient(repo="me/app", exists=True)
    try:
        asyncio.run(gh.fetch_repo_context("not-a-repo"))
        assert False, "expected RuntimeError"
    except RuntimeError:
        pass


# --------------------------------------------------------------------------- #
# Pipeline seeding: edit mode emits repo_context and feeds the Developer
# --------------------------------------------------------------------------- #
def _collect(seed_files, repo):
    async def go():
        events = []
        async for ev in run_pipeline("Add a logout endpoint", MockProvider(),
                                     seed_files=seed_files, repo=repo):
            events.append(ev)
        return events
    return asyncio.run(go())


def test_pipeline_emits_repo_context_event():
    gh = MockGitHubClient(repo="me/app", exists=True)
    seed = asyncio.run(gh.fetch_repo_context("me/app"))
    events = _collect(seed, "me/app")
    ctx = [e for e in events if e["type"] == "repo_context"]
    assert ctx and ctx[0]["repo"] == "me/app"
    assert ctx[0]["count"] >= 1


def test_pipeline_without_seed_has_no_repo_context():
    events = _collect(None, None)
    assert not [e for e in events if e["type"] == "repo_context"]

