# Project 001 — Agent from Scratch (Weather Agent)

This project contains the **first completed agent** in this repository: a weather-focused assistant that can fetch and present live weather data in a clean, user-friendly way.

## What this agent does

- Accepts a user weather query
- Uses a tool function to retrieve weather data
- Pulls weather from **wttr.in** as the primary source
- Falls back to **OpenWeather API** when wttr.in is unavailable
- Returns a curated assistant response based on tool output

## Core behavior implemented

- **Auto-location support:** if no city is provided, the system attempts city detection using IP (`ipapi.co`)
- **Resilience via fallback:** automatic fallback from wttr.in to OpenWeather
- **Structured tool schema:** tool-call arguments validated with Pydantic
- **Agent loop with tool-calls:** model can decide when to call tools and continue with tool outputs in memory

## Project Files

- `agent.py` — main agent logic, tool definition, weather fetch flow, and execution loop
- `wttr_weather_test.py` — quick script to inspect wttr.in weather payload shape
- `open_weather_test.py` — quick API key and endpoint validation for OpenWeather
- `pyproject.toml` — project metadata and dependencies

## Requirements

- Python **3.12+**
- Environment variables in `.env`:
  - `HF_TOKEN` (for Hugging Face Inference Client)
  - `OpenWeather_API_KEY` (used for weather fallback)

## Setup

1. Create and activate a Python environment.
2. Install dependencies from `pyproject.toml`.
3. Add required environment variables in a `.env` file.
4. Run the main script:

```bash
python agent.py
```

## Data Sources Used

- Primary: `https://wttr.in/{city}?format=j1`
- Fallback: `https://api.openweathermap.org/data/2.5/weather`

## Learning Outcome

This first project demonstrates a practical baseline for building reliable AI agents: combine model reasoning with deterministic tools, and design for graceful failure recovery.
