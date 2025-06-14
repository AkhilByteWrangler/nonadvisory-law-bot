import requests
from dotenv import load_dotenv

# This module provides a function to query the Google Gemini API for text generation or evaluation.

import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


def palm_chat(messages):
    if not GEMINI_API_KEY:
        raise Exception("GEMINI_API_KEY not set.")
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    # Map roles: 'user' stays 'user', anything else becomes 'model'
    def map_role(author):
        return 'user' if author == 'user' else 'model'
    data = {
        "contents": [
            {"role": map_role(m["author"]), "parts": [{"text": m["content"]}]} for m in messages
        ],
        "generationConfig": {"temperature": 0.3, "candidateCount": 1}
    }
    print("The URL is:", GEMINI_API_URL)
    response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=data)
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]
