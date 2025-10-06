
from pyrogram import Client, filters, enums 
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import UserNotParticipant
from config import Config
from helper.database import db

async def not_subscribed(_, client, message):
    await db.add_user(client, message)
    if not Config.FORCE_SUB:
        return False
    try:             
        user = await client.get_chat_member(Config.FORCE_SUB, message.from_user.id) 
        if user.status == enums.ChatMemberStatus.BANNED:
            return True 
        else:
            return False                
    except UserNotParticipant:
        pass
    return True


@Client.on_message(filters.private & filters.create(not_subscribed))
async def forces_sub(client, message):
    buttons = [[InlineKeyboardButton(text="📢 Join Update Channel 📢", url=f"https://t.me/{Config.FORCE_SUB}") ]]
    text = "**HEY DUDE YOU'RE NOT JOINED MY CHANNEL 😞. SO PLEASE JOIN OUR CHANNEL BEFORE USING ME........ 😇**"
    try:
        user = await client.get_chat_member(Config.FORCE_SUB, message.from_user.id)    
        if user.status == enums.ChatMemberStatus.BANNED:                                   
            return await client.send_message(message.from_user.id, text="𝚈𝙾𝚄'𝚁𝙴 𝙱𝙰𝙽𝙽𝙴𝙳 𝚃𝙾 𝚄𝚂𝙴 𝙼𝙴 𝙵𝙾𝚁 𝙼𝙾𝚁𝙴 𝙳𝙴𝚃𝙰𝙸𝙻𝚂 𝙲𝙾𝙽𝚃𝙰𝙲𝚃 𝙰𝙳𝙼𝙸𝙽 𝙾𝚁 𝙾𝚆𝙽𝙴𝚁 🥰")  
    except UserNotParticipant:                       
        return await message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(buttons))
    return await message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(buttons))
          



