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

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
PORT = int(os.getenv("PORT", "10000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN تنظیم نشده است.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()


def main_menu(user_id: int):
    buttons = [
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
            )
        ]
    ]

    if user_id == OWNER_ID:
        buttons.append([
            InlineKeyboardButton(
                text="👑 پنل مالک",
                callback_data="owner_panel"
            )
        ])

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


@dp.message(CommandStart())
async def start_handler(message: Message):

    user_id = message.from_user.id
    name = message.from_user.first_name or "دوست من"

    text = (
        f"سلام <b>{name}</b> 👋\n\n"
        "<b>CACTUC STUDIO</b>\n"
        "استودیوی فارسی تولید محتوای تلگرام.\n\n"
        "👇 چه کاری می‌خوای انجام بدی؟"
    )

    await message.answer(
        text,
        reply_markup=main_menu(user_id)
    )


@dp.callback_query(F.data == "owner_panel")
async def owner_panel(callback: CallbackQuery):

    if callback.from_user.id != OWNER_ID:
        await callback.answer(
            "⛔ این بخش فقط برای مالک ربات است.",
            show_alert=True
        )
        return

    text = (
        "👑 <b>پنل مالک CACTUC STUDIO</b>\n\n"
        "وضعیت ربات: 🟢 فعال\n"
        f"شناسه مالک: <code>{OWNER_ID}</code>\n\n"
        "بخش‌های مدیریتی بعداً از همین‌جا اضافه می‌شوند."
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 آمار",
                    callback_data="owner_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ تنظیمات",
                    callback_data="owner_settings"
                )
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


@dp.callback_query(F.data == "owner_stats")
async def owner_stats(callback: CallbackQuery):

    if callback.from_user.id != OWNER_ID:
        await callback.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True
        )
        return

    await callback.answer()

    await callback.message.edit_text(
        "📊 <b>آمار ربات</b>\n\n"
        "این بخش در نسخه بعدی با دیتابیس واقعی فعال می‌شود.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 پنل مالک",
                        callback_data="owner_panel"
                    )
                ]
            ]
        )
    )


@dp.callback_query(F.data == "owner_settings")
async def owner_settings(callback: CallbackQuery):

    if callback.from_user.id != OWNER_ID:
        await callback.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True
        )
        return

    await callback.answer()

    await callback.message.edit_text(
        "⚙️ <b>تنظیمات مالک</b>\n\n"
        "تنظیمات پیشرفته در مرحله اتصال دیتابیس و سرویس‌های تولید محتوا اضافه می‌شود.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 پنل مالک",
                        callback_data="owner_panel"
                    )
                ]
            ]
        )
    )


@dp.callback_query(F.data == "banner")
async def banner_handler(callback: CallbackQuery):

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
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛍 فروش",
                    callback_data="banner_shop"
                ),
                InlineKeyboardButton(
                    text="📣 معرفی کانال",
                    callback_data="banner_channel"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎵 موزیک",
                    callback_data="banner_music"
                ),
                InlineKeyboardButton(
                    text="💎 Premium / Stars",
                    callback_data="banner_premium"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ طراحی دلخواه",
                    callback_data="banner_custom"
                )
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
        "🎨 <b>استودیو طراحی بنر</b>\n\n"
        "نوع بنر را انتخاب کن:",
        reply_markup=keyboard
    )

    await callback.answer()


@dp.callback_query(F.data == "video")
async def video_handler(callback: CallbackQuery):

    await callback.message.edit_text(
        "🎬 <b>استودیو ویدیو</b>\n\n"
        "اینجا عکس، متن و اطلاعات پروژه را می‌گیریم "
        "و بعد به موتور واقعی تولید ویدیو وصل می‌کنیم.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 برگشت",
                        callback_data="home"
                    )
                ]
            ]
        )
    )

    await callback.answer()


@dp.callback_query(F.data == "brand")
async def brand_handler(callback: CallbackQuery):

    await callback.message.edit_text(
        "👤 <b>برند و پروفایل</b>\n\n"
        "نام برند، عکس، رنگ و موضوع فعالیت را می‌گیریم "
        "و هویت تصویری یکپارچه برای پروژه می‌سازیم.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 برگشت",
                        callback_data="home"
                    )
                ]
            ]
        )
    )

    await callback.answer()


@dp.callback_query(F.data == "challenge")
async def challenge_handler(callback: CallbackQuery):

    await callback.message.edit_text(
        "🏆 <b>استودیو چالش</b>\n\n"
        "ساخت مسابقه، ثبت شرکت‌کنندگان، امتیازدهی "
        "و اعلام برندگان در نسخه کامل فعال می‌شود.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 برگشت",
                        callback_data="home"
                    )
                ]
            ]
        )
    )

    await callback.answer()


@dp.callback_query(F.data == "campaign")
async def campaign_handler(callback: CallbackQuery):

    await callback.message.edit_text(
        "🚀 <b>استودیو کمپین</b>\n\n"
        "ساخت یک بسته کامل تبلیغاتی شامل بنر، ویدیو، "
        "متن و لینک در این بخش انجام می‌شود.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 برگشت",
                        callback_data="home"
                    )
                ]
            ]
        )
    )

    await callback.answer()


@dp.callback_query(F.data == "about")
async def about_handler(callback: CallbackQuery):

    await callback.message.edit_text(
        "ℹ️ <b>CACTUC STUDIO</b>\n\n"
        "یک استودیوی فارسی برای تولید محتوای حرفه‌ای "
        "مخصوص تلگرام.\n\n"
        "🎨 طراحی\n"
        "🎬 ویدیو\n"
        "👤 برند\n"
        "🏆 چالش\n"
        "🚀 کمپین",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 برگشت",
                        callback_data="home"
                    )
                ]
            ]
        )
    )

    await callback.answer()


@dp.callback_query(F.data == "home")
async def home_handler(callback: CallbackQuery):

    await callback.message.edit_text(
        "🏠 <b>CACTUC STUDIO</b>\n\n"
        "چه کاری می‌خوای انجام بدی؟",
        reply_markup=main_menu(callback.from_user.id)
    )

    await callback.answer()


async def health(request):
    return web.Response(
        text="CACTUC STUDIO is running."
    )


async def start_web_server():

    app = web.Application()

    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        PORT
    )

    await site.start()


async def main():

    await start_web_server()

    logging.info("CACTUC STUDIO starting...")

    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )


if __name__ == "__main__":
    asyncio.run(main())
