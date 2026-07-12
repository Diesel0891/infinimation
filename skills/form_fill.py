"""
skills/form_fill.py — Infinimation Form Filling Skill
Opens a URL in Chrome and attempts to fill form fields via UI automation.
Honest about limitations: web content inside Chrome WebViews may not be
fully visible to uiautomator. Native Android forms work perfectly.
"""

import sys
import os
import time
import urllib.parse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.ui_automation import _sh, dump_ui, parse_ui, tap_text, input_text, take_screenshot


def open_url(url: str) -> bool:
    """Open URL in the default browser via Android intent."""
    safe_url = url.replace("'", "'\\''")
    _, _, rc = _sh(f"am start -a android.intent.action.VIEW -d '{safe_url}'")
    return rc == 0


def find_input_field(label: str = None) -> dict | None:
    """Find an input field by label text or class. Returns element dict or None."""
    if not dump_ui():
        return None
    elements = parse_ui()

    # Strategy 1: Find by label text, then look for nearest EditText
    if label:
        label_lower = label.lower()
        for i, el in enumerate(elements):
            text_combined = f"{el['text']} {el['desc']}".lower()
            if label_lower in text_combined:
                # Search forward for an input field
                for j in range(i, min(i + 6, len(elements))):
                    cls = elements[j]["class"]
                    if any(k in cls for k in ("EditText", "AutoCompleteTextView", "MultiAutoCompleteTextView")):
                        return elements[j]

    # Strategy 2: Find any empty EditText
    for el in elements:
        if "EditText" in el["class"] and el["text"] == "":
            return el

    # Strategy 3: Find any input-class element
    for el in elements:
        if any(k in el["class"] for k in ("EditText", "AutoCompleteTextView")):
            return el

    return None


def find_submit_button(submit_text: str = None) -> dict | None:
    """Find a submit button by text or common labels."""
    if not dump_ui():
        return None
    elements = parse_ui()

    candidates = [submit_text] if submit_text else []
    candidates += ["Submit", "Send", "Login", "Sign in", "Continue", "Next", "OK", "Save", "Done", "Search"]

    for btn_text in candidates:
        if not btn_text:
            continue
        for el in elements:
            text_combined = f"{el['text']} {el['desc']}".lower()
            if btn_text.lower() in text_combined and el["clickable"]:
                return el
    return None


def fill_form(url: str, fields: dict, submit_text: str = None) -> dict:
    """Open URL and attempt to fill form fields."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    if not open_url(url):
        return {"success": False, "message": "Failed to open browser"}

    # Wait for page/app to load
    time.sleep(4)

    # Initial screenshot
    screenshot_before = take_screenshot("form_before.png")

    filled = []
    failed = []

    for label, value in fields.items():
        field = find_input_field(label)
        if field:
            x, y = field["center"]
            _sh(f"input tap {x} {y}")
            time.sleep(0.5)
            # Clear existing text if any
            _sh("input keyevent KEYCODE_CTRL_LEFT KEYCODE_A")
            time.sleep(0.2)
            _sh("input keyevent KEYCODE_DEL")
            time.sleep(0.2)
            input_text(str(value))
            time.sleep(0.5)
            filled.append(label)
        else:
            failed.append(label)

    # Attempt submit
    submit_el = find_submit_button(submit_text)
    submit_tapped = False
    if submit_el:
        x, y = submit_el["center"]
        _sh(f"input tap {x} {y}")
        submit_tapped = True
        time.sleep(1)

    # Final screenshot
    screenshot_after = take_screenshot("form_after.png")

    msg = f"Filled {len(filled)}/{len(fields)} fields"
    if failed:
        msg += f"; failed: {', '.join(failed)}"
    msg += f". Submit: {'tapped' if submit_tapped else 'not found'}"
    if failed and not submit_tapped:
        msg += " (WebView content may not be visible to uiautomator. Accessibility service needed for full web form support.)"

    return {
        "success": len(failed) == 0 and submit_tapped,
        "message": msg,
        "data": {
            "filled": filled,
            "failed": failed,
            "submit_tapped": submit_tapped,
            "screenshots": [screenshot_before, screenshot_after],
            "url": url,
        }
    }


# ── Skill interface for engine ──
def run(args: dict) -> dict:
    url = args.get("url") or args.get("link") or args.get("website")
    if not url:
        return {"success": False, "message": "No URL provided. Usage: fill form at <url> with field1=value1 field2=value2"}

    # Extract fields from args (skip meta keys)
    skip = {"url", "link", "website", "action", "submit", "submit_text", "skill", "confidence", "raw_text", "param_0"}
    fields = {k: v for k, v in args.items() if k not in skip}

    submit_text = args.get("submit") or args.get("submit_text")

    return fill_form(url, fields, submit_text)


# ── Direct test ──
if __name__ == "__main__":
    # Safe test: opens Google search (works via URL, not true form fill)
    print("Testing form fill skill...")
    print("This will open Chrome to example.com and attempt to find inputs.")
    print("Since example.com has no form, it should report 0/0 filled.")
    result = fill_form("https://example.com", {}, None)
    print(f"Result: {result['message']}")
    print(f"Screenshots: {result['data']['screenshots']}")
