from __future__ import annotations

from typing import Any, Dict

import httpx


class WeatherTool:
    """Open-Meteo API tool for current weather (no API key required)."""

    _GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
    _FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

    _WEATHER_CODES = {
        0: "clear sky",
        1: "mainly clear",
        2: "partly cloudy",
        3: "overcast",
        45: "fog",
        48: "depositing rime fog",
        51: "light drizzle",
        53: "moderate drizzle",
        55: "dense drizzle",
        61: "slight rain",
        63: "moderate rain",
        65: "heavy rain",
        71: "slight snow",
        73: "moderate snow",
        75: "heavy snow",
        80: "rain showers",
        95: "thunderstorm",
    }

    def current_weather(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        city = payload.get("city")
        if not city:
            raise ValueError("city is required for weather_current")

        with httpx.Client(timeout=10) as client:
            geo_resp = client.get(self._GEOCODE_URL, params={"name": city, "count": 1})
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()
            results = geo_data.get("results") or []
            if not results:
                raise ValueError(f"No location found for city '{city}'")
            location = results[0]

            forecast_resp = client.get(
                self._FORECAST_URL,
                params={
                    "latitude": location["latitude"],
                    "longitude": location["longitude"],
                    "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code",
                },
            )
            forecast_resp.raise_for_status()
            data = forecast_resp.json()

        current = data.get("current", {})
        code = current.get("weather_code")
        return {
            "city": location.get("name"),
            "country": location.get("country"),
            "temperature": current.get("temperature_2m"),
            "feels_like": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "conditions": self._WEATHER_CODES.get(code, "unknown"),
            "weather_code": code,
        }
