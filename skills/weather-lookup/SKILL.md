---
name: weather-lookup
description: Retrieve current weather conditions for a specific city. Use when the user asks for weather updates, temperature, or current conditions.
---

# Weather Lookup Skill

This skill allows you to fetch real-time weather information for any city using the `wttr.in` service.

## Tools

### weather.py

A Python script that fetches current weather data and returns it in JSON format.

**Location:** `skills/weather-lookup/weather.py`

**Usage:**

To get the weather for a city, run the script via shell command:

```bash
python skills/weather-lookup/weather.py "City Name"
```

**Example:**

```bash
python skills/weather-lookup/weather.py "Beijing"
```

**Output Format:**

The script returns a JSON object with the following fields:

- `city`: The requested city name
- `temperature_C`: Current temperature in Celsius
- `weather_desc`: Text description of the weather (e.g., "Partly cloudy")
- `humidity`: Humidity percentage
- `wind_speed_kmph`: Wind speed in km/h
- `observation_time`: Time of observation

**Error Handling:**

If the city is not found or the service is unavailable, the script will return a JSON object with an `error` field.
