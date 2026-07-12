# Infinimation

Zero-cost, self-hosted Android automation engine. Runs inside Termux. Controlled via Telegram. Modular, device-agnostic, built for future monetization.

## What It Does

Send plain-language commands via Telegram. Your phone executes them:

- Web scraping
- App launching
- UI automation (tap, type, swipe)
- Screen reading
- System monitoring
- Screenshots
- Scheduled tasks

## Quick Start

1. Clone: `git clone https://github.com/Diesel0891/infinimation.git ~/infinimation`
2. Install: `cd ~/infinimation && pip install -r requirements.txt`
3. Configure: `cp config/engine.yaml.example config/engine.yaml` and fill in keys
4. Start Shizuku, verify with `rish -c "echo hello"`
5. Launch: `python3 bot.py`

## Architecture

Telegram Bot <-> Termux Engine <-> GitHub Repo
                    |
        +-----------+-----------+
        |           |           |
   Scraping    UI Automator   System Tools
   (BS4)       (Shizuku)      (Cron)

## LLM Providers

Cloud-first with automatic failover: Gemini -> Groq -> OpenRouter -> Ollama (deferred on low RAM).

## Skills

web_scrape, app_launch, ui_automation, read_screen, form_fill, system_status, send_message, take_screenshot, show_help

## Monetization

Open core (free) + premium accessibility-service companion app (future).

## License

MIT
