import asyncio
import logging
import httpx

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from dotenv import load_dotenv
import os

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
        "Welcome to <b>Da3wa Bot</b>",
        reply_markup=get_main_keyboard()
    )


@dp.message(F.text == "📍 Set My Location")
async def ask_location(message: types.Message):
    await message.answer(
        "📍 Send your city and country:\n\n"
        "<code>Casablanca, Morocco</code>\n"
        "<code>Dubai, UAE</code>",
        reply_markup=ReplyKeyboardRemove()
    )


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
        async with httpx.AsyncClient(follow_redirects=True) as client:   # ← This fixes the 302
            resp = await client.get(
                "https://api.aladhan.com/v1/timingsByCity",
                params={
                    "city": city,
                    "country": country,
                    "method": 5,      # Muslim World League
                    "school": 0       # Shafi
                },
                timeout=12.0
            )

            data_json = resp.json()

            if data_json.get("code") != 200:
                raise Exception(f"API Error: {data_json.get('status')}")

            timings = data_json["data"]["timings"]

            text = f"🕌 <b>Prayer Times for Today</b>\n\n"
            text += f"📍 {city}" + (f", {country}" if country else "") + "\n\n"

            for prayer in ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]:
                time = timings.get(prayer, "N/A")
                text += f"<b>{prayer}</b>: {time}\n"

            await message.answer(text)

    except Exception as e:
        logging.error(f"Prayer time error: {e}")
        await message.answer(
            "❌ Could not fetch prayer times.\n\n"
            "Try these major cities:\n"
            "• Casablanca, Morocco\n"
            "• Rabat, Morocco\n"
            "• Dubai, UAE\n"
            "• London, United Kingdom"
        )


@dp.message(F.text == "🕒 Next Prayer")
async def next_prayer(message: types.Message):
    await message.answer("🕒 Next Prayer feature coming soon In sha Allah...")


@dp.message(F.text == "⚙️ Settings")
async def settings(message: types.Message):
    await message.answer("⚙️ Settings coming soon...")


# General handler for location (MUST stay last)
@dp.message()
async def handle_location_input(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()

    if text in ["🕌 Today's Prayer Times", "🕒 Next Prayer", "📍 Set My Location", "⚙️ Settings"]:
        return

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
        await message.answer("❌ Please send as: <code>City, Country</code>")


if __name__ == "__main__":
    print("🚀 Da3wa Bot is running...")
    asyncio.run(dp.start_polling(bot))
    