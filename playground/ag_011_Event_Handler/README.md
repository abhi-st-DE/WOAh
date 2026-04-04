# Agent_011_EventHandler

A hands-on project demonstrating a custom-built AI agent capable of autonomously managing schedules, creating events, and navigating timezones using the Google Calendar API.

## Current Progress

✅ **EventHandler Agent completed**: a fully autonomous scheduling agent built from scratch, featuring:
- **Google Calendar API integration** for real-time event creation and management.
- **Dynamic Context Injection**: The agent is aware of "Today" and "Now," allowing it to handle relative dates like "tomorrow" or "next Friday."
- **Robust Timezone Logic**: Fetching user-specific primary timezone settings from Google to ensure 100% accuracy across regions.
- **Pydantic Validation**: A strict data-cleaning layer that converts LLM string hallucinations into valid Python `datetime` objects.
- **Anti-Hallucination Guardrails**: Specialized system prompts and function-level checks to prevent the AI from "guessing" missing information.

This setup demonstrates advanced agent engineering: building a reliable "human-in-the-loop" experience where the agent asks for missing details rather than making mistakes.

## Repository Structure

- **Event_Handler.py** — core agent logic, Pydantic schemas, and the tool-calling execution loop.
- **google_auth.py** — Google API OAuth 2.0 flow specifically configured for Calendar scopes.
- **README.md** — project documentation and progress tracking.

## Why this project exists

This project focuses on the complex "Date & Time" reasoning challenge in AI Agent development:

- **Handle Naive vs. Aware Datetimes**: Managing the transition between human-readable strings and ISO 8601 timestamps.
- **Implement Tool-Level Validation**: Using Pydantic to ensure the LLM provides valid arguments before an API call is made.
- **Contextual Reasoning**: Teaching an LLM to perform date math (e.g., "add 1 hour if end time is missing") using only system instructions.
- **Stateful Interaction**: Maintaining a conversation where the agent can prompt the user for specific missing fields (Name/Date).

## Next Direction

Future enhancements for this project will focus on coordination and conflict resolution:

- **Conflict Detection**: A new tool to check for existing events before scheduling a new one.
- **Natural Language "Vague" Queries**: Improving the agent's ability to handle "Set a meeting sometime Tuesday afternoon."
- **Multi-Calendar Support**: Allowing the agent to coordinate across personal, work, and shared family calendars.
- **Batch Operations**: Deleting or moving multiple events in a single interaction.
