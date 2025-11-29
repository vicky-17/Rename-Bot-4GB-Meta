# Ultra-Forward-Bot-main\plugins\login.py
from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PasswordHashInvalid, PhoneNumberInvalid, ApiIdInvalid, ApiIdPublishedFlood
import asyncio
import os

@Client.on_message(filters.command("generate_session") & filters.private)
async def generate_session(bot, message):
    user_id = message.from_user.id
    
    # 1. API ID
    ask = await bot.ask(user_id, "<b>Send your API ID:</b>\n\n/cancel to stop.", timeout=300)
    if ask.text == "/cancel": return await ask.reply("Cancelled.")
    try:
        api_id = int(ask.text)
    except:
        return await ask.reply("Invalid API ID. Cancelled.")
        
    # 2. API HASH
    ask = await bot.ask(user_id, "<b>Send your API HASH:</b>", timeout=300)
    if ask.text == "/cancel": return await ask.reply("Cancelled.")
    api_hash = ask.text
    
    # 3. Phone Number
    ask = await bot.ask(user_id, "<b>Send your Phone Number</b> (with country code, e.g., +91...):", timeout=300)
    if ask.text == "/cancel": return await ask.reply("Cancelled.")
    phone_number = ask.text
    
    # 4. Attempt Connection
    msg = await bot.send_message(user_id, "♻️ Processing...")
    
    client = Client(f"session_gen_{user_id}", api_id, api_hash, in_memory=True)
    try:
        await client.connect()
    except Exception as e:
        return await msg.edit(f"❌ Connection Failed: {e}")
    
    try:
        code = await client.send_code(phone_number)
    except PhoneNumberInvalid:
        await msg.edit("❌ Invalid Phone Number.")
        return
    except ApiIdInvalid:
        await msg.edit("❌ Invalid API ID/Hash.")
        return
    except Exception as e:
        await msg.edit(f"❌ Error sending code: {e}")
        return
        
    # 5. Ask for OTP
    try:
        ask = await bot.ask(user_id, "<b>Send the OTP code</b> you received on Telegram.\n\nformat: `1 2 3 4 5` (space between numbers) or just `12345`.", timeout=300)
        if ask.text == "/cancel": return await ask.reply("Cancelled.")
        phone_code = ask.text.replace(" ", "")
        
        try:
            await client.sign_in(phone_number, code.phone_code_hash, phone_code)
        except PhoneCodeInvalid:
            await msg.edit("❌ Invalid OTP.")
            return
        except SessionPasswordNeeded:
            # 6. 2FA Password
            ask = await bot.ask(user_id, "<b>Two-Step Verification detected.</b>\nSend your Password:", timeout=300)
            if ask.text == "/cancel": return await ask.reply("Cancelled.")
            password = ask.text
            try:
                await client.check_password(password)
            except PasswordHashInvalid:
                await msg.edit("❌ Invalid Password.")
                return
                
        # 7. Generate String
        session_string = await client.export_session_string()
        await client.disconnect()
        
        await bot.send_message(user_id, f"<b>✅ Session Generated!</b>\n\nTap to copy:\n<code>{session_string}</code>\n\n⚠️ Keep this safe!")
        await msg.delete()
        
    except Exception as e:
        await msg.edit(f"An error occurred: {e}")
        try: await client.disconnect()
        except: pass