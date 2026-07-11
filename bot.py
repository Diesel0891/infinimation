#!/data/data/com.termux/files/usr/bin/env python3
"""
Infinimation Telegram Bot Interface
Wires python-telegram-bot v21.x to the engine.
"""
import os
import sys
import yaml
import logging
import asyncio
from pathlib import Path

# Ensure project root is on path
BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import engine

# Logging
logging.basicConfig(
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("infinimation.bot")

# Load config
CONFIG_PATH = BASE_DIR / "config" / "engine.yaml"
with open(CONFIG_PATH, 'r') as f:
    cfg = yaml.safe_load(f)

TELEGRAM_CFG = cfg.get('telegram', {})
TOKEN = TELEGRAM_CFG.get('token')
ALLOWED_USERNAMES = [u.lower() for u in TELEGRAM_CFG.get('allowed_usernames', [])]

if not TOKEN or TOKEN == 'YOUR_BOT_TOKEN_HERE':
    logger.error("Telegram token not configured. Exiting.")
    sys.exit(1)

# ── Handlers ──────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Infinimation is online.*\n"
        "Send me any command and I'll execute it.\n"
        "Type /help for available commands.",
        parse_mode='Markdown'
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Available commands (natural language):\n"
        "• scrape <url> <class> — Web scrape\n"
        "• open <app> — Launch app\n"
        "• status — System status\n"
        "• send message to <name> — Messaging (pending)\n"
        "• screenshot — Take screenshot (pending)\n"
        "• Any other text → LLM fallback (pending)"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    
    logger.info(f"MSG from {user.username or user.id}: {text[:50]}")
    
    # Optional whitelist
    if ALLOWED_USERNAMES and user.username and user.username.lower() not in ALLOWED_USERNAMES:
        await update.message.reply_text("⛔ Unauthorized.")
        return
    
    # Execute via engine
    result = engine.execute_command(text)
    
    response = result['output']
    if not result['success']:
        response = f"⚠️ {response}"
    
    await update.message.reply_text(response)

def main():
    # Python 3.14 fix: explicitly create event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot polling started.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
