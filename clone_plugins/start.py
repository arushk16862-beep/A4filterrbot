from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.users_chats_db import db
from info import LOG_CHANNEL
from plugins.Mods.clone import clonedme


@Client.on_message(
    filters.command("start") & filters.private
)
async def clone_start(client, message):

    try:
        user = message.from_user

        # Save user
        if user:
            if not await db.is_user_exist(user.id):
                await db.add_user(
                    user.id,
                    user.first_name
                )

        # Default values
        bot_name = clonedme.B_NAME or "My Bot"
        bot_username = clonedme.U_NAME or ""

        buttons = [
            [
                InlineKeyboardButton(
                    "🕵️ HELP",
                    callback_data="help"
                )
            ],
            [
                InlineKeyboardButton(
                    "👑 OWNER",
                    callback_data="owner_info"
                ),
                InlineKeyboardButton(
                    "ℹ️ ABOUT",
                    callback_data="about"
                )
            ]
        ]

        if bot_username:
            buttons.append([
                InlineKeyboardButton(
                    "➕ ADD ME TO GROUP",
                    url=f"https://t.me/{bot_username}?startgroup=true"
                )
            ])

        text = (
            f"<b>👋 Hello {user.mention}!</b>\n\n"
            f"🤖 Welcome to <b>{bot_name}</b>.\n\n"
            "Send me a movie name to search."
        )

        await message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )

    except Exception as e:
        await message.reply_text(
            f"⚠️ <b>Start Error</b>\n\n"
            f"<code>{e}</code>"
        )
