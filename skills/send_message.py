"""
skills/send_message.py — Infinimation Send Message Skill
Opens SMS composer, pre-fills recipient and message, auto-taps Send.
Validates phone numbers to prevent invalid recipient errors.
"""

import subprocess
import sys
import os
import time
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.ui_automation import find_element, dump_ui, parse_ui


def _sh(cmd: str) -> tuple:
    env = os.environ.copy()
    env["RISH_APPLICATION_ID"] = "com.termux"
    result = subprocess.run(["rish", "-c", cmd], capture_output=True, text=True, env=env)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def validate_phone(number: str) -> tuple:
    """
    Validate and normalize phone number.
    Returns (is_valid: bool, normalized: str, error_msg: str)
    """
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)\.]', '', number)
    
    # Check if it's purely digits (possibly with + prefix)
    if not re.match(r'^\+?\d+$', cleaned):
        return False, number, f"'{number}' is not a valid phone number. Use digits only, e.g., +265985965871"
    
    # Minimum length check
    digits_only = re.sub(r'\D', '', cleaned)
    if len(digits_only) < 7:
        return False, number, f"Phone number too short: '{number}'. Minimum 7 digits."
    
    return True, cleaned, ""


def send_sms(recipient: str, message: str, auto_send: bool = True) -> dict:
    """Launch SMS composer with pre-filled content. Optionally auto-tap Send."""
    if not recipient or not message:
        return {"success": False, "message": "Recipient and message are required"}

    # Validate phone number
    is_valid, normalized, error = validate_phone(recipient)
    if not is_valid:
        return {"success": False, "message": error}

    safe_body = message.replace("'", "'\\''")
    intent = (
        f"am start -a android.intent.action.SENDTO "
        f"-d 'sms:{normalized}' "
        f"--es sms_body '{safe_body}'"
    )

    out, err, rc = _sh(intent)
    if rc != 0:
        return {"success": False, "message": f"Failed to launch SMS composer: {err}"}

    if not auto_send:
        return {
            "success": True,
            "message": f"SMS composer opened for {normalized}. Tap Send manually.",
            "data": {"recipient": normalized, "message": message, "auto_send": False}
        }

    time.sleep(2.5)

    # Find send button by content-desc first (ImageButtons), then text
    send_labels = ["Send", "SEND", "send", "Send message", "SMS"]
    tapped = False

    for label in send_labels:
        el = find_element(desc=label, partial=True)
        if el and el["clickable"]:
            x, y = el["center"]
            _sh(f"input tap {x} {y}")
            tapped = True
            break
        el = find_element(text=label, partial=True)
        if el and el["clickable"]:
            x, y = el["center"]
            _sh(f"input tap {x} {y}")
            tapped = True
            break

    if not tapped:
        return {
            "success": False,
            "message": "Opened composer but could not find Send button. Screen may be blocked by an error dialog.",
            "data": {"recipient": normalized, "message": message, "auto_send": False}
        }

    return {
        "success": True,
        "message": f"Send button tapped for {normalized}. Message should be sent.",
        "data": {"recipient": normalized, "message": message, "auto_send": True}
    }


def run(args: dict) -> dict:
    recipient = args.get("recipient") or args.get("contact") or args.get("to")
    message = args.get("message") or args.get("text") or args.get("body")
    auto_send = args.get("auto_send", True)

    if not recipient:
        return {"success": False, "message": "No recipient specified. Usage: send message to <phone_number> saying <text>"}

    if not message:
        return {"success": False, "message": "No message body specified."}

    return send_sms(recipient, message, auto_send)


if __name__ == "__main__":
    print("Testing send_message validation...")
    
    tests = [
        "john",
        "+265985965871",
        "0985965871",
        "123",
        "abc-def",
    ]
    
    for num in tests:
        valid, norm, err = validate_phone(num)
        print(f"  {num:20} -> valid={valid}, normalized={norm}, error={err or 'OK'}")
