"""
Skill: app_launch
Launches Android apps via package intent through Shizuku.
"""
import subprocess
import os
import logging

logger = logging.getLogger("infinimation")

APP_PACKAGES = {
    # Messaging & Communication
    "whatsapp": "com.whatsapp/.Main",
    "telegram": "org.telegram.messenger/org.telegram.ui.LaunchActivity",
    "gmail": "com.google.android.gm/.ConversationListActivityGmail",
    "email": "com.google.android.gm/.ConversationListActivityGmail",
    "phone": "com.android.dialer/.main.impl.MainActivity",
    "dialer": "com.android.dialer/.main.impl.MainActivity",
    "contacts": "com.android.contacts/.activities.PeopleActivity",
    "messages": "com.google.android.apps.messaging/.ui.ConversationListActivity",
    "sms": "com.google.android.apps.messaging/.ui.ConversationListActivity",
    
    # Browsers
    "chrome": "com.android.chrome/com.google.android.apps.chrome.Main",
    "browser": "com.android.chrome/com.google.android.apps.chrome.Main",
    
    # Media
    "youtube": "com.google.android.youtube/.app.honeycomb.Shell$HomeActivity",
    "gallery": "com.android.gallery3d/.app.GalleryActivity",
    "photos": "com.google.android.apps.photos/.home.HomeActivity",
    "camera": "com.android.camera/.Camera",
    
    # System & Tools
    "settings": "com.android.settings/.Settings",
    "maps": "com.google.android.apps.maps/com.google.android.maps.MapsActivity",
    "playstore": "com.android.vending/.AssetBrowserActivity",
    "clock": "com.android.deskclock/.DeskClock",
    "calculator": "com.google.android.calculator/com.android.calculator2.Calculator",
    "files": "com.google.android.apps.nbu.files/.home.HomeActivity",
    "filemanager": "com.google.android.apps.nbu.files/.home.HomeActivity",
    "calendar": "com.google.android.calendar/.AllInOneCalendarActivity",
    "notes": "com.google.android.keep/.activities.BrowseActivity",
    "keep": "com.google.android.keep/.activities.BrowseActivity",
    
    # Samsung-specific (Galaxy A03)
    "samsunginternet": "com.sec.android.app.sbrowser/.SBrowserMainActivity",
    "samsungbrowser": "com.sec.android.app.sbrowser/.SBrowserMainActivity",
}

def _sh(cmd: str) -> tuple:
    env = os.environ.copy()
    env["RISH_APPLICATION_ID"] = "com.termux"
    result = subprocess.run(["rish", "-c", cmd], capture_output=True, text=True, env=env)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def run(args, *extra_args, raw_text: str = "") -> str:
    if isinstance(args, dict):
        app_name = args.get("app", "")
    else:
        app_name = str(args)

    if not app_name:
        return "No app name provided."

    package = APP_PACKAGES.get(app_name.lower())
    if not package:
        known = ', '.join(sorted(APP_PACKAGES.keys()))
        return f"Unknown app '{app_name}'.\nKnown apps: {known}"

    cmd = f"am start -n {package}"
    out, err, rc = _sh(cmd)
    
    if rc == 0:
        logger.info(f"APP_LAUNCHED: {app_name}")
        return f"✅ Launched {app_name}."
    else:
        logger.error(f"APP_LAUNCH_FAILED: {app_name} | err={err}")
        return f"❌ Failed to launch {app_name}: {err}"

if __name__ == "__main__":
    print("Testing app_launch...")
    print(run({"app": "chrome"}))
