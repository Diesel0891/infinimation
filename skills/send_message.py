"""
send_message: Launch SMS composer or messaging app with pre-filled content.
Phase 1: Intent-based pre-fill (manual send). Phase 2: Shizuku auto-tap (pending).
"""
import subprocess
import logging

logger = logging.getLogger("infinimation")

def run(contact=None, raw_text=None, **kwargs):
    # Handle both regex args (contact string) and LLM args (dict)
    if contact is None or contact == '':
        contact = kwargs.get('recipient', kwargs.get('contact', kwargs.get('args', {}).get('recipient', '')))
    
    message = kwargs.get('message', kwargs.get('args', {}).get('message', ''))
    
    if not message and raw_text:
        # Try to extract message from raw text after contact name
        parts = raw_text.split()
        if len(parts) > 4:
            # "send message to john hello there" -> "hello there"
            message = ' '.join(parts[4:])
    
    if not contact:
        return "❌ Please specify a contact. Example: `send message to john hello`"
    
    if not message:
        return f"👤 Contact: *{contact}*\nWhat message should I send? Reply with:\n`send message to {contact} <your message here>`"
    
    # Launch SMS composer with pre-filled content
    try:
        subprocess.run([
            "am", "start", "-a", "android.intent.action.SENDTO",
            "-d", f"sms:{contact}",
            "--es", "sms_body", message
        ], check=False, capture_output=True)
        logger.info(f"SMS_PREFILL: {contact} | {message[:50]}")
        return f"✉️ SMS composer opened for *{contact}*\nMessage: _{message}_\nTap Send to deliver."
    except Exception as e:
        logger.error(f"SMS_ERROR: {str(e)}")
        return f"❌ Failed to open SMS: {str(e)}"
