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
from PIL import Image
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
        
        max_size = 4000 * 1024 * 1024 if premium_client else 2000 * 1024 * 1024
        max_size_text = "4GB" if premium_client else "2GB"
        
        if file.file_size > max_size:
            return await message.reply_text(f"Sorry, this bot doesn't support files bigger than {max_size_text}")

        # Check for Jai Bajarangabali special handling
        if filename.lower().startswith("jai bajarangabali") or filename.lower().startswith("jai.bajarangabali"):
            await handle_jai_bajarangabali(client, message, file, filename)
            return

        # Check rename mode
        rename_mode = await db.get_rename_mode(user_id)
        
        if rename_mode == "auto":
            await handle_auto_rename(client, message, file, filename, user_id)
        else:
            await handle_manual_rename(client, message, file, filename)
    
    except Exception as e:
        print(f"Error in rename_start: {e}")
        try:
            await message.reply_text(f"❌ Error: {e}")
        except:
            pass


async def handle_jai_bajarangabali(client, message, file, filename):
    """Handle Jai Bajarangabali special upload"""
    file_path = None
    thumb_path = None
    edited_thumb_path = None
    
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
    
    except Exception as e:
        print(f"Error in handle_jai_bajarangabali: {e}")
        try:
            await message.reply_text(f"❌ Eʀʀᴏʀ: {e}")
        except:
            pass
    
    finally:
        # Cleanup
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)
            if edited_thumb_path and os.path.exists(edited_thumb_path):
                os.remove(edited_thumb_path)
        except Exception as e:
            print(f"Cleanup error: {e}")


async def handle_auto_rename(client, message, file, filename, user_id):
    """Handle auto rename mode - SIMPLIFIED (remove/replace words only)"""
    try:
        settings = await db.get_all_rename_settings(user_id)
        
        # Auto rename using settings
        new_filename = await auto_rename_file(filename, settings)
        
        # Directly start upload process instead of asking
        await start_upload_process(client, message, new_filename, file, user_id)
    
    except Exception as e:
        print(f"Error in handle_auto_rename: {e}")
        await message.reply_text(f"❌ Error: {e}")


async def handle_manual_rename(client, message, file, filename):
    """Handle manual rename mode"""
    try:
        await message.reply_text(
            text=f"**__Pʟᴇᴀꜱᴇ Eɴᴛᴇʀ Nᴇᴡ Fɪʟᴇɴᴀᴍᴇ...__**\n\n**Oʟᴅ Fɪʟᴇ Nᴀᴍᴇ** :- `{filename}`",
            reply_to_message_id=message.id,  
            reply_markup=ForceReply(True, placeholder="Enter new filename...")
        )       
        await sleep(30)
    except FloodWait as e:
        await sleep(e.value)
        try:
            await message.reply_text(
                text=f"**__Pʟᴇᴀꜱᴇ Eɴᴛᴇʀ Nᴇᴡ Fɪʟᴇɴᴀᴍᴇ...__**\n\n**Oʟᴅ Fɪʟᴇ Nᴀᴍᴇ** :- `{filename}`",
                reply_to_message_id=message.id,  
                reply_markup=ForceReply(True, placeholder="Enter new filename...")
            )
        except Exception as e:
            print(f"Error in FloodWait retry: {e}")
    except Exception as e:
        print(f"Error in handle_manual_rename: {e}")


async def start_upload_process(client, file_message, new_filename, file, user_id):
    """Start upload process directly based on settings"""
    file_path = None
    ph_path = None
    
    try:
        upload_client = premium_client if premium_client else client
        
        file_path = f"downloads/{new_filename}"
        
        status_msg = "Tʀyɪɴɢ Tᴏ Dᴏᴡɴʟᴏᴀᴅɪɴɢ...."
        if premium_client:
            status_msg += "\n✅ Premium Mode (4GB)"
        ms = await file_message.reply_text(status_msg)
        
        try:
            path = await upload_client.download_media(
                message=file_message, 
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
        
        media = getattr(file_message, file_message.media.value)
        c_caption = await db.get_caption(user_id)
        c_thumb = await db.get_thumbnail(user_id)

        # Priority 1: Use custom caption if set
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
        # Priority 2: Use file caption if exists
        elif file_message.caption:
            caption = file_message.caption
        # Priority 3: Use filename
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
        
        # Get upload type from settings
        upload_as = await db.get_upload_as(user_id)
        
        try:
            if upload_as == "video" and file_message.media in [MessageMediaType.VIDEO, MessageMediaType.DOCUMENT]:
                await upload_client.send_video(
                    destination,
                    video=file_path,
                    caption=caption,
                    thumb=ph_path,
                    duration=duration,
                    progress=progress_for_pyrogram,
                    progress_args=("Uᴩʟᴏᴀᴅ Sᴛᴀʀᴛᴇᴅ....", ms, time.time())
                )
            elif upload_as == "audio" and file_message.media == MessageMediaType.AUDIO:
                await upload_client.send_audio(
                    destination,
                    audio=file_path,
                    caption=caption,
                    thumb=ph_path,
                    duration=duration,
                    progress=progress_for_pyrogram,
                    progress_args=("Uᴩʟᴏᴀᴅ Sᴛᴀʀᴛᴇᴅ....", ms, time.time())
                )
            else:
                # Default to document
                await upload_client.send_document(
                    destination,
                    document=file_path,
                    thumb=ph_path, 
                    caption=caption, 
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
    
    except Exception as e:
        print(f"Error in start_upload_process: {e}")
        try:
            await file_message.reply_text(f"❌ Eʀʀᴏʀ: {e}")
        except:
            pass
    
    finally:
        # Cleanup after upload
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            if ph_path and os.path.exists(ph_path):
                os.remove(ph_path)
        except Exception as e:
            print(f"Cleanup error: {e}")


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
            
            # Directly start upload process
            user_id = message.from_user.id
            await start_upload_process(client, file, new_name, media, user_id)
    
    except Exception as e:
        print(f"Error in refunc: {e}")


@Client.on_callback_query(filters.regex("upload"))
async def doc(bot, update):
    """Legacy callback handler - kept for backward compatibility but not used in new flow"""
    file_path = None
    ph_path = None
    
    try:
        upload_client = premium_client if premium_client else bot
        
        new_name = update.message.text
        new_filename = new_name.split(":-")[-1].strip().replace("`", "")
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
        
        media = getattr(file, file.media.value)
        c_caption = await db.get_caption(user_id)
        c_thumb = await db.get_thumbnail(user_id)

        # Priority 1: Use custom caption if set
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
        # Priority 2: Use file caption if exists
        elif file.caption:
            caption = file.caption
        # Priority 3: Use filename
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
    
    except Exception as e:
        print(f"Error in doc callback: {e}")
        try:
            await update.message.edit(f"❌ Eʀʀᴏʀ: {e}")
        except:
            pass
    
    finally:
        # Cleanup after upload
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            if ph_path and os.path.exists(ph_path):
                os.remove(ph_path)
        except Exception as e:
            print(f"Cleanup error: {e}")
