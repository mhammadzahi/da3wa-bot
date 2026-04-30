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

user_data = {}   # {user_id: {"city": , "country": , "method": 5}}


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


@dp.message(F.text == "📍 Set My Location")
async def ask_location(message: types.Message):
    await message.answer(
        "📍 Send your city and country like this:\n\n"
        "<code>Casablanca, Morocco</code>\n"
        "<code>London, United Kingdom</code>",
        reply_markup=ReplyKeyboardRemove()
    )


# Handle location input
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


# ====================== TODAY'S PRAYER TIMES (Improved) ======================
@dp.message(F.text == "🕌 Today's Prayer Times")
async def show_prayer_times(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_data or "city" not in user_data[user_id]:
        await message.answer("⚠️ Please set your location first.")
        return

    data = user_data[user_id]
    city = data["city"]
    country = data.get("country", "")

    await message.answer("⏳ Fetching prayer times...")

    try:
        async with httpx.AsyncClient() as client:
            url = "https://api.aladhan.com/v1/timingsByCity"
            params = {
                "city": city,
                "country": country,
                "method": 5,           # 5 = Muslim World League (good default)
                "school": 0            # 0 = Shafi'i
            }

            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            if data.get("code") != 200:
                raise Exception(data.get("status"))

            timings = data["data"]["timings"]

            text = f"🕌 <b>Prayer Times Today</b>\n\n"
            text += f"📍 {city}" + (f", {country}" if country else "") + "\n\n"

            prayers = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]

            for prayer in prayers:
                time = timings.get(prayer, "N/A")
                text += f"<b>{prayer}</b>: {time}\n"

            await message.answer(text)

    except Exception as e:
        logging.error(f"Prayer time error: {e}")
        await message.answer(
            "❌ Could not fetch prayer times.\n\n"
            "Tips:\n"
            "• Try a bigger nearby city (e.g. Casablanca instead of Khouribga)\n"
            "• Check spelling\n"
            "• Try without country first"
        )


@dp.message(F.text == "🕒 Next Prayer")
async def next_prayer(message: types.Message):
    await message.answer("🕒 Next Prayer feature coming soon In sha Allah...")

@dp.message(F.text == "⚙️ Settings")
async def settings(message: types.Message):
    await message.answer("⚙️ Settings coming soon...")


if __name__ == "__main__":
    print("🚀 Da3wa Bot is running...")
    asyncio.run(dp.start_polling(bot))
    