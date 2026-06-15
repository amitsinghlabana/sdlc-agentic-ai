"""Tests for LLM provider wiring: TLS helper, provider construction, endpoints.

All offline/free — no real Azure/OpenAI calls. Provider construction is exercised
with dummy settings (no network happens until ``complete`` is awaited), which
validates the custom ``http_client`` / TLS wiring added for corporate networks.
"""
from __future__ import annotations

import ssl
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.llm import factory
from app.main import app
from app.net import build_ssl_verify

client = TestClient(app)


# --------------------------------------------------------------------------- #
# TLS helper
# --------------------------------------------------------------------------- #
def test_build_ssl_verify_disabled_returns_false():
    assert build_ssl_verify("", False) is False


def test_build_ssl_verify_custom_bundle_returns_path():
    assert build_ssl_verify("C:/certs/corp.pem", True) == "C:/certs/corp.pem"


def test_build_ssl_verify_default_uses_truststore_context():
    verify = build_ssl_verify("", True)
    # truststore is installed → we get an SSLContext (OS trust store).
    assert isinstance(verify, ssl.SSLContext)


# --------------------------------------------------------------------------- #
# Provider construction (no network until complete() is awaited)
# --------------------------------------------------------------------------- #
def _azure_settings(**overrides):
    base = dict(
        azure_openai_api_key="dummy-key",
        azure_openai_api_version="2024-08-01-preview",
        azure_openai_endpoint="https://example.openai.azure.com/",
        azure_openai_deployment="gpt-4o-mini",
        request_timeout=30.0,
        llm_connect_timeout=15.0,
        llm_max_retries=1,
        llm_http_keepalive=False,
        llm_ca_bundle="",
        llm_verify_ssl=True,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_azure_provider_constructs_with_custom_http_client():
    from app.llm.azure_openai import AzureOpenAIProvider

    provider = AzureOpenAIProvider(_azure_settings())
    assert provider.name == "azure"
    assert "gpt-4o-mini" in provider.label


def test_openai_provider_constructs_with_custom_http_client():
    from app.llm.openai_provider import OpenAIProvider

    s = SimpleNamespace(
        openai_api_key="dummy",
        openai_model="gpt-4o-mini",
        request_timeout=30.0,
        llm_connect_timeout=15.0,
        llm_max_retries=1,
        llm_http_keepalive=False,
        llm_ca_bundle="",
        llm_verify_ssl=True,
    )
    provider = OpenAIProvider(s)
    assert provider.name == "openai"
    assert "gpt-4o-mini" in provider.label


# --------------------------------------------------------------------------- #
# Factory selection
# --------------------------------------------------------------------------- #
def test_factory_selects_azure_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "azure")
    monkeypatch.setattr(settings, "azure_openai_endpoint", "https://example.openai.azure.com/")
    monkeypatch.setattr(settings, "azure_openai_api_key", "dummy-key")
    factory.reset_llm()
    try:
        provider = factory.get_llm()
        assert provider.name == "azure"
    finally:
        factory.reset_llm()


def test_factory_falls_back_to_mock_when_azure_unconfigured(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "azure")
    monkeypatch.setattr(settings, "azure_openai_endpoint", "")
    monkeypatch.setattr(settings, "azure_openai_api_key", "")
    factory.reset_llm()
    try:
        assert factory.get_llm().name == "mock"
    finally:
        factory.reset_llm()


# --------------------------------------------------------------------------- #
# Endpoints (mock provider — deterministic, free)
# --------------------------------------------------------------------------- #
def test_llm_test_endpoint_ok_with_mock():
    factory.reset_llm()  # default provider is mock
    data = client.get("/api/llm/test").json()
    assert data["ok"] is True
    assert data["provider"] == "mock"


def test_config_endpoint_reports_provider():
    factory.reset_llm()
    data = client.get("/api/config").json()
    assert "provider" in data and "is_mock" in data

