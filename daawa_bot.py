import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from dotenv import load_dotenv
import os

# Aladhan
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

# In-memory storage
user_data = {}  

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
        "Use the menu below:",
        reply_markup=get_main_keyboard()
    )


# ====================== SET LOCATION ======================
@dp.message(lambda msg: msg.text == "📍 Set My Location")
async def ask_for_location(message: types.Message):
    await message.answer(
        "📍 Please send your city and country in this format:\n\n"
        "<code>Khouribga, Morocco</code>\n"
        "<code>London, United Kingdom</code>\n"
        "<code>New York, USA</code>",
        reply_markup=ReplyKeyboardRemove()
    )


# This handler now ONLY triggers if user is NOT pressing a main menu button
@dp.message()
async def handle_any_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()

    # Ignore main menu buttons
    main_buttons = {
        "🕌 Today's Prayer Times",
        "🕒 Next Prayer",
        "📍 Set My Location",
        "⚙️ Settings"
    }

    if text in main_buttons:
        return  # Let the specific handlers handle these

    # If we reach here → user is sending location
    try:
        if "," in text:
            city, country = [x.strip() for x in text.split(",", 1)]
        else:
            city = text
            country = ""

        user_data[user_id] = {
            "city": city,
            "country": country,
            "method": 5  # Muslim World League by default
        }

        await message.answer(
            f"✅ Location saved successfully!\n\n"
            f"📍 City: <b>{city}</b>\n"
            f"🌍 Country: <b>{country or 'Not specified'}</b>\n\n"
            "Now you can check prayer times.",
            reply_markup=get_main_keyboard()
        )
    except Exception:
        await message.answer("❌ Sorry, I couldn't understand that.\n"
                             "Please send location like: <code>City, Country</code>")


# ====================== TODAY'S PRAYER TIMES ======================
@dp.message(lambda msg: msg.text == "🕌 Today's Prayer Times")
async def today_prayer_times(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_data or "city" not in user_data[user_id]:
        await message.answer("⚠️ Please set your location first using the button '📍 Set My Location'")
        return

    data = user_data[user_id]
    city = data["city"]
    country = data.get("country", "")

    await message.answer("⏳ Fetching latest prayer times...")

    try:
        timings = client.get_timings_by_city(
            city=city,
            country=country,
            method=data.get("method", 5)
        )

        text = f"🕌 <b>Prayer Times Today</b>\n\n"
        text += f"📍 {city}" + (f", {country}" if country else "") + "\n\n"

        prayers = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]

        for p in prayers:
            if hasattr(timings, p.lower()):
                t = getattr(timings, p.lower())
                text += f"<b>{p}</b>: {t}\n"

        await message.answer(text)

    except Exception as e:
        logging.error(e)
        await message.answer("❌ Could not fetch prayer times.\n"
                             "Please make sure the city name is correct.")


# ====================== OTHER BUTTONS ======================
@dp.message(lambda msg: msg.text == "🕒 Next Prayer")
async def next_prayer(message: types.Message):
    await message.answer("🕒 Next Prayer feature coming soon In sha Allah...")

@dp.message(lambda msg: msg.text == "⚙️ Settings")
async def settings(message: types.Message):
    await message.answer("⚙️ Settings will be available soon.")


if __name__ == "__main__":
    print("🚀 Da3wa Bot is running...")
    asyncio.run(dp.start_polling(bot))
    