# Learning Agents

A growing collection of hands-on projects for learning how AI agents are designed, built, and improved over time.

## Current Progress

✅ **Project 001: WeatherReporter**
- A robust weather retrieval agent using **wttr.in** and **OpenWeather API** as a fallback.
- Focused on: Tool use, fallback reliability, and user-facing responses.

✅ **Project 010: MailMan**
- An autonomous email management agent for monitoring and archiving Gmail messages.
- Focused on: **Gmail API integration**, local archiving, and complex MIME/HTML payload parsing.

✅ **Project 011: EventHandler**
- An intelligent scheduling agent for managing Google Calendar events across timezones.
- Focused on: **Google Calendar API**, dynamic "today" context, Pydantic-based data validation, and anti-hallucination guardrails.

## Repository Structure

- `ag_001_WeatherReporter/` — Weather retrieval with API fallbacks.
- `ag_010_MailMan/` — Gmail monitoring, parsing, and local archiving.
- `ag_011_Event_Handler/` — Autonomous scheduling and timezone-aware event management.

## Why this repository exists

This repository is focused on incremental, project-by-project learning:
- **Build real agents end-to-end**: Moving from simple information retrieval to real-world action (Email/Calendar).
- **Understand tool-calling workflows**: Building custom ReAct loops without heavy frameworks.
- **Improve reliability**: Using Pydantic and strict system prompts to maintain agent stability.
- **Manage Real-World APIs**: Navigating OAuth 2.0, token management, and complex JSON data structures.

## Next Direction

Additional agent projects will continue to focus on distinct capabilities:
- **Project Coordination**: Enabling multiple agents (like MailMan and EventHandler) to collaborate on a single task.
- **Persistent Memory**: Moving from flat-file storage to structured databases for agent long-term memory.
- **Human-in-the-Loop**: Refining how agents ask for clarification when user intent is ambiguous.
