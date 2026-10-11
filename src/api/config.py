"""Application configuration and settings loader.

Reads runtime environment variables injected via Infisical.
"""

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    """Runtime application settings for Bhashini Multilingual Bot."""

    bhashini_user_id: str = field(default_factory=lambda: os.getenv("BHASHINI_USER_ID", ""))
    bhashini_api_key: str = field(default_factory=lambda: os.getenv("BHASHINI_API_KEY", ""))
    bhashini_pipeline_id: str = field(
        default_factory=lambda: os.getenv("BHASHINI_PIPELINE_ID", "64392f96daac500b55c543d6")
    )
    whatsapp_token: str = field(default_factory=lambda: os.getenv("WHATSAPP_TOKEN", ""))
    whatsapp_phone_number_id: str = field(
        default_factory=lambda: os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    )
    whatsapp_verify_token: str = field(
        default_factory=lambda: os.getenv("WHATSAPP_VERIFY_TOKEN", "bhashini_verify_token_secure")
    )
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))


def get_settings() -> Settings:
    """Return a fresh Settings instance reading active runtime environment."""
    return Settings()
