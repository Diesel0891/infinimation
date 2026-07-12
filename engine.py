#!/data/data/com.termux/files/usr/bin/env python3
"""
Infinimation Engine v0.1
Primary automation orchestrator for Mate 9.
"""
import os
import sys
import json
import re
import subprocess
import time
import logging
import logging.handlers
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()
CONFIG_DIR = BASE_DIR / "config"
LOGS_DIR = BASE_DIR / "logs"
SKILLS_DIR = BASE_DIR / "skills"

CONFIG_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
SKILLS_DIR.mkdir(exist_ok=True)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.handlers.RotatingFileHandler(
            LOGS_DIR / "engine.log", maxBytes=5*1024*1024, backupCount=3
        ),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("infinimation")

# ── Intent Classifier (Layer 1: Regex) ────────────────────────
INTENT_PATTERNS = {
    r'\bscrape\b.*?(https?://\S+)': 'web_scrape',
    r'\bopen\s+(\w+)': 'app_launch',
    r'\bsend\s+(?:message|text|msg)\s+to\s+(\w+)': 'send_message',
    r'\bscreenshot\b': 'take_screenshot',
    r'\bstatus\b': 'system_status',
    r'\bhelp\b': 'show_help',
}

def classify_intent(text: str) -> tuple:
    """
    Layer 1: Fast regex classification.
    Returns (skill_name, extracted_params) or (None, None) for LLM fallback.
    """
    text_lower = text.lower().strip()
    for pattern, skill_name in INTENT_PATTERNS.items():
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            params = match.groups()
            logger.info(f"INTENT_MATCH: {skill_name} | params={params}")
            return skill_name, params
    logger.info("INTENT_FALLBACK: No regex match, routing to LLM")
    return None, None

# ── Skill Loader ──────────────────────────────────────────────
def load_skill(skill_name: str):
    """Dynamically import skill module from skills/ directory."""
    skill_path = SKILLS_DIR / f"{skill_name}.py"
    if not skill_path.exists():
        logger.error(f"SKILL_MISSING: {skill_name}.py not found")
        return None
    import importlib.util
    spec = importlib.util.spec_from_file_location(skill_name, skill_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# ── Core Execution Loop ───────────────────────────────────────
def execute_command(text: str) -> dict:
    """Main entry point for any incoming command."""
    result = {"success": False, "output": "", "skill_used": None}
    
    skill_name, params = classify_intent(text)
    
    if skill_name:
        skill = load_skill(skill_name)
        if skill and hasattr(skill, 'run'):
            try:
                output = skill.run(*params, raw_text=text)
                result.update({"success": True, "output": output, "skill_used": skill_name})
            except Exception as e:
                result["output"] = f"Skill error: {str(e)}"
                logger.exception(f"SKILL_ERROR: {skill_name}")
        else:
            result["output"] = f"Skill '{skill_name}' exists but has no run() function."
    else:
        try:
            import llm_interface
            parsed = llm_interface.parse_intent(text)
            llm_skill = parsed.get("skill", "unknown")
            confidence = parsed.get("confidence", 0.0)
            
            if llm_skill != "unknown" and confidence >= 0.5:
                skill = load_skill(llm_skill)
                if skill and hasattr(skill, "run"):
                    try:
                        output = skill.run(raw_text=text)
                        result.update({"success": True, "output": output, "skill_used": llm_skill})
                    except TypeError:
                        result["output"] = f"Detected intent: {llm_skill}, but need more details. Try a more specific command."
                        result["skill_used"] = "llm_partial"
                    except Exception as e:
                        result["output"] = f"Skill error: {str(e)}"
                        logger.exception(f"SKILL_ERROR: {llm_skill}")
                else:
                    result["output"] = f"Skill '{llm_skill}' not available."
                    result["skill_used"] = "llm_fallback"
            else:
                result["output"] = "I did not understand that command. Try: scrape <url>, open <app>, send message to <contact>, screenshot, status, or help."
                result["skill_used"] = "unknown"
        except Exception as e:
            result["output"] = f"LLM fallback unavailable: {str(e)}"
            result["skill_used"] = "llm_error"
    
    return result

if __name__ == "__main__":
    # Quick self-test
    test_cmds = [
        "scrape https://example.com prices",
        "open whatsapp",
        "send message to john",
        "what is the weather today"
    ]
    for cmd in test_cmds:
        print(f"\n>>> {cmd}")
        print(execute_command(cmd))
