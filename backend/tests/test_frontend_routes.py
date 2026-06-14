"""Tests for static frontend routing — works for either UI mode.

The backend serves the built React app (``web/dist``) when present, else the
zero-build ``frontend/`` (landing at /, app at /app). These tests assert the
invariants that hold in BOTH modes so they stay green regardless of build state.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _is_html(text: str) -> bool:
    low = text.lower()
    return "<!doctype html" in low or "<html" in low


def test_root_serves_an_html_page():
    r = client.get("/")
    assert r.status_code == 200
    assert _is_html(r.text)
    # Loads the SPA bundle (React: /assets/*.js, zero-build: /main.js).
    assert "/assets/" in r.text or "/main.js" in r.text


def test_app_route_serves_an_html_page():
    r = client.get("/app")
    assert r.status_code == 200
    assert _is_html(r.text)


def test_api_routes_take_precedence_over_static():
    # The static mount must never shadow /api/*.
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_unknown_path_falls_back_to_html_shell():
    # Deep links / refreshes on client routes resolve to an HTML shell (no 404).
    r = client.get("/some/client/route")
    assert r.status_code == 200
    assert _is_html(r.text)


def test_missing_api_endpoint_still_404s():
    # SPA fallback must NOT swallow unknown /api/* routes.
    r = client.get("/api/definitely-not-a-route")
    assert r.status_code == 404


