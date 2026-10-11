"""Unit tests for runtime configuration loading.

Covers:
- FR-011: Infisical environment variables runtime injection.
"""

from src.api.config import get_settings


def test_fr_011_settings_loads_from_environment(monkeypatch):
    """FR-011: Verify settings reads runtime environment variables injected via Infisical."""
    monkeypatch.setenv("BHASHINI_USER_ID", "test_user_123")
    monkeypatch.setenv("BHASHINI_API_KEY", "test_key_456")
    monkeypatch.setenv("WHATSAPP_TOKEN", "test_wa_token_789")

    settings = get_settings()
    assert settings.bhashini_user_id == "test_user_123"
    assert settings.bhashini_api_key == "test_key_456"
    assert settings.whatsapp_token == "test_wa_token_789"
