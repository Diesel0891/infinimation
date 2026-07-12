"""
skills/ui_automation.py — Infinimation UI Automation Skill
Uses Shizuku (rish) + uiautomator dump for device-agnostic screen interaction.
"""

import subprocess
import xml.etree.ElementTree as ET
import re
import os
from datetime import datetime

RISH = "rish"
DUMP_PATH = "/sdcard/window_dump.xml"
SCREENSHOT_DIR = "/sdcard/Pictures/Screenshots"


def _sh(cmd: str) -> tuple:
    """Execute via rish. Returns (stdout, stderr, returncode)."""
    result = subprocess.run([RISH, "-c", cmd], capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def dump_ui() -> bool:
    """Dump current screen hierarchy to XML. Returns True on success."""
    out, err, rc = _sh(f"uiautomator dump {DUMP_PATH}")
    success = rc == 0
    if not success:
        print(f"[dump_ui] rc={rc} out={out} err={err}")
    return success


def parse_ui() -> list:
    """Parse dumped XML into list of element dicts."""
    if not os.path.exists(DUMP_PATH):
        return []
    try:
        tree = ET.parse(DUMP_PATH)
        root = tree.getroot()
        elements = []
        for node in root.iter("node"):
            bounds = node.get("bounds", "")
            nums = list(map(int, re.findall(r"\d+", bounds)))
            if len(nums) == 4:
                elements.append({
                    "text": node.get("text", ""),
                    "desc": node.get("content-desc", ""),
                    "class": node.get("class", ""),
                    "package": node.get("package", ""),
                    "clickable": node.get("clickable", "false") == "true",
                    "focusable": node.get("focusable", "false") == "true",
                    "bounds": bounds,
                    "center": ((nums[0] + nums[2]) // 2, (nums[1] + nums[3]) // 2),
                })
        return elements
    except ET.ParseError as e:
        print(f"[parse_ui] XML parse error: {e}")
        return []


def find_element(text: str = None, desc: str = None, partial: bool = True) -> dict | None:
    """Find element by visible text or content-desc."""
    if not dump_ui():
        return None
    elements = parse_ui()
    target = text or desc
    for el in elements:
        field = el["text"] if text else el["desc"]
        if partial:
            if target.lower() in field.lower():
                return el
        else:
            if field.lower() == target.lower():
                return el
    return None


def tap_text(text: str, partial: bool = True) -> bool:
    """Tap element by its visible text."""
    el = find_element(text=text, partial=partial)
    if el:
        x, y = el["center"]
        _sh(f"input tap {x} {y}")
        return True
    return False


def input_text(text: str) -> bool:
    """Type text into currently focused field."""
    safe = text.replace("'", "'\\''")
    _, _, rc = _sh(f"input text '{safe}'")
    return rc == 0


def swipe(start: tuple, end: tuple, duration_ms: int = 300) -> bool:
    """Swipe from start (x,y) to end (x,y)."""
    x1, y1 = start
    x2, y2 = end
    _, _, rc = _sh(f"input swipe {x1} {y1} {x2} {y2} {duration_ms}")
    return rc == 0


def take_screenshot(filename: str = None) -> str:
    """Capture screen via /system/bin/screencap."""
    if not filename:
        filename = f"ui_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    path = f"{SCREENSHOT_DIR}/{filename}"
    _sh(f"screencap -p {path}")
    return path


def get_screen_text() -> list:
    """Return all visible text nodes on screen."""
    if not dump_ui():
        return []
    return [el["text"] for el in parse_ui() if el["text"]]


# ── Skill interface for engine ──
def run(args: dict) -> dict:
    action = args.get("action", "")

    if action == "tap_text":
        text = args.get("text", "")
        ok = tap_text(text)
        return {"success": ok, "message": f"Tapped '{text}'" if ok else f"Not found: '{text}'"}

    elif action == "input_text":
        text = args.get("text", "")
        ok = input_text(text)
        return {"success": ok, "message": f"Typed '{text}'" if ok else "Failed to type"}

    elif action == "swipe":
        s = args.get("start", [500, 1500])
        e = args.get("end", [500, 500])
        ok = swipe(tuple(s), tuple(e))
        return {"success": ok, "message": "Swiped"}

    elif action == "dump_ui":
        ok = dump_ui()
        els = parse_ui() if ok else []
        return {"success": ok, "message": f"{len(els)} elements", "data": els[:30]}

    elif action == "get_screen_text":
        texts = get_screen_text()
        return {"success": True, "message": f"{len(texts)} text nodes", "data": texts}

    elif action == "screenshot":
        path = take_screenshot()
        return {"success": True, "message": f"Screenshot: {path}", "data": path}

    else:
        return {"success": False, "message": f"Unknown action: {action}"}


# ── Direct test ──
if __name__ == "__main__":
    print("Testing UI dump...")
    ok = dump_ui()
    print(f"Dump success: {ok}")
    if ok:
        els = parse_ui()
        print(f"Elements found: {len(els)}")
        for e in els[:5]:
            txt = e['text'][:30] if e['text'] else e['desc'][:30]
            print(f"  {txt:30} | center={e['center']} | clickable={e['clickable']}")
    else:
        print("Dump failed.")
