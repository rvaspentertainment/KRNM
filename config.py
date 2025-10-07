import re, os, time

id_pattern = re.compile(r'^.\d+$') 

class Config(object):
    # pyro client config
    API_ID    = os.environ.get("API_ID", "")
    API_HASH  = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "") 
   
    # premium session config for 4GB uploads
    PREMIUM_SESSION = os.environ.get("PREMIUM_SESSION", "")
    
    # database config
    DB_NAME = os.environ.get("DB_NAME","Cluster0")     
    DB_URL  = os.environ.get("DB_URL","")
 
    # other configs
    BOT_UPTIME  = time.time()
    START_PIC   = os.environ.get("START_PIC", "")
    ADMIN       = [int(admin) if id_pattern.search(admin) else admin for admin in os.environ.get('ADMIN', '').split()]
    FORCE_SUB   = os.environ.get("FORCE_SUB", "") 
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "0"))

    # wes response configuration     
    WEBHOOK = bool(os.environ.get("WEBHOOK", "True"))



class Txt(object):
    # part of text configuration
    START_TXT = """<b>Hᴀɪ {} 👋,
    
I Aᴍ Fɪʟᴇ Rᴇɴᴀᴍᴇ Bᴏᴛ Wɪᴛʜ Cᴜsᴛᴏᴍ Tʜᴜᴍʙɴᴀɪʟ & Cᴀᴘᴛɪᴏɴ Sᴜᴘᴘᴏʀᴛ.
Aɴᴅ Rᴇɴᴀᴍᴇ Wɪᴛʜᴏᴜᴛ Dᴏᴡɴʟᴏᴀᴅ 💯 Fᴜʟʟʏ Wᴏʀᴋ Oɴ Tɢ</b>"""

    ABOUT_TXT = """<b>╭───────────⍟
├🤖 ᴍy ɴᴀᴍᴇ : {}
├🖥️ Dᴇᴠᴇʟᴏᴩᴇʀꜱ : <a href=https://t.me/TG_LINKS_CHANNEL2>CLICK HERE</a> 
├👨‍💻 Pʀᴏɢʀᴀᴍᴇʀ : <a href=https://t.me/TG_UPDATES1>CLICK HERE</a>
├📕 Lɪʙʀᴀʀy : <a href=https://github.com/Kushalhk>CLICK HERE</a>
├✏️ Lᴀɴɢᴜᴀɢᴇ: <a href=https://www.python.org>Pyᴛʜᴏɴ 3</a>
├💾 Dᴀᴛᴀ Bᴀꜱᴇ: <a href=https://cloud.mongodb.com>Mᴏɴɢᴏ DB</a>
├📊 Bᴜɪʟᴅ Vᴇʀꜱɪᴏɴ: Rᴇɴᴀᴍᴇʀ V3.0.0</a></b>     
╰───────────────⍟ """

    HELP_TXT = """
  <b><u>Hᴏᴡ Cᴀɴ I Hᴇʟᴘ Yᴏᴜ?</b></u>

ɪ ᴄᴀɴ ʀᴇɴᴀᴍᴇ ᴍᴇᴅɪᴀ ᴡɪᴛʜᴏᴜᴛ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ɪᴛ!
sᴘᴇᴇᴅ ᴅᴇᴘᴇɴᴅs ᴏɴ ʏᴏᴜʀ ᴍᴇᴅɪᴀ ᴅᴄ.

ɪᴜsᴛ sᴇɴᴅ ᴍᴇ ᴍᴇᴅɪᴀ ᴛᴏ ʀᴇɴᴀᴍᴇ
sᴇɴᴅ ɪᴍᴀɢᴇ ᴛᴏ sᴇᴛ ᴛʜᴜᴍʙɴᴀɪʟ 
ᴛᴏ sᴇᴇ ᴄᴜsᴛᴏᴍ ᴛʜᴜᴍʙɴᴀɪʟ ᴘʀᴇss

ℹ️ 𝗔𝗻𝘆 𝗢𝘁𝗵𝗲𝗿 𝗛𝗲𝗹𝗽 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 :- <a href=https://t.me/TG_SUPPORT_GROUP>𝑺𝑼𝑷𝑷𝑶𝑹𝑻 𝑮𝑹𝑶𝑼𝑷</a>
"""

#⚠️ Dᴏɴ'ᴛ Rᴇᴍᴏᴠᴇ Oᴜʀ Cʀᴇᴅɪᴛꜱ @ᴩyʀᴏ_ʙᴏᴛᴢ🙏🥲
    DEV_TXT = """<b><u>𝕁𝕆𝕀ℕ 𝕆𝕌ℝ 𝔾ℝ𝕆ℙ𝕊 𝔸ℕ𝔻 ℂℍ𝔸ℕℕ𝔼𝕃</b></u>
» 𝗠𝗢𝗩𝗜𝗘𝗦 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 : <a href=https://telegram.me/TG_LINKS_CHANNEL2>CLICK HERE</a>
» 𝗥𝗘𝗤𝗨𝗘𝗦𝗧 𝗚𝗥𝗢𝗨𝗣 : <a href=https://telegram.me/movies_hub_official2>CLICK HERE</a> """

    PROGRESS_BAR = """<b>\n
╭━━━━❰ᴘʀᴏɢʀᴇss ʙᴀʀ❱━➣
┣⪼ 🗃️ Sɪᴢᴇ: {1} | {2}
┣⪼ ⏳️ Dᴏɴᴇ : {0}%
┣⪼ 🚀 Sᴩᴇᴇᴅ: {3}/s
┣⪼ ⏰️ Eᴛᴀ: {4}
╰━━━━━━━━━━━━━━━➣ </b>"""

    SETTINGS_TXT = """<b>
ʜᴇʀᴇ ʏᴏᴜ ᴄᴀɴ ꜱᴇᴛᴜᴘ ʏᴏᴜʀ ꜱᴇᴛᴛɪɴɢs: </b>"""

    CAP_TXT = """<b>
<u>📑 Hᴏᴡ Tᴏ Sᴇᴛ Cᴜꜱᴛᴏᴍ Cᴀᴩᴛɪᴏɴ</u>

ᴏᴋᴇʏ,
ꜱᴇɴᴅ ᴍᴇ ʏᴏᴜʀ ᴄᴀᴩᴛɪᴏɴ
ɢᴏ ᴛᴏ ʜᴇʟᴩ ᴍᴇɴᴜᴇ ᴛᴏ ᴄʜᴇᴄᴋ ᴩᴀʀꜱᴇ_ᴍᴏᴅᴇ ᴇxᴀᴍᴩʟᴇꜱ

ᴇɢ:- 

<b>{file_name}</b>

File Size: <b>{file_size}</b>

Join us :- @TG_UPDATES1 </b>"""

    THUMBNAIL_TXT = """<b>
 /del_thumb Uꜱᴇ Tʜɪꜱ Cᴏᴍᴍᴀɴᴅ Tᴏ Dᴇʟᴇᴛᴇ Yᴏᴜʀ Oʟᴅ Tʜᴜᴍʙɴɪʟᴇ.
 /view_thumb Uꜱᴇ Tʜɪꜱ Cᴏᴍᴍᴀɴᴅ Tᴏ Vɪᴇᴡ Yᴏᴜʀ Cᴜʀʀᴇɴᴛ Tʜᴜᴍʙɴɪʟᴇ
</b>"""
  
    EXTRA_TXT = """<b>
    Exᴛʀᴀ Mᴏᴅᴜʟᴇs
ɴᴏᴛᴇ:
ᴛʜᴇꜱᴇ ᴀʀᴇ ᴛʜᴇ ᴇxᴛʀᴀ ꜰᴇᴀᴛᴜʀᴇꜱ ᴏꜰ ᴛʜɪꜱ ʙᴏᴛ

𝙲𝙻𝙸𝙲𝙺 𝙱𝙴𝙻𝙾𝚆 𝙱𝚄𝚃𝚃𝙾𝙽𝚂 𝙰𝙽𝙳 𝚄𝚂𝙴 𝙴𝚇𝚃𝚁𝙰 𝙼𝙾𝙳𝚂... 
𝚂𝚃𝙰𝚈 𝚆𝙸𝚃𝙷 𝚄𝚂 𝙰𝙽𝙳 𝚂𝚄𝙿𝙿𝙾𝚁𝚃 𝚃𝙾 𝙱𝚁𝙸𝙽𝙶 𝙼𝙾𝚁𝙴 𝙵𝙴𝙰𝚃𝚄𝚁𝙴𝚂 𝚁𝙴𝙶𝙰𝚁𝙳𝙸𝙽𝙶 𝚃𝙴𝙻𝙴𝙶𝚁𝙰𝙼 𝙱𝙾𝚃𝚂 🥰
</b>"""

    MAHAAN_TXT = """<b>
𝙷𝙴𝚁𝙴 𝚈𝙾𝚄 𝙲𝙰𝙽 𝙳𝙾𝚆𝙽𝙻𝙾𝙰𝙳 𝚂𝙾𝙼𝙴 𝚂𝙾𝙽𝙶𝚂 𝙾𝙵 𝚈𝙾𝚄𝚃𝚄𝙱𝙴. 
𝙹𝚄𝚂𝚃 𝚈𝙾𝚄 𝙽𝙴𝙴𝙳 𝚃𝙾 𝚂𝙴𝙽𝙳 𝙰 𝙲𝙾𝙼𝙼𝙰𝙽𝙳 𝚃𝙾 𝙼𝙴 /𝚜𝚘𝚗𝚐

𝙴𝚇𝙰𝙼𝙿𝙻𝙴 :- /𝚜𝚘𝚗𝚐 𝚏𝚊𝚍𝚎𝚍

𝙲𝚁𝙴𝙳𝙸𝚃𝚂 @TG_UPDATED1

𝚃𝙷𝙰𝙽𝙺 𝚈𝙾𝚄 🫶</b>"""

    LYRICS_TXT = """<b> 
𝙷𝙴𝚁𝙴 𝚈𝙾𝚄 𝙲𝙰𝙽 𝙶𝙴𝚃 𝙰 𝙻𝚈𝚁𝙸𝙲𝚂 𝙹𝚄𝚂𝚃 𝚈𝙾𝚄 𝙽𝙴𝙴𝙳 𝚃𝙾 𝚁𝙴𝙿𝙻𝚈 𝚃𝙾 𝙰 𝚂𝙿𝙴𝙲𝙸𝙵𝙸𝙲 𝙵𝙸𝙻𝙴 𝚃𝙾 𝙶𝙴𝚃 𝙻𝚈𝚁𝙸𝙲𝚂 

𝙲𝙾𝙼𝙼𝙰𝙽𝙳 /𝚕𝚢𝚛𝚒𝚌𝚜 

𝙲𝚁𝙴𝙳𝙸𝚃𝚂 :- 
@TG_UPDATES1

𝚃𝙷𝙰𝙽𝙺 𝚈𝙾𝚄 𝙰𝙻𝙻 🫶</b>"""
    
    RENAME_MODE_TXT = """<b>
🔧 <u>Rᴇɴᴀᴍᴇ Mᴏᴅᴇ Sᴇᴛᴛɪɴɢꜱ</u>

Cᴜʀʀᴇɴᴛ Mᴏᴅᴇ: <code>{mode}</code>

📌 <b>Mᴀɴᴜᴀʟ Mᴏᴅᴇ:</b>
• Yᴏᴜ ᴡɪʟʟ ʙᴇ ᴀꜱᴋᴇᴅ ᴛᴏ ᴇɴᴛᴇʀ ᴀ ɴᴇᴡ ɴᴀᴍᴇ ꜰᴏʀ ᴇᴀᴄʜ ꜰɪʟᴇ

🤖 <b>Aᴜᴛᴏ Mᴏᴅᴇ:</b>
• Aᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟy ᴅᴇᴛᴇᴄᴛꜱ ᴀɴᴅ ᴄʟᴇᴀɴꜱ ꜰɪʟᴇɴᴀᴍᴇꜱ
• Rᴇᴍᴏᴠᴇꜱ ᴜɴᴡᴀɴᴛᴇᴅ ᴡᴏʀᴅꜱ
• Dᴇᴛᴇᴄᴛꜱ ʟᴀɴɢᴜᴀɢᴇ, Qᴜᴀʟɪᴛy, ᴍᴇᴅɪᴀ ᴛyᴩᴇ
• Aᴘᴘʟɪᴇꜱ ᴄᴜꜱᴛᴏᴍ ʀᴜʟᴇꜱ

Cʜᴏᴏꜱᴇ ʏᴏᴜʀ ᴘʀᴇꜰᴇʀʀᴇᴅ ᴍᴏᴅᴇ:</b>"""
    
    AUTO_SETTINGS_TXT = """<b>
⚙️ <u>Aᴜᴛᴏ Rᴇɴᴀᴍᴇ Sᴇᴛᴛɪɴɢꜱ</u>

🔹 Aᴜᴛᴏ Dᴇᴛᴇᴄᴛ Tyᴘᴇ: <code>{detect_type}</code>
🔹 Aᴜᴛᴏ Dᴇᴛᴇᴄᴛ Lᴀɴɢᴜᴀɢᴇ: <code>{detect_lang}</code>
🔹 Qᴜᴀʟɪᴛy Fᴏʀᴍᴀᴛ: <code>{quality}</code>
🔹 Aᴜᴛᴏ Cʟᴇᴀɴ: <code>{auto_clean}</code>
🔹 Pʀᴇꜰɪx: <code>{prefix}</code>
🔹 Sᴜꜰꜰɪx: <code>{suffix}</code>
🔹 Rᴇᴍᴏᴠᴇ Wᴏʀᴅꜱ: <code>{remove_words}</code>
🔹 Rᴇᴘʟᴀᴄᴇ Wᴏʀᴅꜱ: <code>{replace_words}</code>

Cᴏɴꜰɪɢᴜʀᴇ ʏᴏᴜʀ ᴀᴜᴛᴏ-ʀᴇɴᴀᴍᴇ ꜱᴇᴛᴛɪɴɢꜱ:</b>"""

