#!/data/data/com.termux/files/usr/bin/python3
"""
Infinimation Engine v0.3
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

# ── Fuzzy App Name Mapping ────────────────────────────────────
# Maps common variations to canonical app names
FUZZY_APP_MAP = {
    # Chrome / Browser
    "chrome": "chrome", "google chrome": "chrome", "browser": "chrome",
    "web browser": "chrome", "internet": "chrome", "google browser": "chrome",
    # WhatsApp
    "whatsapp": "whatsapp", "whats app": "whatsapp", "wa": "whatsapp",
    # Gmail
    "gmail": "gmail", "email": "gmail", "mail": "gmail", "google mail": "gmail",
    # YouTube
    "youtube": "youtube", "you tube": "youtube", "yt": "youtube",
    # Maps
    "maps": "maps", "google maps": "maps", "navigation": "maps", "gps": "maps",
    # Camera
    "camera": "camera", "cam": "camera", "photo": "camera",
    # Settings
    "settings": "settings", "config": "settings", "configuration": "settings",
    "preferences": "settings",
    # Phone
    "phone": "phone", "dialer": "phone", "call": "phone", "telephone": "phone",
    # Messages
    "messages": "messages", "sms": "messages", "texts": "messages",
    # Gallery
    "gallery": "gallery", "photos": "gallery", "pictures": "gallery", "album": "gallery",
    # Calendar
    "calendar": "calendar", "schedule": "calendar", "agenda": "calendar",
    # Clock
    "clock": "clock", "alarm": "clock", "timer": "clock", "stopwatch": "clock",
    # Calculator
    "calculator": "calculator", "calc": "calculator",
    # Files
    "files": "files", "file manager": "files", "documents": "files", "folder": "files",
    # Notes
    "notes": "notes", "keep": "notes", "google keep": "notes", "memo": "notes",
    # Play Store
    "playstore": "playstore", "play store": "playstore", "app store": "playstore",
    "google play": "playstore",
    # Samsung
    "samsung internet": "samsunginternet", "samsung browser": "samsungbrowser",
}

def resolve_app_name(text: str) -> str | None:
    """Extract app name from natural language using fuzzy matching."""
    text_lower = text.lower()
    
    # Direct mention: "open X", "launch X", "start X"
    direct_patterns = [
        r'\b(?:open|launch|start|go to|take me to|show me|i want|can you|please)\s+(?:the\s+)?(?:app\s+)?(\w+(?:\s+\w+)?)',
        r'\b(?:in|on|using|via)\s+(?:the\s+)?(\w+(?:\s+\w+)?)\b',
    ]
    
    for pattern in direct_patterns:
        match = re.search(pattern, text_lower)
        if match:
            candidate = match.group(1).strip()
            # Check fuzzy map
            if candidate in FUZZY_APP_MAP:
                return FUZZY_APP_MAP[candidate]
            # Try partial match
            for key, value in FUZZY_APP_MAP.items():
                if key in candidate or candidate in key:
                    return value
    
    return None

# ── Intent Classifier (Layer 1: Regex) ────────────────────────
INTENT_PATTERNS = {
    # Web
    r'\bscrape\b.*?(https?://\S+)': 'web_scrape',
    r'\b(?:check|visit|go to|open)\s+(https?://\S+)': 'web_scrape',
    
    # Apps - explicit
    r'\b(?:open|launch|start)\s+(?:the\s+)?(?:app\s+)?(\w+(?:\s+\w+)?)': 'app_launch',
    
    # SMS
    r'\bsend\s+(?:message|text|msg)\s+to\s+(.+?)(?:\s+(?:say|saying)\s+(.+)|\s+with\s+(.+)|$)': 'send_message',
    
    # System
    r'\b(?:check|what|how).{0,20}(?:battery|power|charge|health|storage|ram|memory)': 'system_status',
    r'\bstatus\b': 'system_status',
    
    # Screenshot
    r'\bscreenshot\b': 'take_screenshot',
    r'\bscreen\s+cap\b': 'take_screenshot',
    r'\bcapture\s+(?:the\s+)?screen\b': 'take_screenshot',
    
    # Help
    r'\bhelp\b': 'show_help',
    r'\bwhat\s+can\s+you\s+do\b': 'show_help',
    r'\bcommands\b': 'show_help',
    
    # UI Automation
    r'\b(?:tap|click|press)\s+(?:on\s+)?(.+)': 'ui_automation',
    r'\b(?:type|enter|input)\s+(?:text\s+)?(.+)': 'ui_automation',
    r'\bswipe\s+(?:up|down|left|right)\b': 'ui_automation',
    
    # Screen Reading
    r'\bread\s+(?:the\s+)?screen\b': 'read_screen',
    r'\bwhat\'?s\s+on\s+(?:the\s+)?screen\b': 'read_screen',
    r'\bshow\s+me\s+(?:the\s+)?screen\b': 'read_screen',
    
    # Form Filling
    r'\bfill\s+(?:form\s+)?at\s+(https?://\S+)': 'form_fill',
    r'\bcomplete\s+(?:the\s+)?form\b': 'form_fill',
}

def classify_intent(text: str) -> tuple:
    """
    Layer 1: Fast regex classification.
    Returns (skill_name, args_dict) or (None, None) for LLM fallback.
    """
    text_lower = text.lower().strip()
    
    # Try explicit regex patterns first
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
                    resolved = resolve_app_name(text)
                    args["app"] = resolved if resolved else groups[0]
                elif skill_name == 'send_message':
                    args["recipient"] = groups[0].strip()
                    message_body = groups[1] if len(groups) > 1 and groups[1] else (groups[2] if len(groups) > 2 and groups[2] else "")
                    if message_body:
                        args["message"] = message_body.strip()
                elif skill_name == 'ui_automation':
                    if re.search(r'\b(?:tap|click|press)\b', text, re.I):
                        args["action"] = "tap_text"
                        args["text"] = groups[0]
                    elif re.search(r'\b(?:type|enter|input)\b', text, re.I):
                        args["action"] = "input_text"
                        args["text"] = groups[0]
                    elif re.search(r'\bswipe\b', text, re.I):
                        direction = groups[0].lower() if groups else "down"
                        args["action"] = "swipe"
                        args["direction"] = direction
                elif skill_name == 'form_fill':
                    args["url"] = groups[0]
            logger.info(f"INTENT_MATCH: {skill_name} | args={args}")
            return skill_name, args
    
    # Fuzzy fallback: try to detect app launch from natural language
    fuzzy_app = resolve_app_name(text)
    if fuzzy_app:
        args = {"raw_text": text, "app": fuzzy_app, "param_0": fuzzy_app}
        logger.info(f"INTENT_MATCH: app_launch (fuzzy) | app={fuzzy_app}")
        return 'app_launch', args
    
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

    # Check for multi-step or conditional commands
    multi_step_keywords = [' then ', ' and then ', ' after that ', ' if ', 'first ', 'second ']
    is_multi_step = any(kw in text.lower() for kw in multi_step_keywords)
    
    if is_multi_step:
        try:
            from skills.planner.engine import run as planner_run
            plan_result = planner_run({"raw_text": text})
            return plan_result
        except Exception as e:
            logger.error(f"PLANNER_ERROR: {e}")
            # Fall through to normal execution if planner fails

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
                result["output"] = "I did not understand that command. Try: open <app>, send message to <contact> saying <text>, read screen, check battery, or help."
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
        "I want to do something in chrome",
        "Can you launch the browser",
        "Take me to google maps",
        "send message to john saying hello",
        "read screen",
        "check my battery",
        "help",
        "what is the weather today"
    ]
    for cmd in test_cmds:
        print(f"\n>>> {cmd}")
        print(execute_command(cmd))
