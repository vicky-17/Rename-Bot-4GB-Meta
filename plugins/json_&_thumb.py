from pyrogram import Client, filters
from pyrogram.enums import ParseMode
import os, json
from datetime import datetime


# -------------------- CALLBACK -------------------- #
@Client.on_callback_query(filters.regex("getthumb"))
async def get_thumb_callback(client, update):
    await download_thumb(client, update.message)

@Client.on_callback_query(filters.regex("getcover"))
async def get_cover_callback(client, update):
    await download_cover(client, update.message)

@Client.on_callback_query(filters.regex("jsondump"))
async def jsondump_callback(client, update):
    await jsondump(client, update.message)


# -------------------- COMMAND -------------------- #
@Client.on_message(filters.private & filters.command("get_thumb"))
async def get_thumb_command(client, message):
    try:
        print("get_thumb command is trigered.")
        print("This is the message object when get_thumb command is send ::",message)
    except Exception as e:
        print("⚠️ Error !! ::",e)

@Client.on_message(filters.private & filters.command("get_cover"))
async def get_cover_command(client, message):
    await download_cover(client, message)

@Client.on_message(filters.command("jsondump"))
async def get_json_command(client, message):
    if len(message.command) < 2 or message.command[1].lower() != "ok":
        return await message.reply("⚠️ Usage: /jsondump ok")
    await jsondump(client, message)



# ------------------- GET THUMB FUNCTION LOGIC ------------------- #
async def download_thumb(client, message):
    try:
        replied = message.reply_to_message
        if not replied or not replied.media:
            return await message.reply("⚠️ Please reply to a media file first.")

        ms = await message.reply("⏳ Downloading thumbnail...")

        thumb_path = None
        if replied.photo:
            thumb_path = await client.download_media(replied.photo.file_id, file_name="thumb.jpg")
        elif replied.video and replied.video.thumbs:
            thumb_path = await client.download_media(replied.video.thumbs[0].file_id, file_name="thumb.jpg")
        elif replied.document and replied.document.thumbs:
            thumb_path = await client.download_media(replied.document.thumbs[0].file_id, file_name="thumb.jpg")

        if thumb_path:
            await ms.edit("📤 Uploading thumbnail...")
            await message.reply_photo(thumb_path, caption="🖼 Here is the thumbnail")
            os.remove(thumb_path)
            await ms.delete()
        else:
            await ms.edit("⚠️ No thumbnail available for this media.")
    except Exception as e:
        await message.reply(f"⚠️ Error: {e}")


# ------------------- GET COVER FUNCTION LOGIC ------------------- #
async def download_cover(client, message):
    try:
        print("This is in Download cover , Message object :: \n",message)
        replied = message.reply_to_message
        if not replied or not replied.media:
            return await message.reply("⚠️ Please reply to a media file first.")

        ms = await message.reply("⏳ Downloading Cover...")

        cover_path = None

        if replied.video and replied.video.cover:
            cover_path = await client.download_media(replied.video.cover.file_id, file_name="thumb.jpg")
        elif replied.photo:
            await message.reply_text(f"This is not a Video File", 
                reply_to_message_id = replied.id
            )
            return
        elif replied.document and replied.document:
            await message.reply_text(f"This is not a Video File", 
                reply_to_message_id = replied.id
            )
            return
        else:
            await message.reply("⚠️ Unknow error ocuured at downloading or detecting the cover.")

        if cover_path:
            await ms.edit("📤 Uploading Cover...")
            await message.reply_photo(cover_path, caption="🖼 Here is the Cover")
            os.remove(cover_path)
            await ms.delete()
        else:
            await ms.edit("⚠️ No cover available for this media.")
    except Exception as e:
        await message.reply(f"⚠️ Error: {e}")


# ------------------- JSON FUNCTION LOGIC ------------------- #
def pyrogram_to_dict(obj):
    """Recursively convert Pyrogram object to JSON-friendly dict, skipping empty/None values."""
    if isinstance(obj, list):
        # Filter out completely empty items
        result = [pyrogram_to_dict(i) for i in obj if i is not None]
        return [r for r in result if r not in (None, {}, [], "")]
    
    if isinstance(obj, dict):
        result = {k: pyrogram_to_dict(v) for k, v in obj.items() if v not in (None, {}, [], "")}
        return {k: v for k, v in result.items() if v not in (None, {}, [], "")}
    
    if hasattr(obj, "__dict__"):
        result = {k: pyrogram_to_dict(v) for k, v in vars(obj).items() 
                  if not k.startswith("_") and v not in (None, {}, [], "")}
        return {k: v for k, v in result.items() if v not in (None, {}, [], "")}
    
    if isinstance(obj, datetime):
        return obj.isoformat()
    
    if isinstance(obj, bytes):
        return obj.hex()
    
    # ✅ Preserve real JSON types
    if obj is None or isinstance(obj, (bool, int, float)):
        return obj
    
    return str(obj)  # fallback only



async def jsondump(client, message):
    try:
        replied = message.reply_to_message
        if not replied:
            return await message.reply("⚠️ Please reply to a media file.")

        # 🔑 If reply is a bot message with buttons, try to get its "parent" media
        if replied.reply_to_message:
            target = replied.reply_to_message
        else:
            target = replied

        # Convert only the real media message
        msg_dict = pyrogram_to_dict(target)
        json_str = json.dumps(msg_dict, indent=2, ensure_ascii=False)

        for i in range(0, len(json_str), 4000):
            await message.reply_text(
                f"<pre>{json_str[i:i+4000]}</pre>",
                parse_mode=ParseMode.HTML
            )

    except Exception as e:
        await message.reply(f"⚠️ Error: {e}")
