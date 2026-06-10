# Local-Forge: AI Agents

A growing collection of hands-on projects for learning how AI agents are designed, built, and improved over time, now featuring a unified web interface for running all agents.

## 🚀 Unified Agent Server (Web UI)

We have introduced a **Unified Agent Server** (`web_app.py` & `index.html`) that allows you to interact with all the agents from a clean, modern browser interface.
- Serves as a single entry point for all projects.
- Live streaming of agent "Thinking" and "Final Results".
- Built-in support for MCP documentation lookups directly from the UI.

## 🤖 Current Agents

✅ **Project 001: WeatherReporter** (`ag_001_WeatherReporter`)
- A robust weather retrieval agent using **wttr.in** and **OpenWeather API** as a fallback.
- Focused on: Tool use, fallback reliability, and user-facing responses.

✅ **Project 010: MailMan** (`ag_010_MailMan`)
- An autonomous email management agent for monitoring and archiving Gmail messages.
- Focused on: **Gmail API integration**, local archiving, and complex MIME/HTML payload parsing.

✅ **Project 011: EventHandler** (`ag_011_Event_Handler`)
- An intelligent scheduling agent for managing Google Calendar events across timezones.
- Focused on: **Google Calendar API**, dynamic "today" context, Pydantic-based data validation, and anti-hallucination guardrails.

✅ **Project 100: DeepResearcher** (`ag_100_DeepResearcher`)
- An advanced web research agent leveraging **Firecrawl** and **Groq (Llama-3.3-70b-versatile)**.
- Focused on: Performing deep internet searches, directly scraping web results into Markdown, and reasoning over current web data.

✅ **Project 101: PdfAuditor** (`ag_101_PdfAuditor`)
- A secure document processing agent using **Chunkr API** and **Groq**.
- Focused on: Extracting text from PDFs and other documents (up to 20MB), async document parsing, strict token/iteration limits, and bounded execution for auditing local files.

## 🔌 MCP Integration

✅ **Model Context Protocol (MCP)** (`mcp/`)
- A directory containing multiple MCP server implementations:
  - **Documentation Server**: Powered by **Google Serper API** and **BeautifulSoup** to dynamically retrieve up-to-date documentation for multiple frameworks and languages (e.g., Python, React, LangChain, etc.).
  - **Webcrawl & Database Servers**: Exploring advanced MCP implementations for crawling content and interfacing with databases.

## 📂 Repository Structure

- `web_app.py` & `index.html` — The Unified Agent Web UI and Server.
- `ag_001_WeatherReporter/` — Weather retrieval with API fallbacks.
- `ag_010_MailMan/` — Gmail monitoring, parsing, and local archiving.
- `ag_011_Event_Handler/` — Autonomous scheduling and timezone-aware event management.
- `ag_100_DeepResearcher/` — Deep web search and markdown scraping via Firecrawl.
- `ag_101_PdfAuditor/` — Safe local document extraction and auditing via Chunkr.
- `mcp/` — Model Context Protocol servers (documentation, webcrawl, database).

## 🧠 Why this repository exists

This repository is focused on incremental, project-by-project learning:
- **Build real agents end-to-end**: Moving from simple information retrieval to real-world action (Email/Calendar/Web Search/Docs).
- **Understand tool-calling workflows**: Building custom ReAct loops without heavy frameworks.
- **Improve reliability**: Using Pydantic, strict system prompts, and hard limits to maintain agent stability.
- **Manage Real-World APIs**: Navigating OAuth 2.0, token management, Firecrawl, Chunkr, Serper, and complex JSON data structures.

## 🔮 Next Direction

Additional agent projects will continue to focus on distinct capabilities:
- **Project Coordination**: Enabling multiple agents (like MailMan and EventHandler) to collaborate on a single task.
- **Persistent Memory**: Moving from flat-file storage to structured databases for agent long-term memory.
- **Human-in-the-Loop**: Refining how agents ask for clarification when user intent is ambiguous.
