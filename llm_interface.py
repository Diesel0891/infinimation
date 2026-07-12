"""
LLM Interface with provider router.
Supports: gemini, groq, openrouter, ollama, none.
"""
import json
import re
import logging
from router import route_inference

logger = logging.getLogger("infinimation.llm")

def infer(prompt: str, max_tokens: int = 256) -> str:
    return route_inference(prompt, max_tokens)

def parse_intent(text: str) -> dict:
    prompt = f"""You are an intent classifier for a phone automation bot.
Available skills: web_scrape, app_launch, send_message, take_screenshot, system_status, show_help, unknown.
Given the user command, return ONLY a JSON object with no markdown formatting:
{{"skill": "skill_name", "args": {{"key": "value"}}, "confidence": 0.0-1.0}}

User command: {text}

Response:"""
    
    raw = infer(prompt, max_tokens=128)
    
    try:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            return parsed
    except Exception:
        pass
    
    return {"skill": "unknown", "args": {}, "confidence": 0.0}
