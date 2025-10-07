import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply, CallbackQuery, Message
from pyrogram.errors import (
    MessageNotModified, MessageDeleteForbidden, QueryIdInvalid, UserIsBlocked,
    ApiIdInvalid, PhoneNumberInvalid, PhoneCodeInvalid, PhoneCodeExpired,
    SessionPasswordNeeded, PasswordHashInvalid
)
from helper.database import db
from config import Config, Txt
import asyncio
from helper.settings_handler import user_setting_state
# Dictionary to store user session generation states and settings input states
user_states = {}

class SessionState:
    def __init__(self):
        self.api_id = None
        self.api_hash = None
        self.phone = None
        self.client = None
        self.phone_code_hash = None
        self.step = None


# ============ STRING SESSION GENERATOR ============

@Client.on_message(filters.private & filters.command("string"))
async def generate_string_session(client, message: Message):
    user_id = message.from_user.id
    
    try:
        await message.reply_text(
            "<b>📱 STRING SESSION GENERATOR</b>\n\n"
            "⚠️ <b>WARNING:</b> Never share your string session with anyone!\n\n"
            "Please send your <b>API_ID</b>\n\n"
            "Get it from: https://my.telegram.org",
            disable_web_page_preview=True
        )
        
        user_states[user_id] = SessionState()
        user_states[user_id].step = "api_id"
        
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")


async def cleanup_session(user_id):
    """Clean up session generation state"""
    if user_id in user_states:
        state = user_states[user_id]
        
        if hasattr(state, 'client') and state.client:
            try:
                await state.client.disconnect()
            except:
                pass
        
        del user_states[user_id]


@Client.on_message(filters.private & filters.command("cancel"))
async def cancel_operation(client, message: Message):
    user_id = message.from_user.id
    
    if user_id in user_states:
        await cleanup_session(user_id)
        await message.reply_text("✅ Operation cancelled.")
    else:
        await message.reply_text("❌ No active operation to cancel.")


# ============ START COMMAND ============

@Client.on_message(filters.private & filters.command("start"))
async def start(client, message):
    user = message.from_user
    try:
        await db.add_user(client, message)
    except Exception as e:
        print(f"Error adding user: {e}")
        
    button = InlineKeyboardMarkup([[
        InlineKeyboardButton('𝐂𝐇𝐀𝐍𝐍𝐄𝐋', url='https://t.me/+JrRgnfZT0GYwOGZl'),
        InlineKeyboardButton('Sᴜᴩᴩᴏʀᴛ', url='https://t.me/TG_SUPPORT_GROUP')
        ],[
        InlineKeyboardButton('⚙️ 𝐒𝐄𝐓𝐓𝐈𝐍𝐆𝐒 ⚙️', callback_data='settings') 
        ]])
    
    try:
        if Config.START_PIC:
            await message.reply_photo(Config.START_PIC, caption=Txt.START_TXT.format(user.mention), reply_markup=button)       
        else:
            await message.reply_text(text=Txt.START_TXT.format(user.mention), reply_markup=button, disable_web_page_preview=True)
    except UserIsBlocked:
        print(f"User {user.id} has blocked the bot")
    except Exception as e:
        print(f"Error in start command: {e}")


# ============ TEXT MESSAGE HANDLER (for both string session and settings input) ============

@Client.on_message(filters.private & filters.text & ~filters.command(["start", "cancel", "string", "help"]))
async def handle_text_input(client, message: Message):
    user_id = message.from_user.id
    
    # Check if user is in string session generation
    if user_id in user_states and isinstance(user_states[user_id], SessionState):
        state = user_states[user_id]
        text = message.text.strip()
        await handle_string_session_steps(client, message, state, text)
        return
    
    # Check if user is inputting settings (handled by settings_handler.py)
    if user_id in user_setting_state:
        return  # Let settings_handler.py handle this



async def handle_string_session_steps(client, message, state, text):
    """Handle string session generation steps"""
    user_id = message.from_user.id
    
    try:
        # Step 1: Receive API_ID
        if state.step == "api_id":
            if not text.isdigit():
                await message.reply_text("❌ API_ID must be a number. Please send a valid API_ID:")
                return
            
            state.api_id = int(text)
            state.step = "api_hash"
            await message.reply_text("✅ API_ID received!\n\nNow send your <b>API_HASH</b>")
        
        # Step 2: Receive API_HASH
        elif state.step == "api_hash":
            state.api_hash = text
            state.step = "phone"
            await message.reply_text(
                "✅ API_HASH received!\n\n"
                "Now send your <b>Phone Number</b> with country code\n"
                "Example: +1234567890"
            )
        
        # Step 3: Receive Phone Number
        elif state.step == "phone":
            state.phone = text
            
            try:
                from pyrogram import Client as PyroClient
                state.client = PyroClient(
                    name=f"session_{user_id}",
                    api_id=state.api_id,
                    api_hash=state.api_hash,
                    in_memory=True
                )
                
                await state.client.connect()
                code = await state.client.send_code(state.phone)
                state.phone_code_hash = code.phone_code_hash
                state.step = "otp"
                
                await message.reply_text(
                    "✅ OTP sent to your Telegram account!\n\n"
                    "Please send the <b>OTP code</b> you received.\n"
                    "Example: 12345"
                )
                
            except ApiIdInvalid:
                await message.reply_text("❌ Invalid API_ID or API_HASH. Please start again with /string")
                await cleanup_session(user_id)
            except PhoneNumberInvalid:
                await message.reply_text("❌ Invalid phone number. Please start again with /string")
                await cleanup_session(user_id)
            except Exception as e:
                await message.reply_text(f"❌ Error: {str(e)}\n\nPlease start again with /string")
                await cleanup_session(user_id)
        
        # Step 4: Receive OTP
        elif state.step == "otp":
            otp = text.replace(" ", "")
            
            try:
                await state.client.sign_in(state.phone, state.phone_code_hash, otp)
                string_session = await state.client.export_session_string()
                
                await message.reply_text(
                    "✅ <b>String Session Generated Successfully!</b>\n\n"
                    f"<code>{string_session}</code>\n\n"
                    "⚠️ <b>Keep this safe and never share it with anyone!</b>",
                    disable_web_page_preview=True
                )
                
                await cleanup_session(user_id)
                
            except PhoneCodeInvalid:
                await message.reply_text("❌ Invalid OTP code. Please try again.\nSend the correct OTP:")
            except PhoneCodeExpired:
                await message.reply_text("❌ OTP has expired. Please start again with /string")
                await cleanup_session(user_id)
            except SessionPasswordNeeded:
                state.step = "2fa"
                await message.reply_text("🔐 Your account has 2FA enabled.\n\nPlease send your <b>2FA Password</b>:")
            except Exception as e:
                await message.reply_text(f"❌ Error: {str(e)}")
                await cleanup_session(user_id)
        
        # Step 5: Receive 2FA Password
        elif state.step == "2fa":
            try:
                await state.client.check_password(text)
                string_session = await state.client.export_session_string()
                
                await message.reply_text(
                    "✅ <b>String Session Generated Successfully!</b>\n\n"
                    f"<code>{string_session}</code>\n\n"
                    "⚠️ <b>Keep this safe and never share it with anyone!</b>",
                    disable_web_page_preview=True
                )
                
                await cleanup_session(user_id)
                
            except PasswordHashInvalid:
                await message.reply_text("❌ Invalid 2FA password. Please try again.\nSend the correct password:")
            except Exception as e:
                await message.reply_text(f"❌ Error: {str(e)}")
                await cleanup_session(user_id)
    
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")
        await cleanup_session(user_id)


async def handle_settings_input_data(client, message, setting_type, text):
    """Handle settings input (prefix, suffix, remove/replace words)"""
    user_id = message.from_user.id
    
    try:
        if setting_type == "prefix":
            await db.set_prefix(user_id, text)
            await message.reply_text(
                f"✅ **Prefix Set:** `{text}`",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Back to Settings", callback_data="auto_settings")
                ]])
            )
        
        elif setting_type == "suffix":
            await db.set_suffix(user_id, text)
            await message.reply_text(
                f"✅ **Suffix Set:** `{text}`",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Back to Settings", callback_data="auto_settings")
                ]])
            )
        
        elif setting_type == "remove_words":
            words = [w.strip() for w in text.split(',') if w.strip()]
            await db.set_remove_words(user_id, words)
            await message.reply_text(
                f"✅ **Remove Words Set ({len(words)} words):**\n`{', '.join(words)}`",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Back to Settings", callback_data="auto_settings")
                ]])
            )
        
        elif setting_type == "replace_words":
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
        
        # Clear state
        del user_states[user_id]
    
    except Exception as e:
        print(f"Error processing settings input: {e}")
        await message.reply_text(f"❌ **Error:** {e}")
        if user_id in user_states:
            del user_states[user_id]


# ============ CALLBACK QUERY HANDLER ============

@Client.on_callback_query()
async def cb_handler(client, query: CallbackQuery):
    data = query.data 
    user_id = query.from_user.id
    
    try:
        if data == "start":
            await query.message.edit_text(
                text=Txt.START_TXT.format(query.from_user.mention),
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton('𝐂𝐇𝐀𝐍𝐍𝐄𝐋', url='https://t.me/+JrRgnfZT0GYwOGZl'),
                    InlineKeyboardButton('Sᴜᴩᴩᴏʀᴛ', url='https://t.me/TG_SUPPORT_GROUP')
                    ],[
                    InlineKeyboardButton('⚙️ 𝐒𝐄𝐓𝐓𝐈𝐍𝐆𝐒 ⚙️', callback_data='settings') 
                    ]])
            )
        
        elif data == "settings":
            await query.message.edit_text(
                text=Txt.SETTINGS_TXT.format(client.mention),
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("𝐒𝐄𝐓 𝐂𝐀𝐏𝐓𝐈𝐎𝐍", callback_data='cap')
                    ],[
                    InlineKeyboardButton('𝐓𝐇𝐔𝐌𝐁𝐍𝐀𝐈𝐋', callback_data='thumbnail') 
                    ],[
                    InlineKeyboardButton('🔧 𝐑𝐄𝐍𝐀𝐌𝐄 𝐌𝐎𝐃𝐄', callback_data='rename_mode')
                    ],[
                    InlineKeyboardButton("🔒 Cʟᴏꜱᴇ", callback_data="close"),
                    InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="start")
                ]])            
            )
        
        elif data == "cap":
            await query.message.edit_text(
                text=Txt.CAP_TXT,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔒 Cʟᴏꜱᴇ", callback_data="close"),
                    InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="settings")
                ]])            
            )
        
        elif data == "thumbnail":
            await query.message.edit_text(
                text=Txt.THUMBNAIL_TXT.format(client.mention),
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔒 Cʟᴏꜱᴇ", callback_data="close"),
                    InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="settings")
                ]])            
            )
        
        elif data == "rename_mode":
            current_mode = await db.get_rename_mode(user_id)
            mode_emoji = "🤖" if current_mode == "auto" else "📝"
            
            await query.message.edit_text(
                text=Txt.RENAME_MODE_TXT.format(mode=f"{mode_emoji} {current_mode.upper()}"),
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📝 Mᴀɴᴜᴀʟ", callback_data="set_manual_mode"),
                    InlineKeyboardButton("🤖 Aᴜᴛᴏ", callback_data="set_auto_mode")
                    ],[
                    InlineKeyboardButton("⚙️ Aᴜᴛᴏ Sᴇᴛᴛɪɴɢꜱ", callback_data="auto_settings")
                    ],[
                    InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="settings")
                ]])
            )
        
        elif data == "set_manual_mode":
            await db.set_rename_mode(user_id, "manual")
            await query.answer("✅ Sᴇᴛ ᴛᴏ Mᴀɴᴜᴀʟ Mᴏᴅᴇ", show_alert=True)
            await cb_handler(client, CallbackQuery(client=client, id=query.id, from_user=query.from_user, message=query.message, data="rename_mode"))
        
        elif data == "set_auto_mode":
            await db.set_rename_mode(user_id, "auto")
            await query.answer("✅ Sᴇᴛ ᴛᴏ Aᴜᴛᴏ Mᴏᴅᴇ", show_alert=True)
            await cb_handler(client, CallbackQuery(client=client, id=query.id, from_user=query.from_user, message=query.message, data="rename_mode"))
        
        elif data == "auto_settings":
            await show_auto_settings(client, query)
        
        elif data in ["toggle_detect_type", "toggle_detect_lang", "toggle_auto_clean"]:
            await handle_toggle(client, query, data)
        
        elif data == "set_quality":
            await query.message.edit_text(
                text="<b>Sᴇʟᴇᴄᴛ Qᴜᴀʟɪᴛy Fᴏʀᴍᴀᴛ:</b>",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Kᴇᴇᴘ", callback_data="quality_keep"),
                    InlineKeyboardButton("Rᴇᴍᴏᴠᴇ", callback_data="quality_remove")
                    ],[
                    InlineKeyboardButton("480ᴘ", callback_data="quality_480p"),
                    InlineKeyboardButton("720ᴘ", callback_data="quality_720p"),
                    InlineKeyboardButton("1080ᴘ", callback_data="quality_1080p")
                    ],[
                    InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="auto_settings")
                ]])
            )
        
        elif data.startswith("quality_"):
            quality = data.split("_")[1]
            await db.set_quality_format(user_id, quality)
            await query.answer(f"✅ Qᴜᴀʟɪᴛy: {quality.upper()}", show_alert=True)
            await show_auto_settings(client, query)
        
        elif data in ["set_prefix", "set_suffix", "set_remove_words", "set_replace_words"]:
            await initiate_input(client, query, data)
        
        elif data in ["clear_prefix", "clear_suffix", "clear_remove_words", "clear_replace_words"]:
            await handle_clear(client, query, data)
        
        elif data == "close":
            try:
                await query.message.delete()
                if query.message.reply_to_message:
                    await query.message.reply_to_message.delete()
            except:
                pass
    
    except MessageNotModified:
        pass
    except Exception as e:
        print(f"Error in callback handler: {e}")
        try:
            await query.answer("❌ Error occurred", show_alert=True)
        except:
            pass


async def show_auto_settings(client, query):
    """Show auto settings page"""
    try:
        user_id = query.from_user.id
        settings = await db.get_all_rename_settings(user_id)
        
        detect_type = "✅" if settings['auto_detect_type'] else "❌"
        detect_lang = "✅" if settings['auto_detect_language'] else "❌"
        auto_clean = "✅" if settings['auto_clean'] else "❌"
        quality = settings['quality_format']
        prefix = settings['prefix'] if settings['prefix'] else "None"
        suffix = settings['suffix'] if settings['suffix'] else "None"
        
        remove_words = ', '.join(settings['remove_words'][:5]) if settings['remove_words'] else "None"
        if len(settings['remove_words']) > 5:
            remove_words += f"... (+{len(settings['remove_words'])-5})"
        
        replace_words = ', '.join([f"{k}→{v}" for k, v in list(settings['replace_words'].items())[:3]]) if settings['replace_words'] else "None"
        if len(settings['replace_words']) > 3:
            replace_words += f"... (+{len(settings['replace_words'])-3})"
        
        text = f"""**⚙️ Auto Rename Settings**

**Detection:**
├ Type: {detect_type} | Lang: {detect_lang}
└ Auto Clean: {auto_clean}

**Quality:** {quality}
**Prefix:** `{prefix}`
**Suffix:** `{suffix}`
**Remove:** `{remove_words}`
**Replace:** `{replace_words}`"""
        
        await query.message.edit_text(
            text=text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(f"{detect_type} Type", callback_data="toggle_detect_type"),
                InlineKeyboardButton(f"{detect_lang} Lang", callback_data="toggle_detect_lang")
                ],[
                InlineKeyboardButton("🎞️ Quality", callback_data="set_quality"),
                InlineKeyboardButton(f"{auto_clean} Clean", callback_data="toggle_auto_clean")
                ],[
                InlineKeyboardButton("➕ Prefix", callback_data="set_prefix"),
                InlineKeyboardButton("➕ Suffix", callback_data="set_suffix")
                ],[
                InlineKeyboardButton("🗑️ Remove", callback_data="set_remove_words"),
                InlineKeyboardButton("🔄 Replace", callback_data="set_replace_words")
                ],[
                InlineKeyboardButton("◀️ Back", callback_data="rename_mode")
            ]])
        )
    except Exception as e:
        print(f"Error showing auto settings: {e}")


async def handle_toggle(client, query, data):
    """Handle toggle callbacks"""
    try:
        user_id = query.from_user.id
        
        if data == "toggle_detect_type":
            current = await db.get_auto_detect_type(user_id)
            await db.set_auto_detect_type(user_id, not current)
            await query.answer(f"✅ Detect Type: {'OFF' if current else 'ON'}", show_alert=True)
        elif data == "toggle_detect_lang":
            current = await db.get_auto_detect_language(user_id)
            await db.set_auto_detect_language(user_id, not current)
            await query.answer(f"✅ Detect Lang: {'OFF' if current else 'ON'}", show_alert=True)
        elif data == "toggle_auto_clean":
            current = await db.get_auto_clean(user_id)
            await db.set_auto_clean(user_id, not current)
            await query.answer(f"✅ Auto Clean: {'OFF' if current else 'ON'}", show_alert=True)
        
        await show_auto_settings(client, query)
    except Exception as e:
        print(f"Error in toggle: {e}")


async def initiate_input(client, query, data):
    """Initiate input for prefix/suffix/remove/replace"""
    try:
        user_id = query.from_user.id
        setting = data.replace("set_", "")
        
        user_states[user_id] = setting
        
        messages = {
            "prefix": "Send me the prefix:\n\nExample: `@YourChannel`\n\n/cancel to cancel",
            "suffix": "Send me the suffix:\n\nExample: `@YourChannel`\n\n/cancel to cancel",
            "remove_words": "Send words to remove (comma separated):\n\nExample: `hdcam, sample, x264`\n\n/cancel to cancel",
            "replace_words": "Send replacement pairs:\n\nFormat: `old:new, old2:new2`\n\nExample: `tamil:kannada, 480p:720p`\n\n/cancel to cancel"
        }
        
        await query.message.edit_text(
            f"**{messages[setting]}**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data=f"clear_{setting}")
            ]])
        )
    except Exception as e:
        print(f"Error initiating input: {e}")


async def handle_clear(client, query, data):
    """Handle clear callbacks"""
    try:
        user_id = query.from_user.id
        
        if data == "clear_prefix":
            await db.set_prefix(user_id, "")
            await query.answer("✅ Prefix Cleared", show_alert=True)
        elif data == "clear_suffix":
            await db.set_suffix(user_id, "")
            await query.answer("✅ Suffix Cleared", show_alert=True)
        elif data == "clear_remove_words":
            await db.set_remove_words(user_id, [])
            await query.answer("✅ Remove Words Cleared", show_alert=True)
        elif data == "clear_replace_words":
            await db.set_replace_words(user_id, {})
            await query.answer("✅ Replace Words Cleared", show_alert=True)
        
        if user_id in user_states:
            del user_states[user_id]
        
        await show_auto_settings(client, query)
    except Exception as e:
        print(f"Error in clear: {e}")
