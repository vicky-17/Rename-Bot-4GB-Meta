# Rename-Bot-4GB-Meta-main\plugins\cb_data.py
import os
from helper.progress import progress_for_pyrogram
from pyrogram import Client, filters
from pyrogram.types import (InlineKeyboardButton, InlineKeyboardMarkup, ForceReply, CallbackQuery)
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from helper.database import *
import os, random, time, asyncio, humanize
from PIL import Image
from datetime import timedelta
from helper.ffmpeg import (
    take_screen_shot,
    fix_thumb,
    add_metadata,
    ai_rename_file,
    smart_language_detection,
    probe_media_with_ffprobe
)
from iso639 import languages

from helper.progress import humanbytes
from helper.set import escape_invalid_curly_brackets
from config import *
from helper.media_scanner import extract_media_info



app = Client("VickyBotz", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)



@Client.on_callback_query(filters.regex('cancel'))
async def cancel(bot, update):
    try:
        await update.message.delete()
        await update.message.reply_to_message.delete()
        await update.message.continue_propagation()
    except:
        await update.message.delete()
        await update.message.continue_propagation()
        return



@Client.on_callback_query(filters.regex('^rename$'))
async def rename(bot, update):
    print("📌 Manual renamer is called.")
    date_fa = str(update.message.date)
    pattern = '%Y-%m-%d %H:%M:%S'
    date = int(time.mktime(time.strptime(date_fa, pattern)))
    chat_id = update.message.chat.id
    id = update.message.reply_to_message_id
    await update.message.delete()
    await update.message.reply_text(f"__Please Enter The New Filename...__\n\n**Note :** Extension Not Required",
                                    reply_to_message_id=id,
                                    reply_markup=ForceReply(True)
                                    )
    dateupdate(chat_id, date)





@Client.on_callback_query(filters.regex("vid"))
async def vid(bot, update):
    print("📌 This is in Video call back data :: ")

    # Creating Directory for Metadata
    if not os.path.isdir("Metadata"):
        os.mkdir("Metadata")

    
    used_ = find_one(update.from_user.id)
    used = used_["used_limit"]
    date = used_["date"]

    new_name = update.message.text
    name = new_name.split(":-")
    new_filename = name[1].strip()
    file_path = f"downloads/{new_filename}"
    print("file name :",new_filename)

    message = update.message.reply_to_message

    file = message.document or message.video or message.audio

    hinata = message

    ms = await update.message.edit("🚀 Try To Download...  ⚡")
    used_limit(update.from_user.id, file.file_size)
    c_time = time.time()
    total_used = used + int(file.file_size)
    used_limit(update.from_user.id, total_used)

    try:
        path = await bot.download_media(
            message=file,
            progress=progress_for_pyrogram,
            progress_args=("🚀 Try To Downloading...  ⚡",  ms, c_time)
        )

    except Exception as e:
        neg_used = used - int(file.file_size)
        used_limit(update.from_user.id, neg_used)
        await ms.edit(e)
        return

    file_name = file.file_name
    # AI Rename
    if "AI_Renamer" in new_filename:
        print("🤖 AI Renamer Detected – Running AI Rename Flow")
        try:
            ai_new_name = await ai_rename_file(bot, path, file_name)

            new_filename = ai_new_name  # use this name for captions
            print(f"✅ AI suggested file name: {new_filename}")

        except Exception as e:
            print(f"❌ Error in AI Renamer flow: {e}")
            final_path = path  # fallback


    # Metadata Adding Code
    _bool_metadata = find(int(message.chat.id))[2]
    
    if _bool_metadata:
        metadata = find(int(message.chat.id))[3]
        metadata_path = f"Metadata/{new_filename}"
        await add_metadata(path, metadata_path, metadata, ms)
    else:
        await ms.edit("🚀 Mode Changing...  ⚡")

    # Ensure downloads folder exists
    if not os.path.exists("downloads"):
        os.mkdir("downloads")

    final_path = f"downloads/{new_filename}"

    # Only rename if path is different and file exists
    if os.path.exists(path) and path != final_path:
        # print("You are in Rename function, path ::",path)
        # print("final Path ::",final_path)
        os.rename(path, final_path)
    else:
        final_path = path  # Use downloaded path directly

    user_id = int(update.message.chat.id)
    data = find(user_id)
    try:
        c_caption = data[1]
    except:
        pass
    thumb = data[0]

    duration = 0
    width = file.width if hasattr(file, "width") else 0
    height = file.height if hasattr(file, "height") else 0
    print(width,"x",height)

    metadata = extractMetadata(createParser(final_path))
    if metadata:
        if metadata.has("duration"):
            duration = metadata.get("duration").seconds


    if c_caption:
        vid_list = ["filename", "filesize", "duration"]
        new_tex = escape_invalid_curly_brackets(c_caption, vid_list)
        caption = new_tex.format(filename=new_filename, filesize=humanbytes(
            file.file_size), duration=timedelta(seconds=duration))
    else:
        caption = f"**{new_filename}**"

    if thumb:
        ph_path = await bot.download_media(thumb)
        Image.open(ph_path).convert("RGB").save(ph_path)
        img = Image.open(ph_path)
        img = img.resize((320, 180))  # ✅ fixed size
        img.save(ph_path, "JPEG")
        c_time = time.time()
    elif (update.message.reply_to_message.video):
        media = update.message.reply_to_message.video
        if (media.cover):
            print("Cover Detected, adding cover Image to the Video.")
            ph_path = await bot.download_media(media.cover.file_id)
        elif media.thumbs:
            print("✅ Adding Thumb Image to the Video.")
            first_thumb = media.thumbs[0]  # pick the first thumbnail
            ph_path = await bot.download_media(first_thumb.file_id)
        else:
            print("No Cover & Thumb Detected.")

    else:
        try:
            ph_path_ = await take_screen_shot(
                final_path,
                os.path.dirname(os.path.abspath(final_path)),
                random.randint(0, max(1, duration - 1))
            )
            width, height, ph_path = await fix_thumb(ph_path_)
            # force resize screenshot too
            img = Image.open(ph_path)
            img = img.resize((320, 180))
            img.save(ph_path, "JPEG")
        except Exception as e:
            ph_path = None
            print("Error at screenshot for thumb :: ",e)


    value = 2090000000
    if value < file.file_size:
        await ms.edit("🚀 Try To Upload...  ⚡")
        try:
            filw = await app.send_video(
                LOG_CHANNEL,
                video=metadata_path if _bool_metadata else final_path,
                file_name=new_filename,
                thumb=ph_path,
                duration=duration,
                width=width,
                height=height,
                caption=caption,
                progress=progress_for_pyrogram,
                progress_args=("🚀 Try To Uploading...  ⚡",  ms, c_time)
            )

            from_chat = filw.chat.id
            mg_id = filw.id
            time.sleep(2)
            await bot.copy_message(update.from_user.id, from_chat, mg_id)
            
            os.remove(file_path)

            try:
                if ph_path and os.path.exists(ph_path):
                    os.remove(ph_path)
                    os.remove(metadata_path if _bool_metadata else final_path)
                    await ms.delete()
            except:
                pass
                
        except Exception as e:
            neg_used = used - int(file.file_size)
            used_limit(update.from_user.id, neg_used)
            await ms.edit(e)
            os.remove(file_path)
            try:
                if ph_path and os.path.exists(ph_path):
                    os.remove(ph_path)
                    await ms.delete()
            except:
                return
    else:
        await ms.edit("🚀 Try To Upload...  ⚡")
        c_time = time.time()
        try:
            await bot.send_video(
                update.from_user.id,
                video=metadata_path if _bool_metadata else final_path,
                file_name=new_filename,
                thumb=ph_path,
                duration=duration,
                width=width,
                height=height,
                caption=caption,
                progress=progress_for_pyrogram,
                progress_args=("🚀 Try To Uploading...  ⚡", ms, c_time)
            )
            print("File Path :: ",file_name)
            # os.remove(file_path)
            await ms.delete()
            
        except Exception as e:
            neg_used = used - int(file.file_size)
            used_limit(update.from_user.id, neg_used)
            await ms.edit(e)
            os.remove(file_path)
            return




@Client.on_callback_query(filters.regex("doc"))
async def doc(bot, update):

    # Creating Directory for Metadata
    if not os.path.isdir("Metadata"):
        os.mkdir("Metadata")

    new_name = update.message.text
    used_ = find_one(update.from_user.id)
    used = used_["used_limit"]
    date = used_["date"]
    new_filename = new_name.split(":-")[1].strip()
    file_path = f"downloads/{new_filename}"
    message = update.message.reply_to_message
    file = message.document or message.video or message.audio
    hinata = message
    ms = await update.message.edit("🚀 Try To Download...  ⚡")
    used_limit(update.from_user.id, file.file_size)
    c_time = time.time()
    total_used = used + int(file.file_size)
    used_limit(update.from_user.id, total_used)
    try:
        path = await bot.download_media(message=file, progress=progress_for_pyrogram, progress_args=("🚀 Try To Downloading...  ⚡",  ms, c_time))

    except Exception as e:
        neg_used = used - int(file.file_size)
        used_limit(update.from_user.id, neg_used)
        await ms.edit(e)
        return
    
    # Metadata Adding Code
    _bool_metadata = find(int(message.chat.id))[2] 
    
    if _bool_metadata:
        metadata = find(int(message.chat.id))[3]
        metadata_path = f"Metadata/{new_filename}"
        await add_metadata(path, metadata_path, metadata, ms)
    else:
        await ms.edit("🚀 Mode Changing...  ⚡")

    # Ensure downloads folder exists
    if not os.path.exists("downloads"):
        os.mkdir("downloads")

    final_path = f"downloads/{new_filename}"

    # Only rename if path is different and file exists
    if os.path.exists(path) and path != final_path:
        os.rename(path, final_path)
    else:
        final_path = path  # Use downloaded path directly

    user_id = int(update.message.chat.id)
    data = find(user_id)
    try:
        c_caption = data[1]
    except:
        pass
    thumb = data[0]
    if c_caption:
        doc_list = ["filename", "filesize"]
        new_tex = escape_invalid_curly_brackets(c_caption, doc_list)
        caption = new_tex.format(
            filename=new_filename, filesize=humanbytes(file.file_size))
    else:
        caption = f"**{new_filename}**"
    if thumb:
        ph_path = await bot.download_media(thumb)
        Image.open(ph_path).convert("RGB").save(ph_path)
        img = Image.open(ph_path)
        img.resize((320, 320))
        img.save(ph_path, "JPEG")
        c_time = time.time()

    else:
        ph_path = None

    value = 2090000000
    if value < file.file_size:
        await ms.edit("🚀 Try To Upload...  ⚡")
        try:
            filw = await app.send_document(
                LOG_CHANNEL,
                document=metadata_path if _bool_metadata else final_path,
                file_name=new_filename,
                thumb=ph_path,
                caption=caption,
                progress=progress_for_pyrogram,
                progress_args=("🚀 Try To Uploading...  ⚡", ms, c_time)
            )
            from_chat = filw.chat.id
            mg_id = filw.id
            time.sleep(2)
            await bot.copy_message(update.from_user.id, from_chat, mg_id)
            await ms.delete()
            
            os.remove(file_path)
            try:
                if ph_path and os.path.exists(ph_path):
                    os.remove(ph_path)

            except:
                pass
            
        except Exception as e:
            neg_used = used - int(file.file_size)
            used_limit(update.from_user.id, neg_used)
            await ms.edit(e)
            os.remove(file_path)
            try:
                if ph_path and os.path.exists(ph_path):
                    os.remove(ph_path)
            except:
                return
    else:
        await ms.edit("🚀 Try To Upload...  ⚡")
        c_time = time.time()
        try:
            await bot.send_document(
                update.from_user.id,
                document=metadata_path if _bool_metadata else final_path,
                file_name=new_filename,
                thumb=ph_path,
                caption=caption,
                progress=progress_for_pyrogram,
                progress_args=("🚀 Try To Uploading...  ⚡",  ms, c_time)
            )
            await ms.delete()
            
            os.remove(file_path)
            
        except Exception as e:
            neg_used = used - int(file.file_size)
            used_limit(update.from_user.id, neg_used)
            await ms.edit(e)
            os.remove(file_path)
            return



@Client.on_callback_query(filters.regex("aud"))
async def aud(bot, update):

    # Creating Directory for Metadata
    if not os.path.isdir("Metadata"):
        os.mkdir("Metadata")

    new_name = update.message.text
    used_ = find_one(update.from_user.id)
    used = used_["used_limit"]
    name = new_name.split(":-")
    new_filename = name[1].strip()
    file_path = f"downloads/{new_filename}"
    message = update.message.reply_to_message
    file = message.document or message.video or message.audio
    hinata = message
    total_used = used + int(file.file_size)
    used_limit(update.from_user.id, total_used)
    ms = await update.message.edit("🚀 Try To Download...  ⚡")
    c_time = time.time()
    try:
        path = await bot.download_media(message=file, progress=progress_for_pyrogram, progress_args=("🚀 Try To Downloading...  ⚡",  ms, c_time))
    except Exception as e:
        neg_used = used - int(file.file_size)
        used_limit(update.from_user.id, neg_used)
        await ms.edit(e)
        return
    
    # Metadata Adding Code
    _bool_metadata = find(int(message.chat.id))[2] 
    
    if _bool_metadata:
        metadata = find(int(message.chat.id))[3]
        metadata_path = f"Metadata/{new_filename}"
        await add_metadata(path, metadata_path, metadata, ms)
    else:
        await ms.edit("🚀 Mode Changing...  ⚡")
        
    # Ensure downloads folder exists
    if not os.path.exists("downloads"):
        os.mkdir("downloads")

    final_path = f"downloads/{new_filename}"

    # Only rename if path is different and file exists
    if os.path.exists(path) and path != final_path:
        os.rename(path, final_path)
    else:
        final_path = path  # Use downloaded path directly

    duration = 0
    metadata = extractMetadata(createParser(final_path))
    if metadata.has("duration"):
        duration = metadata.get('duration').seconds
    user_id = int(update.message.chat.id)
    data = find(user_id)
    c_caption = data[1]
    thumb = data[0]
    if c_caption:
        aud_list = ["filename", "filesize", "duration"]
        new_tex = escape_invalid_curly_brackets(c_caption, aud_list)
        caption = new_tex.format(filename=new_filename, filesize=humanbytes(
            file.file_size), duration=timedelta(seconds=duration))
    else:
        caption = f"**{new_filename}**"

    if thumb:
        ph_path = await bot.download_media(thumb)
        Image.open(ph_path).convert("RGB").save(ph_path)
        img = Image.open(ph_path)
        img.resize((320, 320))
        img.save(ph_path, "JPEG")
        await ms.edit("🚀 Try To Upload...  ⚡")
        c_time = time.time()
        try:
            await bot.send_audio(
                update.message.chat.id,
                audio=metadata_path if _bool_metadata else final_path,
                file_name=new_filename,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("🚀 Try To Uploading...  ⚡",  ms, c_time)
            )
            await ms.delete()
            
            os.remove(file_path)
            if ph_path and os.path.exists(ph_path):
                    os.remove(ph_path)
            
        except Exception as e:
            neg_used = used - int(file.file_size)
            used_limit(update.from_user.id, neg_used)
            await ms.edit(e)
            os.remove(file_path)
            if ph_path and os.path.exists(ph_path):
                    os.remove(ph_path)
    else:
        await ms.edit("🚀 Try To Upload...  ⚡")
        c_time = time.time()
        try:
            await bot.send_audio(
                update.message.chat.id,
                audio=metadata_path if _bool_metadata else final_path,
                file_name=new_filename,
                caption=caption,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("🚀 Try To Uploading...  ⚡",  ms, c_time)
            )
            await ms.delete()
            
            os.remove(file_path)
            
        except Exception as e:
            await ms.edit(e)
            neg_used = used - int(file.file_size)
            used_limit(update.from_user.id, neg_used)
            os.remove(file_path)






@Client.on_callback_query(filters.regex("ai_detect_language"))
async def ai_detect_language_handler(bot, update):
    await update.answer("Detecting language, please wait...", show_alert=False)
    message = update.message.reply_to_message
    if not message:
        await update.message.edit("<b>❌ Reply-to message not found.</b>")
        return

    file = message.document or message.video or message.audio
    if not file:
        await update.message.edit("<b>❌ No media found in replied message.</b>")
        return

    # Initial status
    ms = await update.message.reply_text(
        "<b>🎧 Preparing to download first 10% & detect languages...</b>",
        reply_to_message_id=message.id
    )

    overall_start = time.time()

    try:
        lang_results = await smart_language_detection(
            bot,        # client
            message,    # original message with media
            ms=ms
        )
    except Exception as e:
        print(f"❌ detect_language_handler error: {e}")
        await ms.edit("<b>❌ Error while detecting language.</b>")
        return

    if not lang_results:
        await ms.edit("<b>❌ No audio streams or language could be detected.</b>")
        return

    total_elapsed = int(time.time() - overall_start)

    # Build result text
    lines = ["<b>✅ Language detection complete (first 10% of file):</b>", ""]
    for idx, lang in lang_results.items():
        lines.append(f"▫️ <b>Audio Track {idx + 1}:</b> {lang}")

    lines.append(f"\n⏱ <b>Total time:</b> {total_elapsed}s")

    await ms.edit("\n".join(lines))









@Client.on_callback_query(filters.regex("^ffprobe_detect_language$"))
async def ffprobe_detect_language_callback(bot, callback):
    message = callback.message.reply_to_message
    probe_data = await probe_media_with_ffprobe(bot, message)

    if not probe_data:
        await message.reply_text("❌ Failed to probe media.")
        return

    streams = probe_data.get("streams", [])

    audio_languages = []
    subtitle_languages = []

    for stream in streams:
        codec_type = stream.get("codec_type")
        tags = stream.get("tags", {})
        lang_code = tags.get("language")

        if not lang_code:
            continue

        # Convert ISO code to full language name
        try:
            lang_name = get_full_language_name(lang_code)
        except:
            lang_name = lang_code.upper()

        if codec_type == "audio":
            audio_languages.append(lang_name)

        elif codec_type == "subtitle":
            subtitle_languages.append(lang_name)

    # Remove duplicates
    audio_languages = list(dict.fromkeys(audio_languages))
    subtitle_languages = list(dict.fromkeys(subtitle_languages))

    # Format output
    text = "🎬 <b>Language Information</b>\n\n"

    if audio_languages:
        text += "🔊 <b>Audio Tracks:</b>\n"
        for i, lang in enumerate(audio_languages, 1):
            text += f"  {i}. {lang}\n"
    else:
        text += "🔊 <b>Audio Tracks:</b> Not found\n"

    text += "\n"

    if subtitle_languages:
        text += "💬 <b>Subtitles:</b>\n"
        for i, lang in enumerate(subtitle_languages, 1):
            text += f"  {i}. {lang}\n"
    else:
        text += "💬 <b>Subtitles:</b> Not found\n"

    await callback.message.reply_text(text)




def get_full_language_name(lang_code):
    if not lang_code:
        return None

    lang_code = lang_code.lower()

    try:
        # Try alpha3
        if len(lang_code) == 3:
            return languages.get(alpha3=lang_code).name

        # Try alpha2
        if len(lang_code) == 2:
            return languages.get(alpha2=lang_code).name

    except:
        pass

    return lang_code.upper()






@Client.on_callback_query(filters.regex("^detect_language$"))
async def detect_language_callback(bot, update):
    print("🌐 [Callback] 'detect_language' triggered.")
    
    # Get the original message containing the media
    message = update.message.reply_to_message 
    
    if not message:
        print("❌ [Callback] Error: Original message with media not found.")
        await update.message.reply_text("❌ Could not find the original message with the media file.")
        return

    print("📤 [Callback] Notifying user that scan is starting...")
    # Optional: Send a temporary new message to show progress so the user knows it's working
    temp_msg = await update.message.reply_text("📡 **Starting media scan... Fetching file headers...**")
    
    try:
        print("🔄 [Callback] Calling extract_media_info...")
        
        # Get the result from the helper file
        result_text = await extract_media_info(bot, message)
        
        print("📤 [Callback] Sending final scan result as a new message.")
        # Send the final result as a NEW message
        await update.message.reply_text(result_text)
        
    except Exception as e:
        print(f"❌ [Callback] Unexpected error: {e}")
        await update.message.reply_text(f"❌ An unexpected error occurred: {e}")
        
    finally:
        # Delete the temporary progress message
        await temp_msg.delete()
        # Acknowledge the callback so the button stops loading
        await update.answer()
