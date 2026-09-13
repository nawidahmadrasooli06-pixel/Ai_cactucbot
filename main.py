import asyncio
import io
import os
import sqlite3
import time
from pathlib import Path

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BufferedInputFile,
)

from PIL import Image, ImageDraw, ImageFont, ImageFilter

# =========================================================
# CACTUC STUDIO
# نسخه رایگان
# سازنده: Nawid / @cactuc580
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "8659480577"))
PORT = int(os.getenv("PORT", "10000"))

# اختیاری:
# اگر HF_TOKEN نگذاری، ربات بدون AI خارجی هم کار می‌کند.
HF_TOKEN = os.getenv("HF_TOKEN", "")

DB_FILE = "cactuc_studio.db"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN تنظیم نشده است.")

bot = Bot(
    BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()

# =========================================================
# DATABASE
# =========================================================

db = sqlite3.connect(DB_FILE, check_same_thread=False)
db.row_factory = sqlite3.Row

db.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    created_at INTEGER
)
""")

db.execute("""
CREATE TABLE IF NOT EXISTS usage (
    user_id INTEGER PRIMARY KEY,
    count INTEGER DEFAULT 0,
    window_start INTEGER DEFAULT 0
)
""")

db.execute("""
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    project_type TEXT,
    title TEXT,
    created_at INTEGER
)
""")

db.commit()


# =========================================================
# FONT
# =========================================================

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

FONT_BOLD = FONT_PATHS[1]
FONT_NORMAL = FONT_PATHS[0]


def font(size, bold=False):
    path = FONT_BOLD if bold else FONT_NORMAL
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()


# =========================================================
# USER
# =========================================================

def register_user(user):
    db.execute(
        """
        INSERT INTO users(user_id, username, first_name, created_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
        username=excluded.username,
        first_name=excluded.first_name
        """,
        (
            user.id,
            user.username or "",
            user.first_name or "",
            int(time.time())
        )
    )
    db.commit()


# =========================================================
# QUOTA
# 6 خروجی در یک پنجره 24 ساعته
# =========================================================

MAX_DAILY = 6
WINDOW = 24 * 60 * 60


def quota_status(user_id):
    row = db.execute(
        "SELECT count, window_start FROM usage WHERE user_id=?",
        (user_id,)
    ).fetchone()

    now = int(time.time())

    if not row:
        return 0, MAX_DAILY

    if now - row["window_start"] >= WINDOW:
        db.execute(
            "DELETE FROM usage WHERE user_id=?",
            (user_id,)
        )
        db.commit()
        return 0, MAX_DAILY

    used = row["count"]
    return used, max(0, MAX_DAILY - used)


def use_quota(user_id):
    now = int(time.time())

    row = db.execute(
        "SELECT count, window_start FROM usage WHERE user_id=?",
        (user_id,)
    ).fetchone()

    if not row or now - row["window_start"] >= WINDOW:
        db.execute(
            """
            INSERT INTO usage(user_id,count,window_start)
            VALUES (?,1,?)
            ON CONFLICT(user_id)
            DO UPDATE SET count=1, window_start=excluded.window_start
            """,
            (user_id, now)
        )
        db.commit()
        return True

    if row["count"] >= MAX_DAILY:
        return False

    db.execute(
        "UPDATE usage SET count=count+1 WHERE user_id=?",
        (user_id,)
    )
    db.commit()

    return True


# =========================================================
# PROJECT LOG
# =========================================================

def save_project(user_id, project_type, title):
    db.execute(
        """
        INSERT INTO projects(user_id, project_type, title, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            project_type,
            title,
            int(time.time())
        )
    )
    db.commit()


# =========================================================
# MAIN MENU
# =========================================================

def main_keyboard(user_id):

    buttons = [
        [
            InlineKeyboardButton(
                text="🎨 بنرساز",
                callback_data="banner"
            ),
            InlineKeyboardButton(
                text="🖼️ تصویرساز",
                callback_data="image"
            )
        ],
        [
            InlineKeyboardButton(
                text="👤 Brand Studio",
                callback_data="brand"
            ),
            InlineKeyboardButton(
                text="✍️ نویسنده",
                callback_data="writer"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏆 Challenge Studio",
                callback_data="challenge"
            ),
            InlineKeyboardButton(
                text="🚀 Campaign Studio",
                callback_data="campaign"
            )
        ],
        [
            InlineKeyboardButton(
                text="ℹ️ درباره سازنده",
                callback_data="creator"
            )
        ]
    ]

    if user_id == OWNER_ID:
        buttons.append([
            InlineKeyboardButton(
                text="👑 پنل مالک",
                callback_data="owner"
            )
        ])

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


# =========================================================
# STATES
# =========================================================

class Banner(StatesGroup):
    kind = State()
    title = State()
    text = State()
    link = State()
    photo = State()
    style = State()


class ImageMaker(StatesGroup):
    prompt = State()
    style = State()


class Brand(StatesGroup):
    name = State()
    topic = State()
    colors = State()
    style = State()


class Writer(StatesGroup):
    purpose = State()
    details = State()


class Challenge(StatesGroup):
    title = State()
    description = State()
    first = State()
    second = State()
    third = State()


# =========================================================
# START
# =========================================================

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):

    await state.clear()

    register_user(message.from_user)

    used, left = quota_status(message.from_user.id)

    await message.answer(
        f"""
<b>CACTUC STUDIO</b> 🖤

سلام <b>{message.from_user.first_name or "رفیق"}</b> 👋

یک استودیوی فارسی برای ساخت محتوای تلگرامی.

🎨 بنر
🖼️ تصویر
👤 برند
✍️ متن
🏆 چالش
🚀 کمپین

سهمیه طراحی تصویری:
<b>{left} از ۶</b>

یکی را انتخاب کن:
""",
        reply_markup=main_keyboard(message.from_user.id)
    )


@dp.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):

    await state.clear()

    await message.answer(
        "❌ عملیات لغو شد.",
        reply_markup=main_keyboard(message.from_user.id)
    )


# =========================================================
# BANNER
# =========================================================

@dp.callback_query(F.data == "banner")
async def banner_start(callback: CallbackQuery, state: FSMContext):

    await state.clear()

    await state.set_state(Banner.kind)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎂 تولد",
                    callback_data="bkind:تولد"
                ),
                InlineKeyboardButton(
                    text="📢 تبلیغ",
                    callback_data="bkind:تبلیغ"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛍 فروش",
                    callback_data="bkind:فروش"
                ),
                InlineKeyboardButton(
                    text="📣 معرفی کانال",
                    callback_data="bkind:کانال"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 Premium / Stars",
                    callback_data="bkind:تلگرام"
                ),
                InlineKeyboardButton(
                    text="✏️ دلخواه",
                    callback_data="bkind:دلخواه"
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
        "🎨 <b>بنرساز</b>\n\nنوع بنر را انتخاب کن:",
        reply_markup=keyboard
    )

    await callback.answer()


@dp.callback_query(Banner.kind, F.data.startswith("bkind:"))
async def banner_kind(callback: CallbackQuery, state: FSMContext):

    await state.update_data(
        kind=callback.data.replace("bkind:", "")
    )

    await state.set_state(Banner.title)

    await callback.message.answer(
        "1️⃣ عنوان یا نامی که باید روی بنر نوشته شود را بفرست:"
    )

    await callback.answer()


@dp.message(Banner.title)
async def banner_title(message: Message, state: FSMContext):

    await state.update_data(
        title=message.text or ""
    )

    await state.set_state(Banner.text)

    await message.answer(
        "2️⃣ متن اصلی بنر را بفرست:"
    )


@dp.message(Banner.text)
async def banner_text(message: Message, state: FSMContext):

    await state.update_data(
        text=message.text or ""
    )

    await state.set_state(Banner.link)

    await message.answer(
        "3️⃣ لینک کانال، آیدی یا راه ارتباطی را بفرست.\n"
        "اگر نمی‌خواهی، بنویس: ندارم"
    )


@dp.message(Banner.link)
async def banner_link(message: Message, state: FSMContext):

    await state.update_data(
        link=message.text or ""
    )

    await state.set_state(Banner.photo)

    await message.answer(
        "4️⃣ اگر عکس یا لوگو داری بفرست.\n"
        "اگر نداری بنویس: بدون عکس"
    )


@dp.message(Banner.photo, F.photo)
async def banner_photo(message: Message, state: FSMContext):

    file = await bot.get_file(
        message.photo[-1].file_id
    )

    path = Path(
        f"reference_{message.from_user.id}.jpg"
    )

    await bot.download_file(
        file.file_path,
        destination=path
    )

    await state.update_data(
        photo=str(path)
    )

    await state.set_state(Banner.style)

    await message.answer(
        "5️⃣ سبک بنر را بنویس.\n\n"
        "مثلاً:\n"
        "لوکس، مشکی طلایی، مدرن و حرفه‌ای"
    )


@dp.message(Banner.photo)
async def banner_no_photo(message: Message, state: FSMContext):

    await state.update_data(
        photo=""
    )

    await state.set_state(Banner.style)

    await message.answer(
        "5️⃣ سبک بنر را بنویس.\n\n"
        "مثلاً:\n"
        "لوکس، مشکی طلایی، مدرن و حرفه‌ای"
    )


@dp.message(Banner.style)
async def banner_finish(message: Message, state: FSMContext):

    if not use_quota(message.from_user.id):

        await state.clear()

        await message.answer(
            "⛔ <b>سهمیه امروزت تمام شده.</b>\n\n"
            "هر کاربر در هر ۲۴ ساعت حداکثر ۶ خروجی تصویری دارد."
        )

        return

    data = await state.get_data()

    await message.answer(
        "🎨 در حال طراحی بنر..."
    )

    try:

        image = create_banner(
            kind=data.get("kind", ""),
            title=data.get("title", ""),
            text=data.get("text", ""),
            link=data.get("link", ""),
            style=message.text or "",
            reference=data.get("photo", "")
        )

        save_project(
            message.from_user.id,
            "banner",
            data.get("title", "بنر")
        )

        await message.answer_photo(
            BufferedInputFile(
                image,
                filename="cactuc_banner.png"
            ),
            caption=(
                "✅ <b>بنر آماده شد.</b>\n\n"
                "ساخته‌شده با CACTUC STUDIO"
            )
        )

    except Exception as e:

        print("BANNER ERROR:", e)

        await message.answer(
            "❌ ساخت بنر با خطا مواجه شد."
        )

    await state.clear()


# =========================================================
# IMAGE STUDIO
# =========================================================

@dp.callback_query(F.data == "image")
async def image_start(callback: CallbackQuery, state: FSMContext):

    await state.clear()

    await state.set_state(ImageMaker.prompt)

    await callback.message.edit_text(
        "🖼️ <b>Image Studio</b>\n\n"
        "توضیح بده چه تصویری می‌خواهی بسازی.\n\n"
        "مثال:\n"
        "«یک پوستر لوکس برای فروش Premium با فضای مشکی و طلایی»"
    )

    await callback.answer()


@dp.message(ImageMaker.prompt)
async def image_prompt(message: Message, state: FSMContext):

    await state.update_data(
        prompt=message.text or ""
    )

    await state.set_state(ImageMaker.style)

    await message.answer(
        "سبک را بنویس.\n"
        "مثلاً: سینمایی، لوکس، مینیمال، دارک، مدرن"
    )


@dp.message(ImageMaker.style)
async def image_finish(message: Message, state: FSMContext):

    if not use_quota(message.from_user.id):

        await state.clear()

        await message.answer(
            "⛔ سهمیه ۶ تصویر در ۲۴ ساعت تمام شده."
        )

        return

    data = await state.get_data()

    await message.answer(
        "🖼️ در حال ساخت تصویر..."
    )

    try:

        image = create_design(
            prompt=data.get("prompt", ""),
            style=message.text or ""
        )

        save_project(
            message.from_user.id,
            "image",
            data.get("prompt", "")[:100]
        )

        await message.answer_photo(
            BufferedInputFile(
                image,
                filename="cactuc_image.png"
            ),
            caption="✅ تصویر آماده شد."
        )

    except Exception as e:

        print("IMAGE ERROR:", e)

        await message.answer(
            "❌ ساخت تصویر انجام نشد."
        )

    await state.clear()


# =========================================================
# BRAND
# =========================================================

@dp.callback_query(F.data == "brand")
async def brand_start(callback: CallbackQuery, state: FSMContext):

    await state.clear()

    await state.set_state(Brand.name)

    await callback.message.edit_text(
        "👤 <b>Brand Studio</b>\n\n"
        "نام برند یا کانال را بفرست:"
    )

    await callback.answer()


@dp.message(Brand.name)
async def brand_name(message: Message, state: FSMContext):

    await state.update_data(
        name=message.text or ""
    )

    await state.set_state(Brand.topic)

    await message.answer(
        "موضوع فعالیت برند چیست؟"
    )


@dp.message(Brand.topic)
async def brand_topic(message: Message, state: FSMContext):

    await state.update_data(
        topic=message.text or ""
    )

    await state.set_state(Brand.colors)

    await message.answer(
        "رنگ‌های مورد علاقه را بفرست.\n"
        "مثلاً: آبی تیره و سفید"
    )


@dp.message(Brand.colors)
async def brand_colors(message: Message, state: FSMContext):

    await state.update_data(
        colors=message.text or ""
    )

    await state.set_state(Brand.style)

    await message.answer(
        "سبک برند را بگو.\n"
        "مثلاً: لوکس، دارک، مینیمال"
    )


@dp.message(Brand.style)
async def brand_finish(message: Message, state: FSMContext):

    if not use_quota(message.from_user.id):

        await state.clear()

        await message.answer(
            "⛔ سهمیه تصویری امروزت تمام شده."
        )

        return

    data = await state.get_data()

    await message.answer(
        "👤 در حال ساخت هویت برند..."
    )

    image = create_brand(
        name=data.get("name", ""),
        topic=data.get("topic", ""),
        colors=data.get("colors", ""),
        style=message.text or ""
    )

    save_project(
        message.from_user.id,
        "brand",
        data.get("name", "")
    )

    await message.answer_photo(
        BufferedInputFile(
            image,
            filename="cactuc_brand.png"
        ),
        caption="✅ Brand Studio آماده کرد."
    )

    await state.clear()


# =========================================================
# WRITER
# =========================================================

@dp.callback_query(F.data == "writer")
async def writer_start(callback: CallbackQuery, state: FSMContext):

    await state.clear()

    await state.set_state(Writer.purpose)

    await callback.message.edit_text(
        "✍️ <b>نویسنده</b>\n\n"
        "برای چه چیزی متن می‌خواهی؟\n\n"
        "مثلاً:\n"
        "تبلیغ، تولد، معرفی کانال، فروش، اطلاعیه"
    )

    await callback.answer()


@dp.message(Writer.purpose)
async def writer_purpose(message: Message, state: FSMContext):

    await state.update_data(
        purpose=message.text or ""
    )

    await state.set_state(Writer.details)

    await message.answer(
        "اطلاعاتی که باید داخل متن باشد را بفرست:"
    )


@dp.message(Writer.details)
async def writer_finish(message: Message, state: FSMContext):

    data = await state.get_data()

    purpose = data.get("purpose", "")
    details = message.text or ""

    text = make_persian_text(
        purpose,
        details
    )

    await message.answer(
        text
    )

    await state.clear()


# =========================================================
# CHALLENGE
# =========================================================

@dp.callback_query(F.data == "challenge")
async def challenge_start(callback: CallbackQuery, state: FSMContext):

    await state.clear()

    await state.set_state(Challenge.title)

    await callback.message.edit_text(
        "🏆 <b>Challenge Studio</b>\n\n"
        "عنوان چالش را بفرست:"
    )

    await callback.answer()


@dp.message(Challenge.title)
async def challenge_title(message: Message, state: FSMContext):

    await state.update_data(title=message.text or "")

    await state.set_state(Challenge.description)

    await message.answer(
        "توضیح و قوانین چالش:"
    )


@dp.message(Challenge.description)
async def challenge_desc(message: Message, state: FSMContext):

    await state.update_data(
        description=message.text or ""
    )

    await state.set_state(Challenge.first)

    await message.answer(
        "🥇 جایزه نفر اول:"
    )


@dp.message(Challenge.first)
async def challenge_first(message: Message, state: FSMContext):

    await state.update_data(
        first=message.text or ""
    )

    await state.set_state(Challenge.second)

    await message.answer(
        "🥈 جایزه نفر دوم:"
    )


@dp.message(Challenge.second)
async def challenge_second(message: Message, state: FSMContext):

    await state.update_data(
        second=message.text or ""
    )

    await state.set_state(Challenge.third)

    await message.answer(
        "🥉 جایزه نفر سوم:"
    )


@dp.message(Challenge.third)
async def challenge_third(message: Message, state: FSMContext):

    data = await state.get_data()

    await message.answer(
        f"""
🏆 <b>چالش ساخته شد</b>

<b>{data.get("title")}</b>

{data.get("description")}

🥇 {data.get("first")}
🥈 {data.get("second")}
🥉 {message.text}

━━━━━━━━━━━━━━
ساخته‌شده با CACTUC STUDIO
"""
    )

    save_project(
        message.from_user.id,
        "challenge",
        data.get("title", "")
    )

    await state.clear()


# =========================================================
# CAMPAIGN
# =========================================================

@dp.callback_query(F.data == "campaign")
async def campaign(callback: CallbackQuery):

    await callback.message.edit_text(
        """
🚀 <b>Campaign Studio</b>

برای یک کمپین حرفه‌ای می‌توانی از این ترکیب استفاده کنی:

🎨 بنر
✍️ متن تبلیغ
👤 هویت برند
🏆 چالش

همه برای استفاده در تلگرام.
""",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🎨 ساخت بنر",
                        callback_data="banner"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✍️ ساخت متن",
                        callback_data="writer"
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
    )

    await callback.answer()


# =========================================================
# CREATOR
# =========================================================

@dp.callback_query(F.data == "creator")
async def creator(callback: CallbackQuery):

    await callback.message.edit_text(
        """
ℹ️ <b>CACTUC STUDIO</b>

یک پروژه فارسی برای ساخت محتوای تلگرامی.

👤 <b>طراح و سازنده:</b>
نوید

📱 Telegram:
@cactuc580

🆔 Creator ID:
<code>8659480577</code>

━━━━━━━━━━━━━━

© CACTUC STUDIO
Designed & Developed by Nawid
""",
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


# =========================================================
# OWNER
# =========================================================

@dp.callback_query(F.data == "owner")
async def owner(callback: CallbackQuery):

    if callback.from_user.id != OWNER_ID:

        await callback.answer(
            "⛔ این بخش فقط برای مالک ربات است.",
            show_alert=True
        )

        return

    users = db.execute(
        "SELECT COUNT(*) AS n FROM users"
    ).fetchone()["n"]

    projects = db.execute(
        "SELECT COUNT(*) AS n FROM projects"
    ).fetchone()["n"]

    banners = db.execute(
        "SELECT COUNT(*) AS n FROM projects WHERE project_type='banner'"
    ).fetchone()["n"]

    images = db.execute(
        "SELECT COUNT(*) AS n FROM projects WHERE project_type='image'"
    ).fetchone()["n"]

    await callback.message.edit_text(
        f"""
👑 <b>پنل مالک CACTUC STUDIO</b>

👥 کاربران:
<b>{users}</b>

📁 کل پروژه‌ها:
<b>{projects}</b>

🎨 بنرها:
<b>{banners}</b>

🖼️ تصاویر:
<b>{images}</b>

━━━━━━━━━━━━━━

👤 مالک:
<code>{OWNER_ID}</code>

🟢 سیستم فعال است.
""",
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


# =========================================================
# HOME
# =========================================================

@dp.callback_query(F.data == "home")
async def home(callback: CallbackQuery, state: FSMContext):

    await state.clear()

    await callback.message.edit_text(
        "🏠 <b>CACTUC STUDIO</b>\n\n"
        "چه کاری می‌خواهی انجام بدهی؟",
        reply_markup=main_keyboard(
            callback.from_user.id
        )
    )

    await callback.answer()


# =========================================================
# DESIGN ENGINE
# =========================================================

def gradient_background(size, top, bottom):

    width, height = size

    image = Image.new(
        "RGB",
        size
    )

    pixels = image.load()

    for y in range(height):

        ratio = y / max(1, height - 1)

        r = int(
            top[0] * (1-ratio) +
            bottom[0] * ratio
        )

        g = int(
            top[1] * (1-ratio) +
            bottom[1] * ratio
        )

        b = int(
            top[2] * (1-ratio) +
            bottom[2] * ratio
        )

        for x in range(width):
            pixels[x, y] = (r, g, b)

    return image


def fit_text(draw, text, max_width, start_size=80):

    size = start_size

    while size > 20:

        f = font(size, True)

        box = draw.textbbox(
            (0, 0),
            text,
            font=f
        )

        if box[2] - box[0] <= max_width:
            return f

        size -= 2

    return font(20, True)


def draw_center(draw, text, y, image_width, f, fill):

    box = draw.textbbox(
        (0, 0),
        text,
        font=f
    )

    width = box[2] - box[0]

    x = (image_width - width) // 2

    draw.text(
        (x, y),
        text,
        font=f,
        fill=fill
    )


def create_banner(
    kind,
    title,
    text,
    link,
    style,
    reference=""
):

    W = 1280
    H = 720

    image = gradient_background(
        (W, H),
        (8, 12, 25),
        (35, 20, 60)
    )

    draw = ImageDraw.Draw(image)

    # decorative circles
    for x, y, r in [
        (100, 100, 180),
        (1180, 620, 240),
        (1100, 100, 100)
    ]:

        overlay = Image.new(
            "RGBA",
            (W, H),
            (0, 0, 0, 0)
        )

        od = ImageDraw.Draw(overlay)

        od.ellipse(
            (
                x-r,
                y-r,
                x+r,
                y+r
            ),
            fill=(120, 70, 255, 55)
        )

        overlay = overlay.filter(
            ImageFilter.GaussianBlur(35)
        )

        image = Image.alpha_composite(
            image.convert("RGBA"),
            overlay
        ).convert("RGB")

        draw = ImageDraw.Draw(image)

    # top label
    label = f"CACTUC STUDIO • {kind}"

    draw.text(
        (70, 55),
        label,
        font=font(28, True),
        fill=(210, 210, 230)
    )

    # title
    title_font = fit_text(
        draw,
        title,
        1100,
        88
    )

    draw_center(
        draw,
        title,
        190,
        W,
        title_font,
        (255, 255, 255)
    )

    # main text
    lines = []

    words = text.split()

    line = ""

    for word in words:

        test = (line + " " + word).strip()

        box = draw.textbbox(
            (0, 0),
            test,
            font=font(38)
        )

        if box[2] - box[0] > 1000:

            if line:
                lines.append(line)

            line = word

        else:
            line = test

    if line:
        lines.append(line)

    y = 320

    for line in lines[:4]:

        draw_center(
            draw,
            line,
            y,
            W,
            font(38),
            (235, 235, 245)
        )

        y += 55

    # link
    if link and link.lower() != "ندارم":

        draw_center(
            draw,
            link,
            570,
            W,
            font(30, True),
            (210, 180, 255)
        )

    # footer
    draw_center(
        draw,
        "@cactuc580",
        650,
        W,
        font(23),
        (160, 160, 180)
    )

    output = io.BytesIO()

    image.save(
        output,
        format="PNG",
        optimize=True
    )

    return output.getvalue()


def create_design(prompt, style):

    return create_banner(
        "تصویر",
        "CACTUC STUDIO",
        prompt,
        "",
        style
    )


def create_brand(
    name,
    topic,
    colors,
    style
):

    return create_banner(
        "BRAND",
        name,
        topic,
        colors,
        style
    )


# =========================================================
# PERSIAN WRITER
# =========================================================

def make_persian_text(purpose, details):

    p = purpose.lower()

    if "تبلیغ" in p:

        return (
            "🔥 <b>یک پیشنهاد ویژه برای شما</b>\n\n"
            f"{details}\n\n"
            "📩 برای اطلاعات بیشتر پیام بده.\n"
            "✨ همین حالا اقدام کن."
        )

    if "تولد" in p:

        return (
            "🎂✨ <b>تولدت مبارک!</b>\n\n"
            f"{details}\n\n"
            "امیدوارم سال جدید زندگی‌ات پر از "
            "آرامش، موفقیت و اتفاق‌های خوب باشد. ❤️"
        )

    if "فروش" in p:

        return (
            "🛍️ <b>پیشنهاد ویژه</b>\n\n"
            f"{details}\n\n"
            "📩 برای سفارش و اطلاعات بیشتر پیام بده."
        )

    if "معرفی" in p:

        return (
            "✨ <b>معرفی</b>\n\n"
            f"{details}\n\n"
            "برای دنبال‌کردن و دریافت مطالب بیشتر همراه ما باشید."
        )

    return (
        f"<b>{purpose}</b>\n\n"
        f"{details}\n\n"
        "━━━━━━━━━━━━━━\n"
        "ساخته‌شده با CACTUC STUDIO"
    )


# =========================================================
# HEALTH SERVER
# =========================================================

async def health(request):

    return web.Response(
        text="CACTUC STUDIO is running."
    )


async def start_web():

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


# =========================================================
# RUN
# =========================================================

async def main():

    await start_web()

    print("CACTUC STUDIO IS RUNNING")

    await dp.start_polling(
        bot
    )


if __name__ == "__main__":

    asyncio.run(main())
