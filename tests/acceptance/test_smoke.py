"""Acceptance smoke test ensuring application boots and core routes respond."""

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.app import app


@pytest.mark.asyncio
async def test_baseline_application_smoke():
    """Smoke test verifying application startup and endpoint availability."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
