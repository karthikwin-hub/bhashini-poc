"""Acceptance tests for User Story 4: Multilingual Weather Advisory (Weather).

Covers:
- FR-008: Weather forecast based on GPS location or text city/town.
- US4-AS1: WhatsApp GPS location message yields translated weather forecast for current & next day.
- US4-AS2: Text city name yields geocoded translated weather forecast for current & next day.
- US4-AS3: Unrecognized location prompts for clarification.
"""

from unittest.mock import AsyncMock

import pytest
from src.adapters.bhashini.client import BhashiniPipelineClient
from src.adapters.weather.client import OpenMeteoClient
from src.domain.session import SessionState, UserSessionManager


@pytest.mark.asyncio
async def test_us4_as1_weather_via_gps_location():
    """US4-AS1: Given user in Weather mode with languages [Hindi, Bengali],
    when WhatsApp location pin (lat, lon) is sent, then 2-day forecast is returned in
    both languages.
    """
    mock_weather = AsyncMock(spec=OpenMeteoClient)
    mock_weather.get_forecast_by_coords.return_value = (
        "Weather for Goa: Today: Sunny, 32°C. Tomorrow: Light showers, 29°C."
    )
    mock_bhashini = AsyncMock(spec=BhashiniPipelineClient)
    mock_bhashini.translate_text.side_effect = lambda text, src, target: (
        f"[Hindi Weather: {text}]" if target == "hi" else f"[Bengali Weather: {text}]"
    )

    manager = UserSessionManager(weather_client=mock_weather, bhashini_client=mock_bhashini)
    phone = "919876543240"
    session = manager.get_or_create_session(phone)
    session.state = SessionState.AWAITING_WEATHER_LOCATION
    session.selected_languages = ["hi", "bn"]

    results = await manager.process_weather_location(
        phone=phone,
        latitude=15.4909,
        longitude=73.8278,
    )

    assert len(results) == 2
    assert any("[Hindi Weather:" in r for r in results)
    assert any("[Bengali Weather:" in r for r in results)


@pytest.mark.asyncio
async def test_us4_as2_weather_via_text_city():
    """US4-AS2: Given user in Weather mode with languages [Hindi, Telugu],
    when city name 'Hyderabad' is provided, then forecast is geocoded and delivered in
    both languages.
    """
    mock_weather = AsyncMock(spec=OpenMeteoClient)
    mock_weather.get_forecast_by_city.return_value = (
        "Weather for Hyderabad: Today: Clear, 30°C. Tomorrow: Partly cloudy, 31°C."
    )
    mock_bhashini = AsyncMock(spec=BhashiniPipelineClient)
    mock_bhashini.translate_text.side_effect = lambda text, src, target: (
        f"[Hindi: {text}]" if target == "hi" else f"[Telugu: {text}]"
    )

    manager = UserSessionManager(weather_client=mock_weather, bhashini_client=mock_bhashini)
    phone = "919876543241"
    session = manager.get_or_create_session(phone)
    session.state = SessionState.AWAITING_WEATHER_LOCATION
    session.selected_languages = ["hi", "te"]

    results = await manager.process_weather_location(
        phone=phone,
        location_text="Hyderabad",
    )

    assert len(results) == 2
    assert any("[Hindi:" in r for r in results)
    assert any("[Telugu:" in r for r in results)


@pytest.mark.asyncio
async def test_us4_as3_weather_unrecognized_location():
    """US4-AS3: Given user in Weather mode, when unrecognizable location is provided,

    then system prompts for a valid city or GPS location without crashing.
    """
    mock_weather = AsyncMock(spec=OpenMeteoClient)
    mock_weather.get_forecast_by_city.side_effect = ValueError("Location not found")

    manager = UserSessionManager(weather_client=mock_weather)
    phone = "919876543242"
    session = manager.get_or_create_session(phone)
    session.state = SessionState.AWAITING_WEATHER_LOCATION
    session.selected_languages = ["hi"]

    results = await manager.process_weather_location(
        phone=phone,
        location_text="NonExistentPlaceXYZ123",
    )

    assert len(results) == 1
    assert (
        "not found" in results[0].lower() or "शहर" in results[0] or "location" in results[0].lower()
    )
