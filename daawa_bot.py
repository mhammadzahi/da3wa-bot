import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from dotenv import load_dotenv
import os

# Aladhan import
import aladhan

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN not found! Please create a .env file with your bot token.")

# Initialize bot and dispatcher
bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher()

# Logging
logging.basicConfig(level=logging.INFO)

# In-memory storage (user settings)
user_data = {}  # {user_id: {"city": str, "country": str, "method": int}}

# Create Aladhan client (synchronous for simplicity)
client = aladhan.Client()


def get_main_keyboard():
    keyboard = [
        [KeyboardButton(text="🕌 Today's Prayer Times")],
        [KeyboardButton(text="🕒 Next Prayer")],
        [KeyboardButton(text="📍 Set My Location")],
        [KeyboardButton(text="⚙️ Settings")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "🤲 <b>Assalamu alaikum wa rahmatullah</b>\n\n"
        "Welcome to <b>Da3wa Bot</b> — Your Personal Salat Reminder\n\n"
        "Use the buttons below to begin.",
        reply_markup=get_main_keyboard()
    )


# ====================== SET LOCATION ======================
@dp.message(lambda msg: msg.text == "📍 Set My Location")
async def ask_location(message: types.Message):
    await message.answer(
        "Please send your **City** and **Country** like this:\n\n"
        "<code>London, United Kingdom</code>\n"
        "<code>New York, USA</code>\n"
        "<code>Cairo, Egypt</code>",
        reply_markup=ReplyKeyboardRemove()
    )


@dp.message()
async def handle_location_input(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()

    try:
        if "," in text:
            city, country = [x.strip() for x in text.split(",", 1)]
        else:
            city = text
            country = ""

        user_data[user_id] = {
            "city": city,
            "country": country,
            "method": 5   # Default: Muslim World League
        }

        await message.answer(
            f"✅ Location saved!\n\n"
            f"📍 City: <b>{city}</b>\n"
            f"🌍 Country: <b>{country or 'Not specified'}</b>\n\n"
            "You can now get prayer times.",
            reply_markup=get_main_keyboard()
        )
    except Exception:
        await message.answer("❌ Invalid format. Please send as: City, Country")


# ====================== TODAY'S PRAYER TIMES ======================
@dp.message(lambda msg: msg.text == "🕌 Today's Prayer Times")
async def today_prayer_times(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_data or "city" not in user_data[user_id]:
        await message.answer("⚠️ Please set your location first using '📍 Set My Location'")
        return

    data = user_data[user_id]
    city = data["city"]
    country = data.get("country", "")

    await message.answer("⏳ Fetching prayer times...")

    try:
        timings = client.get_timings_by_city(city=city, country=country, method=data.get("method", 5))

        text = f"🕌 <b>Prayer Times for Today</b>\n\n"
        text += f"📍 {city}" + (f", {country}" if country else "") + "\n\n"

        prayer_order = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]

        for prayer in prayer_order:
            if hasattr(timings, prayer.lower()):
                time = getattr(timings, prayer.lower())
                text += f"<b>{prayer}</b>: {time}\n"

        await message.answer(text)
    except Exception as e:
        logging.error(e)
        await message.answer("❌ Failed to fetch prayer times. Please check your location or try again later.")


# ====================== NEXT PRAYER (Basic) ======================
@dp.message(lambda msg: msg.text == "🕒 Next Prayer")
async def next_prayer(message: types.Message):
    await message.answer("🕒 Next Prayer feature is coming soon In sha Allah...")


# ====================== SETTINGS (Placeholder) ======================
@dp.message(lambda msg: msg.text == "⚙️ Settings")
async def settings(message: types.Message):
    await message.answer("⚙️ Settings menu is under development.\n\n"
                         "Soon you will be able to change calculation method (MWL, Egyptian, etc.).")


if __name__ == "__main__":
    print("🚀 Da3wa Bot is starting...")
    asyncio.run(dp.start_polling(bot))
