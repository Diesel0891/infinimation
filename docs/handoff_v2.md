INFINIMATION PROJECT — HANDOFF SUMMARY V2
Date: 2026-07-11
Technical Lead: Kimi K2.6
Hands: Diesel0891
Repo: https://github.com/Diesel0891/infinimation

PROJECT OVERVIEW
Infinimation is a zero-cost, self-hosted Android automation engine running inside Termux on a Huawei Mate 9 (Android 9, EMUI 9.1, 4GB RAM, aarch64). It is controlled via Telegram bot commands and executes web scraping, app launching, system monitoring, and eventually UI automation (screen tapping, form filling) via Shizuku. The architecture is modular (skill-based), device-agnostic, and designed for future monetization through a premium accessibility-service companion app. All code is version-controlled on GitHub.

CORE CONSTRAINTS
Primary device: Huawei Mate 9, Android 9, 4GB RAM, no root, no PC access ever.
Secondary device: Android 13 phone with 3GB RAM, used ONLY as a Shizuku bootstrap appliance. It stays in a drawer. The Mate 9 sends UI automation commands to it over local Wi-Fi when needed. When the user upgrades to an Android 11+ device in the future, the Android 13 device retires permanently and everything collapses to single-device operation.
Shizuku on Android 9 requires a one-time ADB activation from a PC. Since no PC is available, the Android 13 device (which supports Wireless ADB pairing natively) will host the Shizuku server. The Mate 9 will SSH or HTTP-relay ADB commands to it.
Local LLM: Qwen 2.5 1.5B Q4_K_M GGUF via llama.cpp, loaded on-demand and unloaded immediately after inference to preserve RAM. Regex intent classifier handles 90 percent of commands to avoid LLM overhead.

ARCHITECTURE
Layer 1: Telegram Bot (python-telegram-bot v21.11.1, async) receives plain text commands.
Layer 2: Intent Classifier (regex pattern matcher) routes to known skills instantly.
Layer 3: Skill Engine dynamically loads Python modules from the skills directory.
Layer 4: LLM Fallback (llama.cpp subprocess) handles ambiguous natural language only when regex fails.
Layer 5: Execution modules perform web scraping (requests + BeautifulSoup), app launching (Android intents), system queries (termux-api), and UI automation (Shizuku relay to Android 13 device).

PROVEN STACK (EXACT VERSIONS)
Python 3.14.6 (installed via pkg install python)
python-telegram-bot 21.11.1 (upgraded from 20.7 due to Python 3.14 __slots__ compatibility)
httpx 0.28.1
requests 2.31.0
beautifulsoup4 4.12.2
PyYAML 6.0.1
termux-api 0.59.1-1
cronie (installed)
git (installed)

WHAT HAS BEEN BUILT
1. Project directory at ~/infinimation with modular structure: skills/, config/, logs/, models/, bin/, docs/
2. engine.py — core orchestrator with regex intent classifier, dynamic skill loader, and execution loop. Uses RotatingFileHandler for logs. Self-test at bottom validates scraping, app launching, intent matching, and LLM fallback routing. The intent classifier maps regex patterns to skill names: scrape -> web_scrape, open <app> -> app_launch, send message to <contact> -> send_message, screenshot -> take_screenshot, status -> system_status, help -> show_help.
3. bot.py — Telegram bot interface. Wires python-telegram-bot v21.11.1 to the engine. Handles /start, /help, and all text messages. Includes Python 3.14 event loop fix (explicitly creates loop if missing). Logs all messages and routes them through engine.execute_command(). Returns skill output or error messages to Telegram chat.
4. skills/web_scrape.py — scrapes static HTML by URL and optional CSS class. Returns title and preview or extracted element texts. Uses requests + BeautifulSoup.
5. skills/app_launch.py — launches Android apps via am start intents using known package mappings (WhatsApp, Chrome, Settings, Camera, Telegram). Logs APP_LAUNCHED events.
6. skills/system_status.py — reports battery, storage, and RAM via termux-battery-status and proc meminfo.
7. skills/show_help.py — dynamically discovers all .py files in skills/ directory, extracts first-line docstring descriptions, and returns a formatted markdown list of available capabilities.
8. skills/send_message.py — Phase 1: Intent-based pre-fill. Extracts contact name and message body from natural language via regex. Launches SMS composer or WhatsApp share intent with pre-filled content. User taps Send manually. Phase 2 (pending): Shizuku UI automation will auto-tap when available.
9. skills/take_screenshot.py — Saves screenshots to ~/storage/shared/Pictures/Screenshots with timestamp filenames. Uses /system/bin/screencap -p (native Android binary, verified working on Mate 9). Falls back to termux-screenshot if available, or Shizuku relay if neither works.
10. config/engine.yaml — configuration with Telegram bot token (live), LLM model path placeholder, Shizuku host IP placeholder (192.168.1.100:8022), and skill auto-load settings.
11. requirements.txt — pinned dependency versions reflecting the actual installed stack.
12. .gitignore — excludes sensitive configs, logs, and model files.
13. GitHub repository initialized and pushed to https://github.com/Diesel0891/infinimation

VERIFIED WORKING (LIVE TELEGRAM BOT)
The bot is running and polling successfully. Confirmed working commands via Telegram:
- /start -> Returns welcome message
- /help -> Returns available commands list
- scrape https://example.com prices -> Returns title and preview
- open whatsapp -> Launches WhatsApp (APP_LAUNCHED logged)
- open chrome -> Launches Chrome (APP_LAUNCHED logged)
- status -> Returns battery, storage, RAM info
- help -> Returns dynamic skill list
- send message to john hello there -> Opens SMS composer pre-filled
- send message to john -> Returns prompt asking for message body
- screenshot -> Captures screen via /system/bin/screencap and saves to Gallery

CRITICAL MILESTONE: SCREENCAP NATIVE ACCESS
The unrooted Mate 9 can execute /system/bin/screencap directly from Termux without root or Shizuku. This was discovered during take_screenshot skill development. The binary writes PNG files successfully to shared storage. This is a major capability unlock for UI automation and monitoring.

KNOWN ISSUES RESOLVED
1. Python 3.14.6 compatibility with python-telegram-bot v20.7: Upgraded to v21.11.1 which resolves the __slots__ attribute assignment error in Updater.
2. Python 3.14 event loop removal: bot.py now explicitly creates an event loop via asyncio.new_event_loop() if get_event_loop() raises RuntimeError.
3. Stale bot_token field in engine.yaml: Removed during Step 4 configuration.
4. GitHub repo naming: Initially created with trailing hyphen (infinimation-), renamed to infinimation.
5. termux-screenshot missing: The termux-api package v0.59.1-1 does not include termux-screenshot. Fallback to /system/bin/screencap works perfectly.

KNOWN ISSUES OPEN
1. Python 3.14.6 is very new. PyYAML built from source successfully but monitor for compatibility issues with other packages.
2. GitHub Personal Access Token (REDACTED_PAT_REVOKE_AND_REPLACE) was exposed in terminal history. It should be revoked and replaced after this session.
3. Local LLM is not downloaded or integrated.
4. Shizuku is not installed on either device.
5. Cron jobs are not configured.
6. EMUI battery management has not been whitelisted for Termux or cronie.
7. The am start command in send_message.py may fail inside Termux sandbox for some intents. Works for basic app launching but SMS SENDTO may need Shizuku relay.
8. Bot token is visible in engine.yaml. The file is gitignored but exists locally. Consider moving to environment variable.

FILE STRUCTURE
~/infinimation/
  engine.py
  bot.py
  requirements.txt
  .gitignore
  config/
    engine.yaml
  skills/
    web_scrape.py
    app_launch.py
    system_status.py
    show_help.py
    send_message.py
    take_screenshot.py
  logs/
    engine.log
  models/
    .gitkeep
  bin/
  docs/

HOW TO VERIFY STATE
cd ~/infinimation
python engine.py
This should print four test results with no errors.

cd ~/infinimation
python bot.py
This should start polling and log Bot polling started.

HOW TO PUSH CHANGES TO GITHUB
cd ~/infinimation
git add .
git commit -m "descriptive message"
git push origin main

If authentication fails, the remote may need updating. The remote was set with an embedded PAT which will expire once revoked. Future pushes should use a new PAT or SSH key.

IMMEDIATE NEXT STEPS
Step 6: Local LLM Integration
- Download llama.cpp aarch64 binary or build from source in Termux
- Download Qwen 2.5 1.5B Q4_K_M GGUF model to models/
- Create llm_interface.py that loads the model on-demand, runs inference, unloads
- Wire the LLM fallback in engine.py to call llm_interface.py when regex returns None
- Update config/engine.yaml llm.enabled to true

Step 7: Shizuku Bootstrap on Android 13 Device
- Install Shizuku on Android 13 device
- Pair via Wireless ADB (no PC needed on Android 13)
- Start Shizuku server
- Note the device IP address on local Wi-Fi
- Update config/engine.yaml shizuku_host with that IP
- Build a lightweight relay script on Android 13 to receive HTTP commands from Mate 9 and execute them via rish

Step 8: UI Automation Skills
- Build skills that use uiautomator dump via Shizuku relay to parse screen XML
- Implement dynamic text-based tapping (find element by text, calculate center coordinates, tap)
- Build form-filling skills that combine Chrome intents with UI automation fallback
- Leverage the verified /system/bin/screencap for visual verification

Step 9: Cron Scheduling
- Configure cronie to run periodic scrapes or health checks
- Ensure EMUI battery settings whitelist Termux and cronie

Step 10: Documentation and README
- Write a proper README.md for the GitHub repo
- Document setup instructions for future users
- Document the monetization path (open source core + premium accessibility app)

CRITICAL NOTES FOR A NEW SESSION
- Always use cd ~/infinimation before any command.
- Never ask the user to edit files. Use cat heredocs or sed commands in Termux.
- The Mate 9 has 4GB RAM. The LLM will consume about 1GB during inference. Always unload it after use.
- The Android 13 device is a temporary crutch. Do not architect the system to permanently depend on it.
- All file creation, edits, and deletions must be done via terminal commands.
- The user prefers one executable step at a time with confirmation before proceeding.
- Proven stacks only. No beta software.
- The ultimate goal is full autonomy: virtually anything the user does on phone or web should be achievable via plain language Telegram commands.
- /system/bin/screencap is available natively on the Mate 9 and works from Termux. This is a powerful capability for screenshot-based automation workflows.
- The Telegram bot is live and polling. Do not regenerate the bot token unless necessary.

END OF HANDOFF SUMMARY V2
