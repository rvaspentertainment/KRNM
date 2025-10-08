from datetime import datetime
from pytz import timezone
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from config import Config
from aiohttp import web
from route import web_server
import aiohttp
import asyncio

# Import pyromod for .ask() functionality
try:
    import pyromod
    PYROMOD_AVAILABLE = True
    print("✅ Pyromod imported successfully")
except ImportError:
    PYROMOD_AVAILABLE = False
    print("⚠️ pyromod not installed - .ask() feature disabled")

async def keep_alive_ping():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://running-aime-file-get-81528fdc.koyeb.app/") as resp:
                    print(f"Pinged self: {resp.status}")
        except Exception as e:
            print(f"Ping error: {e}")
        await asyncio.sleep(60)

class Bot(Client):

    def __init__(self):
        super().__init__(
            name="renamer",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=200,
            plugins={"root": "plugins"},
            sleep_threshold=15,
        )

    async def start(self):
        await super().start()
        asyncio.create_task(keep_alive_ping())
        me = await self.get_me()
        self.mention = me.mention
        self.username = me.username  
        self.uptime = Config.BOT_UPTIME     
        if Config.WEBHOOK:
            app = web.AppRunner(await web_server())
            await app.setup()       
            await web.TCPSite(app, "0.0.0.0", 8080).start()     
        print(f"{me.first_name} Iꜱ Sᴛᴀʀᴛᴇᴅ.....✨️")
        
        # Start premium client if available
        global premium_client
        if premium_client:
            try:
                await premium_client.start()
                print("✅ Premium Client Started (4GB Upload Limit)")
            except Exception as e:
                print(f"❌ Premium Client Failed: {e}")
                print("⚠️ Continuing with Bot Only (50MB limit)")
                premium_client = None
        
        for id in Config.ADMIN:
            try: 
                status_msg = f"**__{me.first_name} Iꜱ Sᴛᴀʀᴛᴇᴅ.....✨️__**"
                if premium_client:
                    status_msg += "\n\n✅ **Premium Mode Active (4GB Upload)**"
                else:
                    status_msg += "\n\n⚠️ **Bot Mode Only (50MB Upload)**"
                await self.send_message(id, status_msg)
            except: 
                pass
                
        if Config.LOG_CHANNEL:
            try:
                curr = datetime.now(timezone("Asia/Kolkata"))
                date = curr.strftime('%d %B, %Y')
                time = curr.strftime('%I:%M:%S %p')
                log_msg = f"**__{me.mention} Iꜱ Rᴇsᴛᴀʀᴛᴇᴅ !!**\n\n📅 Dᴀᴛᴇ : `{date}`\n⏰ Tɪᴍᴇ : `{time}`\n🌐 Tɪᴍᴇᴢᴏɴᴇ : `Asia/Kolkata`\n\n🉐 Vᴇʀsɪᴏɴ : `v{__version__} (Layer {layer})`"
                if premium_client:
                    log_msg += "\n\n✅ **Premium Session Active**\n📤 Upload Limit: **4GB**"
                else:
                    log_msg += "\n\n⚠️ **Bot Mode Only**\n📤 Upload Limit: **50MB**"
                await self.send_message(Config.LOG_CHANNEL, log_msg)
            except:
                print("Pʟᴇᴀꜱᴇ Mᴀᴋᴇ Tʜɪꜱ Iꜱ Aᴅᴍɪɴ Iɴ Yᴏᴜʀ Lᴏɢ Cʜᴀɴɴᴇʟ")

    async def stop(self, *args):
        if premium_client:
            try:
                await premium_client.stop()
                print("Premium Client Stopped")
            except:
                pass
        await super().stop()
        print("Bot Stopped")

# Initialize bot
bot = Bot()

# Initialize premium client if session provided
premium_client = None

def validate_session_string(session_string):
    """Validate if session string format is correct"""
    try:
        if not session_string or len(session_string.strip()) < 100:
            return False, "Session string too short"
        
        # Basic validation - should be base64-like string
        import base64
        try:
            decoded = base64.urlsafe_b64decode(session_string + "==")
            if len(decoded) < 271:
                return False, f"Decoded session too short ({len(decoded)} bytes, need 271)"
            return True, "Valid"
        except Exception as e:
            return False, f"Invalid base64: {e}"
    except Exception as e:
        return False, f"Validation error: {e}"

if hasattr(Config, 'PREMIUM_SESSION') and Config.PREMIUM_SESSION:
    session_string = Config.PREMIUM_SESSION.strip()
    
    # Validate session string
    is_valid, validation_msg = validate_session_string(session_string)
    
    if not is_valid:
        print(f"❌ Invalid Premium Session: {validation_msg}")
        print("⚠️ Please generate a new session string using /string command")
        print("⚠️ Continuing with Bot Only (50MB limit)")
        premium_client = None
    else:
        try:
            premium_client = Client(
                name="premium_uploader",
                api_id=Config.API_ID,
                api_hash=Config.API_HASH,
                session_string=session_string,
                workers=50,
                sleep_threshold=15,
            )
            print("✅ Premium Client Initialized (Session Valid)")
        except Exception as e:
            print(f"❌ Premium Client Initialization Error: {e}")
            print("⚠️ Continuing with Bot Only (50MB limit)")
            premium_client = None
else:
    print("⚠️ No Premium Session Configured")
    print("💡 Use /string command to generate session for 4GB uploads")
    print("⚠️ Bot Mode Only (50MB limit)")

# Run the bot
if __name__ == "__main__":
    bot.run()
