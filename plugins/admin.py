# plugins\admin.py
from pyrogram.types import (InlineKeyboardButton, InlineKeyboardMarkup)
from config import *
from pyrogram import Client, filters
from helper.date import add_date
from helper.database import uploadlimit, usertype, addpre, find_one





@Client.on_message(filters.private & filters.user(ADMIN) & filters.command(["warn"]))
async def warn(c, m):
    if len(m.command) >= 3:
        try:
            user_id = m.text.split(' ', 2)[1]
            reason = m.text.split(' ', 2)[2]
            await m.reply_text("User Notfied Sucessfully 😁")
            await c.send_message(chat_id=int(user_id), text=reason)
        except:
            await m.reply_text("User Not Notfied Sucessfully 😔")
            
            

@Client.on_message(filters.private & filters.user(ADMIN) & filters.command(["addpremium"]))
async def buypremium(bot, message):
    print("📌Add premium Command.", message)
    # Split by spaces (all parts)
    parts = message.text.strip().split()
    print(f"Parts lenth {len(parts)} :: \n {parts}")

    if len(parts) < 2:
        await message.reply_text(
            "⚠️ Please provide a user ID.\nExample: `/addpremium 6216066502`"
        )
        return
    elif len(parts) > 2:
        await message.reply_text(
            "⚠️ Please provide One user ID at a time.\nExample: `/addpremium 6216066502`"
        )
        return
    else:
        user_id = parts[1]
        # Check if it's a valid number
        if not user_id.isdigit():
            await message.reply_text(
                "❌ Invalid user ID format.\nPlease provide only numeric user ID.\nExample: `/addpremium 6216066502`"
            )
            return
    
    try:
        user_id = int(parts[1])
        user_data = find_one(user_id)
        if user_data:
            user = await bot.get_users(user_id)
            print("User fetched successfully:", user.first_name)
        else:
            await message.reply_text(
                "❌ Invalid or unreachable user ID.\n"
                "This user has not started the bot yet.\n\n"
                "Ask them to send /start to the bot first."
            )
            return
    except Exception as e:
        await message.reply_text(f"⚠️ Error checking user ID: `{e}`")
        return

    button = InlineKeyboardMarkup([
        [InlineKeyboardButton("🪙 Basic", callback_data="vip1"),
        InlineKeyboardButton("⚡ Standard", callback_data="vip2")],
        [InlineKeyboardButton("💎 Pro", callback_data="vip3")],
        [InlineKeyboardButton("✖️ Cancel ✖️",callback_data = "cancel")]
        ])
        
    await message.reply_text(f"🦋 Select Plan To Upgrade...\n For user : [{user.first_name}](tg://user?id={user.id}) ", quote=True, reply_markup=button)
    
    

@Client.on_message((filters.channel | filters.private) & filters.user(ADMIN) & filters.command(["ceasepower"]))
async def ceasepremium(bot, message):
    button = InlineKeyboardMarkup([
        [InlineKeyboardButton("Limit 1GB", callback_data="cp1"),
        InlineKeyboardButton("All Power Cease", callback_data="cp2")],
        [InlineKeyboardButton("✖️ Cancel ✖️",callback_data = "cancel")]
        ])
	
    await message.reply_text("😁 Power Cease Mode...", quote=True, reply_markup=button)



@Client.on_message((filters.channel | filters.private) & filters.user(ADMIN) & filters.command(["resetpower"]))
async def resetpower(bot, message):
    button = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Yes",callback_data = "dft"),
        InlineKeyboardButton("❌ No",callback_data = "cancel")]
        ])
        
    await message.reply_text(text=f"Do You Really Want To Reset Daily Limit To Default Data Limit 2GB ?", quote=True, reply_markup=button)
    
    

# PREMIUM POWER MODE
@Client.on_callback_query(filters.regex('vip1'))
async def vip1(bot,update):
    await update.answer("Piracy is Crime...", show_alert=False)
    print("📌 Update at vip1",update)

    id = update.message.reply_to_message.text.split("/addpremium")
    user_id = id[1].replace(" ", "")
    print("User ID ::",user_id)
    inlimit  = 21474836500
    uploadlimit(int(user_id),21474836500)
    usertype(int(user_id),"🪙 Basic")
    addpre(int(user_id))
    await update.message.edit("Added Successfully To Premium Upload Limit 20 GB")
    await bot.send_message(user_id, f"Hey {update.from_user.mention} \n\nYou Are Upgraded To <b>🪙 Basic</b>. Check Your Plan Here /myplan")



@Client.on_callback_query(filters.regex('vip2'))
async def vip2(bot,update):
    await update.answer("Piracy is Crime...", show_alert=False)
    id = update.message.reply_to_message.text.split("/addpremium")
    user_id = id[1].replace(" ", "")
    inlimit = 53687091200
    uploadlimit(int(user_id), 53687091200)
    usertype(int(user_id),"⚡ Standard")
    addpre(int(user_id))
    await update.message.edit("Added Successfully To Premium Upload Limit 50 GB")
    await bot.send_message(user_id, f"Hey {update.from_user.mention} \n\nYou Are Upgraded To <b>⚡ Standard</b>. Check Your Plan Here /myplan")



@Client.on_callback_query(filters.regex('vip3'))
async def vip3(bot,update):
    await update.answer("Piracy is Crime...", show_alert=False)
    id = update.message.reply_to_message.text.split("/addpremium")
    user_id = id[1].replace(" ", "")
    inlimit = 107374182400
    uploadlimit(int(user_id), 107374182400)
    usertype(int(user_id),"💎 Pro")
    addpre(int(user_id))
    await update.message.edit("Added Successfully To Premium Upload Limit 100 GB")
    await bot.send_message(user_id, f"Hey {update.from_user.mention} \n\nYou Are Upgraded To <b>💎 Pro</b>. Check Your Plan Here /myplan")





# CEASE POWER MODE 
@Client.on_callback_query(filters.regex('cp1'))
async def cp1(bot,update):
    await update.answer("Piracy is Crime...", show_alert=False)
    id = update.message.reply_to_message.text.split("/ceasepower")
    user_id = id[1].replace(" ", "")
    inlimit  = 2147483652
    uploadlimit(int(user_id), 2147483652)
    usertype(int(user_id),"⚠️ Account Downgraded")
    addpre(int(user_id))
    await update.message.edit("Added Successfully To Upload Limit 2GB")
    await bot.send_message(user_id, f"Hey {update.from_user.mention} \n\nYou Are Downgraded To Cease <b>Limit 2GB</b>. Check Your Plan Here /myplan \n\n<b>Contact Admin :</b> @FilmyswapOfficial")



@Client.on_callback_query(filters.regex('cp2'))
async def cp2(bot,update):
    await update.answer("Piracy is Crime...", show_alert=False)
    id = update.message.reply_to_message.text.split("/ceasepower")
    user_id = id[1].replace(" ", "")
    inlimit  = 0
    uploadlimit(int(user_id), 0)
    usertype(int(user_id),"⚠️ Account Downgraded")
    addpre(int(user_id))
    await update.message.edit("Added Successfully To Upload Limit 0GB")
    await bot.send_message(user_id, f"Hey {update.from_user.mention} \n\nYou Are Downgraded To Cease <b>Limit 0GB</b>. Check Your Plan Here /myplan \n\n<b>Contact Admin :</b> @FilmyswapOfficial")




# RESET POWER MODE
@Client.on_callback_query(filters.regex('dft'))
async def dft(bot,update):
    await update.answer("Piracy is Crime...", show_alert=False)
    id = update.message.reply_to_message.text.split("/resetpower")
    user_id = id[1].replace(" ", "")
    inlimit = 2147483652
    uploadlimit(int(user_id), 2147483652)
    usertype(int(user_id),"🆓 Free")
    addpre(int(user_id))
    await update.message.edit("Daily Data Limit Has Been Reset Successfully.\n\nThis Account Has Default 2GB Remaining Capacity")
    await bot.send_message(user_id, f"Hey {update.from_user.mention} \n\nYour Daily Data Limit Has Been Reset Successfully. Check Your Plan Here /myplan\n\n<b>Contact Admin :</b> @FilmyswapOfficial")

