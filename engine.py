#!/data/data/com.termux/files/usr/bin/python3
"""
Infinimation Engine v0.2
Primary automation orchestrator.
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
    # Existing
    r'\bscrape\b.*?(https?://\S+)': 'web_scrape',
    r'\bopen\s+(\w+)': 'app_launch',
    r'\bsend\s+(?:message|text|msg)\s+to\s+(\w+)': 'send_message',
    r'\bscreenshot\b': 'take_screenshot',
    r'\bstatus\b': 'system_status',
    r'\bhelp\b': 'show_help',
    # New: UI Automation
    r'\b(?:tap|click|press)\s+(?:on\s+)?(.+)': 'ui_automation',
    r'\b(?:type|enter|input)\s+(?:text\s+)?(.+)': 'ui_automation',
    # New: Screen Reading
    r'\bread\s+(?:the\s+)?screen\b': 'read_screen',
    r'\bwhat\'?s\s+on\s+(?:the\s+)?screen\b': 'read_screen',
    r'\bshow\s+me\s+(?:the\s+)?screen\b': 'read_screen',
    # New: Form Filling
    r'\bfill\s+(?:form\s+)?at\s+(https?://\S+)': 'form_fill',
    r'\bcomplete\s+(?:the\s+)?form\b': 'form_fill',
}

def classify_intent(text: str) -> tuple:
    """
    Layer 1: Fast regex classification.
    Returns (skill_name, args_dict) or (None, None) for LLM fallback.
    """
    text_lower = text.lower().strip()
    for pattern, skill_name in INTENT_PATTERNS.items():
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            args = {"raw_text": text}
            groups = match.groups()
            if groups:
                args["param_0"] = groups[0]
                # Skill-specific arg mapping
                if skill_name == 'web_scrape':
                    args["url"] = groups[0]
                elif skill_name == 'app_launch':
                    args["app"] = groups[0]
                elif skill_name == 'send_message':
                    args["recipient"] = groups[0]
                elif skill_name == 'ui_automation':
                    if re.search(r'\b(?:tap|click|press)\b', text, re.I):
                        args["action"] = "tap_text"
                        args["text"] = groups[0]
                    elif re.search(r'\b(?:type|enter|input)\b', text, re.I):
                        args["action"] = "input_text"
                        args["text"] = groups[0]
                elif skill_name == 'form_fill':
                    args["url"] = groups[0]
            logger.info(f"INTENT_MATCH: {skill_name} | args={args}")
            return skill_name, args
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

    skill_name, args = classify_intent(text)

    if skill_name:
        skill = load_skill(skill_name)
        if skill and hasattr(skill, 'run'):
            try:
                # New convention: pass args dict
                output = skill.run(args)
                result.update({"success": True, "output": output, "skill_used": skill_name})
            except TypeError:
                # Fallback: old convention with positional args
                try:
                    params = args.get("param_0", "")
                    if params:
                        output = skill.run(params, raw_text=text)
                    else:
                        output = skill.run(raw_text=text)
                    result.update({"success": True, "output": output, "skill_used": skill_name})
                except Exception as e:
                    result["output"] = f"Skill error: {str(e)}"
                    logger.exception(f"SKILL_ERROR: {skill_name}")
            except Exception as e:
                result["output"] = f"Skill error: {str(e)}"
                logger.exception(f"SKILL_ERROR: {skill_name}")
        else:
            result["output"] = f"Skill '{skill_name}' exists but has no run() function."
    else:
        # LLM fallback
        try:
            import llm_interface
            parsed = llm_interface.parse_intent(text)
            llm_skill = parsed.get("skill", "unknown")
            confidence = parsed.get("confidence", 0.0)
            llm_args = parsed.get("args", {})
            llm_args["raw_text"] = text

            if llm_skill != "unknown" and confidence >= 0.5:
                skill = load_skill(llm_skill)
                if skill and hasattr(skill, "run"):
                    try:
                        output = skill.run(llm_args)
                        result.update({"success": True, "output": output, "skill_used": llm_skill})
                    except TypeError:
                        try:
                            output = skill.run(raw_text=text)
                            result.update({"success": True, "output": output, "skill_used": llm_skill})
                        except Exception as e:
                            result["output"] = f"Skill error: {str(e)}"
                            logger.exception(f"SKILL_ERROR: {llm_skill}")
                    except Exception as e:
                        result["output"] = f"Skill error: {str(e)}"
                        logger.exception(f"SKILL_ERROR: {llm_skill}")
                else:
                    result["output"] = f"Skill '{llm_skill}' not available."
                    result["skill_used"] = "llm_fallback"
            else:
                result["output"] = "I did not understand that command. Try: scrape <url>, open <app>, send message to <contact>, screenshot, status, help, tap <text>, read screen, or fill form at <url>."
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
        "tap Send",
        "type hello world",
        "read screen",
        "fill form at https://example.com",
        "what is the weather today"
    ]
    for cmd in test_cmds:
        print(f"\n>>> {cmd}")
        print(execute_command(cmd))
