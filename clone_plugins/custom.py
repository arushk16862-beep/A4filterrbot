import logging
from pymongo import MongoClient

from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from info import DATABASE_URI

logger = logging.getLogger(__name__)

mongo_client = MongoClient(DATABASE_URI)
mongo_db = mongo_client["cloned_bots"]
bots_col = mongo_db.bots


def get_settings(bot_id):
    bot = bots_col.find_one({"bot_id": bot_id})

    default = {
        "start_text": None,
        "start_image": None,
        "buttons": [],
        "force_sub": None,
        "auto_delete": False
    }

    if not bot:
        return default

    settings = bot.get("custom_settings", {})
    default.update(settings)
    return default


def save_setting(bot_id, key, value):
    bots_col.update_one(
        {"bot_id": bot_id},
        {"$set": {f"custom_settings.{key}": value}},
        upsert=False
    )


def is_owner(bot_id, user_id):
    bot = bots_col.find_one({
        "bot_id": bot_id,
        "user_id": user_id
    })
    return bool(bot)


def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📝 Start Text",
                callback_data="cc_start_text"
            ),
            InlineKeyboardButton(
                "🖼️ Start Image",
                callback_data="cc_start_image"
            )
        ],
        [
            InlineKeyboardButton(
                "🔘 Buttons",
                callback_data="cc_buttons"
            )
        ],
        [
            InlineKeyboardButton(
                "📢 Force Subscribe",
                callback_data="cc_fsub"
            )
        ],
        [
            InlineKeyboardButton(
                "🗑️ Auto Delete",
                callback_data="cc_autodel"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Close",
                callback_data="cc_close"
            )
        ]
    ])


# --------------------------------------------------
# CUSTOMIZATION MENU
# --------------------------------------------------

@Client.on_callback_query(filters.regex("^clone_customize$"))
async def customize_menu(client, query):

    if not is_owner(client.me.id, query.from_user.id):
        return await query.answer(
            "❌ You are not the owner of this clone.",
            show_alert=True
        )

    await query.message.edit_text(
        "<b>⚙️ Clone Customization</b>\n\n"
        "Choose what you want to customize:",
        reply_markup=main_menu()
    )

    await query.answer()


# --------------------------------------------------
# START TEXT
# --------------------------------------------------

@Client.on_callback_query(filters.regex("^cc_start_text$"))
async def start_text_button(client, query):

    if not is_owner(client.me.id, query.from_user.id):
        return await query.answer(
            "❌ Owner only.",
            show_alert=True
        )

    await query.message.edit_text(
        "<b>📝 Start Text</b>\n\n"
        "Send your new Start Text as a normal message.\n\n"
        "HTML formatting is supported.\n\n"
        "Example:\n"
        "<code>Hello {mention} ❤️</code>",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="cc_menu"
                )
            ]
        ])
    )

    await query.answer()


# --------------------------------------------------
# START IMAGE
# --------------------------------------------------

@Client.on_callback_query(filters.regex("^cc_start_image$"))
async def start_image_button(client, query):

    if not is_owner(client.me.id, query.from_user.id):
        return await query.answer(
            "❌ Owner only.",
            show_alert=True
        )

    await query.message.edit_text(
        "<b>🖼️ Start Image</b>\n\n"
        "Send the image you want to use as Start Image.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="cc_menu"
                )
            ]
        ])
    )

    await query.answer()


# --------------------------------------------------
# BUTTONS
# --------------------------------------------------

@Client.on_callback_query(filters.regex("^cc_buttons$"))
async def buttons_menu(client, query):

    if not is_owner(client.me.id, query.from_user.id):
        return await query.answer(
            "❌ Owner only.",
            show_alert=True
        )

    await query.message.edit_text(
        "<b>🔘 Start Buttons</b>\n\n"
        "Send buttons in this format:\n\n"
        "<code>Button Name - https://example.com</code>\n\n"
        "Send one button per line.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🗑️ Remove All Buttons",
                    callback_data="cc_clear_buttons"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="cc_menu"
                )
            ]
        ])
    )

    await query.answer()


@Client.on_callback_query(filters.regex("^cc_clear_buttons$"))
async def clear_buttons(client, query):

    if not is_owner(client.me.id, query.from_user.id):
        return await query.answer(
            "❌ Owner only.",
            show_alert=True
        )

    save_setting(client.me.id, "buttons", [])

    await query.answer(
        "✅ All buttons removed.",
        show_alert=True
    )

    await query.message.edit_text(
        "<b>🔘 Buttons</b>\n\n"
        "All custom buttons have been removed.",
        reply_markup=main_menu()
    )


# --------------------------------------------------
# FORCE SUBSCRIBE
# --------------------------------------------------

@Client.on_callback_query(filters.regex("^cc_fsub$"))
async def force_sub_button(client, query):

    if not is_owner(client.me.id, query.from_user.id):
        return await query.answer(
            "❌ Owner only.",
            show_alert=True
        )

    settings = get_settings(client.me.id)
    current = settings.get("force_sub")

    status = "❌ OFF"

    if current:
        status = f"✅ {current}"

    await query.message.edit_text(
        "<b>📢 Force Subscribe</b>\n\n"
        f"Current: {status}\n\n"
        "Send the channel username as a normal message.\n\n"
        "Example:\n"
        "<code>@mychannel</code>\n\n"
        "To disable, use the button below.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔴 Disable",
                    callback_data="cc_fsub_off"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="cc_menu"
                )
            ]
        ])
    )

    await query.answer()


@Client.on_callback_query(filters.regex("^cc_fsub_off$"))
async def force_sub_off(client, query):

    if not is_owner(client.me.id, query.from_user.id):
        return await query.answer(
            "❌ Owner only.",
            show_alert=True
        )

    save_setting(client.me.id, "force_sub", None)

    await query.answer(
        "✅ Force Subscribe disabled.",
        show_alert=True
    )

    await query.message.edit_text(
        "<b>📢 Force Subscribe</b>\n\n"
        "Status: ❌ OFF",
        reply_markup=main_menu()
    )


# --------------------------------------------------
# AUTO DELETE
# --------------------------------------------------

@Client.on_callback_query(filters.regex("^cc_autodel$"))
async def auto_delete_button(client, query):

    if not is_owner(client.me.id, query.from_user.id):
        return await query.answer(
            "❌ Owner only.",
            show_alert=True
        )

    settings = get_settings(client.me.id)
    enabled = settings.get("auto_delete", False)

    status = "✅ ON" if enabled else "❌ OFF"

    await query.message.edit_text(
        "<b>🗑️ Auto Delete</b>\n\n"
        f"Current Status: {status}\n\n"
        "Choose an option:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ ON",
                    callback_data="cc_autodel_on"
                ),
                InlineKeyboardButton(
                    "❌ OFF",
                    callback_data="cc_autodel_off"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="cc_menu"
                )
            ]
        ])
    )

    await query.answer()


@Client.on_callback_query(filters.regex("^cc_autodel_on$"))
async def auto_delete_on(client, query):

    if not is_owner(client.me.id, query.from_user.id):
        return await query.answer(
            "❌ Owner only.",
            show_alert=True
        )

    save_setting(client.me.id, "auto_delete", True)

    await query.answer(
        "✅ Auto Delete enabled.",
        show_alert=True
    )

    await query.message.edit_text(
        "<b>🗑️ Auto Delete</b>\n\n"
        "Status: ✅ ON",
        reply_markup=main_menu()
    )


@Client.on_callback_query(filters.regex("^cc_autodel_off$"))
async def auto_delete_off(client, query):

    if not is_owner(client.me.id, query.from_user.id):
        return await query.answer(
            "❌ Owner only.",
            show_alert=True
        )

    save_setting(client.me.id, "auto_delete", False)

    await query.answer(
        "❌ Auto Delete disabled.",
        show_alert=True
    )

    await query.message.edit_text(
        "<b>🗑️ Auto Delete</b>\n\n"
        "Status: ❌ OFF",
        reply_markup=main_menu()
    )


# --------------------------------------------------
# BACK
# --------------------------------------------------

@Client.on_callback_query(filters.regex("^cc_menu$"))
async def back_menu(client, query):

    if not is_owner(client.me.id, query.from_user.id):
        return await query.answer(
            "❌ Owner only.",
            show_alert=True
        )

    await query.message.edit_text(
        "<b>⚙️ Clone Customization</b>\n\n"
        "Choose what you want to customize:",
        reply_markup=main_menu()
    )

    await query.answer()


# --------------------------------------------------
# CLOSE
# --------------------------------------------------

@Client.on_callback_query(filters.regex("^cc_close$"))
async def close_menu(client, query):

    if not is_owner(client.me.id, query.from_user.id):
        return await query.answer(
            "❌ Owner only.",
            show_alert=True
        )

    await query.message.delete()
    await query.answer()
