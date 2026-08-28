from typing import Any
import asyncio
import httpx
import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "mcp-client", ".env"))

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
port = int(os.getenv("PORT", 8085))
mcp = FastMCP("weather", host="0.0.0.0", port=port)

# Constants
WEATHERAPI_BASE = "https://api.weatherapi.com/v1"
USER_AGENT = "weather-app/1.0"

# Get API key from environment variable
API_KEY = os.getenv("WEATHERAPI_KEY")

# Mock data fallback for offline / test mode when WEATHERAPI_KEY is not configured
MOCK_WEATHER_DATA = {
    "hanoi": {
        "location": {"name": "Hanoi", "region": "Ha Noi", "country": "Vietnam"},
        "current": {
            "temp_c": 29.0, "temp_f": 84.2, "feelslike_c": 32.5, "feelslike_f": 90.5,
            "condition": {"text": "Partly cloudy"}, "humidity": 78,
            "wind_kph": 14.4, "wind_mph": 8.9, "wind_dir": "SE", "pressure_mb": 1008.0,
            "uv": 6.0, "vis_km": 10.0, "last_updated": "2026-08-28 17:00"
        }
    },
    "danang": {
        "location": {"name": "Danang", "region": "Da Nang", "country": "Vietnam"},
        "current": {
            "temp_c": 31.0, "temp_f": 87.8, "feelslike_c": 35.0, "feelslike_f": 95.0,
            "condition": {"text": "Sunny"}, "humidity": 70,
            "wind_kph": 11.2, "wind_mph": 7.0, "wind_dir": "E", "pressure_mb": 1010.0,
            "uv": 8.0, "vis_km": 10.0, "last_updated": "2026-08-28 17:00"
        }
    },
    "tokyo": {
        "location": {"name": "Tokyo", "region": "Tokyo", "country": "Japan"},
        "current": {
            "temp_c": 22.0, "temp_f": 71.6, "feelslike_c": 22.0, "feelslike_f": 71.6,
            "condition": {"text": "Clear"}, "humidity": 55,
            "wind_kph": 9.0, "wind_mph": 5.6, "wind_dir": "N", "pressure_mb": 1015.0,
            "uv": 4.0, "vis_km": 10.0, "last_updated": "2026-08-28 17:00"
        }
    },
    "brisbane": {
        "location": {"name": "Brisbane", "region": "Queensland", "country": "Australia"},
        "current": {
            "temp_c": 24.0, "temp_f": 75.2, "feelslike_c": 24.5, "feelslike_f": 76.1,
            "condition": {"text": "Sunny"}, "humidity": 60,
            "wind_kph": 18.0, "wind_mph": 11.2, "wind_dir": "ENE", "pressure_mb": 1018.0,
            "uv": 7.0, "vis_km": 10.0, "last_updated": "2026-08-28 17:00"
        }
    }
}

async def make_weather_request(endpoint: str, params: dict[str, str]) -> dict[str, Any] | None:
    """Make a request to the WeatherAPI with proper error handling and mock fallback."""
    if not API_KEY:
        city_key = params.get("q", "").lower().strip()
        if city_key in MOCK_WEATHER_DATA:
            base = MOCK_WEATHER_DATA[city_key]
        else:
            base = {
                "location": {"name": params.get("q", "Unknown"), "region": "Region", "country": "World"},
                "current": {
                    "temp_c": 27.0, "temp_f": 80.6, "feelslike_c": 28.0, "feelslike_f": 82.4,
                    "condition": {"text": "Partly cloudy"}, "humidity": 65,
                    "wind_kph": 12.0, "wind_mph": 7.5, "wind_dir": "NE", "pressure_mb": 1012.0,
                    "uv": 5.0, "vis_km": 10.0, "last_updated": "2026-08-28 17:00"
                }
            }
        
        if endpoint == "current.json":
            return base
        elif endpoint == "forecast.json":
            return {
                **base,
                "forecast": {
                    "forecastday": [
                        {
                            "date": "2026-08-29",
                            "day": {
                                "maxtemp_c": base["current"]["temp_c"] + 2,
                                "maxtemp_f": base["current"]["temp_f"] + 4,
                                "mintemp_c": base["current"]["temp_c"] - 4,
                                "mintemp_f": base["current"]["temp_f"] - 7,
                                "condition": {"text": "Sunny with light clouds"},
                                "daily_chance_of_rain": 10,
                                "maxwind_kph": 15.0,
                                "uv": 6.0
                            }
                        },
                        {
                            "date": "2026-08-30",
                            "day": {
                                "maxtemp_c": base["current"]["temp_c"] + 1,
                                "maxtemp_f": base["current"]["temp_f"] + 2,
                                "mintemp_c": base["current"]["temp_c"] - 3,
                                "mintemp_f": base["current"]["temp_f"] - 5,
                                "condition": {"text": "Scattered showers"},
                                "daily_chance_of_rain": 45,
                                "maxwind_kph": 20.0,
                                "uv": 5.0
                            }
                        },
                        {
                            "date": "2026-08-31",
                            "day": {
                                "maxtemp_c": base["current"]["temp_c"] + 3,
                                "maxtemp_f": base["current"]["temp_f"] + 5,
                                "mintemp_c": base["current"]["temp_c"] - 2,
                                "mintemp_f": base["current"]["temp_f"] - 4,
                                "condition": {"text": "Partly cloudy"},
                                "daily_chance_of_rain": 20,
                                "maxwind_kph": 12.0,
                                "uv": 7.0
                            }
                        }
                    ]
                }
            }
        
    headers = {
        "User-Agent": USER_AGENT,
    }
    params["key"] = API_KEY
    url = f"{WEATHERAPI_BASE}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"WeatherAPI request error: {e}")
            return None

@mcp.tool()
async def get_current_weather(city: str) -> str:
    """Get current weather conditions for a city.

    Args:
        city: City name (e.g., "Hanoi", "Haiphong", "Danang", "Brisbane", "Sydney", "Tokyo")
    """
    params = {
        "q": city,
        "aqi": "no"
    }
    
    data = await make_weather_request("current.json", params)

    if not data:
        return f"Unable to fetch current weather data for {city}. Please check the city name."

    current = data["current"]
    location = data["location"]
    
    return f"""
Current Weather for {location['name']}, {location['region']}, {location['country']}:

Temperature: {current['temp_c']}°C ({current['temp_f']}°F)
Feels like: {current['feelslike_c']}°C ({current['feelslike_f']}°F)
Condition: {current['condition']['text']}
Humidity: {current['humidity']}%
Wind: {current['wind_kph']} km/h ({current['wind_mph']} mph) {current['wind_dir']}
Pressure: {current['pressure_mb']} mb
UV Index: {current['uv']}
Visibility: {current['vis_km']} km

Last updated: {current['last_updated']}
"""

@mcp.tool()
async def get_forecast(city: str, days: int = 3) -> str:
    """Get weather forecast for a city.

    Args:
        city: City name (e.g., "Hanoi", "Haiphong", "Danang", "Brisbane", "Sydney", "Melbourne", "Tokyo")
        days: Number of days to forecast (1-3 for free tier, max 10 for paid)
    """
    days = min(days, 3)
    
    params = {
        "q": city,
        "days": str(days),
        "aqi": "no",
        "alerts": "no"
    }
    
    data = await make_weather_request("forecast.json", params)

    if not data or "forecast" not in data:
        return f"Unable to fetch forecast data for {city}. Please check the city name."

    location = data["location"]
    forecast_days = data["forecast"]["forecastday"]
    
    forecasts = []
    forecasts.append(f"Weather Forecast for {location['name']}, {location['region']}, {location['country']}:")
    
    for day in forecast_days[:days]:
        day_data = day["day"]
        date = day["date"]
        
        forecast = f"""
{date}:
High: {day_data['maxtemp_c']}°C ({day_data['maxtemp_f']}°F)
Low: {day_data['mintemp_c']}°C ({day_data['mintemp_f']}°F)
Condition: {day_data['condition']['text']}
Chance of Rain: {day_data['daily_chance_of_rain']}%
Max Wind: {day_data['maxwind_kph']} km/h
UV Index: {day_data['uv']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

@mcp.tool()
async def health_check() -> str:
    """Health check endpoint for deployment verification."""
    return "✅ Weather MCP Server is running! Ready to provide weather data for Australian cities and worldwide."

print("✅ MCP server initialized with Streamable HTTP transport")
print("🔧 Available tools: get_current_weather, get_forecast, health_check")

if __name__ == "__main__":
    import sys
    
    # Default to streamable-http transport unless --stdio is explicitly requested
    if "--stdio" in sys.argv:
        print("Starting FastMCP server in stdio mode for local client", file=sys.stderr)
        mcp.run()
    else:
        print(f"🚀 Starting MCP server on http://0.0.0.0:{port}/mcp")
        mcp.run(transport="streamable-http")