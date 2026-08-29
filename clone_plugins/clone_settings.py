import json
import logging
from typing import Any

from pymongo import MongoClient
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from info import DATABASE_URI, ADMINS

log = logging.getLogger(__name__)
mongo = MongoClient(DATABASE_URI)
db = mongo["cloned_bots"]
collection = db["clone_settings"]

DEFAULTS = {
    "start_message": "Welcome {mention}! 🎬\n\nUse the buttons below to search and get files.",
    "help_message": "Use the buttons below to use this bot.",
    "about_message": "This is a customized Movie Auto Filter Bot.",
    "file_send_message": "Here is your requested file.",
    "verify_message": "You are not verified!\nPlease verify to continue.",
    "start_buttons": [
        [{"text": "🕵️ Help", "callback": "help"}],
        [{"text": "🤷 About", "callback": "about"}],
    ],
    "help_buttons": [[{"text": "⟸ Back", "callback": "start"}]],
    "about_buttons": [[{"text": "⟸ Back", "callback": "start"}]],
    "file_buttons": [[{"text": "𝙾𝚆𝙽𝙴𝚁", "url": "https://t.me/benana_assistbot"}]],
    "auto_delete_files": True,
    "auto_delete_seconds": 600,
    "verify_bot_enabled": False,
}

def _bot_id(client):
    me = getattr(client, "me", None)
    return getattr(me, "id", None)

async def get_clone_settings(client):
    bot_id = _bot_id(client)
    if not bot_id:
        me = await client.get_me()
        bot_id = me.id
    doc = await collection.find_one({"bot_id": bot_id})
    if not doc:
        doc = {"bot_id": bot_id, **DEFAULTS}
        await collection.insert_one(doc.copy())
    else:
        changed = False
        for k, v in DEFAULTS.items():
            if k not in doc:
                doc[k] = v
                changed = True
        if changed:
            await collection.update_one({"bot_id": bot_id}, {"$set": {k: doc[k] for k in DEFAULTS}})
    return doc

async def update_clone_setting(client, key, value):
    bot_id = _bot_id(client)
    if not bot_id:
        bot_id = (await client.get_me()).id
    await collection.update_one(
        {"bot_id": bot_id},
        {"$set": {key: value}},
        upsert=True,
    )

async def clone_owner(client, user_id):
    if str(user_id) in {str(x) for x in ADMINS}:
        return True
    bot_id = _bot_id(client)
    if not bot_id:
        bot_id = (await client.get_me()).id
    owner = await db["bots"].find_one({"bot_id": bot_id})
    return bool(owner and str(owner.get("user_id")) == str(user_id))

def render(text, message):
    values = {
        "mention": getattr(message.from_user, "mention", ""),
        "first_name": getattr(message.from_user, "first_name", ""),
        "username": getattr(message.from_user, "username", "") or "",
        "bot_username": getattr(getattr(message, "_bot", None), "username", "") or "",
    }
    try:
        return text.format(**values)
    except Exception:
        return text

def markup(rows):
    out = []
    for row in rows or []:
        buttons = []
        for b in row:
            text = str(b.get("text", "Button"))
            if b.get("url"):
                buttons.append(InlineKeyboardButton(text, url=b["url"]))
            elif b.get("callback"):
                buttons.append(InlineKeyboardButton(text, callback_data=b["callback"]))
        if buttons:
            out.append(buttons)
    return InlineKeyboardMarkup(out) if out else None

async def can_edit(client, message):
    return await clone_owner(client, message.from_user.id)

def parse_button(arg):
    # Format: /set_startbutton Button text | https://example.com
    if "|" not in arg:
        return None
    text, target = [x.strip() for x in arg.split("|", 1)]
    if not text or not target:
        return None
    if target.startswith("callback:"):
        return {"text": text, "callback": target.split(":", 1)[1]}
    return {"text": text, "url": target}

@Client.on_message(filters.command("clonesettings") & filters.private)
async def clone_settings(client, message):
    if not await can_edit(client, message):
        return await message.reply_text("Only the clone owner/admin can change clone settings.")
    s = await get_clone_settings(client)
    text = (
        "<b>⚙️ Clone Custom Settings</b>\n\n"
        f"Start: <code>{'set' if s.get('start_message') else 'default'}</code>\n"
        f"Help: <code>{'set' if s.get('help_message') else 'default'}</code>\n"
        f"About: <code>{'set' if s.get('about_message') else 'default'}</code>\n"
        f"File message: <code>{'set' if s.get('file_send_message') else 'default'}</code>\n"
        f"Auto delete: <b>{'ON' if s.get('auto_delete_files') else 'OFF'}</b> "
        f"({s.get('auto_delete_seconds', 600)} sec)\n"
        f"Verify bot: <b>{'ON' if s.get('verify_bot_enabled') else 'OFF'}</b>\n\n"
        "<b>Commands</b>\n"
        "<code>/set_start text</code>\n"
        "<code>/set_help text</code>\n"
        "<code>/set_about text</code>\n"
        "<code>/set_file_message text</code>\n"
        "<code>/set_verify_message text</code>\n"
        "<code>/set_autodelete 600</code> or <code>/set_autodelete off</code>\n"
        "<code>/set_verify on</code> or <code>/set_verify off</code>\n"
        "<code>/set_startbutton Text | URL</code>\n"
        "<code>/clear_startbuttons</code>\n"
    )
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)

async def _text_setting(client, message, key, label):
    if not await can_edit(client, message):
        return await message.reply_text("Only the clone owner/admin can change clone settings.")
    if len(message.command) < 2:
        return await message.reply_text(f"Usage: /{message.command[0]} your {label}")
    value = message.text.split(None, 1)[1]
    await update_clone_setting(client, key, value)
    await message.reply_text(f"✅ {label} updated for this clone.")

@Client.on_message(filters.command("set_start") & filters.private)
async def set_start(client, message):
    await _text_setting(client, message, "start_message", "start message")

@Client.on_message(filters.command("set_help") & filters.private)
async def set_help(client, message):
    await _text_setting(client, message, "help_message", "help message")

@Client.on_message(filters.command("set_about") & filters.private)
async def set_about(client, message):
    await _text_setting(client, message, "about_message", "about message")

@Client.on_message(filters.command("set_file_message") & filters.private)
async def set_file_message(client, message):
    await _text_setting(client, message, "file_send_message", "file-send message")

@Client.on_message(filters.command("set_verify_message") & filters.private)
async def set_verify_message(client, message):
    await _text_setting(client, message, "verify_message", "verification message")

@Client.on_message(filters.command("set_autodelete") & filters.private)
async def set_autodelete(client, message):
    if not await can_edit(client, message):
        return await message.reply_text("Only the clone owner/admin can change clone settings.")
    if len(message.command) < 2:
        return await message.reply_text("Usage: /set_autodelete 600 or /set_autodelete off")
    arg = message.command[1].lower()
    if arg == "off":
        await update_clone_setting(client, "auto_delete_files", False)
        return await message.reply_text("✅ Auto-delete disabled.")
    try:
        seconds = max(5, min(int(arg), 86400))
    except ValueError:
        return await message.reply_text("Enter seconds, e.g. /set_autodelete 600")
    await update_clone_setting(client, "auto_delete_files", True)
    await update_clone_setting(client, "auto_delete_seconds", seconds)
    await message.reply_text(f"✅ Auto-delete enabled: {seconds} seconds.")

@Client.on_message(filters.command("set_verify") & filters.private)
async def set_verify(client, message):
    if not await can_edit(client, message):
        return await message.reply_text("Only the clone owner/admin can change clone settings.")
    if len(message.command) < 2 or message.command[1].lower() not in ("on", "off"):
        return await message.reply_text("Usage: /set_verify on or /set_verify off")
    enabled = message.command[1].lower() == "on"
    await update_clone_setting(client, "verify_bot_enabled", enabled)
    await message.reply_text(f"✅ Verify bot: {'ON' if enabled else 'OFF'}")

@Client.on_message(filters.command("set_startbutton") & filters.private)
async def set_startbutton(client, message):
    if not await can_edit(client, message):
        return await message.reply_text("Only the clone owner/admin can change clone settings.")
    if len(message.command) < 2:
        return await message.reply_text("Usage: /set_startbutton Text | URL")
    b = parse_button(message.text.split(None, 1)[1])
    if not b:
        return await message.reply_text("Use: Button text | https://example.com")
    s = await get_clone_settings(client)
    rows = s.get("start_buttons", [])
    rows.append([b])
    await update_clone_setting(client, "start_buttons", rows)
    await message.reply_text("✅ Start button added.")

@Client.on_message(filters.command("clear_startbuttons") & filters.private)
async def clear_startbuttons(client, message):
    if not await can_edit(client, message):
        return await message.reply_text("Only the clone owner/admin can change clone settings.")
    await update_clone_setting(client, "start_buttons", [])
    await message.reply_text("✅ Start buttons cleared.")

@Client.on_callback_query(filters.regex(r"^(clone_custom_help|clone_custom_about|clone_custom_back)$"))
async def custom_pages(client, query):
    s = await get_clone_settings(client)
    if query.data == "clone_custom_help":
        await query.message.edit_text(render(s["help_message"], query.message), reply_markup=markup(s.get("help_buttons")))
    elif query.data == "clone_custom_about":
        await query.message.edit_text(render(s["about_message"], query.message), reply_markup=markup(s.get("about_buttons")))
    else:
        await query.message.edit_text(render(s["start_message"], query.message), reply_markup=markup(s.get("start_buttons")))
    await query.answer()
