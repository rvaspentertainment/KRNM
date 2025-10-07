from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from helper.database import db

# Dictionary to track what user is setting
user_setting_state = {}


@Client.on_message(filters.private & filters.text & ~filters.command(["start", "cancel", "help"]))
async def handle_settings_input(client, message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Check if user has a pending setting state
    if user_id not in user_setting_state:
        return
    
    setting_type = user_setting_state.get(user_id)
    
    try:
        if setting_type == "prefix":
            await db.set_prefix(user_id, text)
            await message.reply_text(
                f"✅ **Pʀᴇꜰɪx Sᴇᴛ:** `{text}`",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Bᴀᴄᴋ ᴛᴏ Sᴇᴛᴛɪɴɢꜱ", callback_data="auto_settings")
                ]])
            )
            del user_setting_state[user_id]
        
        elif setting_type == "suffix":
            await db.set_suffix(user_id, text)
            await message.reply_text(
                f"✅ **Sᴜꜰꜰɪx Sᴇᴛ:** `{text}`",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Bᴀᴄᴋ ᴛᴏ Sᴇᴛᴛɪɴɢꜱ", callback_data="auto_settings")
                ]])
            )
            del user_setting_state[user_id]
        
        elif setting_type == "remove_words":
            # Parse comma-separated words
            words = [w.strip() for w in text.split(',') if w.strip()]
            await db.set_remove_words(user_id, words)
            await message.reply_text(
                f"✅ **Rᴇᴍᴏᴠᴇ Wᴏʀᴅꜱ Sᴇᴛ:** `{', '.join(words)}`",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Bᴀᴄᴋ ᴛᴏ Sᴇᴛᴛɪɴɢꜱ", callback_data="auto_settings")
                ]])
            )
            del user_setting_state[user_id]
        
        elif setting_type == "replace_words":
            # Parse word pairs (old:new, old2:new2)
            pairs = [p.strip() for p in text.split(',') if ':' in p]
            replace_dict = {}
            for pair in pairs:
                if ':' in pair:
                    old, new = pair.split(':', 1)
                    replace_dict[old.strip()] = new.strip()
            
            await db.set_replace_words(user_id, replace_dict)
            words_display = ', '.join([f"{k}→{v}" for k,v in replace_dict.items()])
            await message.reply_text(
                f"✅ **Rᴇᴘʟᴀᴄᴇ Wᴏʀᴅꜱ Sᴇᴛ:** `{words_display}`",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Bᴀᴄᴋ ᴛᴏ Sᴇᴛᴛɪɴɢꜱ", callback_data="auto_settings")
                ]])
            )
            del user_setting_state[user_id]
    
    except Exception as e:
        await message.reply_text(f"❌ **Eʀʀᴏʀ:** {e}")
        del user_setting_state[user_id]


@Client.on_message(filters.private & filters.command("cancel"))
async def cancel_setting(client, message):
    user_id = message.from_user.id
    if user_id in user_setting_state:
        del user_setting_state[user_id]
        await message.reply_text(
            "❌ **Cᴀɴᴄᴇʟʟᴇᴅ**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Bᴀᴄᴋ ᴛᴏ Sᴇᴛᴛɪɴɢꜱ", callback_data="auto_settings")
            ]])
        )


# Update callback handlers to set state
@Client.on_callback_query(filters.regex("^(set_prefix|set_suffix|set_remove_words|set_replace_words)$"))
async def set_state_handler(client, query):
    user_id = query.from_user.id
    setting = query.data.replace("set_", "")
    user_setting_state[user_id] = setting
