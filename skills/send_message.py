"""
skills/send_message.py — Infinimation Send Message Skill
Opens SMS composer, pre-fills recipient and message, auto-taps Send.
"""

import subprocess
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.ui_automation import find_element


def _sh(cmd: str) -> tuple:
    env = os.environ.copy()
    env["RISH_APPLICATION_ID"] = "com.termux"
    result = subprocess.run(["rish", "-c", cmd], capture_output=True, text=True, env=env)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def send_sms(recipient: str, message: str, auto_send: bool = True) -> dict:
    """Launch SMS composer with pre-filled content. Optionally auto-tap Send."""
    if not recipient or not message:
        return {"success": False, "message": "Recipient and message are required"}

    safe_body = message.replace("'", "'\\''")
    intent = (
        f"am start -a android.intent.action.SENDTO "
        f"-d 'sms:{recipient}' "
        f"--es sms_body '{safe_body}'"
    )

    out, err, rc = _sh(intent)
    if rc != 0:
        return {"success": False, "message": f"Failed to launch SMS composer: {err}"}

    if not auto_send:
        return {
            "success": True,
            "message": f"SMS composer opened for {recipient}. Tap Send manually.",
            "data": {"recipient": recipient, "message": message, "auto_send": False}
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
            "message": "Opened composer but could not find Send button",
            "data": {"recipient": recipient, "message": message, "auto_send": False}
        }

    return {
        "success": True,
        "message": f"Send button tapped for {recipient}. Message should be sent.",
        "data": {"recipient": recipient, "message": message, "auto_send": True}
    }


def run(args: dict) -> dict:
    recipient = args.get("recipient") or args.get("contact") or args.get("to")
    message = args.get("message") or args.get("text") or args.get("body")
    auto_send = args.get("auto_send", True)

    if not recipient:
        return {"success": False, "message": "No recipient specified. Usage: send message to <name> saying <text>"}

    if not message:
        return {"success": False, "message": "No message body specified."}

    return send_sms(recipient, message, auto_send)


if __name__ == "__main__":
    print("Testing send_message skill...")
    print("Opening SMS composer for +265985965871 with auto_send=False")
    result = send_sms("+265985965871", "Infinimation test message", auto_send=False)
    print(result)
