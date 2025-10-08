from pyrogram import Client, filters
from pyrogram.enums import MessageMediaType
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply

from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

from helper.utils import progress_for_pyrogram, convert, humanbytes
from helper.database import db

from asyncio import sleep
from PIL import Image
import os, time, re


def sanitize_filename(filename):
    """Sanitize filename to make it safe for file system"""
    # Remove backticks that might be in the filename
    filename = filename.strip('`').strip()
    # Replace problematic characters with underscore
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple spaces
    filename = re.sub(r'\s+', ' ', filename)
    # Strip leading/trailing spaces and dots
    filename = filename.strip('. ')
    # Limit filename length (keeping extension)
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext
    return filename


@Client.on_message(filters.private & (filters.document | filters.audio | filters.video))
async def rename_start(client, message):
    file = getattr(message, message.media.value)
    filename = file.file_name  
    if file.file_size > 2000 * 1024 * 1024:
         return await message.reply_text("Sᴏʀʀy Bʀᴏ Tʜɪꜱ Bᴏᴛ Iꜱ Dᴏᴇꜱɴ'ᴛ Sᴜᴩᴩᴏʀᴛ Uᴩʟᴏᴀᴅɪɴɢ Fɪʟᴇꜱ Bɪɢɢᴇʀ Tʜᴀɴ 2Gʙ")

    try:
        await message.reply_text(
            text=f"**__Pʟᴇᴀꜱᴇ Eɴᴛᴇʀ Nᴇᴡ Fɪʟᴇɴᴀᴍᴇ...__**\n\n**Oʟᴅ Fɪʟᴇ Nᴀᴍᴇ** :- `{filename}`",
            reply_to_message_id=message.id,  
            reply_markup=ForceReply(True)
        )       
        await sleep(30)
    except FloodWait as e:
        await sleep(e.value)
        await message.reply_text(
            text=f"**__Pʟᴇᴀꜱᴇ Eɴᴛᴇʀ Nᴇᴡ Fɪʟᴇɴᴀᴍᴇ...__**\n\n**Oʟᴅ Fɪʟᴇ Nᴀᴍᴇ** :- `{filename}`",
            reply_to_message_id=message.id,  
            reply_markup=ForceReply(True)
        )
    except:
        pass


@Client.on_message(filters.private & filters.reply)
async def refunc(client, message):
    reply_message = message.reply_to_message
    if (reply_message.reply_markup) and isinstance(reply_message.reply_markup, ForceReply):
        new_name = message.text 
        await message.delete() 
        msg = await client.get_messages(message.chat.id, reply_message.id)
        file = msg.reply_to_message
        media = getattr(file, file.media.value)
        
        # Sanitize the new filename
        new_name = sanitize_filename(new_name)
        
        if not "." in new_name:
            if "." in media.file_name:
                extn = media.file_name.rsplit('.', 1)[-1]
            else:
                extn = "mkv"
            new_name = new_name + "." + extn
        
        await reply_message.delete()

        button = [[InlineKeyboardButton("📁 Dᴏᴄᴜᴍᴇɴᴛ",callback_data = "upload_document")]]
        if file.media in [MessageMediaType.VIDEO, MessageMediaType.DOCUMENT]:
            button.append([InlineKeyboardButton("🎥 Vɪᴅᴇᴏ", callback_data = "upload_video")])
        elif file.media == MessageMediaType.AUDIO:
            button.append([InlineKeyboardButton("🎵 Aᴜᴅɪᴏ", callback_data = "upload_audio")])
        await message.reply(
            text=f"**Sᴇʟᴇᴄᴛ Tʜᴇ Oᴜᴛᴩᴜᴛ Fɪʟᴇ Tyᴩᴇ**\n**• Fɪʟᴇ Nᴀᴍᴇ :-** `{new_name}`",
            reply_to_message_id=file.id,
            reply_markup=InlineKeyboardMarkup(button)
        )


@Client.on_callback_query(filters.regex("upload"))
async def doc(bot, update):
    try:
        new_name = update.message.text
        # Extract filename more carefully, handling backticks
        if ":-" in new_name:
            new_filename = new_name.split(":-")[1].strip()
            # Remove backticks if present
            new_filename = new_filename.strip('`').strip()
        else:
            return await update.message.edit("❌ Eʀʀᴏʀ: Cᴏᴜʟᴅɴ'ᴛ Exᴛʀᴀᴄᴛ Fɪʟᴇɴᴀᴍᴇ")
        
        # Sanitize filename
        new_filename = sanitize_filename(new_filename)
        
        file = update.message.reply_to_message
        
        # Ensure downloads directory exists
        os.makedirs("downloads", exist_ok=True)
        
        # Use timestamp to avoid conflicts with multiple files
        timestamp = int(time.time())
        file_path = f"downloads/{timestamp}_{new_filename}"

        ms = await update.message.edit("Tʀyɪɴɢ Tᴏ Dᴏᴡɴʟᴏᴀᴅɪɴɢ....")
        
        try:
            path = await bot.download_media(
                message=file, 
                file_name=file_path, 
                progress=progress_for_pyrogram,
                progress_args=("Dᴏᴡɴʟᴏᴀᴅ Sᴛᴀʀᴛᴇᴅ....", ms, time.time())
            )
        except Exception as e:
            return await ms.edit(f"❌ Dᴏᴡɴʟᴏᴀᴅ Eʀʀᴏʀ: {e}")
        
        # Verify file was downloaded
        if not os.path.exists(file_path):
            return await ms.edit("❌ Dᴏᴡɴʟᴏᴀᴅ Fᴀɪʟᴇᴅ: Fɪʟᴇ Nᴏᴛ Sᴀᴠᴇᴅ")
        
        # Verify file size
        if os.path.getsize(file_path) == 0:
            os.remove(file_path)
            return await ms.edit("❌ Dᴏᴡɴʟᴏᴀᴅ Fᴀɪʟᴇᴅ: Eᴍᴩᴛy Fɪʟᴇ")
             
        duration = 0
        try:
            metadata = extractMetadata(createParser(file_path))
            if metadata and metadata.has("duration"):
                duration = metadata.get('duration').seconds
        except:
            pass
        
        ph_path = None
        user_id = int(update.message.chat.id) 
        media = getattr(file, file.media.value)
        c_caption = await db.get_caption(update.message.chat.id)
        c_thumb = await db.get_thumbnail(update.message.chat.id)

        if c_caption:
            try:
                caption = c_caption.format(
                    filename=new_filename, 
                    filesize=humanbytes(media.file_size), 
                    duration=convert(duration)
                )
            except Exception as e:
                if os.path.exists(file_path):
                    os.remove(file_path)
                return await ms.edit(text=f"Yᴏᴜʀ Cᴀᴩᴛɪᴏɴ Eʀʀᴏʀ Exᴄᴇᴩᴛ Kᴇyᴡᴏʀᴅ Aʀɢᴜᴍᴇɴᴛ ●> ({e})")             
        else:
            caption = f"**{new_filename}**"
     
        if (media.thumbs or c_thumb):
            try:
                if c_thumb:
                    ph_path = await bot.download_media(c_thumb) 
                else:
                    ph_path = await bot.download_media(media.thumbs[0].file_id)
                
                if ph_path and os.path.exists(ph_path):
                    Image.open(ph_path).convert("RGB").save(ph_path)
                    img = Image.open(ph_path)
                    img = img.resize((320, 320))
                    img.save(ph_path, "JPEG")
            except Exception as e:
                print(f"Thumbnail error: {e}")
                ph_path = None

        await ms.edit("Tʀyɪɴɢ Tᴏ Uᴩʟᴏᴀᴅɪɴɢ....")
        type = update.data.split("_")[1]
        
        try:
            if type == "document":
                await bot.send_document(
                    update.message.chat.id,
                    document=file_path,
                    thumb=ph_path, 
                    caption=caption, 
                    progress=progress_for_pyrogram,
                    progress_args=("Uᴩʟᴏᴅ Sᴛᴀʀᴛᴇᴅ....", ms, time.time())
                )
            elif type == "video": 
                await bot.send_video(
                    update.message.chat.id,
                    video=file_path,
                    caption=caption,
                    thumb=ph_path,
                    duration=duration,
                    progress=progress_for_pyrogram,
                    progress_args=("Uᴩʟᴏᴅ Sᴛᴀʀᴛᴇᴅ....", ms, time.time())
                )
            elif type == "audio": 
                await bot.send_audio(
                    update.message.chat.id,
                    audio=file_path,
                    caption=caption,
                    thumb=ph_path,
                    duration=duration,
                    progress=progress_for_pyrogram,
                    progress_args=("Uᴩʟᴏᴅ Sᴛᴀʀᴛᴇᴅ....", ms, time.time())
                )
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            if ph_path and os.path.exists(ph_path):
                os.remove(ph_path)
            return await ms.edit(f"❌ Uᴩʟᴏᴀᴅ Eʀʀᴏʀ: {e}")
     
        await ms.delete()
        
    except Exception as e:
        print(f"Error in doc function: {e}")
        try:
            await update.message.edit(f"❌ Eʀʀᴏʀ: {e}")
        except:
            pass
    finally:
        # Cleanup
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            if 'ph_path' in locals() and ph_path and os.path.exists(ph_path):
                os.remove(ph_path)
        except Exception as e:
            print(f"Cleanup error: {e}")
