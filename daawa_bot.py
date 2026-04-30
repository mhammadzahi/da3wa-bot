import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
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

user_data = {}
client = aladhan.Client()


def get_main_keyboard():
    kb = [
        [KeyboardButton(text="🕌 Today's Prayer Times")],
        [KeyboardButton(text="🕒 Next Prayer")],
        [KeyboardButton(text="📍 Set My Location")],
        [KeyboardButton(text="⚙️ Settings")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🤲 <b>Assalamu alaikum wa rahmatullah</b>\n\n"
        "Welcome to <b>Da3wa Bot</b> — Your Salat Reminder",
        reply_markup=get_main_keyboard()
    )


# 1. Set Location Button
@dp.message(F.text == "📍 Set My Location")
async def ask_location(message: types.Message):
    await message.answer(
        "📍 Please send your city and country:\n\n"
        "<code>Khouribga, Morocco</code>",
        reply_markup=ReplyKeyboardRemove()
    )


# 2. Today's Prayer Times Button  ← This must come BEFORE the general handler
@dp.message(F.text == "🕌 Today's Prayer Times")
async def show_prayer_times(message: types.Message):
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

        response = f"🕌 <b>Prayer Times for Today</b>\n\n"
        response += f"📍 {city}" + (f", {country}" if country else "") + "\n\n"

        prayers = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]

        for prayer in prayers:
            if hasattr(timings, prayer.lower()):
                time = getattr(timings, prayer.lower())
                response += f"<b>{prayer}</b>: {time}\n"

        await message.answer(response)

    except Exception as e:
        logging.error(e)
        await message.answer("❌ Failed to fetch prayer times.\nPlease check the city name.")


# 3. Other buttons
@dp.message(F.text == "🕒 Next Prayer")
async def next_prayer(message: types.Message):
    await message.answer("🕒 Next Prayer feature coming soon In sha Allah...")

@dp.message(F.text == "⚙️ Settings")
async def settings(message: types.Message):
    await message.answer("⚙️ Settings coming soon...")


# 4. General handler for location input - MUST BE LAST
@dp.message()
async def handle_location_input(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()

    # Ignore main menu buttons
    if text in ["🕌 Today's Prayer Times", "🕒 Next Prayer", "📍 Set My Location", "⚙️ Settings"]:
        return

    # Process location
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
            f"🌍 Country: <b>{country or 'Not specified'}</b>",
            reply_markup=get_main_keyboard()
        )
    except:
        await message.answer("❌ Please send in this format:\n<code>City, Country</code>")


if __name__ == "__main__":
    print("🚀 Da3wa Bot is running...")
    asyncio.run(dp.start_polling(bot))
    