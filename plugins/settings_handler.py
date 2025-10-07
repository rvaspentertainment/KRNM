from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from helper.database import db

# Dictionary to track what user is setting
user_setting_state = {}


@Client.on_message(filters.private & filters.text & ~filters.command(["start", "cancel", "help", "string"]))
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
                f"✅ **Prefix Set:** `{text}`",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Back to Settings", callback_data="auto_settings")
                ]])
            )
            del user_setting_state[user_id]
        
        elif setting_type == "suffix":
            await db.set_suffix(user_id, text)
            await message.reply_text(
                f"✅ **Suffix Set:** `{text}`",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Back to Settings", callback_data="auto_settings")
                ]])
            )
            del user_setting_state[user_id]
        
        elif setting_type == "upload_channel":
            # Handle channel ID
            channel_id = text
            if channel_id.startswith('@'):
                # Username format
                pass
            elif channel_id.lstrip('-').isdigit():
                # Numeric ID
                channel_id = int(channel_id)
            else:
                await message.reply_text("❌ Invalid channel ID/username format")
                return
            
            await db.set_upload_channel(user_id, channel_id)
            await message.reply_text(
                f"✅ **Upload Channel Set:** `{channel_id}`",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Back to Settings", callback_data="upload_settings")
                ]])
            )
            del user_setting_state[user_id]
        
        elif setting_type == "remove_words":
            # Parse comma-separated words - trim and clean
            words = []
            for w in text.split(','):
                w = w.strip()
                if w:
                    words.append(w)
            
            if words:
                await db.set_remove_words(user_id, words)
                await message.reply_text(
                    f"✅ **Remove Words Set ({len(words)} words):**\n`{', '.join(words)}`",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("◀️ Back to Settings", callback_data="auto_settings")
                    ]])
                )
            else:
                await message.reply_text("❌ No valid words provided")
                return
            del user_setting_state[user_id]
        
        elif setting_type == "replace_words":
            # Parse word pairs (old:new, old2:new2)
            pairs = [p.strip() for p in text.split(',')]
            replace_dict = {}
            
            for pair in pairs:
                if ':' in pair:
                    parts = pair.split(':', 1)
                    if len(parts) == 2:
                        old, new = parts[0].strip(), parts[1].strip()
                        if old and new:
                            replace_dict[old] = new
            
            if replace_dict:
                await db.set_replace_words(user_id, replace_dict)
                words_display = '\n'.join([f"• {k} → {v}" for k, v in replace_dict.items()])
                await message.reply_text(
                    f"✅ **Replace Words Set ({len(replace_dict)} pairs):**\n\n{words_display}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("◀️ Back to Settings", callback_data="auto_settings")
                    ]])
                )
            else:
                await message.reply_text(
                    "❌ **Invalid Format!**\n\nUse: `old:new, old2:new2`",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("◀️ Back to Settings", callback_data="auto_settings")
                    ]])
                )
                return
            del user_setting_state[user_id]
    
    except Exception as e:
        await message.reply_text(f"❌ **Error:** {e}")
        if user_id in user_setting_state:
            del user_setting_state[user_id]


@Client.on_message(filters.private & filters.command("cancel"))
async def cancel_setting(client, message):
    user_id = message.from_user.id
    if user_id in user_setting_state:
        del user_setting_state[user_id]
        await message.reply_text(
            "❌ **Cancelled**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Back to Settings", callback_data="settings")
            ]])
        )
