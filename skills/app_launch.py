"""
Skill: app_launch
Launches Android apps via package intent through Shizuku.
"""
import subprocess
import os
import logging

logger = logging.getLogger("infinimation")

APP_PACKAGES = {
    "whatsapp": "com.whatsapp/.Main",
    "chrome": "com.android.chrome/com.google.android.apps.chrome.Main",
    "settings": "com.android.settings/.Settings",
    "camera": "com.android.camera/.Camera",
    "telegram": "org.telegram.messenger/org.telegram.ui.LaunchActivity",
}

def _sh(cmd: str) -> tuple:
    env = os.environ.copy()
    env["RISH_APPLICATION_ID"] = "com.termux"
    result = subprocess.run(["rish", "-c", cmd], capture_output=True, text=True, env=env)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def run(args, *extra_args, raw_text: str = "") -> str:
    # Handle both dict (new engine) and string (old engine)
    if isinstance(args, dict):
        app_name = args.get("app", "")
    else:
        app_name = str(args)

    if not app_name:
        return "No app name provided."

    package = APP_PACKAGES.get(app_name.lower())
    if not package:
        return f"Unknown app '{app_name}'. Known: {', '.join(APP_PACKAGES.keys())}"

    cmd = f"am start -n {package}"
    out, err, rc = _sh(cmd)
    
    if rc == 0:
        logger.info(f"APP_LAUNCHED: {app_name}")
        return f"Launched {app_name}."
    else:
        logger.error(f"APP_LAUNCH_FAILED: {app_name} | err={err}")
        return f"Failed to launch {app_name}: {err}"
