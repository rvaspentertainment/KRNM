from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from pyrogram.errors import (
    MessageNotModified, ApiIdInvalid, PhoneNumberInvalid, PhoneCodeInvalid, 
    PhoneCodeExpired, SessionPasswordNeeded, PasswordHashInvalid
)
from helper.database import db
from config import Config, Txt
import asyncio

# Try to import ListenerTimeout from pyromod if available
try:
    from pyromod.exceptions import ListenerTimeout
except ImportError:
    # Fallback: create a custom exception if pyromod is not installed
    class ListenerTimeout(Exception):
        pass

# ============ STRING SESSION GENERATOR ============

@Client.on_message(filters.private & filters.command("string"))
async def generate_string_session(client, message: Message):
    user_id = message.from_user.id
    
    try:
        # Step 1: Get API_ID
        api_id_msg = await client.ask(
            chat_id=user_id,
            text="<b>📱 STRING SESSION GENERATOR</b>\n\n"
                 "⚠️ <b>WARNING:</b> Never share your string session with anyone!\n\n"
                 "Please send your <b>API_ID</b>\n\n"
                 "Get it from: https://my.telegram.org\n\n"
                 "Send /cancel to cancel",
            timeout=300
        )
        
        if api_id_msg.text == "/cancel":
            return await api_id_msg.reply_text("✅ Operation cancelled.")
        
        if not api_id_msg.text.isdigit():
            return await api_id_msg.reply_text("❌ API_ID must be a number. Please try again with /string")
        
        api_id = int(api_id_msg.text)
        
        # Step 2: Get API_HASH
        api_hash_msg = await client.ask(
            chat_id=user_id,
            text="✅ API_ID received!\n\nNow send your <b>API_HASH</b>\n\nSend /cancel to cancel",
            timeout=300
        )
        
        if api_hash_msg.text == "/cancel":
            return await api_hash_msg.reply_text("✅ Operation cancelled.")
        
        api_hash = api_hash_msg.text.strip()
        
        # Step 3: Get Phone Number
        phone_msg = await client.ask(
            chat_id=user_id,
            text="✅ API_HASH received!\n\n"
                 "Now send your <b>Phone Number</b> with country code\n"
                 "Example: +1234567890\n\nSend /cancel to cancel",
            timeout=300
        )
        
        if phone_msg.text == "/cancel":
            return await phone_msg.reply_text("✅ Operation cancelled.")
        
        phone = phone_msg.text.strip()
        
        # Connect and send OTP
        try:
            from pyrogram import Client as PyroClient
            temp_client = PyroClient(
                name=f"session_{user_id}",
                api_id=api_id,
                api_hash=api_hash,
                in_memory=True
            )
            
            await temp_client.connect()
            code = await temp_client.send_code(phone)
            phone_code_hash = code.phone_code_hash
            
            # Step 4: Get OTP
            otp_msg = await client.ask(
                chat_id=user_id,
                text="✅ OTP sent to your Telegram account!\n\n"
                     "Please send the <b>OTP code</b> you received.\n"
                     "Example: 12345\n\nSend /cancel to cancel",
                timeout=300
            )
            
            if otp_msg.text == "/cancel":
                await temp_client.disconnect()
                return await otp_msg.reply_text("✅ Operation cancelled.")
            
            otp = otp_msg.text.replace(" ", "")
            
            # Try to sign in
            try:
                await temp_client.sign_in(phone, phone_code_hash, otp)
                string_session = await temp_client.export_session_string()
                
                await otp_msg.reply_text(
                    "✅ <b>String Session Generated Successfully!</b>\n\n"
                    f"<code>{string_session}</code>\n\n"
                    "⚠️ <b>Keep this safe and never share it with anyone!</b>",
                    disable_web_page_preview=True
                )
                
                await temp_client.disconnect()
                
            except SessionPasswordNeeded:
                # Step 5: Get 2FA Password
                password_msg = await client.ask(
                    chat_id=user_id,
                    text="🔐 Your account has 2FA enabled.\n\nPlease send your <b>2FA Password</b>:\n\nSend /cancel to cancel",
                    timeout=300
                )
                
                if password_msg.text == "/cancel":
                    await temp_client.disconnect()
                    return await password_msg.reply_text("✅ Operation cancelled.")
                
                try:
                    await temp_client.check_password(password_msg.text)
                    string_session = await temp_client.export_session_string()
                    
                    await password_msg.reply_text(
                        "✅ <b>String Session Generated Successfully!</b>\n\n"
                        f"<code>{string_session}</code>\n\n"
                        "⚠️ <b>Keep this safe and never share it with anyone!</b>",
                        disable_web_page_preview=True
                    )
                    
                    await temp_client.disconnect()
                    
                except PasswordHashInvalid:
                    await temp_client.disconnect()
                    return await password_msg.reply_text("❌ Invalid 2FA password. Please try again with /string")
            
        except ApiIdInvalid:
            return await message.reply_text("❌ Invalid API_ID or API_HASH. Please try again with /string")
        except PhoneNumberInvalid:
            return await message.reply_text("❌ Invalid phone number. Please try again with /string")
        except PhoneCodeInvalid:
            return await message.reply_text("❌ Invalid OTP code. Please try again with /string")
        except PhoneCodeExpired:
            return await message.reply_text("❌ OTP has expired. Please try again with /string")
    
    except ListenerTimeout:
        await message.reply_text("❌ Timeout! Please try again with /string")
    except asyncio.TimeoutError:
        await message.reply_text("❌ Timeout! Please try again with /string")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}\n\nPlease try again with /string")


# ============ CANCEL COMMAND ============

@Client.on_message(filters.private & filters.command("cancel"))
async def cancel_command(client, message):
    """Cancel command - stops any ongoing operation"""
    await message.reply_text("✅ Send /start to use the bot")


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
    except Exception as e:
        print(f"Error in start command: {e}")


# ============ CALLBACK QUERY HANDLER ============

# ============ CALLBACK QUERY HANDLER ============

@Client.on_callback_query()
async def cb_handler(client, query: CallbackQuery):
    data = query.data 
    user_id = query.from_user.id
    
    try:
        # REMOVED UPLOAD BUTTON HANDLERS - they were causing the error
        # Upload buttons (upload_document, upload_video, upload_audio) are no longer used
        # The new system automatically uploads based on settings
        
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
        
        elif data == "cap":
            await query.message.edit_text(
                text=Txt.CAP_TXT,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="settings")
                ]])
            )
        
        elif data == "thumbnail":
            await query.message.edit_text(
                text=Txt.THUMBNAIL_TXT,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="settings")
                ]])
            )
        
        elif data == "upload_settings":
            await show_upload_settings(client, query)
        
        elif data.startswith("upload_type_"):
            upload_type = data.replace("upload_type_", "")
            await db.set_upload_as(user_id, upload_type)
            await query.answer(f"✅ Upload as {upload_type.upper()}", show_alert=True)
            await show_upload_settings(client, query)
        
        elif data == "set_upload_channel":
            try:
                channel_msg = await client.ask(
                    chat_id=user_id,
                    text="**📢 Send Channel ID or Username:**\n\n"
                         "Examples:\n"
                         "• `-1001234567890`\n"
                         "• `@username`\n\n"
                         "Send /cancel to cancel",
                    timeout=300
                )
                
                if channel_msg.text == "/cancel":
                    await channel_msg.reply_text("✅ Cancelled")
                    return await show_upload_settings(client, query)
                
                channel_id = channel_msg.text.strip()
                if channel_id.startswith('@'):
                    pass
                elif channel_id.lstrip('-').isdigit():
                    channel_id = int(channel_id)
                else:
                    await channel_msg.reply_text("❌ Invalid format")
                    return await show_upload_settings(client, query)
                
                await db.set_upload_channel(user_id, channel_id)
                await channel_msg.reply_text(f"✅ **Channel Set:** `{channel_id}`")
                await show_upload_settings(client, query)
                
            except (ListenerTimeout, asyncio.TimeoutError):
                await query.message.reply_text("❌ Timeout!")
                await show_upload_settings(client, query)
        
        elif data == "clear_upload_channel":
            await db.set_upload_channel(user_id, None)
            await query.answer("✅ Channel Cleared", show_alert=True)
            await show_upload_settings(client, query)
        
        elif data == "rename_mode":
            await show_rename_mode(client, query)
        
        elif data == "set_manual_mode":
            await db.set_rename_mode(user_id, "manual")
            await query.answer("✅ Manual Mode Enabled", show_alert=True)
            await show_rename_mode(client, query)
        
        elif data == "set_auto_mode":
            await db.set_rename_mode(user_id, "auto")
            await query.answer("✅ Auto Mode Enabled", show_alert=True)
            await show_rename_mode(client, query)
        
        elif data == "auto_settings":
            await show_auto_settings(client, query)
        
        elif data == "toggle_auto_clean":
            current = await db.get_auto_clean(user_id)
            await db.set_auto_clean(user_id, not current)
            await query.answer(f"✅ Auto Clean: {'ON' if not current else 'OFF'}", show_alert=True)
            await show_auto_settings(client, query)
        
        elif data == "set_prefix":
            await handle_prefix_input(client, query)
        
        elif data == "set_suffix":
            await handle_suffix_input(client, query)
        
        elif data == "set_remove_words":
            await handle_remove_words_input(client, query)
        
        elif data == "set_replace_words":
            await handle_replace_words_input(client, query)
        
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

# ============ HELPER FUNCTIONS ============

async def show_upload_settings(client, query):
    """Show upload settings page"""
    try:
        user_id = query.from_user.id
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
                InlineKeyboardButton("📢 Set Channel", callback_data="set_upload_channel"),
                InlineKeyboardButton("❌ Clear", callback_data="clear_upload_channel")
            ],[
                InlineKeyboardButton("◀️ Back", callback_data="settings")
            ]])
        )
    except Exception as e:
        print(f"Error in show_upload_settings: {e}")


async def show_rename_mode(client, query):
    """Show rename mode settings"""
    try:
        user_id = query.from_user.id
        current_mode = await db.get_rename_mode(user_id)
        mode_emoji = "🤖" if current_mode == "auto" else "📝"
        
        await query.message.edit_text(
            text=f"**🔧 Rename Mode Settings**\n\n**Current Mode:** {mode_emoji} {current_mode.upper()}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📝 Manual", callback_data="set_manual_mode"),
                InlineKeyboardButton("🤖 Auto", callback_data="set_auto_mode")
                ],[
                InlineKeyboardButton("⚙️ Auto Settings", callback_data="auto_settings")
                ],[
                InlineKeyboardButton("◀️ Back", callback_data="settings")
            ]])
        )
    except Exception as e:
        print(f"Error in show_rename_mode: {e}")


async def show_auto_settings(client, query):
    """Show auto settings page"""
    try:
        user_id = query.from_user.id
        settings = await db.get_all_rename_settings(user_id)
        
        auto_clean = "✅" if settings['auto_clean'] else "❌"
        prefix = settings['prefix'][:20] if settings['prefix'] else "None"
        suffix = settings['suffix'][:20] if settings['suffix'] else "None"
        
        remove_count = len(settings['remove_words'])
        replace_count = len(settings['replace_words'])
        
        text = f"""**⚙️ Auto Rename Settings**

**Auto Clean:** {auto_clean} (Remove junk words)

**Customization:**
├ Prefix: `{prefix}`
├ Suffix: `{suffix}`
├ Remove Words: {remove_count} words
└ Replace Words: {replace_count} pairs"""
        
        await query.message.edit_text(
            text=text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(f"{auto_clean} Auto Clean", callback_data="toggle_auto_clean")
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


async def handle_prefix_input(client, query):
    """Handle prefix input using bot.ask()"""
    try:
        user_id = query.from_user.id
        
        prefix_msg = await client.ask(
            chat_id=user_id,
            text="**➕ Send me the prefix:**\n\nExample: `@YourChannel`\n\nSend /cancel to cancel",
            timeout=300
        )
        
        if prefix_msg.text == "/cancel":
            await prefix_msg.reply_text("✅ Cancelled")
            return await show_auto_settings(client, query)
        
        await db.set_prefix(user_id, prefix_msg.text)
        await prefix_msg.reply_text(f"✅ **Prefix Set:** `{prefix_msg.text}`")
        await show_auto_settings(client, query)
        
    except (ListenerTimeout, asyncio.TimeoutError):
        await query.message.reply_text("❌ Timeout!")
        await show_auto_settings(client, query)


async def handle_suffix_input(client, query):
    """Handle suffix input using bot.ask()"""
    try:
        user_id = query.from_user.id
        
        suffix_msg = await client.ask(
            chat_id=user_id,
            text="**➕ Send me the suffix:**\n\nExample: `@YourChannel`\n\nSend /cancel to cancel",
            timeout=300
        )
        
        if suffix_msg.text == "/cancel":
            await suffix_msg.reply_text("✅ Cancelled")
            return await show_auto_settings(client, query)
        
        await db.set_suffix(user_id, suffix_msg.text)
        await suffix_msg.reply_text(f"✅ **Suffix Set:** `{suffix_msg.text}`")
        await show_auto_settings(client, query)
        
    except (ListenerTimeout, asyncio.TimeoutError):
        await query.message.reply_text("❌ Timeout!")
        await show_auto_settings(client, query)


async def handle_remove_words_input(client, query):
    """Handle remove words input using bot.ask()"""
    try:
        user_id = query.from_user.id
        
        remove_msg = await client.ask(
            chat_id=user_id,
            text="**🗑️ Send words to remove (comma separated):**\n\nExample: `hdcam, sample, x264, torrent`\n\nSend /cancel to cancel",
            timeout=300
        )
        
        if remove_msg.text == "/cancel":
            await remove_msg.reply_text("✅ Cancelled")
            return await show_auto_settings(client, query)
        
        words = [w.strip() for w in remove_msg.text.split(',') if w.strip()]
        if words:
            await db.set_remove_words(user_id, words)
            await remove_msg.reply_text(f"✅ **Remove Words Set ({len(words)} words):**\n`{', '.join(words)}`")
        else:
            await remove_msg.reply_text("❌ No valid words provided")
        
        await show_auto_settings(client, query)
        
    except (ListenerTimeout, asyncio.TimeoutError):
        await query.message.reply_text("❌ Timeout!")
        await show_auto_settings(client, query)


async def handle_replace_words_input(client, query):
    """Handle replace words input using bot.ask()"""
    try:
        user_id = query.from_user.id
        
        replace_msg = await client.ask(
            chat_id=user_id,
            text="**🔄 Send replacement pairs:**\n\nFormat: `old:new, old2:new2`\n\nExample: `tamil:kannada, 480p:720p`\n\nSend /cancel to cancel",
            timeout=300
        )
        
        if replace_msg.text == "/cancel":
            await replace_msg.reply_text("✅ Cancelled")
            return await show_auto_settings(client, query)
        
        pairs = [p.strip() for p in replace_msg.text.split(',')]
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
            await replace_msg.reply_text(f"✅ **Replace Words Set ({len(replace_dict)} pairs):**\n\n{words_display}")
        else:
            await replace_msg.reply_text("❌ **Invalid Format!**\n\nUse: `old:new, old2:new2`")
        
        await show_auto_settings(client, query)
        
    except (ListenerTimeout, asyncio.TimeoutError):
        await query.message.reply_text("❌ Timeout!")
        await show_auto_settings(client, query)


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
        
        await show_auto_settings(client, query)
    except Exception as e:
        print(f"Error in clear: {e}")
