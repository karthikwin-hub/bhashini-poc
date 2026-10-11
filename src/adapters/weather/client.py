"""Open-Meteo weather client for GPS and geocoded city forecasts."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO Weather interpretation codes
WMO_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class OpenMeteoClient:
    """Client for Open-Meteo weather and geocoding services."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=15.0)
        return self._client

    async def get_coordinates_for_city(self, city_name: str) -> tuple[float, float, str]:
        """Geocode city name to (latitude, longitude, display_name)."""
        if not city_name or not city_name.strip():
            raise ValueError("City name cannot be blank.")

        client = await self._get_client()
        params = {
            "name": city_name.strip(),
            "count": 1,
            "language": "en",
            "format": "json",
        }

        resp = await client.get(GEOCODING_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results")
        if not results:
            raise ValueError(f"Location not found: {city_name}")

        match = results[0]
        lat = float(match["latitude"])
        lon = float(match["longitude"])
        name = match.get("name", city_name)
        country = match.get("country", "")
        display = f"{name}, {country}" if country else name
        return lat, lon, display

    async def get_forecast_by_coords(
        self, lat: float, lon: float, location_name: str = "your area"
    ) -> str:
        """Fetch current and 2-day weather forecast by latitude and longitude."""
        client = await self._get_client()
        params: dict[str, Any] = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,weather_code",
            "timezone": "auto",
        }

        resp = await client.get(FORECAST_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

        current = data.get("current", {})
        curr_temp = current.get("temperature_2m", 25)
        curr_code = current.get("weather_code", 0)
        curr_cond = WMO_CODE_MAP.get(curr_code, "Pleasant")

        daily = data.get("daily", {})
        max_temps = daily.get("temperature_2m_max", [curr_temp, curr_temp])
        min_temps = daily.get("temperature_2m_min", [curr_temp - 5, curr_temp - 5])
        codes = daily.get("weather_code", [curr_code, curr_code])

        today_cond = WMO_CODE_MAP.get(codes[0] if codes else 0, curr_cond)
        tom_cond = WMO_CODE_MAP.get(codes[1] if len(codes) > 1 else 0, "Partly cloudy")
        tom_max = max_temps[1] if len(max_temps) > 1 else curr_temp
        tom_min = min_temps[1] if len(min_temps) > 1 else curr_temp - 5

        return (
            f"Weather for {location_name}: Today: {today_cond}, {curr_temp:.0f}°C. "
            f"Tomorrow: {tom_cond}, {tom_min:.0f}°C - {tom_max:.0f}°C."
        )

    async def get_forecast_by_city(self, city_name: str) -> str:
        """Geocode city and fetch current and 2-day weather forecast."""
        lat, lon, display = await self.get_coordinates_for_city(city_name)
        return await self.get_forecast_by_coords(lat, lon, location_name=display)
