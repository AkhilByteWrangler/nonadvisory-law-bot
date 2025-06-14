# nonadvisory_law_bot_backend

A simple FastAPI backend for the nonadvisory-law-bot. This service receives user queries, crafts a prompt for the LLM, and returns a general, non-legal advice response with a disclaimer.

## Setup

1. Install dependencies:
   ```bash
   pip install fastapi uvicorn openai
   ```

2. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

## Endpoints

- `POST /ask` - Accepts a user query and returns a response from the LLM.

## Disclaimer
This service provides general information only and does not constitute legal advice.
