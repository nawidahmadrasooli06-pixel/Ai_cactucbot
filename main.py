import asyncio
import logging
import os

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

# =========================
# تنظیمات
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN تنظیم نشده است.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()


# =========================
# منوی اصلی
# =========================

def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎨 طراحی بنر",
                    callback_data="banner"
                ),
                InlineKeyboardButton(
                    text="🎬 ساخت ویدیو",
                    callback_data="video"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👤 برند و پروفایل",
                    callback_data="brand"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏆 ساخت چالش",
                    callback_data="challenge"
                ),
                InlineKeyboardButton(
                    text="🚀 ساخت کمپین",
                    callback_data="campaign"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="ℹ️ درباره ربات",
                    callback_data="about"
                ),
            ],
        ]
    )


# =========================
# /start
# =========================

@dp.message(CommandStart())
async def start_handler(message: Message):

    name = message.from_user.first_name or "دوست من"

    text = (
        f"سلام <b>{name}</b> 👋\n\n"
        "به <b>CACTUC STUDIO</b> خوش آمدی.\n\n"
        "اینجا می‌تونی برای تلگرام "
        "بنر، ویدیو، برند و کمپین حرفه‌ای بسازی.\n\n"
        "👇 یکی از بخش‌ها رو انتخاب کن:"
    )

    await message.answer(
        text,
        reply_markup=main_menu()
    )


# =========================
# دکمه طراحی بنر
# =========================

@dp.callback_query(F.data == "banner")
async def banner_handler(callback: CallbackQuery):

    text = (
        "🎨 <b>استودیو طراحی بنر</b>\n\n"
        "نوع بنری که می‌خوای بسازی رو انتخاب کن:"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎂 تولد",
                    callback_data="banner_birthday"
                ),
                InlineKeyboardButton(
                    text="📢 تبلیغات",
                    callback_data="banner_ad"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🛍 فروش",
                    callback_data="banner_shop"
                ),
                InlineKeyboardButton(
                    text="📣 معرفی کانال",
                    callback_data="banner_channel"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎵 موزیک",
                    callback_data="banner_music"
                ),
                InlineKeyboardButton(
                    text="💎 Premium / Stars",
                    callback_data="banner_premium"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✏️ طراحی دلخواه",
                    callback_data="banner_custom"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔙 برگشت",
                    callback_data="home"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard
    )

    await callback.answer()


# =========================
# دکمه ویدیو
# =========================

@dp.callback_query(F.data == "video")
async def video_handler(callback: CallbackQuery):

    text = (
        "🎬 <b>استودیو ویدیو</b>\n\n"
        "به‌زودی می‌تونی عکس، متن و اطلاعاتت رو بدی "
        "و یک ویدیوی آماده برای تلگرام دریافت کنی.\n\n"
        "این بخش در مرحله بعد فعال می‌شه."
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 برگشت",
                    callback_data="home"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard
    )

    await callback.answer()


# =========================
# برند و پروفایل
# =========================

@dp.callback_query(F.data == "brand")
async def brand_handler(callback: CallbackQuery):

    text = (
        "👤 <b>استودیو برند</b>\n\n"
        "اینجا بعداً می‌تونی نام برند، عکس، "
        "رنگ و موضوع فعالیتت رو وارد کنی "
        "تا برایت یک هویت تصویری هماهنگ ساخته بشه."
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 برگشت",
                    callback_data="home"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard
    )

    await callback.answer()


# =========================
# چالش
# =========================

@dp.callback_query(F.data == "challenge")
async def challenge_handler(callback: CallbackQuery):

    text = (
        "🏆 <b>استودیو چالش</b>\n\n"
        "اینجا صاحب کانال می‌تونه "
        "یک مسابقه حرفه‌ای بسازه، "
        "جایزه تعیین کنه و شرکت‌کننده‌ها رو مدیریت کنه.\n\n"
        "این بخش در مرحله بعد ساخته می‌شه."
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 برگشت",
                    callback_data="home"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard
    )

    await callback.answer()


# =========================
# کمپین
# =========================

@dp.callback_query(F.data == "campaign")
async def campaign_handler(callback: CallbackQuery):

    text = (
        "🚀 <b>استودیو کمپین</b>\n\n"
        "اینجا بعداً می‌تونی یک کمپین کامل "
        "برای کانال یا کسب‌وکارت بسازی:\n\n"
        "🖼 بنر\n"
        "🎬 ویدیو\n"
        "📱 نسخه استوری\n"
        "📝 متن تبلیغاتی\n"
        "🔗 لینک\n\n"
        "همه در یک پروژه."
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 برگشت",
                    callback_data="home"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard
    )

    await callback.answer()


# =========================
# درباره
# =========================

@dp.callback_query(F.data == "about")
async def about_handler(callback: CallbackQuery):

    text = (
        "ℹ️ <b>درباره CACTUC STUDIO</b>\n\n"
        "یک استودیوی فارسی برای ساخت "
        "محتوای حرفه‌ای مخصوص تلگرام.\n\n"
        "🎨 طراحی\n"
        "🎬 ویدیو\n"
        "👤 برند\n"
        "🏆 چالش\n"
        "🚀 کمپین"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 برگشت",
                    callback_data="home"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard
    )

    await callback.answer()


# =========================
# برگشت به خانه
# =========================

@dp.callback_query(F.data == "home")
async def home_handler(callback: CallbackQuery):

    text = (
        "🏠 <b>CACTUC STUDIO</b>\n\n"
        "چه کاری می‌خوای انجام بدی؟"
    )

    await callback.message.edit_text(
        text,
        reply_markup=main_menu()
    )

    await callback.answer()


# =========================
# صفحه سلامت برای Render
# =========================

async def health(request):
    return web.Response(
        text="CACTUC STUDIO is running."
    )


async def start_web_server():

    app = web.Application()

    app.router.add_get(
        "/",
        health
    )

    app.router.add_get(
        "/health",
        health
    )

    runner = web.AppRunner(app)

    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        PORT
    )

    await site.start()

    logging.info(
        f"Health server started on port {PORT}"
    )


# =========================
# اجرای ربات
# =========================

async def main():

    await start_web_server()

    logging.info("CACTUC STUDIO starting...")

    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("CACTUC STUDIO stopped.")
