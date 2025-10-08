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
import os, time, re, requests, traceback
from io import BytesIO

# File processing queue for handling multiple files
user_queues = {}
user_processing = {}

# Configuration for Jai Bajarangabali auto-upload
JAI_BAJARANGABALI_CONFIG = {
    "channel_id": -1002987317144,
    "thumbnail_url": "https://envs.sh/zcf.jpg",
    "caption_template": "**Jai Bajarangabali Episode {episode}**\n\n📺 Quality: {quality}\n💾 Size: {filesize}\n⏱ Duration: {duration}"
}


def sanitize_filename(filename):
    """
    Sanitize filename for file system compatibility
    - Removes non-ASCII characters (emojis, special unicode)
    - Removes invalid filesystem characters
    - Preserves extension
    """
    try:
        # Split filename and extension
        if '.' in filename:
            name_part = filename.rsplit('.', 1)[0]
            extension = filename.rsplit('.', 1)[1]
        else:
            name_part = filename
            extension = 'mkv'
        
        # Remove non-ASCII characters (emojis, unicode)
        name_part = re.sub(r'[^\x00-\x7F]+', '', name_part)
        
        # Remove invalid filesystem characters
        name_part = re.sub(r'[<>:"|?*]', '', name_part)
        
        # Replace forward/backward slashes
        name_part = name_part.replace('/', '_').replace('\\', '_')
        
        # Remove multiple spaces
        name_part = re.sub(r'\s+', ' ', name_part).strip()
        
        # If name becomes empty, generate a fallback
        if not name_part or name_part.isspace():
            name_part = f"renamed_file_{int(time.time())}"
        
        return f"{name_part}.{extension}"
    except Exception as e:
        print(f"Error sanitizing filename: {e}")
        return f"renamed_file_{int(time.time())}.mkv"


def beautify_filename(filename):
    """
    Beautify filename for display after upload
    - Replaces dots and underscores with spaces (except extension)
    - Cleans up formatting
    """
    try:
        # Split filename and extension
        if '.' in filename:
            name_part = filename.rsplit('.', 1)[0]
            extension = filename.rsplit('.', 1)[1]
        else:
            return filename
        
        # Replace dots and underscores with spaces
        name_part = name_part.replace('.', ' ').replace('_', ' ')
        
        # Remove multiple spaces
        name_part = re.sub(r'\s+', ' ', name_part).strip()
        
        return f"{name_part}.{extension}"
    except Exception as e:
        print(f"Error beautifying filename: {e}")
        return filename


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


def get_disk_space():
    """Get available disk space in bytes"""
    try:
        import shutil
        stat = shutil.disk_usage('/')
        return stat.free
    except:
        return 0


@Client.on_message(filters.private & (filters.document | filters.audio | filters.video))
async def rename_start(client, message):
    try:
        file = getattr(message, message.media.value)
        filename = file.file_name
        user_id = message.from_user.id
        
        max_size = 4000 * 1024 * 1024 if premium_client else 2000 * 1024 * 1024
        max_size_text = "4GB" if premium_client else "2GB"
        
        if file.file_size > max_size:
            return await message.reply_text(f"❌ Sorry, this bot doesn't support files bigger than {max_size_text}")

        # Check available disk space
        free_space = get_disk_space()
        if free_space > 0 and file.file_size > free_space:
            return await message.reply_text(
                f"❌ **Insufficient Storage**\n\n"
                f"📁 Required: {humanbytes(file.file_size)}\n"
                f"💾 Available: {humanbytes(free_space)}\n\n"
                f"Please try again later or contact admin."
            )

        # Initialize queue for user if not exists
        if user_id not in user_queues:
            user_queues[user_id] = Queue()
            user_processing[user_id] = False
        
        queue = user_queues[user_id]
        
        # Add file to queue
        await queue.put(message)
        
        # Show queue status if multiple files
        if queue.qsize() > 1:
            await message.reply_text(f"📋 **Added to queue**\n\n**Position:** {queue.qsize()}\n**Processing...**")
        
        # Start processing if not already processing
        if not user_processing[user_id]:
            user_processing[user_id] = True
            create_task(process_file_queue(client, user_id))
    
    except Exception as e:
        print(f"Error in rename_start: {e}\n{traceback.format_exc()}")
        try:
            await message.reply_text(f"❌ **Error**\n\n`{str(e)}`")
        except:
            pass


async def process_file_queue(client, user_id):
    """Process files in queue one by one"""
    try:
        while user_id in user_queues and not user_queues[user_id].empty():
            message = await user_queues[user_id].get()
            
            try:
                file = getattr(message, message.media.value)
                filename = file.file_name
                
                # Check for Jai Bajarangabali special handling
                if filename.lower().startswith("jai bajarangabali") or filename.lower().startswith("jai.bajarangabali"):
                    await handle_jai_bajarangabali(client, message, file, filename)
                else:
                    # Check rename mode
                    rename_mode = await db.get_rename_mode(user_id)
                    
                    if rename_mode == "auto":
                        await handle_auto_rename(client, message, file, filename, user_id)
                    else:
                        await handle_manual_rename(client, message, file, filename)
                
            except Exception as e:
                error_trace = traceback.format_exc()
                print(f"Error processing file: {e}\n{error_trace}")
                try:
                    await message.reply_text(
                        f"❌ **Processing Error**\n\n"
                        f"**File:** `{filename[:50]}`\n"
                        f"**Error:** `{str(e)}`"
                    )
                except:
                    pass
            
            user_queues[user_id].task_done()
            await sleep(1)
            
    finally:
        user_processing[user_id] = False


async def handle_jai_bajarangabali(client, message, file, filename):
    """Handle Jai Bajarangabali special upload"""
    file_path = None
    thumb_path = None
    ms = None
    
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
        
        # Get current working directory
        cwd = os.getcwd()
        print(f"Current working directory: {cwd}")
        
        # Sanitize filename for download
        safe_filename = sanitize_filename(new_name)
        
        # Use absolute paths
        downloads_dir = os.path.join(cwd, "downloads")
        file_path = os.path.join(downloads_dir, safe_filename)
        thumb_path = os.path.join(downloads_dir, f"thumb_{episode_number}.jpg")
        
        # Ensure downloads directory exists with proper permissions
        os.makedirs(downloads_dir, exist_ok=True)
        print(f"Downloads directory: {downloads_dir}")
        print(f"File will be saved as: {file_path}")
        
        status_text = "🔄 Aᴜᴛᴏ-Pʀᴏᴄᴇssɪɴɢ Jᴀɪ Bᴀᴊᴀʀᴀɴɢᴀʙᴀʟɪ...\n📥 Dᴏᴡɴʟᴏᴀᴅɪɴɢ..."
        if premium_client:
            status_text += "\n✅ Using Premium (4GB Support)"
        ms = await message.reply_text(status_text)
        
        # Download with error handling
        try:
            # Get absolute path
            abs_file_path = os.path.abspath(file_path)
            print(f"Attempting download to: {abs_file_path}")
            
            path = await upload_client.download_media(
                message=message, 
                file_name=abs_file_path, 
                progress=progress_for_pyrogram, 
                progress_args=("📥 Dᴏᴡɴʟᴏᴀᴅɪɴɢ....", ms, time.time())
            )
            
            print(f"Pyrogram returned path: {path}")
            
            # Check both returned path and expected path
            actual_path = path if path else abs_file_path
            
            if not os.path.exists(actual_path):
                # Try to find file in downloads directory
                if os.path.exists("downloads"):
                    files = os.listdir("downloads")
                    print(f"Files in downloads/: {files}")
                    raise Exception(f"File not found at expected path: {actual_path}")
                else:
                    raise Exception("Downloads directory doesn't exist")
            
            # Update file_path to actual location
            file_path = actual_path
            
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise Exception("Downloaded file is empty (0 bytes)")
            
            print(f"✅ Download successful: {file_path} ({humanbytes(file_size)})")
            
        except FloodWait as e:
            await ms.edit(f"⏳ **FloodWait**\n\nWaiting {e.value} seconds...")
            await sleep(e.value)
            # Retry download
            path = await upload_client.download_media(
                message=message, 
                file_name=abs_file_path, 
                progress=progress_for_pyrogram, 
                progress_args=("📥 Rᴇᴛʀyɪɴɢ Dᴏᴡɴʟᴏᴀᴅ....", ms, time.time())
            )
            
            # Re-verify after retry
            actual_path = path if path else abs_file_path
            if not os.path.exists(actual_path):
                raise Exception("Retry failed - file still not found")
            file_path = actual_path
        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()
            print(f"Download error: {error_msg}\n{error_trace}")
            
            await ms.edit(
                f"❌ **Dᴏᴡɴʟᴏᴀᴅ Fᴀɪʟᴇᴅ**\n\n"
                f"**Reason:** `{error_msg}`\n"
                f"**File:** `{filename[:50]}`\n\n"
                f"**Possible causes:**\n"
                f"• Network timeout\n"
                f"• Insufficient storage\n"
                f"• File access issues\n"
                f"• Server overload"
            )
            return
        
        # Extract metadata
        duration = 0
        try:
            metadata = extractMetadata(createParser(file_path))
            if metadata and metadata.has("duration"):
                duration = metadata.get('duration').seconds
        except Exception as e:
            print(f"Metadata extraction error: {e}")
        
        # Download thumbnail
        ph_path = None
        try:
            await ms.edit("🎨 Pʀᴇᴘᴀʀɪɴɢ Tʜᴜᴍʙɴᴀɪʟ...")
            if download_thumbnail(JAI_BAJARANGABALI_CONFIG["thumbnail_url"], thumb_path):
                ph_path = thumb_path
        except Exception as e:
            print(f"Thumbnail error: {e}")
        
        media = getattr(message, message.media.value)
        
        # Beautify filename for caption
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
        
        await ms.edit("📤 Uᴩʟᴏᴀᴅɪɴɢ Tᴏ Cʜᴀɴɴᴇʟ...")
        
        try:
            await upload_client.send_video(
                JAI_BAJARANGABALI_CONFIG["channel_id"],
                video=file_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("📤 Uᴩʟᴏᴀᴅɪɴɢ....", ms, time.time())
            )
            
            await ms.edit("✅ Sᴜᴄᴄᴇssғᴜʟʟy Uᴩʟᴏᴀᴅᴇᴅ Tᴏ Cʜᴀɴɴᴇʟ!")
        except Exception as e:
            error_msg = str(e)
            print(f"Upload error: {error_msg}\n{traceback.format_exc()}")
            await ms.edit(f"❌ **Uᴩʟᴏᴀᴅ Fᴀɪʟᴇᴅ**\n\n`{error_msg}`")
    
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"Error in handle_jai_bajarangabali: {error_msg}\n{error_trace}")
        try:
            if ms:
                await ms.edit(f"❌ **Eʀʀᴏʀ**\n\n`{error_msg}`")
            else:
                await message.reply_text(f"❌ **Eʀʀᴏʀ**\n\n`{error_msg}`")
        except:
            pass
    
    finally:
        # Cleanup
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                print(f"Cleaned up: {file_path}")
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)
                print(f"Cleaned up: {thumb_path}")
        except Exception as e:
            print(f"Cleanup error: {e}")


async def handle_auto_rename(client, message, file, filename, user_id):
    """Handle auto rename mode - use caption if available"""
    try:
        settings = await db.get_all_rename_settings(user_id)
        
        # Check if file caption contains video format extensions
        video_extensions = ['.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v']
        use_caption = False
        
        if message.caption:
            caption_lower = message.caption.lower()
            for ext in video_extensions:
                if ext in caption_lower:
                    use_caption = True
                    break
        
        # Use caption if it contains video format, otherwise use filename
        source_text = message.caption if use_caption else filename
        
        # Auto rename using settings
        new_filename = await auto_rename_file(source_text, settings)
        
        # Directly start upload process
        await start_upload_process(client, message, new_filename, file, user_id)
    
    except Exception as e:
        print(f"Error in handle_auto_rename: {e}\n{traceback.format_exc()}")
        await message.reply_text(f"❌ **Auto Rename Error**\n\n`{str(e)}`")


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
        print(f"Error in handle_manual_rename: {e}\n{traceback.format_exc()}")


async def start_upload_process(client, file_message, new_filename, file, user_id):
    """Start upload process directly based on settings"""
    file_path = None
    ph_path = None
    ms = None
    
    try:
        upload_client = premium_client if premium_client else client
        
        # Get current working directory
        cwd = os.getcwd()
        print(f"Current working directory: {cwd}")
        
        # Sanitize filename for file system
        safe_filename = sanitize_filename(new_filename)
        
        # Use absolute path
        downloads_dir = os.path.join(cwd, "downloads")
        file_path = os.path.join(downloads_dir, safe_filename)
        
        # Beautify filename for display in caption
        display_filename = beautify_filename(new_filename)
        
        # Ensure downloads directory exists with proper permissions
        os.makedirs(downloads_dir, exist_ok=True)
        print(f"Downloads directory: {downloads_dir}")
        print(f"File will be saved as: {file_path}")
        
        # Check available disk space before download
        free_space = get_disk_space()
        if free_space > 0 and file.file_size > free_space:
            await file_message.reply_text(
                f"❌ **Insufficient Storage**\n\n"
                f"📁 Required: {humanbytes(file.file_size)}\n"
                f"💾 Available: {humanbytes(free_space)}"
            )
            return
        
        status_msg = "📥 Tʀyɪɴɢ Tᴏ Dᴏᴡɴʟᴏᴀᴅɪɴɢ...."
        if premium_client:
            status_msg += "\n✅ Premium Mode (4GB)"
        ms = await file_message.reply_text(status_msg)
        
        # Download with error handling
        try:
            # Get absolute path
            abs_file_path = os.path.abspath(file_path)
            print(f"Attempting download to: {abs_file_path}")
            
            path = await upload_client.download_media(
                message=file_message, 
                file_name=abs_file_path, 
                progress=progress_for_pyrogram,
                progress_args=("📥 Dᴏᴡɴʟᴏᴀᴅɪɴɢ....", ms, time.time())
            )
            
            print(f"Pyrogram returned path: {path}")
            
            # Check both returned path and expected path
            actual_path = path if path else abs_file_path
            
            if not os.path.exists(actual_path):
                # Try to find file in downloads directory
                if os.path.exists("downloads"):
                    files = os.listdir("downloads")
                    print(f"Files in downloads/: {files}")
                    raise Exception(f"File not found at expected path: {actual_path}")
                else:
                    raise Exception("Downloads directory doesn't exist")
            
            # Update file_path to actual location
            file_path = actual_path
            
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise Exception("Downloaded file is empty (0 bytes)")
            
            print(f"✅ Download successful: {file_path} ({humanbytes(file_size)})")
            
        except FloodWait as e:
            await ms.edit(f"⏳ **FloodWait**\n\nWaiting {e.value} seconds...")
            await sleep(e.value)
            # Retry download
            path = await upload_client.download_media(
                message=file_message, 
                file_name=abs_file_path, 
                progress=progress_for_pyrogram,
                progress_args=("📥 Rᴇᴛʀyɪɴɢ Dᴏᴡɴʟᴏᴀᴅ....", ms, time.time())
            )
            
            # Re-verify after retry
            actual_path = path if path else abs_file_path
            if not os.path.exists(actual_path):
                raise Exception("Retry failed - file still not found")
            file_path = actual_path
        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()
            print(f"Download error: {error_msg}\n{error_trace}")
            
            await ms.edit(
                f"❌ **Dᴏᴡɴʟᴏᴀᴅ Fᴀɪʟᴇᴅ**\n\n"
                f"**Reason:** `{error_msg}`\n"
                f"**File:** `{new_filename[:50]}`\n\n"
                f"**Possible causes:**\n"
                f"• Network timeout\n"
                f"• Insufficient storage ({humanbytes(free_space)} free)\n"
                f"• File access issues\n"
                f"• Server overload\n\n"
                f"**Solutions:**\n"
                f"• Wait and retry\n"
                f"• Check bot storage\n"
                f"• Contact admin if persists"
            )
            return
                
        # Extract metadata
        duration = 0
        try:
            metadata = extractMetadata(createParser(file_path))
            if metadata and metadata.has("duration"):
                duration = metadata.get('duration').seconds
        except Exception as e:
            print(f"Metadata extraction error: {e}")
        
        # Get caption and thumbnail
        media = getattr(file_message, file_message.media.value)
        c_caption = await db.get_caption(user_id)
        c_thumb = await db.get_thumbnail(user_id)

        # Priority 1: Use custom caption if set
        if c_caption:
            try:
                caption = c_caption.format(
                    filename=display_filename, 
                    filesize=humanbytes(media.file_size), 
                    duration=convert(duration)
                )
            except Exception as e:
                print(f"Caption formatting error: {e}")
                await ms.edit(text=f"❌ Yᴏᴜʀ Cᴀᴩᴛɪᴏɴ Eʀʀᴏʀ\n\n`{str(e)}`")
                return
        # Priority 2: Use file caption if exists
        elif file_message.caption:
            caption = file_message.caption
        # Priority 3: Use beautified filename
        else:
            caption = f"**{display_filename}**"
    
        # Handle thumbnail
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
                print(f"Thumbnail processing error: {e}")
                ph_path = None

        await ms.edit("📤 Tʀyɪɴɢ Tᴏ Uᴩʟᴏᴀᴅɪɴɢ....")
        
        # Check if user has set upload channel
        upload_channel = await db.get_upload_channel(user_id)
        destination = upload_channel if upload_channel else user_id
        
        # Get upload type from settings
        upload_as = await db.get_upload_as(user_id)
        
        # Upload with error handling
        try:
            if upload_as == "video" and file_message.media in [MessageMediaType.VIDEO, MessageMediaType.DOCUMENT]:
                await upload_client.send_video(
                    destination,
                    video=file_path,
                    caption=caption,
                    thumb=ph_path,
                    duration=duration,
                    progress=progress_for_pyrogram,
                    progress_args=("📤 Uᴩʟᴏᴀᴅɪɴɢ....", ms, time.time())
                )
            elif upload_as == "audio" and file_message.media == MessageMediaType.AUDIO:
                await upload_client.send_audio(
                    destination,
                    audio=file_path,
                    caption=caption,
                    thumb=ph_path,
                    duration=duration,
                    progress=progress_for_pyrogram,
                    progress_args=("📤 Uᴩʟᴏᴀᴅɪɴɢ....", ms, time.time())
                )
            else:
                # Default to document
                await upload_client.send_document(
                    destination,
                    document=file_path,
                    thumb=ph_path, 
                    caption=caption, 
                    progress=progress_for_pyrogram,
                    progress_args=("📤 Uᴩʟᴏᴀᴅɪɴɢ....", ms, time.time())
                )
            
            if upload_channel:
                await ms.edit("✅ Sᴜᴄᴄᴇssғᴜʟʟy Uᴩʟᴏᴀᴅᴇᴅ Tᴏ Cʜᴀɴɴᴇʟ!")
            else:
                await ms.delete()
        
        except Exception as e:
            error_msg = str(e)
            print(f"Upload error: {error_msg}\n{traceback.format_exc()}")
            await ms.edit(f"❌ **Uᴩʟᴏᴀᴅ Fᴀɪʟᴇᴅ**\n\n`{error_msg}`")
    
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"Error in start_upload_process: {error_msg}\n{error_trace}")
        try:
            if ms:
                await ms.edit(f"❌ **Eʀʀᴏʀ**\n\n`{error_msg}`")
            else:
                await file_message.reply_text(f"❌ **Eʀʀᴏʀ**\n\n`{error_msg}`")
        except:
            pass
    
    finally:
        # Cleanup after upload
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                print(f"Cleaned up: {file_path}")
            if ph_path and os.path.exists(ph_path):
                os.remove(ph_path)
                print(f"Cleaned up: {ph_path}")
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
        print(f"Error in refunc: {e}\n{traceback.format_exc()}")
        try:
            await message.reply_text(f"❌ **Error**\n\n`{str(e)}`")
        except:
            pass
