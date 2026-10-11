"""Pure domain models and formatting for weather forecasts."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GeoCoordinates:
    """Geographic coordinate pair."""

    latitude: float
    longitude: float


@dataclass(frozen=True)
class DailyForecast:
    """Forecast for a single day."""

    date: str
    max_temperature_c: float
    min_temperature_c: float
    condition: str


@dataclass(frozen=True)
class WeatherReport:
    """Aggregated weather report for a location."""

    location_name: str
    current_temperature_c: float
    condition: str
    forecasts: list[DailyForecast] = field(default_factory=list)

    def to_readable_summary(self) -> str:
        lines = [
            f"Weather for {self.location_name}: "
            f"Today: {self.condition}, {self.current_temperature_c:.0f}°C."
        ]
        for f in self.forecasts[:2]:
            lines.append(
                f"{f.date}: {f.condition}, "
                f"{f.min_temperature_c:.0f}°C - {f.max_temperature_c:.0f}°C."
            )
        return " ".join(lines)
