"""
Skill: send_message
Launches messaging apps with pre-filled recipient and message.
Phase 1: Intent-based pre-fill (user taps Send manually).
Phase 2: Shizuku UI automation will auto-tap when available.
"""
import re
import subprocess
import logging

logger = logging.getLogger("infinimation.skill.send_message")

# Known app package mappings
APP_PACKAGES = {
    'whatsapp': 'com.whatsapp',
    'signal': 'org.thoughtcrime.securesms',
    'telegram': 'org.telegram.messenger',
    'sms': 'com.android.mms',
    'messages': 'com.google.android.apps.messaging',
}

def _extract_message(raw_text: str, contact: str) -> str:
    """Extract message body from raw command text."""
    # Patterns: "send message to john hello world" or "send text to john: hello world"
    patterns = [
        rf'send\s+(?:message|text|msg)\s+to\s+{re.escape(contact)}\s*[:,-]?\s*(.+)',
        rf'send\s+(?:message|text|msg)\s+to\s+{re.escape(contact)}\s+(.+)',
    ]
    for pat in patterns:
        m = re.search(pat, raw_text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""

def _launch_sms(contact: str, message: str) -> str:
    """Launch default SMS app with pre-filled recipient and message."""
    try:
        # Try to use termux-open if available
        uri = f"sms:{contact}"
        cmd = [
            "am", "start",
            "-a", "android.intent.action.SENDTO",
            "-d", uri,
            "--es", "sms_body", message
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return f"📩 SMS composer opened for *{contact}* with message pre-filled.\nTap **Send** to deliver."
    except Exception as e:
        logger.error(f"SMS launch failed: {e}")
        return f"⚠️ Could not open SMS composer: {e}"

def _launch_whatsapp(phone: str, message: str) -> str:
    """Launch WhatsApp with pre-filled message."""
    try:
        # Use WhatsApp's direct share intent
        cmd = [
            "am", "start",
            "-a", "android.intent.action.SEND",
            "-t", "text/plain",
            "-e", "android.intent.extra.TEXT", message,
            "-p", "com.whatsapp"
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return f"💬 WhatsApp share opened with message pre-filled.\nSelect *{phone}* and tap **Send**."
    except Exception as e:
        logger.error(f"WhatsApp launch failed: {e}")
        return f"⚠️ Could not open WhatsApp: {e}"

def run(contact: str, raw_text: str = "") -> str:
    """
    Entry point. contact is the regex-captured group.
    raw_text is the full original command for message extraction.
    """
    message = _extract_message(raw_text, contact)
    
    if not message:
        return (f"👤 Contact: *{contact}*\n"
                "What message should I send? Reply with:\n"
                f"`send message to {contact} <your message here>`")
    
    # Detect preferred app from raw text
    text_lower = raw_text.lower()
    app = 'sms'  # default
    
    if 'whatsapp' in text_lower:
        app = 'whatsapp'
    elif 'signal' in text_lower:
        app = 'signal'
    elif 'telegram' in text_lower:
        app = 'telegram'
    
    if app == 'whatsapp':
        return _launch_whatsapp(contact, message)
    else:
        return _launch_sms(contact, message)
