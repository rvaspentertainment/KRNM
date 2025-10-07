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
from plugins.settings_handler import user_setting_state
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
                    InlineKeyboardButton('📤 𝐔𝐏𝐋𝐎𝐀𝐃 𝐒𝐄𝐓𝐓𝐈𝐍𝐆𝐒', callback_data='upload_settings')
                    ],[
                    InlineKeyboardButton("🔒 Cʟᴏꜱᴇ", callback_data="close"),
                    InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="start")
                ]])            
            )
        
        elif data == "upload_settings":
            upload_as = await db.get_upload_as(user_id)
            upload_channel = await db.get_upload_channel(user_id)            
            upload_type_text = {
                "document": "📁 Document", 
                "video": "🎥 Video", 
                "audio": "🎵 Audio"
            }.get(upload_as, "📁 Document")
            channel_text = f"Set: `{upload_channel}`" if upload_channel else "Not Set"
            await query.message.edit_text(
                text=f"**📤 Upload Settings**\n\n**Upload As:** {upload_type_text}\n**Channel:** {channel_text}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📁 Document", callback_data="upload_type_document"),
                    InlineKeyboardButton("🎥 Video", callback_data="upload_type_video")
                ],[
                    InlineKeyboardButton("🎵 Audio", callback_data="upload_type_audio")
                ],[
                    InlineKeyboardButton("📢 Set Channel", callback_data="set_upload_channel")
                ],[
                    InlineKeyboardButton("◀️ Back", callback_data="settings")
                ]])
            )

        
        elif data in ["set_upload_document", "set_upload_video", "set_upload_audio"]:
            upload_type = data.split("_")[2]
            await db.set_upload_as(user_id, upload_type)
            await query.answer(f"✅ Upload as {upload_type.upper()}", show_alert=True)
            await cb_handler(client, CallbackQuery(client=client, id=query.id, from_user=query.from_user, message=query.message, data="upload_settings"))
        
        elif data == "set_upload_channel":
            user_setting_state[user_id] = "upload_channel"
            await query.message.edit_text(
                "**Send Channel ID or Username:**\n\nExample: `-1001234567890` or `@username`\n\n/cancel to cancel",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Clear Channel", callback_data="clear_upload_channel")
                ]])
            )
        
        elif data == "clear_upload_channel":
            await db.set_upload_channel(user_id, None)
            await query.answer("✅ Channel Cleared", show_alert=True)
            if user_id in user_setting_state:
                del user_setting_state[user_id]
            await cb_handler(client, CallbackQuery(client=client, id=query.id, from_user=query.from_user, message=query.message, data="upload_settings"))
        
        elif data == "rename_mode":
            current_mode = await db.get_rename_mode(user_id)
            always_ask = await db.get_always_ask(user_id)
            mode_emoji = "🤖" if current_mode == "auto" else "📝"
            ask_emoji = "✅" if always_ask else "❌"
            
            await query.message.edit_text(
                text=f"**🔧 Rename Mode Settings**\n\n**Current Mode:** {mode_emoji} {current_mode.upper()}\n**Always Ask:** {ask_emoji}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📝 Manual", callback_data="set_manual_mode"),
                    InlineKeyboardButton("🤖 Auto", callback_data="set_auto_mode")
                    ],[
                    InlineKeyboardButton(f"{ask_emoji} Confirm", callback_data="toggle_always_ask")
                    ],[
                    InlineKeyboardButton("⚙️ Auto Settings", callback_data="auto_settings")
                    ],[
                    InlineKeyboardButton("◀️ Back", callback_data="settings")
                ]])
            )
        
        elif data == "toggle_always_ask":
            current = await db.get_always_ask(user_id)
            await db.set_always_ask(user_id, not current)
            await query.answer(f"✅ Confirm: {'ON' if not current else 'OFF'}", show_alert=True)
            await cb_handler(client, CallbackQuery(client=client, id=query.id, from_user=query.from_user, message=query.message, data="rename_mode"))
        
        elif data == "auto_settings":
            await show_auto_settings(client, query)
        
        elif data in ["toggle_auto_detect_all", "toggle_auto_clean"]:
            await handle_toggle(client, query, data)
        
        elif data == "set_quality":
            await query.message.edit_text(
                text="**🎞️ Select Quality Format:**",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Keep Original", callback_data="quality_keep"),
                    InlineKeyboardButton("Remove", callback_data="quality_remove")
                    ],[
                    InlineKeyboardButton("480p", callback_data="quality_480p"),
                    InlineKeyboardButton("720p", callback_data="quality_720p"),
                    InlineKeyboardButton("1080p", callback_data="quality_1080p")
                    ],[
                    InlineKeyboardButton("◀️ Back", callback_data="auto_settings")
                ]])
            )
        
        elif data.startswith("quality_"):
            quality = data.split("_")[1]
            await db.set_quality_format(user_id, quality)
            await query.answer(f"✅ Quality: {quality.upper()}", show_alert=True)
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
        
        # Single toggle for all auto detection
        auto_detect = settings['auto_detect_language'] and settings['auto_detect_year'] and settings['auto_detect_quality']
        detect_emoji = "✅" if auto_detect else "❌"
        auto_clean = "✅" if settings['auto_clean'] else "❌"
        quality = settings['quality_format']
        prefix = settings['prefix'][:20] if settings['prefix'] else "None"
        suffix = settings['suffix'][:20] if settings['suffix'] else "None"
        
        remove_count = len(settings['remove_words'])
        replace_count = len(settings['replace_words'])
        
        text = f"""**⚙️ Auto Rename Settings**

**Auto Detect:** {detect_emoji} (Year, Lang, Quality, etc.)
**Auto Clean:** {auto_clean}
**Quality:** {quality}

**Customization:**
├ Prefix: `{prefix}`
├ Suffix: `{suffix}`
├ Remove Words: {remove_count} words
└ Replace Words: {replace_count} pairs"""
        
        await query.message.edit_text(
            text=text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(f"{detect_emoji} Auto Detect", callback_data="toggle_auto_detect_all"),
                InlineKeyboardButton(f"{auto_clean} Clean", callback_data="toggle_auto_clean")
                ],[
                InlineKeyboardButton("🎞️ Quality", callback_data="set_quality")
                ],[
                InlineKeyboardButton("➕ Prefix", callback_data="set_prefix"),
                InlineKeyboardButton("➕ Suffix", callback_data="set_suffix")
                ],[
                InlineKeyboardButton(f"🗑️ Remove ({remove_count})", callback_data="set_remove_words"),
                InlineKeyboardButton(f"🔄 Replace ({replace_count})", callback_data="set_replace_words")
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
        
        if data == "toggle_auto_detect_all":
            # Toggle all detection settings at once
            current = await db.get_auto_detect_language(user_id)
            new_value = not current
            await db.set_auto_detect_type(user_id, new_value)
            await db.set_auto_detect_language(user_id, new_value)
            await db.set_auto_detect_year(user_id, new_value)
            await db.set_auto_detect_quality(user_id, new_value)
            await db.set_auto_detect_source(user_id, new_value)
            await db.set_auto_detect_ott(user_id, new_value)
            await db.set_auto_detect_encoding(user_id, new_value)
            await db.set_auto_detect_audio(user_id, new_value)
            await query.answer(f"✅ Auto Detect: {'ON' if new_value else 'OFF'}", show_alert=True)
        elif data == "toggle_auto_clean":
            current = await db.get_auto_clean(user_id)
            await db.set_auto_clean(user_id, not current)
            await query.answer(f"✅ Auto Clean: {'ON' if not current else 'OFF'}", show_alert=True)
        
        await show_auto_settings(client, query)
    except Exception as e:
        print(f"Error in toggle: {e}")


async def initiate_input(client, query, data):
    """Initiate input for prefix/suffix/remove/replace"""
    try:
        user_id = query.from_user.id
        setting = data.replace("set_", "")
        
        user_setting_state[user_id] = setting
        
        messages = {
            "prefix": "**Send me the prefix:**\n\nExample: `@YourChannel`\n\n/cancel to cancel",
            "suffix": "**Send me the suffix:**\n\nExample: `@YourChannel`\n\n/cancel to cancel",
            "remove_words": "**Send words to remove (comma separated):**\n\nExample: `hdcam, sample, x264, torrent`\n\n/cancel to cancel",
            "replace_words": "**Send replacement pairs:**\n\nFormat: `old:new, old2:new2`\n\nExample: `tamil:kannada, english:hindi, 480p:720p`\n\n/cancel to cancel"
        }
        
        await query.message.edit_text(
            messages[setting],
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
        
        if user_id in user_setting_state:
            del user_setting_state[user_id]
        
        await show_auto_settings(client, query)
    except Exception as e:
        print(f"Error in clear: {e}")
