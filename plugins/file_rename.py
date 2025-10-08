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

from asyncio import sleep, Queue, create_task
from PIL import Image
import os, time, re, requests, traceback, asyncio
from io import BytesIO


# Safe progress wrapper
async def safe_progress(current, total, message, text, start_time):
    """Wrapper for progress that catches exceptions"""
    try:
        await progress_for_pyrogram(current, total, message, text, start_time)
    except Exception as e:
        print(f"Progress callback error (non-fatal): {e}")

# File processing queue
user_queues = {}
user_processing = {}

# Jai Bajarangabali config
JAI_BAJARANGABALI_CONFIG = {
    "channel_id": -1002987317144,
    "thumbnail_url": "https://envs.sh/zcf.jpg",
    "caption_template": "**Jai Bajarangabali Episode {episode}**\n\n📺 Quality: {quality}\n💾 Size: {filesize}\n⏱ Duration: {duration}"
}


def sanitize_filename(filename):
    """Sanitize filename for file system"""
    try:
        if '.' in filename:
            name_part = filename.rsplit('.', 1)[0]
            extension = filename.rsplit('.', 1)[1]
        else:
            name_part = filename
            extension = 'mkv'
        
        name_part = re.sub(r'[^\x00-\x7F]+', '', name_part)
        name_part = re.sub(r'[<>:"|?*]', '', name_part)
        name_part = name_part.replace('/', '_').replace('\\', '_')
        name_part = re.sub(r'\s+', ' ', name_part).strip()
        
        if not name_part or name_part.isspace():
            name_part = f"renamed_file_{int(time.time())}"
        
        return f"{name_part}.{extension}"
    except Exception as e:
        print(f"Error sanitizing filename: {e}")
        return f"renamed_file_{int(time.time())}.mkv"


def beautify_filename(filename):
    """Beautify filename for display"""
    try:
        if '.' in filename:
            name_part = filename.rsplit('.', 1)[0]
            extension = filename.rsplit('.', 1)[1]
        else:
            return filename
        
        name_part = name_part.replace('.', ' ').replace('_', ' ')
        name_part = re.sub(r'\s+', ' ', name_part).strip()
        
        return f"{name_part}.{extension}"
    except Exception as e:
        print(f"Error beautifying filename: {e}")
        return filename


def extract_episode_number(filename):
    """Extract episode number"""
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
    """Download thumbnail"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            img = img.convert("RGB")
            img.save(save_path, "JPEG")
            return True
    except Exception as e:
        print(f"Thumbnail download error: {e}")
    return False


def get_disk_space():
    """Get free disk space"""
    try:
        import shutil
        stat = shutil.disk_usage('/')
        return stat.free
    except:
        return 0


async def download_file_safe(client, message, file_path, ms=None):
    """
    Safe file download with multiple fallback strategies
    Returns: (success: bool, actual_path: str, error_msg: str)
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Strategy 1: Direct download with progress
        print(f"[Strategy 1] Attempting direct download to: {file_path}")
        try:
            path = await client.download_media(
                message=message,
                file_name=file_path,
                progress=safe_progress,
                progress_args=(ms, "📥 Downloading....", time.time()) if ms else None
            )
            
            if path and os.path.exists(path):
                print(f"✅ Strategy 1 success: {path}")
                return True, path, None
        except Exception as e:
            print(f"Strategy 1 failed: {e}")
        
        # Strategy 2: Download without progress callback
        print(f"[Strategy 2] Retrying without progress...")
        if ms:
            await ms.edit("📥 Retrying download...")
        
        try:
            path = await client.download_media(
                message=message,
                file_name=file_path
            )
            
            if path and os.path.exists(path):
                print(f"✅ Strategy 2 success: {path}")
                return True, path, None
        except Exception as e:
            print(f"Strategy 2 failed: {e}")
        
        # Strategy 3: Download to downloads/ directory only (let Pyrogram choose name)
        print(f"[Strategy 3] Auto-naming download...")
        try:
            downloads_dir = os.path.dirname(file_path)
            path = await client.download_media(
                message=message,
                file_name=downloads_dir + "/"
            )
            
            if path and os.path.exists(path):
                print(f"✅ Strategy 3 success: {path}")
                # Rename to desired filename
                try:
                    os.rename(path, file_path)
                    return True, file_path, None
                except:
                    return True, path, None
        except Exception as e:
            print(f"Strategy 3 failed: {e}")
        
        # Strategy 4: Check if file somehow exists
        if os.path.exists(file_path):
            print(f"✅ Strategy 4: File exists at {file_path}")
            return True, file_path, None
        
        # All strategies failed
        error_msg = "All download strategies failed. Possible causes:\n"
        error_msg += "• Bot lacks permission to access the file\n"
        error_msg += "• File was deleted from Telegram\n"
        error_msg += "• Network/connection issues\n"
        error_msg += "• Insufficient storage space"
        
        return False, None, error_msg
    
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Critical download error: {e}\n{error_trace}")
        return False, None, str(e)


@Client.on_message(filters.private & (filters.document | filters.audio | filters.video))
async def rename_start(client, message):
    try:
        file = getattr(message, message.media.value)
        filename = file.file_name
        user_id = message.from_user.id
        
        max_size = 4000 * 1024 * 1024 if premium_client else 2000 * 1024 * 1024
        max_size_text = "4GB" if premium_client else "2GB"
        
        if file.file_size > max_size:
            return await message.reply_text(f"❌ Files larger than {max_size_text} are not supported")

        free_space = get_disk_space()
        if free_space > 0 and file.file_size > free_space:
            return await message.reply_text(
                f"❌ **Insufficient Storage**\n\n"
                f"📁 Required: {humanbytes(file.file_size)}\n"
                f"💾 Available: {humanbytes(free_space)}"
            )

        if user_id not in user_queues:
            user_queues[user_id] = Queue()
            user_processing[user_id] = False
        
        queue = user_queues[user_id]
        await queue.put(message)
        
        if queue.qsize() > 1:
            await message.reply_text(f"📋 **Queued** - Position: {queue.qsize()}")
        
        if not user_processing[user_id]:
            user_processing[user_id] = True
            create_task(process_file_queue(client, user_id))
    
    except Exception as e:
        print(f"Error in rename_start: {e}\n{traceback.format_exc()}")
        try:
            await message.reply_text(f"❌ **Error:** `{str(e)}`")
        except:
            pass


async def process_file_queue(client, user_id):
    """Process queued files"""
    try:
        while user_id in user_queues and not user_queues[user_id].empty():
            message = await user_queues[user_id].get()
            
            try:
                file = getattr(message, message.media.value)
                filename = file.file_name
                
                if filename.lower().startswith(("jai bajarangabali", "jai.bajarangabali")):
                    await handle_jai_bajarangabali(client, message, file, filename)
                else:
                    rename_mode = await db.get_rename_mode(user_id)
                    
                    if rename_mode == "auto":
                        await handle_auto_rename(client, message, file, filename, user_id)
                    else:
                        await handle_manual_rename(client, message, file, filename)
                
            except Exception as e:
                error_trace = traceback.format_exc()
                print(f"Queue processing error: {e}\n{error_trace}")
                try:
                    await message.reply_text(f"❌ **Error:** `{str(e)}`")
                except:
                    pass
            
            user_queues[user_id].task_done()
            await sleep(1)
            
    finally:
        user_processing[user_id] = False


async def handle_jai_bajarangabali(client, message, file, filename):
    """Handle Jai Bajarangabali auto-upload"""
    file_path = None
    thumb_path = None
    ms = None
    
    try:
        # Extract quality and rename
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
        
        safe_filename = sanitize_filename(new_name)
        downloads_dir = os.path.join(os.getcwd(), "downloads")
        file_path = os.path.join(downloads_dir, safe_filename)
        thumb_path = os.path.join(downloads_dir, f"thumb_{episode_number}.jpg")
        
        os.makedirs(downloads_dir, exist_ok=True)
        
        status_text = "🔄 Auto-Processing Jai Bajarangabali...\n📥 Downloading..."
        if premium_client:
            status_text += "\n✅ Premium Mode (4GB)"
        ms = await message.reply_text(status_text)
        
        # Use safe download
        success, actual_path, error_msg = await download_file_safe(upload_client, message, file_path, ms)
        
        if not success:
            await ms.edit(
                f"❌ **Download Failed**\n\n"
                f"**File:** `{filename[:50]}`\n\n"
                f"**Error:**\n{error_msg}\n\n"
                f"**Free Space:** {humanbytes(get_disk_space())}"
            )
            return
        
        file_path = actual_path
        print(f"✅ Download successful: {file_path} ({humanbytes(os.path.getsize(file_path))})")
        
        # Extract metadata
        duration = 0
        try:
            metadata = extractMetadata(createParser(file_path))
            if metadata and metadata.has("duration"):
                duration = metadata.get('duration').seconds
        except Exception as e:
            print(f"Metadata error: {e}")
        
        # Download thumbnail
        ph_path = None
        try:
            await ms.edit("🎨 Preparing thumbnail...")
            if download_thumbnail(JAI_BAJARANGABALI_CONFIG["thumbnail_url"], thumb_path):
                ph_path = thumb_path
        except Exception as e:
            print(f"Thumbnail error: {e}")
        
        media = getattr(message, message.media.value)
        display_name = beautify_filename(new_name)
        
        try:
            caption = JAI_BAJARANGABALI_CONFIG["caption_template"].format(
                episode=episode_number,
                quality=new_quality,
                filesize=humanbytes(media.file_size),
                duration=convert(duration)
            )
        except:
            caption = f"**Jai Bajarangabali Episode {episode_number}**"
        
        await ms.edit("📤 Uploading to channel...")
        
        try:
            await upload_client.send_video(
                JAI_BAJARANGABALI_CONFIG["channel_id"],
                video=file_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("📤 Uploading....", ms, time.time())
            )
            
            await ms.edit("✅ Successfully uploaded!")
        except Exception as e:
            error_msg = str(e)
            print(f"Upload error: {error_msg}\n{traceback.format_exc()}")
            await ms.edit(f"❌ **Upload Failed**\n\n`{error_msg}`")
    
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Jai Bajarangabali handler error: {e}\n{error_trace}")
        try:
            if ms:
                await ms.edit(f"❌ **Error:** `{str(e)}`")
            else:
                await message.reply_text(f"❌ **Error:** `{str(e)}`")
        except:
            pass
    
    finally:
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)
        except Exception as e:
            print(f"Cleanup error: {e}")


async def handle_auto_rename(client, message, file, filename, user_id):
    """Handle auto rename"""
    try:
        settings = await db.get_all_rename_settings(user_id)
        
        video_extensions = ['.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v']
        use_caption = False
        
        if message.caption:
            caption_lower = message.caption.lower()
            for ext in video_extensions:
                if ext in caption_lower:
                    use_caption = True
                    break
        
        source_text = message.caption if use_caption else filename
        new_filename = await auto_rename_file(source_text, settings)
        
        await start_upload_process(client, message, new_filename, file, user_id)
    
    except Exception as e:
        print(f"Auto rename error: {e}\n{traceback.format_exc()}")
        await message.reply_text(f"❌ **Auto Rename Error:** `{str(e)}`")


async def handle_manual_rename(client, message, file, filename):
    """Handle manual rename"""
    try:
        await message.reply_text(
            text=f"**Enter New Filename**\n\n**Old:** `{filename}`",
            reply_to_message_id=message.id,  
            reply_markup=ForceReply(True, placeholder="Enter new filename...")
        )       
        await sleep(30)
    except FloodWait as e:
        await sleep(e.value)
        try:
            await message.reply_text(
                text=f"**Enter New Filename**\n\n**Old:** `{filename}`",
                reply_to_message_id=message.id,  
                reply_markup=ForceReply(True, placeholder="Enter new filename...")
            )
        except Exception as e:
            print(f"Manual rename error: {e}")


async def start_upload_process(client, file_message, new_filename, file, user_id):
    """Upload process with safe download"""
    file_path = None
    ph_path = None
    ms = None
    
    try:
        upload_client = premium_client if premium_client else client
        
        safe_filename = sanitize_filename(new_filename)
        downloads_dir = os.path.join(os.getcwd(), "downloads")
        file_path = os.path.join(downloads_dir, safe_filename)
        
        display_filename = beautify_filename(new_filename)
        
        os.makedirs(downloads_dir, exist_ok=True)
        
        free_space = get_disk_space()
        if free_space > 0 and file.file_size > free_space:
            await file_message.reply_text(
                f"❌ **Insufficient Storage**\n\n"
                f"📁 Required: {humanbytes(file.file_size)}\n"
                f"💾 Available: {humanbytes(free_space)}"
            )
            return
        
        status_msg = "📥 Downloading..."
        if premium_client:
            status_msg += "\n✅ Premium (4GB)"
        ms = await file_message.reply_text(status_msg)
        
        # Use safe download
        success, actual_path, error_msg = await download_file_safe(upload_client, file_message, file_path, ms)
        
        if not success:
            await ms.edit(
                f"❌ **Download Failed**\n\n"
                f"**File:** `{new_filename[:50]}`\n\n"
                f"**Error:**\n{error_msg}\n\n"
                f"**Free Space:** {humanbytes(free_space)}"
            )
            return
        
        file_path = actual_path
        print(f"✅ Download: {file_path} ({humanbytes(os.path.getsize(file_path))})")
                
        # Extract metadata
        duration = 0
        try:
            metadata = extractMetadata(createParser(file_path))
            if metadata and metadata.has("duration"):
                duration = metadata.get('duration').seconds
        except Exception as e:
            print(f"Metadata error: {e}")
        
        # Get caption/thumbnail
        media = getattr(file_message, file_message.media.value)
        c_caption = await db.get_caption(user_id)
        c_thumb = await db.get_thumbnail(user_id)

        if c_caption:
            try:
                caption = c_caption.format(
                    filename=display_filename, 
                    filesize=humanbytes(media.file_size), 
                    duration=convert(duration)
                )
            except Exception as e:
                print(f"Caption error: {e}")
                await ms.edit(text=f"❌ Caption Error: `{str(e)}`")
                return
        elif file_message.caption:
            caption = file_message.caption
        else:
            caption = f"**{display_filename}**"
    
        # Thumbnail
        if (media.thumbs or c_thumb):
            try:
                if c_thumb:
                    ph_path = await upload_client.download_media(c_thumb) 
                else:
                    ph_path = await upload_client.download_media(media.thumbs[0].file_id)
                
                if ph_path and os.path.exists(ph_path):
                    Image.open(ph_path).convert("RGB").save(ph_path)
                    img = Image.open(ph_path)
                    img = img.resize((320, 320))
                    img.save(ph_path, "JPEG")
            except Exception as e:
                print(f"Thumbnail error: {e}")
                ph_path = None

        await ms.edit("📤 Uploading...")
        
        upload_channel = await db.get_upload_channel(user_id)
        destination = upload_channel if upload_channel else user_id
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
                    progress_args=("📤 Uploading....", ms, time.time())
                )
            elif upload_as == "audio" and file_message.media == MessageMediaType.AUDIO:
                await upload_client.send_audio(
                    destination,
                    audio=file_path,
                    caption=caption,
                    thumb=ph_path,
                    duration=duration,
                    progress=progress_for_pyrogram,
                    progress_args=("📤 Uploading....", ms, time.time())
                )
            else:
                await upload_client.send_document(
                    destination,
                    document=file_path,
                    thumb=ph_path, 
                    caption=caption, 
                    progress=progress_for_pyrogram,
                    progress_args=("📤 Uploading....", ms, time.time())
                )
            
            if upload_channel:
                await ms.edit("✅ Uploaded to channel!")
            else:
                await ms.delete()
        
        except Exception as e:
            error_msg = str(e)
            print(f"Upload error: {error_msg}\n{traceback.format_exc()}")
            await ms.edit(f"❌ **Upload Failed:** `{error_msg}`")
    
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Upload process error: {e}\n{error_trace}")
        try:
            if ms:
                await ms.edit(f"❌ **Error:** `{str(e)}`")
            else:
                await file_message.reply_text(f"❌ **Error:** `{str(e)}`")
        except:
            pass
    
    finally:
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
            
            user_id = message.from_user.id
            await start_upload_process(client, file, new_name, media, user_id)
    
    except Exception as e:
        print(f"Refunc error: {e}\n{traceback.format_exc()}")
        try:
            await message.reply_text(f"❌ **Error:** `{str(e)}`")
        except:
            pass
