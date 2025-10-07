from pyrogram import Client, filters
from pyrogram.enums import MessageMediaType
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply

from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

from helper.utils import progress_for_pyrogram, convert, humanbytes
from helper.database import db
from helper.auto_rename import auto_rename_file
from bot import bot, premium_client

from asyncio import sleep
from PIL import Image, ImageDraw, ImageFont
import os, time, re, requests
from io import BytesIO


# Configuration for Jai Bajarangabali auto-upload
JAI_BAJARANGABALI_CONFIG = {
    "channel_id": -1002987317144,
    "thumbnail_url": "https://envs.sh/zcf.jpg",
    "caption_template": "**Jai Bajarangabali Episode {episode}**\n\n📺 Quality: {quality}\n💾 Size: {filesize}\n⏱ Duration: {duration}"
}


def extract_episode_number(filename):
    """Extract episode number from filename"""
    try:
        match = re.search(r'[Ee]pisode[.\s]*(\d+)', filename, re.IGNORECASE)
        if match:
            return match.group(1)
        match = re.search(r'[Ee]p[.\s]*(\d+)', filename, re.IGNORECASE)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"Error extracting episode: {e}")
    return "Unknown"


def add_text_to_thumbnail(image_path, episode_number, output_path):
    """Add episode number to thumbnail image"""
    try:
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", 80)
            except:
                font = ImageFont.load_default()
        
        text = f"Ep:{episode_number}"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = 30
        y = (img.height - text_height) // 2
        
        outline_range = 3
        for adj_x in range(-outline_range, outline_range + 1):
            for adj_y in range(-outline_range, outline_range + 1):
                draw.text((x + adj_x, y + adj_y), text, font=font, fill="black")
        
        draw.text((x, y), text, font=font, fill="white")
        img.save(output_path, "JPEG")
        return True
    except Exception as e:
        print(f"Error adding text to thumbnail: {e}")
        return False


def download_thumbnail(url, save_path):
    """Download thumbnail from URL"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            img = img.convert("RGB")
            img.save(save_path, "JPEG")
            return True
    except Exception as e:
        print(f"Error downloading thumbnail: {e}")
    return False


@Client.on_message(filters.private & (filters.document | filters.audio | filters.video))
async def rename_start(client, message):
    try:
        file = getattr(message, message.media.value)
        filename = file.file_name
        user_id = message.from_user.id
        
        # Use premium client for file size check if available
        max_size = 4000 * 1024 * 1024 if premium_client else 2000 * 1024 * 1024
        max_size_text = "4GB" if premium_client else "2GB"
        
        if file.file_size > max_size:
            return await message.reply_text(f"Sᴏʀʀy Bʀᴏ Tʜɪꜱ Bᴏᴛ Dᴏᴇꜱɴ'ᴛ Sᴜᴩᴩᴏʀᴛ Uᴩʟᴏᴀᴅɪɴɢ Fɪʟᴇꜱ Bɪɢɢᴇʀ Tʜᴀɴ {max_size_text}")

        # Check for Jai Bajarangabali special handling
        if filename.lower().startswith("jai bajarangabali") or filename.lower().startswith("jai.bajarangabali"):
            await handle_jai_bajarangabali(client, message, file, filename)
            return

        # Check rename mode (manual or auto)
        rename_mode = await db.get_rename_mode(user_id)
        
        if rename_mode == "auto":
            await handle_auto_rename(client, message, file, filename, user_id)
        else:
            await handle_manual_rename(client, message, file, filename)
    
    except Exception as e:
        print(f"Error in rename_start: {e}")
        try:
            await message.reply_text(f"❌ Eʀʀᴏʀ: {e}")
        except:
            pass


async def handle_jai_bajarangabali(client, message, file, filename):
    """Handle Jai Bajarangabali special upload"""
    try:
        bracket_match = re.search(r'\[(\d+p)\]', filename)
        if bracket_match:
            new_quality = bracket_match.group(1)
            new_name = re.sub(r'\d+p', '', filename)
            new_name = re.sub(r'\[.*?\]', '', new_name)
            
            name_parts = new_name.rsplit('.', 1)
            if len(name_parts) == 2:
                new_name = f"{name_parts[0]}{new_quality}.{name_parts[1]}"
            else:
                new_name = f"{new_name}{new_quality}"
            
            new_name = re.sub(r'\.+', '.', new_name)
            new_name = re.sub(r'\s+', ' ', new_name).strip()
        else:
            new_name = filename
            new_quality = "Unknown"
        
        episode_number = extract_episode_number(filename)
        upload_client = premium_client if premium_client else client
        
        file_path = f"downloads/{new_name}"
        thumb_path = f"downloads/thumb_{episode_number}.jpg"
        edited_thumb_path = f"downloads/thumb_edited_{episode_number}.jpg"
        
        status_text = "🔄 Aᴜᴛᴏ-Pʀᴏᴄᴇssɪɴɢ Jᴀɪ Bᴀᴊᴀʀᴀɴɢᴀʙᴀʟɪ...\n📥 Dᴏᴡɴʟᴏᴀᴅɪɴɢ..."
        if premium_client:
            status_text += "\n✅ Using Premium (4GB Support)"
        ms = await message.reply_text(status_text)
        
        try:
            path = await upload_client.download_media(
                message=message, 
                file_name=file_path, 
                progress=progress_for_pyrogram, 
                progress_args=("Dᴏᴡɴʟᴏᴀᴅ Sᴛᴀʀᴛᴇᴅ....", ms, time.time())
            )
        except Exception as e:
            await ms.edit(f"❌ Dᴏᴡɴʟᴏᴀᴅ Eʀʀᴏʀ: {e}")
            return
        
        duration = 0
        try:
            metadata = extractMetadata(createParser(file_path))
            if metadata and metadata.has("duration"):
                duration = metadata.get('duration').seconds
        except Exception as e:
            print(f"Error extracting metadata: {e}")
        
        ph_path = None
        await ms.edit("🎨 Pʀᴇᴘᴀʀɪɴɢ Tʜᴜᴍʙɴᴀɪʟ...")
        
        if download_thumbnail(JAI_BAJARANGABALI_CONFIG["thumbnail_url"], thumb_path):
            if add_text_to_thumbnail(thumb_path, episode_number, edited_thumb_path):
                ph_path = edited_thumb_path
            else:
                ph_path = thumb_path
        
        media = getattr(message, message.media.value)
        try:
            caption = JAI_BAJARANGABALI_CONFIG["caption_template"].format(
                episode=episode_number,
                quality=new_quality,
                filesize=humanbytes(media.file_size),
                duration=convert(duration)
            )
        except:
            caption = f"**Jai Bajarangabali Episode {episode_number}**"
        
        await ms.edit("📤 Uᴩʟᴏᴀᴅɪɴɢ Tᴏ Cʜᴀɴɴᴇʟ...")
        
        try:
            await upload_client.send_video(
                JAI_BAJARANGABALI_CONFIG["channel_id"],
                video=file_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("Uᴩʟᴏᴀᴅ Sᴛᴀʀᴛᴇᴅ....", ms, time.time())
            )
            
            await ms.edit("✅ Sᴜᴄᴄᴇssғᴜʟʟy Uᴩʟᴏᴀᴅᴇᴅ Tᴏ Cʜᴀɴɴᴇʟ!")
        except Exception as e:
            await ms.edit(f"❌ Uᴩʟᴏᴀᴅ Eʀʀᴏʀ: {e}")
        
        # Cleanup
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
            if os.path.exists(edited_thumb_path):
                os.remove(edited_thumb_path)
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    except Exception as e:
        print(f"Error in handle_jai_bajarangabali: {e}")
        try:
            await message.reply_text(f"❌ Eʀʀᴏʀ: {e}")
        except:
            pass


async def handle_auto_rename(client, message, file, filename, user_id):
    """Handle auto rename mode"""
    try:
        settings = await db.get_all_rename_settings(user_id)
        
        # Check if always ask is enabled
        always_ask = settings.get('always_ask', True)
        
        # Generate auto-renamed filename
        try:
            new_filename = await auto_rename_file(
                filename, 
                settings, 
                message.media, 
                file
            )
            
            if always_ask:
                # Show preview and ask for confirmation
                await message.reply_text(
                    text=f"**🤖 Aᴜᴛᴏ Rᴇɴᴀᴍᴇ Pʀᴇᴠɪᴇᴡ**\n\n**Oʟᴅ Nᴀᴍᴇ:**\n`{filename}`\n\n**Nᴇᴡ Nᴀᴍᴇ:**\n`{new_filename}`\n\n**Cʟɪᴄᴋ Cᴏɴꜰɪʀᴍ ᴛᴏ ᴘʀᴏᴄᴇᴇᴅ ᴏʀ Eᴅɪᴛ ᴛᴏ ᴍᴀɴᴜᴀʟʟy ᴄʜᴀɴɢᴇ**",
                    reply_to_message_id=message.id,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("✅ Cᴏɴꜰɪʀᴍ", callback_data=f"auto_confirm_{message.id}"),
                        InlineKeyboardButton("✏️ Eᴅɪᴛ", callback_data=f"auto_edit_{message.id}")
                    ]])
                )
            else:
                # Directly proceed with upload selection
                await show_upload_options(client, message, new_filename, file)
        
        except Exception as e:
            print(f"Auto rename error: {e}")
            await message.reply_text(f"❌ Aᴜᴛᴏ Rᴇɴᴀᴍᴇ Eʀʀᴏʀ: {e}\n\nFᴀʟʟɪɴɢ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɴᴜᴀʟ ᴍᴏᴅᴇ...")
            await handle_manual_rename(client, message, file, filename)
    
    except Exception as e:
        print(f"Error in handle_auto_rename: {e}")
        await message.reply_text(f"❌ Eʀʀᴏʀ: {e}")


async def handle_manual_rename(client, message, file, filename):
    """Handle manual rename mode"""
    try:
        await message.reply_text(
            text=f"**__Pʟᴇᴀꜱᴇ Eɴᴛᴇʀ Nᴇᴡ Fɪʟᴇɴᴀᴍᴇ...__**\n\n**Oʟᴅ Fɪʟᴇ Nᴀᴍᴇ** :- `{filename}`",
            reply_to_message_id=message.id,  
            reply_markup=ForceReply(True)
        )       
        await sleep(30)
    except FloodWait as e:
        await sleep(e.value)
        try:
            await message.reply_text(
                text=f"**__Pʟᴇᴀꜱᴇ Eɴᴛᴇʀ Nᴇᴡ Fɪʟᴇɴᴀᴍᴇ...__**\n\n**Oʟᴅ Fɪʟᴇ Nᴀᴍᴇ** :- `{filename}`",
                reply_to_message_id=message.id,  
                reply_markup=ForceReply(True)
            )
        except Exception as e:
            print(f"Error in FloodWait retry: {e}")
    except Exception as e:
        print(f"Error in handle_manual_rename: {e}")


async def show_upload_options(client, message, new_filename, file):
    """Show upload type selection"""
    try:
        button = [[InlineKeyboardButton("📁 Dᴏᴄᴜᴍᴇɴᴛ", callback_data="upload_document")]]
        
        if message.media in [MessageMediaType.VIDEO, MessageMediaType.DOCUMENT]:
            button.append([InlineKeyboardButton("🎥 Vɪᴅᴇᴏ", callback_data="upload_video")])
        elif message.media == MessageMediaType.AUDIO:
            button.append([InlineKeyboardButton("🎵 Aᴜᴅɪᴏ", callback_data="upload_audio")])
        
        await message.reply(
            text=f"**Sᴇʟᴇᴄᴛ Tʜᴇ Oᴜᴛᴩᴜᴛ Fɪʟᴇ Tyᴩᴇ**\n**• Fɪʟᴇ Nᴀᴍᴇ :-** `{new_filename}`",
            reply_to_message_id=message.id,
            reply_markup=InlineKeyboardMarkup(button)
        )
    except Exception as e:
        print(f"Error in show_upload_options: {e}")


@Client.on_callback_query(filters.regex(r"^auto_confirm_"))
async def auto_confirm_handler(client, query):
    try:
        message_id = int(query.data.split("_")[2])
        user_id = query.from_user.id
        
        # Get the original message
        original_msg = await client.get_messages(query.message.chat.id, message_id)
        file = getattr(original_msg, original_msg.media.value)
        
        # Get auto-renamed filename from settings
        settings = await db.get_all_rename_settings(user_id)
        new_filename = await auto_rename_file(
            file.file_name, 
            settings, 
            original_msg.media, 
            file
        )
        
        await query.message.delete()
        await show_upload_options(client, original_msg, new_filename, file)
    
    except Exception as e:
        print(f"Error in auto_confirm_handler: {e}")
        try:
            await query.answer(f"❌ Eʀʀᴏʀ: {e}", show_alert=True)
        except:
            pass


@Client.on_callback_query(filters.regex(r"^auto_edit_"))
async def auto_edit_handler(client, query):
    try:
        message_id = int(query.data.split("_")[2])
        
        original_msg = await client.get_messages(query.message.chat.id, message_id)
        file = getattr(original_msg, original_msg.media.value)
        
        await query.message.delete()
        await query.message.reply(
            text=f"**__Pʟᴇᴀꜱᴇ Eɴᴛᴇʀ Nᴇᴡ Fɪʟᴇɴᴀᴍᴇ...__**\n\n**Oʟᴅ Fɪʟᴇ Nᴀᴍᴇ** :- `{file.file_name}`",
            reply_to_message_id=original_msg.id,  
            reply_markup=ForceReply(True)
        )
    except Exception as e:
        print(f"Error in auto_edit_handler: {e}")
        try:
            await query.answer(f"❌ Eʀʀᴏʀ: {e}", show_alert=True)
        except:
            pass


@Client.on_message(filters.private & filters.reply)
async def refunc(client, message):
    try:
        reply_message = message.reply_to_message
        if (reply_message.reply_markup) and isinstance(reply_message.reply_markup, ForceReply):
            new_name = message.text 
            await message.delete() 
            msg = await client.get_messages(message.chat.id, reply_message.id)
            file = msg.reply_to_message
            media = getattr(file, file.media.value)
            
            if not "." in new_name:
                if "." in media.file_name:
                    extn = media.file_name.rsplit('.', 1)[-1]
                else:
                    extn = "mkv"
                new_name = new_name + "." + extn
            
            await reply_message.delete()
            await show_upload_options(client, file, new_name, media)
    
    except Exception as e:
        print(f"Error in refunc: {e}")


@Client.on_callback_query(filters.regex("upload"))
async def doc(bot, update):
    try:
        upload_client = premium_client if premium_client else bot
        
        new_name = update.message.text
        new_filename = new_name.split(":-")[1].strip().replace("`", "")
        file_path = f"downloads/{new_filename}"
        file = update.message.reply_to_message
        user_id = update.message.chat.id

        status_msg = "Tʀyɪɴɢ Tᴏ Dᴏᴡɴʟᴏᴀᴅɪɴɢ...."
        if premium_client:
            status_msg += "\n✅ Premium Mode (4GB)"
        ms = await update.message.edit(status_msg)
        
        try:
            path = await upload_client.download_media(
                message=file, 
                file_name=file_path, 
                progress=progress_for_pyrogram,
                progress_args=("Dᴏᴡɴʟᴏᴀᴅ Sᴛᴀʀᴛᴇᴅ....", ms, time.time())
            )                    
        except Exception as e:
            print(f"Download error: {e}")
            await ms.edit(f"❌ Dᴏᴡɴʟᴏᴀᴅ Eʀʀᴏʀ: {e}")
            return
                
        duration = 0
        try:
            metadata = extractMetadata(createParser(file_path))
            if metadata and metadata.has("duration"):
                duration = metadata.get('duration').seconds
        except Exception as e:
            print(f"Metadata error: {e}")
        
        ph_path = None
        media = getattr(file, file.media.value)
        c_caption = await db.get_caption(user_id)
        c_thumb = await db.get_thumbnail(user_id)

        if c_caption:
            try:
                caption = c_caption.format(
                    filename=new_filename, 
                    filesize=humanbytes(media.file_size), 
                    duration=convert(duration)
                )
            except Exception as e:
                print(f"Caption error: {e}")
                await ms.edit(text=f"Yᴏᴜʀ Cᴀᴩᴛɪᴏɴ Eʀʀᴏʀ Exᴄᴇᴩᴛ Kᴇyᴡᴏʀᴅ Aʀɢᴜᴍᴇɴᴛ ●> ({e})")
                return
        else:
            caption = f"**{new_filename}**"
    
        if (media.thumbs or c_thumb):
            try:
                if c_thumb:
                    ph_path = await upload_client.download_media(c_thumb) 
                else:
                    ph_path = await upload_client.download_media(media.thumbs[0].file_id)
                
                Image.open(ph_path).convert("RGB").save(ph_path)
                img = Image.open(ph_path)
                img.resize((320, 320))
                img.save(ph_path, "JPEG")
            except Exception as e:
                print(f"Thumbnail error: {e}")
                ph_path = None

        await ms.edit("Tʀyɪɴɢ Tᴏ Uᴩʟᴏᴀᴅɪɴɢ....")
        
        # Check if user has set upload channel
        upload_channel = await db.get_upload_channel(user_id)
        destination = upload_channel if upload_channel else user_id
        
        type = update.data.split("_")[1]
        try:
            if type == "document":
                await upload_client.send_document(
                    destination,
                    document=file_path,
                    thumb=ph_path, 
                    caption=caption, 
                    progress=progress_for_pyrogram,
                    progress_args=("Uᴩʟᴏᴀᴅ Sᴛᴀʀᴛᴇᴅ....", ms, time.time())
                )
            elif type == "video": 
                await upload_client.send_video(
                    destination,
                    video=file_path,
                    caption=caption,
                    thumb=ph_path,
                    duration=duration,
                    progress=progress_for_pyrogram,
                    progress_args=("Uᴩʟᴏᴀᴅ Sᴛᴀʀᴛᴇᴅ....", ms, time.time())
                )
            elif type == "audio": 
                await upload_client.send_audio(
                    destination,
                    audio=file_path,
                    caption=caption,
                    thumb=ph_path,
                    duration=duration,
                    progress=progress_for_pyrogram,
                    progress_args=("Uᴩʟᴏᴀᴅ Sᴛᴀʀᴛᴇᴅ....", ms, time.time())
                )
            
            if upload_channel:
                await ms.edit("✅ Sᴜᴄᴄᴇssғᴜʟʟy Uᴩʟᴏᴀᴅᴇᴅ Tᴏ Cʜᴀɴɴᴇʟ!")
            else:
                await ms.delete()
        
        except Exception as e:
            print(f"Upload error: {e}")
            await ms.edit(f"❌ Uᴩʟᴏᴀᴅ Eʀʀᴏʀ: {e}")
        finally:
            # Cleanup
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                if ph_path and os.path.exists(ph_path):
                    os.remove(ph_path)
            except Exception as e:
                print(f"Cleanup error: {e}")
    
    except Exception as e:
        print(f"Error in doc handler: {e}")
        try:
            await update.message.edit(f"❌ Eʀʀᴏʀ: {e}")
        except:
            pass
