

import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply, CallbackQuery
from helper.database import db
from config import Config, Txt  
  

@Client.on_message(filters.private & filters.command("start"))
async def start(client, message):
    user = message.from_user
    await db.add_user(client, message)                
    button = InlineKeyboardMarkup([[
        InlineKeyboardButton('𝐂𝐇𝐀𝐍𝐍𝐄𝐋', url='https://t.me/+JrRgnfZT0GYwOGZl'),
        InlineKeyboardButton('Sᴜᴩᴩᴏʀᴛ', url='https://t.me/TG_SUPPORT_GROUP')
        ],[
        InlineKeyboardButton('⚙️ 𝐒𝐄𝐓𝐓𝐈𝐍𝐆𝐒 ⚙️', callback_data='settings') 
        ],[
        InlineKeyboardButton('Aʙᴏᴜᴛ', callback_data='about'),
        InlineKeyboardButton('Hᴇʟᴩ', callback_data='help')
    ]])
    if Config.START_PIC:
        await message.reply_photo(Config.START_PIC, caption=Txt.START_TXT.format(user.mention), reply_markup=button)       
    else:
        await message.reply_text(text=Txt.START_TXT.format(user.mention), reply_markup=button, disable_web_page_preview=True)
   

@Client.on_callback_query()
async def cb_handler(client, query: CallbackQuery):
    data = query.data 
    if data == "start":
        await query.message.edit_text(
            text=Txt.START_TXT.format(query.from_user.mention),
            disable_web_page_preview=True,
            reply_markup = InlineKeyboardMarkup([[
                InlineKeyboardButton('𝐂𝐇𝐀𝐍𝐍𝐄𝐋', url='https://t.me/+JrRgnfZT0GYwOGZl'),
                InlineKeyboardButton('Sᴜᴩᴩᴏʀᴛ', url='https://t.me/TG_SUPPORT_GROUP')
                ],[
                InlineKeyboardButton('⚙️ 𝐒𝐄𝐓𝐓𝐈𝐍𝐆𝐒 ⚙️', callback_data='settings') 
                ],[
                InlineKeyboardButton('Aʙᴏᴜᴛ', callback_data='about'),
                InlineKeyboardButton('Hᴇʟᴩ', callback_data='help')
            ]])
        )
    elif data == "help":
        await query.message.edit_text(
            text=Txt.HELP_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("♦ 𝐄𝐱𝐭𝐫𝐚 𝐌𝐨𝐝", callback_data = "extra")
                ],[
                InlineKeyboardButton("🔒 Cʟᴏꜱᴇ", callback_data = "close"),
                InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data = "start")
            ]])            
        )
    elif data == "about":
        await query.message.edit_text(
            text=Txt.ABOUT_TXT.format(client.mention),
            disable_web_page_preview = True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔒 Cʟᴏꜱᴇ", callback_data = "close"),
                InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data = "start")
            ]])            
        )
    elif data == "settings":
        await query.message.edit_text(
            text=Txt.SETTINGS_TXT.format(client.mention),
            disable_web_page_preview = True,
            reply_markup=InlineKeyboardMarkup([[
                #⚠️ don't change source code & source link ⚠️ #
                InlineKeyboardButton("𝐒𝐄𝐓 𝐂𝐀𝐏𝐓𝐈𝐎𝐍", callback_data='cap')
                ],[
                InlineKeyboardButton('𝐓𝐇𝐔𝐌𝐁𝐍𝐀𝐈𝐋', callback_data='thumbnail') 
                ],[
                InlineKeyboardButton("🔒 Cʟᴏꜱᴇ", callback_data = "close"),
                InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data = "start")
            ]])            
        )
    elif data == "dev":
        await query.message.edit_text(
            text=Txt.DEV_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔒 Cʟᴏꜱᴇ", callback_data = "close"),
                InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data = "settings")
            ]])          
        )
    elif data == "cap":
        await query.message.edit_text(
            text=Txt.CAP_TXT,
            disable_web_page_preview = True,
            reply_markup=InlineKeyboardMarkup([[
                #⚠️ don't change source code & source link ⚠️ #
                InlineKeyboardButton("🔒 Cʟᴏꜱᴇ", callback_data = "close"),
                InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data = "settings")
            ]])            
        )
    elif data == "thumbnail":
        await query.message.edit_text(
            text=Txt.THUMBNAIL_TXT.format(client.mention),
            disable_web_page_preview = True,
            reply_markup=InlineKeyboardMarkup([[
                #⚠️ don't change source code & source link ⚠️ #
                InlineKeyboardButton("🔒 Cʟᴏꜱᴇ", callback_data = "close"),
                InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data = "start")
            ]])            
        )
    elif data == "extra":
        await query.message.edit_text(
            text=Txt.EXTRA_TXT.format(client.mention),
            disable_web_page_preview = True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("𝐒𝐨𝐧𝐠 🎵", callback_data = "mahaan"), 
                InlineKeyboardButton("𝐋𝐲𝐫𝐢𝐜𝐬 🎙", callback_data = "lyrics")
                ],[
                InlineKeyboardButton("🔒 Cʟᴏꜱᴇ", callback_data = "close")
            ]])            
        )
    elif data == "mahaan":
        await query.message.edit_text(
            text=Txt.MAHAAN_TXT.format(client.mention),
            disable_web_page_preview = True,
            reply_markup=InlineKeyboardMarkup([[
                #⚠️ don't change source code & source link ⚠️ #
                InlineKeyboardButton("🔒 Cʟᴏꜱᴇ", callback_data = "close"),
                InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data = "start")
            ]])            
        )
    elif data == "lyrics":
        await query.message.edit_text(
            text=Txt.LYRICS_TXT.format(client.mention),
            disable_web_page_preview = True,
            reply_markup=InlineKeyboardMarkup([[
                #⚠️ don't change source code & source link ⚠️ #
                InlineKeyboardButton("🔒 Cʟᴏꜱᴇ", callback_data = "close"),
                InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data = "start")
            ]])            
        )

    elif data == "close":
        try:
            await query.message.delete()
            await query.message.reply_to_message.delete()
            await query.message.continue_propagation()
        except:
            await query.message.delete()
            await query.message.continue_propagation()




