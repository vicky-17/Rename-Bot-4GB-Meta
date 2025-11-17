# plugins\restart.py
import os, sys, asyncio
from config import *
from pyrogram import filters, Client




@Client.on_message(filters.command("restart") & filters.user(ADMIN))
async def stop_button(bot, message):
    msg = await bot.send_message(text="🔄 Processes Stoped. Bot Is Restarting...", chat_id=message.chat.id)       
    await asyncio.sleep(3)
    await msg.edit("✅️ Bot Is Restarted. Now You Can Use Me")
    os.execl(sys.executable, sys.executable, *sys.argv)

