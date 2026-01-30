# Drug Safety Intelligence MCP - Development Guide

This is an MCP (Model Context Protocol) server for FDA drug safety intelligence.

## Project Structure
- `src/` - Python source code for MCP server
- `data/` - Reference data and SQLite cache
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variables template

## Setup Instructions
1. Copy `.env.example` to `.env` and add your OpenAI API key
2. Install dependencies: `pip install -r requirements.txt`
3. Run the server: `python src/server.py`

## Key Features
- 3 MCP tools for drug safety analysis
- SQLite caching with 24-hour TTL
- FDA API integration
- OpenAI-powered summaries
- Pydantic validation
