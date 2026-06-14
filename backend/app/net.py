"""Shared TLS verification helper for outbound HTTPS.

Corporate networks/antivirus often intercept HTTPS with a *self-signed* root CA.
Python's default bundle (certifi) doesn't trust it → ``CERTIFICATE_VERIFY_FAILED``,
even though the OS (Windows) trust store does. This helper returns the right
``verify`` value for an ``httpx`` client / SSL context. Used by both the JIRA
cloud client and the Azure/OpenAI LLM providers.

Resolution order:
1. ``verify_ssl=False``  → disable verification (INSECURE; last resort).
2. ``ca_bundle=<path>``  → verify against a custom CA bundle (.pem).
3. default               → use the OS trust store via ``truststore`` (picks up the
   corporate root CA automatically); falls back to certifi if unavailable.
"""
from __future__ import annotations

import logging
import ssl

logger = logging.getLogger("sdlc.net")


def build_ssl_verify(ca_bundle: str = "", verify_ssl: bool = True):
    """Return an httpx ``verify`` value: ``False`` | path str | SSLContext | ``True``."""
    if not verify_ssl:
        logger.warning(
            "TLS certificate verification is DISABLED (verify_ssl=false). "
            "Use only on a trusted network; prefer a CA bundle instead."
        )
        return False

    if ca_bundle:
        logger.info("Using custom CA bundle for TLS: %s", ca_bundle)
        return ca_bundle

    try:
        import truststore  # uses the OS (Windows) trust store

        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except Exception:  # noqa: BLE001 — truststore is optional
        logger.debug("truststore unavailable; using httpx default CA bundle.", exc_info=True)
        return True

