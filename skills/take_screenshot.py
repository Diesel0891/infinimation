"""
Skill: take_screenshot
Captures the device screen and saves it to shared storage.
"""
import subprocess
import os
import datetime
from pathlib import Path

def run(*args, raw_text: str = "") -> str:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{timestamp}.png"
    
    # Save to shared Pictures/Screenshots so it is visible in Gallery
    screenshot_dir = Path(os.path.expanduser("~/storage/shared/Pictures/Screenshots"))
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    filepath = screenshot_dir / filename
    
    try:
        result = subprocess.run(
            ["termux-screenshot", "-f", str(filepath)],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            return f"📸 Screenshot saved to Gallery:\n`{filepath}`"
        else:
            raise RuntimeError(result.stderr.strip() or "termux-screenshot returned non-zero")
    except FileNotFoundError:
        return ("⚠️ `termux-screenshot` not found.\n"
                "Install Termux:API app from F-Droid, then run:\n"
                "`pkg install termux-api`\n"
                "Shizuku-based screencap fallback will be added in Step 7.")
    except Exception as e:
        return f"⚠️ Screenshot failed: {e}\nCheck Termux:API permissions."
