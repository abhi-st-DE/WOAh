# World Of AGENTIC Hub (WOAh) :>>

Welcome to the central command for developing, testing, and scaling autonomous AI agents. This repository is dedicated to exploring the frontier of agentic workflows—moving beyond simple chat and into real-world action.

## 🤖 The Agents

### [001] WeatherReporter
The first experiment in tool-calling. A robust agent that navigates multiple meteorological APIs to provide real-time, logic-backed weather reports.
*   **Key Skill**: API Fallback Reliability.

### [010] MailMan
An autonomous communications manager. Capable of securely logging into Gmail, parsing complex thread data, and maintaining a local archive of your digital life.
*   **Key Skill**: Large Payload Parsing & State Persistence.

### [011] EventHandler
The scheduling master. An agent that understands time, navigates timezones, and manages meetings directly on your Google Calendar without supervision.
*   **Key Skill**: Temporal Reasoning & Pydantic-based Data Validation.

---

## 🏗️ Technical Architecture
Every agent built in this hub follows a "Framework-Free" philosophy:
- **Modular Design**: Each agent lives in its own ecosystem with dedicated auth and logic.
- **Strict Validation**: Using Pydantic to ensure the bridge between AI reasoning and API execution is unbreakable.
- **Persistent Memory**: Storing history and IDs locally to prevent redundant work.
- **Dynamic Context**: Using real-time system prompts to give agents an awareness of "Now."

## 📂 Organization
All development and experimental agents are located in the [/playground](./playground) directory, where they are built and refined day-by-day.

---
**Building the future of automation, one agent at a time.**
