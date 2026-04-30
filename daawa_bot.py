import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from dotenv import load_dotenv
import os

import aladhan

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN not found in .env file!")

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

user_data = {}   # {user_id: {"city": , "country": , "method": 5}}
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
        "Welcome to <b>Da3wa Bot</b> — Your Salat Reminder\n\n"
        "Choose from the menu below:",
        reply_markup=get_main_keyboard()
    )


# ====================== SET LOCATION ======================
@dp.message(Text(text="📍 Set My Location"))
async def ask_for_location(message: types.Message):
    await message.answer(
        "📍 Send your city and country like this:\n\n"
        "<code>Khouribga, Morocco</code>\n"
        "<code>London, United Kingdom</code>",
        reply_markup=ReplyKeyboardRemove()
    )


@dp.message()
async def handle_location_input(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()

    # Prevent main menu buttons from being treated as location
    if text in ["🕌 Today's Prayer Times", "🕒 Next Prayer", "📍 Set My Location", "⚙️ Settings"]:
        return

    # Process as location input
    try:
        if "," in text:
            city, country = [x.strip() for x in text.split(",", 1)]
        else:
            city = text
            country = ""

        user_data[user_id] = {"city": city, "country": country, "method": 5}

        await message.answer(
            f"✅ <b>Location Saved!</b>\n\n"
            f"📍 City: <b>{city}</b>\n"
            f"🌍 Country: <b>{country or 'Not specified'}</b>\n\n"
            "You can now view prayer times.",
            reply_markup=get_main_keyboard()
        )
    except:
        await message.answer("❌ Please send location in format: <code>City, Country</code>")


# ====================== TODAY'S PRAYER TIMES ======================
@dp.message(Text(text="🕌 Today's Prayer Times"))
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
        timings = client.get_timings_by_city(city=city, country=country, method=5)

        text = f"🕌 <b>Prayer Times for Today</b>\n\n"
        text += f"📍 {city}" + (f", {country}" if country else "") + "\n\n"

        prayers = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]

        for prayer in prayers:
            if hasattr(timings, prayer.lower()):
                time = getattr(timings, prayer.lower())
                text += f"<b>{prayer}</b>: {time}\n"

        await message.answer(text)

    except Exception as e:
        logging.error(e)
        await message.answer("❌ Failed to get prayer times.\nMake sure the city name is correct.")


# ====================== OTHER FEATURES (Placeholders) ======================
@dp.message(Text(text="🕒 Next Prayer"))
async def next_prayer(message: types.Message):
    await message.answer("🕒 Next Prayer feature is coming soon In sha Allah...")


@dp.message(Text(text="⚙️ Settings"))
async def settings(message: types.Message):
    await message.answer("⚙️ Settings menu coming soon...")


if __name__ == "__main__":
    print("🚀 Da3wa Bot is running...")
    asyncio.run(dp.start_polling(bot))
