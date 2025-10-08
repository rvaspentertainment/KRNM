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
        if premium_client:
            await premium_client.start()
            print("✅ Premium Client Started (4GB Upload Limit)")
        
        for id in Config.ADMIN:
            try: 
                status_msg = f"**__{me.first_name} Iꜱ Sᴛᴀʀᴛᴇᴅ.....✨️__**"
                if premium_client:
                    status_msg += "\n\n✅ **Premium Mode Active (4GB Upload)**"
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
            await premium_client.stop()
            print("Premium Client Stopped")
        await super().stop()
        print("Bot Stopped")

# Initialize bot
bot = Bot()

# Initialize premium client if session provided
premium_client = None
if hasattr(Config, 'PREMIUM_SESSION') and Config.PREMIUM_SESSION:
    try:
        premium_client = Client(
            name="premium_uploader",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            session_string=Config.PREMIUM_SESSION,
            workers=50,
            sleep_threshold=15,
        )
        print("✅ Premium Client Initialized")
    except Exception as e:
        print(f"⚠️ Premium Client Error: {e}")
        premium_client = None
else:
    print("⚠️ No Premium Session - Using Bot Only (50MB limit)")

# Run the bot
if __name__ == "__main__":
    bot.run()
