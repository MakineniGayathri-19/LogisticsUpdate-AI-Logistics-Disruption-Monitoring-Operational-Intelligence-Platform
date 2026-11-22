"""Brief generation module – uses LLM to create operational briefs.
Supports OpenAI's chat completion API (or Gemini if you switch provider).
"""
import os
import json
from typing import List, Dict

import openai
# If you prefer Gemini, uncomment the import and adjust the call below
# import google.generativeai as genai

from .config import OPENAI_API_KEY
from .historical import load_past_events

openai.api_key = OPENAI_API_KEY

SYSTEM_PROMPT = "You are an expert logistics analyst. Given a current disruption event and a list of past similar events with their operational responses, write a concise operational brief (max 200 words). Include: what changed, significance, any prior handling, and recommended actions."

def build_prompt(event: Dict, past_events: List[Dict]) -> List[Dict]:
    user_msg = f"Current event:\n{json.dumps(event, indent=2)}\n\nPast events (up to {len(past_events)}):\n{json.dumps(past_events, indent=2)}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]

def generate_brief(event: Dict) -> str:
    """Generate an operational brief for *event*.
    Retrieves recent past events from the Memento repo and calls the LLM.
    """
    past = load_past_events(limit=10)
    messages = build_prompt(event, past)
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.2,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[ERROR] LLM call failed: {e}"

if __name__ == "__main__":
    # Simple demo – generate brief for a dummy event
    dummy = {"date": "2026-11-20", "location": "Port of Rotterdam", "type": "weather", "description": "Heavy fog causing delays", "source": "example.com"}
    print(generate_brief(dummy))
