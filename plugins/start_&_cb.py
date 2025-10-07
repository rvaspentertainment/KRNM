import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply, CallbackQuery
from pyrogram.errors import MessageNotModified, MessageDeleteForbidden, QueryIdInvalid, UserIsBlocked
from helper.database import db
from config import Config, Txt  


from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import (
    ApiIdInvalid, 
    PhoneNumberInvalid, 
    PhoneCodeInvalid, 
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid
)
import asyncio

# Dictionary to store user session generation states
user_states = {}

class SessionState:
    def __init__(self):
        self.api_id = None
        self.api_hash = None
        self.phone = None
        self.client = None
        self.phone_code_hash = None

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
        
        # Initialize state for this user
        user_states[user_id] = SessionState()
        user_states[user_id].step = "api_id"
        
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")


@Client.on_message(filters.private & filters.text & ~filters.command(["start", "cancel", "string"]))
async def handle_string_session_steps(client, message: Message):
    user_id = message.from_user.id
    
    # Check if user is in string session generation process
    if user_id not in user_states:
        return
    
    state = user_states[user_id]
    text = message.text.strip()
    
    try:
        # Step 1: Receive API_ID
        if state.step == "api_id":
            if not text.isdigit():
                await message.reply_text("❌ API_ID must be a number. Please send a valid API_ID:")
                return
            
            state.api_id = int(text)
            state.step = "api_hash"
            await message.reply_text(
                "✅ API_ID received!\n\n"
                "Now send your <b>API_HASH</b>"
            )
        
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
                # Create client and send OTP
                state.client = Client(
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
                await state.client.sign_in(
                    state.phone,
                    state.phone_code_hash,
                    otp
                )
                
                # Get string session
                string_session = await state.client.export_session_string()
                
                await message.reply_text(
                    "✅ <b>String Session Generated Successfully!</b>\n\n"
                    f"<code>{string_session}</code>\n\n"
                    "⚠️ <b>Keep this safe and never share it with anyone!</b>",
                    disable_web_page_preview=True
                )
                
                await cleanup_session(user_id)
                
            except PhoneCodeInvalid:
                await message.reply_text(
                    "❌ Invalid OTP code. Please try again.\n"
                    "Send the correct OTP:"
                )
            except PhoneCodeExpired:
                await message.reply_text(
                    "❌ OTP has expired. Please start again with /string"
                )
                await cleanup_session(user_id)
            except SessionPasswordNeeded:
                state.step = "2fa"
                await message.reply_text(
                    "🔐 Your account has 2FA enabled.\n\n"
                    "Please send your <b>2FA Password</b>:"
                )
            except Exception as e:
                await message.reply_text(f"❌ Error: {str(e)}")
                await cleanup_session(user_id)
        
        # Step 5: Receive 2FA Password (if enabled)
        elif state.step == "2fa":
            password = text
            
            try:
                await state.client.check_password(password)
                
                # Get string session
                string_session = await state.client.export_session_string()
                
                await message.reply_text(
                    "✅ <b>String Session Generated Successfully!</b>\n\n"
                    f"<code>{string_session}</code>\n\n"
                    "⚠️ <b>Keep this safe and never share it with anyone!</b>",
                    disable_web_page_preview=True
                )
                
                await cleanup_session(user_id)
                
            except PasswordHashInvalid:
                await message.reply_text(
                    "❌ Invalid 2FA password. Please try again.\n"
                    "Send the correct password:"
                )
            except Exception as e:
                await message.reply_text(f"❌ Error: {str(e)}")
                await cleanup_session(user_id)
    
    except Exception as e:
        await message.reply_text(f"❌ An error occurred: {str(e)}")
        await cleanup_session(user_id)


@Client.on_message(filters.private & filters.command("cancel"))
async def cancel_string_generation(client, message: Message):
    user_id = message.from_user.id
    
    if user_id in user_states:
        await cleanup_session(user_id)
        await message.reply_text("✅ String session generation cancelled.")
    else:
        await message.reply_text("❌ No active session generation to cancel.")


async def cleanup_session(user_id):
    """Clean up session generation state"""
    if user_id in user_states:
        state = user_states[user_id]
        
        # Disconnect and clean up client if exists
        if state.client:
            try:
                await state.client.disconnect()
            except:
                pass
        
        # Remove user state
        del user_states[user_id]

@Client.on_message(filters.private & filters.command("start"))
async def start(client, message):
    user = message.from_user
    await db.add_user(client, message)                
    button = InlineKeyboardMarkup([[
        InlineKeyboardButton('𝐂𝐇𝐀𝐍𝐍𝐄𝐋', url='https://t.me/+JrRgnfZT0GYwOGZl'),
        InlineKeyboardButton('Sᴜᴩᴩᴏʀᴛ', url='https://t.me/TG_SUPPORT_GROUP')
        ],[
        InlineKeyboardButton('⚙️ 𝐒𝐄𝐓𝐓𝐈𝐍𝐆𝐒 ⚙️', callback_data='settings') 
        ],[
        
    ]])
    try:
        if Config.START_PIC:
            await message.reply_photo(Config.START_PIC, caption=Txt.START_TXT.format(user.mention), reply_markup=button)       
        else:
            await message.reply_text(text=Txt.START_TXT.format(user.mention), reply_markup=button, disable_web_page_preview=True)
    except UserIsBlocked:
        print(f"User {user_id} has blocked the bot")
    except Exception as e:
        print(f"Error in start command: {e}")
   

@Client.on_callback_query()
async def cb_handler(client, query: CallbackQuery):
    data = query.data 
    user_id = query.from_user.id
    
    if data == "start":
        try:
            await query.message.edit_text(
                text=Txt.START_TXT.format(query.from_user.mention),
                disable_web_page_preview=True,
                reply_markup = InlineKeyboardMarkup([[
                    InlineKeyboardButton('𝐂𝐇𝐀𝐍𝐍𝐄𝐋', url='https://t.me/+JrRgnfZT0GYwOGZl'),
                    InlineKeyboardButton('Sᴜᴩᴩᴏʀᴛ', url='https://t.me/TG_SUPPORT_GROUP')
                    ],[
                    InlineKeyboardButton('⚙️ 𝐒𝐄𝐓𝐓𝐈𝐍𝐆𝐒 ⚙️', callback_data='settings') 
                    ],[
                    
                ]])
            )
        except MessageNotModified:
            pass
        except Exception as e:
            print(f"Error in start callback: {e}")
    
    
    elif data == "settings":
        try:
            await query.message.edit_text(
                text=Txt.SETTINGS_TXT.format(client.mention),
                disable_web_page_preview = True,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("𝐒𝐄𝐓 𝐂𝐀𝐏𝐓𝐈𝐎𝐍", callback_data='cap')
                    ],[
                    InlineKeyboardButton('𝐓𝐇𝐔𝐌𝐁𝐍𝐀𝐈𝐋', callback_data='thumbnail') 
                    ],[
                    InlineKeyboardButton('🔧 𝐑𝐄𝐍𝐀𝐌𝐄 𝐌𝐎𝐃𝐄', callback_data='rename_mode')
                    ],[
                    InlineKeyboardButton("🔒 Cʟᴏꜱᴇ", callback_data = "close"),
                    InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data = "start")
                ]])            
            )
        except MessageNotModified:
            pass
        except Exception as e:
            print(f"Error in settings callback: {e}")
   
    elif data == "cap":
        try:
            await query.message.edit_text(
                text=Txt.CAP_TXT,
                disable_web_page_preview = True,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔒 Cʟᴏꜱᴇ", callback_data = "close"),
                    InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data = "settings")
                ]])            
            )
        except MessageNotModified:
            pass
        except Exception as e:
            print(f"Error in cap callback: {e}")
        
    elif data == "thumbnail":
        try:
            await query.message.edit_text(
                text=Txt.THUMBNAIL_TXT.format(client.mention),
                disable_web_page_preview = True,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔒 Cʟᴏꜱᴇ", callback_data = "close"),
                    InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data = "settings")
                ]])            
            )
        except MessageNotModified:
            pass
        except Exception as e:
            print(f"Error in thumbnail callback: {e}")
    
    # RENAME MODE SETTINGS
    elif data == "rename_mode":
        try:
            current_mode = await db.get_rename_mode(user_id)
            mode_emoji = "🤖" if current_mode == "auto" else "📝"
            
            await query.message.edit_text(
                text=Txt.RENAME_MODE_TXT.format(mode=f"{mode_emoji} {current_mode.upper()}"),
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📝 Mᴀɴᴜᴀʟ Mᴏᴅᴇ", callback_data="set_manual_mode"),
                    InlineKeyboardButton("🤖 Aᴜᴛᴏ Mᴏᴅᴇ", callback_data="set_auto_mode")
                    ],[
                    InlineKeyboardButton("⚙️ Aᴜᴛᴏ Sᴇᴛᴛɪɴɢꜱ", callback_data="auto_settings")
                    ],[
                    InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="settings")
                ]])
            )
        except MessageNotModified:
            pass
        except Exception as e:
            print(f"Error in rename_mode callback: {e}")
    
    elif data == "set_manual_mode":
        try:
            await db.set_rename_mode(user_id, "manual")
            try:
                await query.answer("✅ Sᴇᴛ ᴛᴏ Mᴀɴᴜᴀʟ Mᴏᴅᴇ", show_alert=True)
            except QueryIdInvalid:
                pass
            
            await query.message.edit_text(
                text=Txt.RENAME_MODE_TXT.format(mode="📝 MANUAL"),
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📝 Mᴀɴᴜᴀʟ Mᴏᴅᴇ", callback_data="set_manual_mode"),
                    InlineKeyboardButton("🤖 Aᴜᴛᴏ Mᴏᴅᴇ", callback_data="set_auto_mode")
                    ],[
                    InlineKeyboardButton("⚙️ Aᴜᴛᴏ Sᴇᴛᴛɪɴɢꜱ", callback_data="auto_settings")
                    ],[
                    InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="settings")
                ]])
            )
        except MessageNotModified:
            pass
        except Exception as e:
            print(f"Error in set_manual_mode callback: {e}")
    
    elif data == "set_auto_mode":
        try:
            await db.set_rename_mode(user_id, "auto")
            try:
                await query.answer("✅ Sᴇᴛ ᴛᴏ Aᴜᴛᴏ Mᴏᴅᴇ", show_alert=True)
            except QueryIdInvalid:
                pass
            
            await query.message.edit_text(
                text=Txt.RENAME_MODE_TXT.format(mode="🤖 AUTO"),
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📝 Mᴀɴᴜᴀʟ Mᴏᴅᴇ", callback_data="set_manual_mode"),
                    InlineKeyboardButton("🤖 Aᴜᴛᴏ Mᴏᴅᴇ", callback_data="set_auto_mode")
                    ],[
                    InlineKeyboardButton("⚙️ Aᴜᴛᴏ Sᴇᴛᴛɪɴɢꜱ", callback_data="auto_settings")
                    ],[
                    InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="settings")
                ]])
            )
        except MessageNotModified:
            pass
        except Exception as e:
            print(f"Error in set_auto_mode callback: {e}")
    
    # AUTO SETTINGS MENU
    elif data == "auto_settings":
        try:
            settings = await db.get_all_rename_settings(user_id)
            
            detect_type = "✅ ON" if settings['auto_detect_type'] else "❌ OFF"
            detect_lang = "✅ ON" if settings['auto_detect_language'] else "❌ OFF"
            auto_clean = "✅ ON" if settings['auto_clean'] else "❌ OFF"
            quality = settings['quality_format']
            prefix = settings['prefix'] if settings['prefix'] else "None"
            suffix = settings['suffix'] if settings['suffix'] else "None"
            remove_words = ', '.join(settings['remove_words']) if settings['remove_words'] else "None"
            replace_words = ', '.join([f"{k}→{v}" for k,v in settings['replace_words'].items()]) if settings['replace_words'] else "None"
            
            await query.message.edit_text(
                text=Txt.AUTO_SETTINGS_TXT.format(
                    detect_type=detect_type,
                    detect_lang=detect_lang,
                    quality=quality,
                    auto_clean=auto_clean,
                    prefix=prefix,
                    suffix=suffix,
                    remove_words=remove_words,
                    replace_words=replace_words
                ),
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🎬 Dᴇᴛᴇᴄᴛ Tyᴘᴇ", callback_data="toggle_detect_type"),
                    InlineKeyboardButton("🗣️ Dᴇᴛᴇᴄᴛ Lᴀɴɢ", callback_data="toggle_detect_lang")
                    ],[
                    InlineKeyboardButton("🎞️ Qᴜᴀʟɪᴛy", callback_data="set_quality"),
                    InlineKeyboardButton("🧹 Aᴜᴛᴏ Cʟᴇᴀɴ", callback_data="toggle_auto_clean")
                    ],[
                    InlineKeyboardButton("➕ Pʀᴇꜰɪx", callback_data="set_prefix"),
                    InlineKeyboardButton("➕ Sᴜꜰꜰɪx", callback_data="set_suffix")
                    ],[
                    InlineKeyboardButton("🗑️ Rᴇᴍᴏᴠᴇ Wᴏʀᴅꜱ", callback_data="set_remove_words"),
                    InlineKeyboardButton("🔄 Rᴇᴘʟᴀᴄᴇ Wᴏʀᴅꜱ", callback_data="set_replace_words")
                    ],[
                    InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="rename_mode")
                ]])
            )
        except MessageNotModified:
            pass
        except Exception as e:
            print(f"Error in auto_settings callback: {e}")
    
    # TOGGLE SETTINGS
    elif data == "toggle_detect_type":
        try:
            current = await db.get_auto_detect_type(user_id)
            new_value = not current
            await db.set_auto_detect_type(user_id, new_value)
            try:
                await query.answer(f"✅ Aᴜᴛᴏ Dᴇᴛᴇᴄᴛ Tyᴘᴇ: {'ON' if new_value else 'OFF'}", show_alert=True)
            except QueryIdInvalid:
                pass
            # Refresh settings page
            await cb_handler(client, CallbackQuery(client=client, id=query.id, from_user=query.from_user, message=query.message, data="auto_settings"))
        except Exception as e:
            print(f"Error in toggle_detect_type: {e}")
    
    elif data == "toggle_detect_lang":
        try:
            current = await db.get_auto_detect_language(user_id)
            new_value = not current
            await db.set_auto_detect_language(user_id, new_value)
            try:
                await query.answer(f"✅ Aᴜᴛᴏ Dᴇᴛᴇᴄᴛ Lᴀɴɢᴜᴀɢᴇ: {'ON' if new_value else 'OFF'}", show_alert=True)
            except QueryIdInvalid:
                pass
            await cb_handler(client, CallbackQuery(client=client, id=query.id, from_user=query.from_user, message=query.message, data="auto_settings"))
        except Exception as e:
            print(f"Error in toggle_detect_lang: {e}")
    
    elif data == "toggle_auto_clean":
        try:
            current = await db.get_auto_clean(user_id)
            new_value = not current
            await db.set_auto_clean(user_id, new_value)
            try:
                await query.answer(f"✅ Aᴜᴛᴏ Cʟᴇᴀɴ: {'ON' if new_value else 'OFF'}", show_alert=True)
            except QueryIdInvalid:
                pass
            await cb_handler(client, CallbackQuery(client=client, id=query.id, from_user=query.from_user, message=query.message, data="auto_settings"))
        except Exception as e:
            print(f"Error in toggle_auto_clean: {e}")
    
    elif data == "set_quality":
        try:
            await query.message.edit_text(
                text="<b>Sᴇʟᴇᴄᴛ Qᴜᴀʟɪᴛy Fᴏʀᴍᴀᴛ:</b>",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Kᴇᴇᴘ Oʀɪɢɪɴᴀʟ", callback_data="quality_keep"),
                    InlineKeyboardButton("Rᴇᴍᴏᴠᴇ", callback_data="quality_remove")
                    ],[
                    InlineKeyboardButton("480ᴘ", callback_data="quality_480p"),
                    InlineKeyboardButton("720ᴘ", callback_data="quality_720p"),
                    InlineKeyboardButton("1080ᴘ", callback_data="quality_1080p")
                    ],[
                    InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="auto_settings")
                ]])
            )
        except MessageNotModified:
            pass
        except Exception as e:
            print(f"Error in set_quality: {e}")
    
    elif data.startswith("quality_"):
        try:
            quality = data.split("_")[1]
            await db.set_quality_format(user_id, quality)
            try:
                await query.answer(f"✅ Qᴜᴀʟɪᴛy ꜱᴇᴛ ᴛᴏ: {quality.upper()}", show_alert=True)
            except QueryIdInvalid:
                pass
            await cb_handler(client, CallbackQuery(client=client, id=query.id, from_user=query.from_user, message=query.message, data="auto_settings"))
        except Exception as e:
            print(f"Error in quality setting: {e}")
    
    elif data == "set_prefix":
        try:
            await query.message.edit_text(
                text="<b>Sᴇɴᴅ ᴍᴇ ᴛʜᴇ ᴘʀᴇꜰɪx ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴀᴅᴅ:\n\nExᴀᴍᴘʟᴇ: <code>@YourChannel</code>\n\nSᴇɴᴅ /cancel ᴛᴏ ᴄᴀɴᴄᴇʟ</b>",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🗑️ Cʟᴇᴀʀ Pʀᴇꜰɪx", callback_data="clear_prefix"),
                    InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="auto_settings")
                ]])
            )
        except MessageNotModified:
            pass
        except Exception as e:
            print(f"Error in set_prefix: {e}")
    
    elif data == "clear_prefix":
        try:
            await db.set_prefix(user_id, "")
            try:
                await query.answer("✅ Pʀᴇꜰɪx Cʟᴇᴀʀᴇᴅ", show_alert=True)
            except QueryIdInvalid:
                pass
            await cb_handler(client, CallbackQuery(client=client, id=query.id, from_user=query.from_user, message=query.message, data="auto_settings"))
        except Exception as e:
            print(f"Error in clear_prefix: {e}")
    
    elif data == "set_suffix":
        try:
            await query.message.edit_text(
                text="<b>Sᴇɴᴅ ᴍᴇ ᴛʜᴇ ꜱᴜꜰꜰɪx ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴀᴅᴅ:\n\nExᴀᴍᴘʟᴇ: <code>@YourChannel</code>\n\nSᴇɴᴅ /cancel ᴛᴏ ᴄᴀɴᴄᴇʟ</b>",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🗑️ Cʟᴇᴀʀ Sᴜꜰꜰɪx", callback_data="clear_suffix"),
                    InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="auto_settings")
                ]])
            )
        except MessageNotModified:
            pass
        except Exception as e:
            print(f"Error in set_suffix: {e}")
    
    elif data == "clear_suffix":
        try:
            await db.set_suffix(user_id, "")
            try:
                await query.answer("✅ Sᴜꜰꜰɪx Cʟᴇᴀʀᴇᴅ", show_alert=True)
            except QueryIdInvalid:
                pass
            await cb_handler(client, CallbackQuery(client=client, id=query.id, from_user=query.from_user, message=query.message, data="auto_settings"))
        except Exception as e:
            print(f"Error in clear_suffix: {e}")
    
    elif data == "set_remove_words":
        try:
            current_words = await db.get_remove_words(user_id)
            words_list = ', '.join(current_words) if current_words else "None"
            await query.message.edit_text(
                text=f"<b>Sᴇɴᴅ ᴡᴏʀᴅꜱ ᴛᴏ ʀᴇᴍᴏᴠᴇ (ꜱᴇᴘᴀʀᴀᴛᴇᴅ ʙʏ ᴄᴏᴍᴍᴀ):\n\nCᴜʀʀᴇɴᴛ: <code>{words_list}</code>\n\nExᴀᴍᴘʟᴇ: <code>hdcam, sample, x264</code>\n\nSᴇɴᴅ /cancel ᴛᴏ ᴄᴀɴᴄᴇʟ</b>",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🗑️ Cʟᴇᴀʀ Aʟʟ", callback_data="clear_remove_words"),
                    InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="auto_settings")
                ]])
            )
        except MessageNotModified:
            pass
        except Exception as e:
            print(f"Error in set_remove_words: {e}")
    
    elif data == "clear_remove_words":
        try:
            await db.set_remove_words(user_id, [])
            try:
                await query.answer("✅ Rᴇᴍᴏᴠᴇ Wᴏʀᴅꜱ Cʟᴇᴀʀᴇᴅ", show_alert=True)
            except QueryIdInvalid:
                pass
            await cb_handler(client, CallbackQuery(client=client, id=query.id, from_user=query.from_user, message=query.message, data="auto_settings"))
        except Exception as e:
            print(f"Error in clear_remove_words: {e}")
    
    elif data == "set_replace_words":
        try:
            current_words = await db.get_replace_words(user_id)
            words_list = ', '.join([f"{k}→{v}" for k,v in current_words.items()]) if current_words else "None"
            await query.message.edit_text(
                text=f"<b>Sᴇɴᴅ ᴡᴏʀᴅ ᴘᴀɪʀꜱ ᴛᴏ ʀᴇᴘʟᴀᴄᴇ:\n\nCᴜʀʀᴇɴᴛ: <code>{words_list}</code>\n\nFᴏʀᴍᴀᴛ: <code>old1:new1, old2:new2</code>\n\nExᴀᴍᴘʟᴇ: <code>hdcam:HD, x264:HEVC</code>\n\nSᴇɴᴅ /cancel ᴛᴏ ᴄᴀɴᴄᴇʟ</b>",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🗑️ Cʟᴇᴀʀ Aʟʟ", callback_data="clear_replace_words"),
                    InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="auto_settings")
                ]])
            )
        except MessageNotModified:
            pass
        except Exception as e:
            print(f"Error in set_replace_words: {e}")
    
    elif data == "clear_replace_words":
        try:
            await db.set_replace_words(user_id, {})
            try:
                await query.answer("✅ Rᴇᴘʟᴀᴄᴇ Wᴏʀᴅꜱ Cʟᴇᴀʀᴇᴅ", show_alert=True)
            except QueryIdInvalid:
                pass
            await cb_handler(client, CallbackQuery(client=client, id=query.id, from_user=query.from_user, message=query.message, data="auto_settings"))
        except Exception as e:
            print(f"Error in clear_replace_words: {e}")
    
    elif data == "close":
        try:
            await query.message.delete()
            if query.message.reply_to_message:
                try:
                    await query.message.reply_to_message.delete()
                except MessageDeleteForbidden:
                    pass
        except MessageDeleteForbidden:
            try:
                await query.answer("⚠️ Cᴀɴɴᴏᴛ ᴅᴇʟᴇᴛᴇ ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ", show_alert=True)
            except QueryIdInvalid:
                pass
        except Exception as e:
            print(f"Error in close callback: {e}")


# Handler for receiving prefix/suffix/remove/replace words
@Client.on_message(filters.private & filters.text & ~filters.command(["start", "cancel"]))
async def handle_settings_input(client, message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Check if user is setting prefix (you'll need to track state)
    # For now, this is a simple implementation
    # You might want to use a state management system
    
    # This is just an example - you'll need proper state management
    pass
