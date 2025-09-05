import os
import asyncio
import threading
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

import requests
from flask import Flask
from telebot import TeleBot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ===============================
# Settings
# ===============================
BOT_TOKEN = os.environ.get("7836209169:AAG6XlOv_t8CjwfEvUq_IS7E-igTKiQjxg8")      # Telegram bot token
CHANNEL_ID = os.environ.get("@VIRAXcpl")    # @channel_username or chat_id
UPDATE_INTERVAL = 60  # seconds (every minute)

state = {}  # store message_id

# ===============================
# Web server for Uptime Robot
# ===============================
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running!"

def run_webserver():
    web_app.run(host="0.0.0.0", port=5000)

threading.Thread(target=run_webserver).start()

# ===============================
# Simple Bot (pyTelegramBotAPI)
# ===============================
simple_bot = TeleBot(BOT_TOKEN)

@simple_bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        "با سلام و احترام،\n\n"
        "این ربات به صورت انحصاری تحت نظارت گروه ویراکس طراحی و راه‌اندازی گردیده است.\n"
        "جهت دریافت آخرین اخبار و دسترسی به محتوای اصلی، لطفاً به کانال رسمی ما بپیوندید:\n"
        "👉 @ViraxVip\n\n"
        "––––––––––––––––––––––––––––––––––\n\n"
        "Dear User,\n\n"
        "This bot has been exclusively developed and operated under the supervision of the Virax Group.\n"
        "For the latest updates and access to the main content, please join our official channel:\n"
        "👉 @ViraxVip"
    )
    simple_bot.send_message(message.chat.id, welcome_text)

def run_simple_bot():
    simple_bot.polling()

threading.Thread(target=run_simple_bot).start()

# ===============================
# Bitcoin Price Bot Functions
# ===============================
def fetch_price() -> Decimal:
    r = requests.get("https://api.coingecko.com/api/v3/simple/price",
                     params={"ids": "bitcoin", "vs_currencies": "usd"})
    r.raise_for_status()
    return Decimal(str(r.json()["bitcoin"]["usd"]))

def format_price(val: Decimal) -> str:
    q = Decimal("0.01")
    return f"{val.quantize(q, rounding=ROUND_HALF_UP):,}"

def make_text(price: Decimal) -> str:
    now = datetime.now(timezone.utc)
    baku_offset = 4
    baku_time = now.timestamp() + (baku_offset * 3600)
    dt_str = datetime.fromtimestamp(baku_time).strftime("%Y-%m-%d %H:%M:%S")
    return f"💰 Bitcoin Live Price\n\n📈 BTC: ${format_price(price)} USD\n🕒 Last Updated: {dt_str} (Asia/Baku)"

async def ensure_message(app) -> int:
    if state.get("message_id"):
        return state["message_id"]
    price = fetch_price()
    text = make_text(price)
    price_button_text = f"💰 ${format_price(price)}"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(price_button_text, callback_data="price")]])
    msg = await app.bot.send_message(chat_id=CHANNEL_ID, text=text, reply_markup=keyboard)
    state["message_id"] = msg.message_id
    return msg.message_id

async def updater(app):
    while True:
        try:
            msg_id = await ensure_message(app)
            price = fetch_price()
            text = make_text(price)
            price_button_text = f"💰 ${format_price(price)}"
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(price_button_text, callback_data="price")]])
            await app.bot.edit_message_text(chat_id=CHANNEL_ID, message_id=msg_id, text=text, reply_markup=keyboard)
        except Exception as e:
            print("Error:", e)
        await asyncio.sleep(UPDATE_INTERVAL)

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is now active!")

# ===============================
# Bitcoin Price Bot Main
# ===============================
async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    asyncio.create_task(updater(app))
    await app.initialize()
    await app.start()
    print("Bitcoin Bot started")
    await asyncio.Event().wait()
    await app.stop()
    await app.shutdown()

if __name__ == "__main__":
    print("Starting combined bot...")
    asyncio.run(main())
