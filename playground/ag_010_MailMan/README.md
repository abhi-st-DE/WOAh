# Agent_010_MailMan

A hands-on project demonstrating a custom-built AI agent capable of monitoring, parsing, and archiving Gmail messages locally.

## Current Progress

✅ **MailMan Agent completed**: a fully autonomous email management agent built from scratch, featuring:
- **Gmail API integration** for fetching live inbox data across multiple labels (Inbox, Sent, Important, etc.)
- **Local Archive System** with persistent memory (preventing duplicate email processing on restarts)
- **Hugging Face (Moonshot AI)** integration for intelligent tool-calling and natural language interaction

This setup demonstrates practical agent engineering: manual ReAct loops, complex API payload parsing (Base64/HTML stripping), and bounded task execution to prevent infinite AI loops.

## Repository Structure

- mailman_agent.py — core agent logic, tool definitions, and the execution loop
- gmail_auth.py — Google API OAuth and service initialization


## Why this project exists

This project is focused on understanding the "under the hood" mechanics of AI agents:

- Build a tool-calling loop (ReAct) entirely from scratch without heavy frameworks like LangChain or LangGraph
- Safely handle and clean complex, real-world API data (nested Google JSON payloads, MIME types)
- Manage agent state and persistent memory across different chat sessions
- Design safe, bounded tools that a language model can use without crashing or hanging

## Next Direction

Future enhancements for this project will focus on scale and efficiency:

- Migrate the ID-tracking memory from a text file to a lightweight SQLite database
- Implement Gmail API Batch Requests to fetch multiple emails in a single network call
- Add new tools allowing the AI to draft and send email replies directly