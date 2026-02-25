# helper\ffmpeg.py
import time
import os
import asyncio

from collections import defaultdict

from PIL import Image
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

import json
import subprocess
# from .geminiAI import get_metadata_from_gemini
from config import LOG_CHANNEL, PORT
from .ai_language_detector import ai_detect_audio_language
from .stream_utils import get_hash

from pymediainfo import MediaInfo



async def fix_thumb(thumb):
    width = 0
    height = 0
    try:
        if thumb != None:
            metadata = extractMetadata(createParser(thumb))
            if metadata.has("width"):
                width = metadata.get("width")
            if metadata.has("height"):
                height = metadata.get("height")
                Image.open(thumb).convert("RGB").save(thumb)
                img = Image.open(thumb)
                img.resize((320, height))
                img.save(thumb, "JPEG")
    except Exception as e:
        print(e)
        thumb = None 
       
    return width, height, thumb
    
async def take_screen_shot(video_file, output_directory, ttl):
    out_put_file_name = f"{output_directory}/{time.time()}.jpg"
    file_genertor_command = [
        "ffmpeg",
        "-ss",
        str(ttl),
        "-i",
        video_file,
        "-vframes",
        "1",
        out_put_file_name
    ]
    process = await asyncio.create_subprocess_exec(
        *file_genertor_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    if os.path.lexists(out_put_file_name):
        return out_put_file_name
    return None



async def add_metadata(input_path, output_path, metadata, ms):
    try:
        await ms.edit("<i>I Found Metadata, Adding Into Your File ⚡</i>")
        command = [
            'ffmpeg', '-y', '-i', input_path, '-map', '0', '-c:s', 'copy', '-c:a', 'copy', '-c:v', 'copy',
            '-metadata', f'title={metadata}',  # Set Title Metadata
            '-metadata', f'author={metadata}',  # Set Author Metadata
            '-metadata:s:s', f'title={metadata}',  # Set Subtitle Metadata
            '-metadata:s:a', f'title={metadata}',  # Set Audio Metadata
            '-metadata:s:v', f'title={metadata}',  # Set Video Metadata
            '-metadata', f'artist={metadata}',  # Set Artist Metadata
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        e_response = stderr.decode().strip()
        t_response = stdout.decode().strip()
        # print(e_response)
        # print(t_response)

        
        if os.path.exists(output_path):
            await ms.edit("<i>Metadata Has Been Successfully Added To Your File ✅</i>")
            return output_path
        else:
            await ms.edit("<i>Failed To Add Metadata To Your File ❌</i>")
            return None
    except Exception as e:
        print(f"Error occurred while adding metadata: {str(e)}")
        await ms.edit("<i>An Error Occurred While Adding Metadata To Your File ❌</i>")
        return None





async def ai_rename_file(bot, file_path, file_name):
    try:
        print(f"📌 Checking available audio tracks in: {file_path}")
        print("The Fil Name ::",file_name)

        AI_FILES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "AI_Files")
        os.makedirs(AI_FILES_DIR, exist_ok=True)  # ensure folder exists

        base_name = os.path.splitext(os.path.basename(file_path))[0]
        print("This is the base Name :: ",base_name)

        # Step 1: get streams using helper
        media_streams = await get_media_streams(file_path)
        streams = media_streams["audio"]

        print(f"🎧 Audio streams found: {streams}")


        extracted_files = []

        # Step 2: extract each audio stream
        for i, stream_index in enumerate(streams):
            temp_file = f"{base_name}_audio{i}.aac"

            # Extract short segment for language detection
            command = [
                "ffmpeg", "-y",
                "-i", file_path,
                "-ss", "00:05:00",      # start at 10 min
                "-t", "00:10:00",       # 2-minute clip
                "-map", f"0:a:{i}",
                "-c:a", "aac",
                temp_file
            ]
            proc = await asyncio.create_subprocess_exec(
                *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()

            if not os.path.exists(temp_file):
                print(f"❌ Failed audio stream {i}")
                continue

            # Step 3: detect language
            detected_language = await ai_detect_audio_language(temp_file)
            print(f"🌐 Stream {i} detected language: {detected_language}")

            # Step 4: append detected language to file name
            name, ext = os.path.splitext(file_name)
            file_name = f"{name}_{detected_language}{ext}"
            print(f"📝 Updated file name: {file_name}")

            # # Step 5: rename & move to AI_Files folder
            # output_file = os.path.join(AI_FILES_DIR, f"{base_name}_audio{i}_{detected_language}.aac")
            # os.rename(temp_file, output_file)
            # extracted_files.append(output_file)

            # # Step 6: send to log channel
            # await bot.send_document(
            #     LOG_CHANNEL,
            #     output_file,
            #     caption=f"🎵 Audio Stream {i} ({detected_language}) – 10:00–12:00"
            # )
            # print(f"✅ Extracted audio stream {i} → {output_file}")

            # Step 7: cleanup temp files (if any remain)
            if os.path.exists(temp_file):
                os.remove(temp_file)

        return file_name

    except Exception as e:
        print("❌ Error at audio extractor :: ", e)
        return file_name
















async def probe_media_with_ffprobe(client, message, temp_dir="downloads"):
    print("\n================= FFPROBE DEBUG START =================")

    if not message:
        print("❌ Message is None")
        return None

    media = message.video or message.document or message.audio
    if not media:
        print("❌ No media found in message")
        return None

    print(f"📁 File name: {getattr(media, 'file_name', None)}")
    print(f"📦 File size: {getattr(media, 'file_size', None)}")
    print(f"⏱ Duration: {getattr(media, 'duration', None)}")

    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"probe_{message.id}.mkv")

    CHUNK_LIMIT = 1 * 1024 * 1024  # 1MB
    downloaded = 0

    try:
        print("📥 Starting header download...")

        with open(temp_path, "wb") as f:
            async for chunk in client.stream_media(media, limit=CHUNK_LIMIT):
                f.write(chunk)
                downloaded += len(chunk)
                print(f"   ➜ Downloaded: {downloaded} bytes")

                if downloaded >= CHUNK_LIMIT:
                    break

        print(f"✅ Header download complete. Total: {downloaded} bytes")

        if not os.path.exists(temp_path):
            print("❌ Temp file not created")
            return None

        if downloaded == 0:
            print("❌ Nothing downloaded")
            return None

        # FFPROBE COMMAND
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries",
            "stream=index,codec_type:stream_tags=language",
            "-of", "json",
            temp_path
        ]

        print("🚀 Running ffprobe command:")
        print(" ".join(cmd))

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()

        print(f"🔢 ffprobe return code: {proc.returncode}")
        print("📤 STDOUT:")
        print(stdout.decode(errors="ignore"))
        print("📤 STDERR:")
        print(stderr.decode(errors="ignore"))

        if proc.returncode != 0:
            print("❌ ffprobe failed with non-zero return code")
            return None

        if not stdout:
            print("❌ ffprobe returned empty stdout")
            return None

        try:
            probe_data = json.loads(stdout.decode())
            print("✅ JSON parsed successfully")
            print("Streams found:", probe_data.get("streams"))
            return probe_data
        except Exception as e:
            print("❌ JSON parse error:", e)
            return None

    except Exception as e:
        print("❌ Exception in probe_media_with_ffprobe:", e)
        return None

    finally:
        print("🧹 Cleaning up temp file")
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                print("✅ Temp file removed")
            except Exception as e:
                print("❌ Failed to remove temp file:", e)

        print("================= FFPROBE DEBUG END =================\n")





async def smart_language_detection(client, message, ms=None):
    temp_dir = "downloads"
    os.makedirs(temp_dir, exist_ok=True)

    media = message.video or message.document or message.audio
    if not media:
        print("❌ No media in message.")
        return {}

    # Get duration, fallback to 0 if not present
    duration = getattr(media, "duration", 0)

    # Decide offset: 10 minutes in (600s) to skip intros/silent logos. 
    # If the video is very short, grab from 1/3rd of the way through.
    offset = 600 if duration > 600 else (duration // 3 if duration > 30 else 0)
    clip_seconds = 20  # 20 seconds is plenty for Whisper AI

    if ms:
        try:
            await ms.edit("<b>🔗 Generating Stream Link...</b>")
        except:
            pass

    # --- 1. GENERATE THE DIRECT STREAM URL ---
    try:
        from config import PORT
        from .stream_utils import get_hash
        stream_url = f"http://127.0.0.1:{PORT}/{message.chat.id}/{message.id}?hash={get_hash(message)}"
    except Exception as e:
        print(f"❌ Failed to generate stream URL: {e}")
        return {}

    # --- 2. EXTRACT A 20-SECOND AUDIO-ONLY SAMPLE (SUPER FAST) ---
    if ms:
        try:
            await ms.edit("<b>✂️ Extracting 20s audio sample (Skipping video to save time)...</b>")
        except:
            pass

    sample_mkv = os.path.join(temp_dir, f"audio_sample_{message.id}.mkv")
    
    cmd_extract = [
        "ffmpeg", "-y",
        "-ss", str(offset),
        "-i", stream_url,
        "-t", str(clip_seconds),
        "-map", "0:a",      # Grab ALL audio tracks at once
        "-vn", "-sn",       # NO video, NO subtitles (Saves massive bandwidth and time)
        "-c:a", "copy",     # Direct copy, no CPU encoding
        sample_mkv
    ]
    
    proc = await asyncio.create_subprocess_exec(
        *cmd_extract,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await proc.communicate()

    # Fallback: If fast seek failed (rare, but happens with bad MKV headers), grab the first 20s
    if not os.path.exists(sample_mkv) or os.path.getsize(sample_mkv) < 1024:
        print("⚠️ Seek failed, falling back to start of file...")
        cmd_extract_fallback = [
            "ffmpeg", "-y",
            "-i", stream_url,
            "-t", str(clip_seconds),
            "-map", "0:a",
            "-vn", "-sn",
            "-c:a", "copy",
            sample_mkv
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd_extract_fallback, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()

    if not os.path.exists(sample_mkv) or os.path.getsize(sample_mkv) < 1024:
        print("❌ Failed to extract audio sample.")
        return {}

    # --- 3. PROCESS WITH WHISPER AI ---
    from pymediainfo import MediaInfo
    from helper.ai_language_detector import ai_detect_audio_language
    
    media_info = MediaInfo.parse(sample_mkv)
    audio_tracks = [t for t in media_info.tracks if t.track_type == "Audio"]
    
    results = {}
    
    if ms:
        try:
            await ms.edit(f"<b>🎙 Running AI detection on {len(audio_tracks)} audio tracks...</b>")
        except:
            pass

    for idx, track in enumerate(audio_tracks):
        temp_audio = os.path.join(temp_dir, f"temp_audio_{message.id}_{idx}.aac")
        
        # Extract individual audio tracks to feed into Whisper
        cmd_extract_audio = [
            "ffmpeg", "-y",
            "-i", sample_mkv,
            "-map", f"0:a:{idx}",
            "-c:a", "aac",
            temp_audio
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd_extract_audio,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        
        if os.path.exists(temp_audio):
            try:
                # Send to Whisper
                detected_lang, prob = await ai_detect_audio_language(temp_audio)
                results[idx] = f"{detected_lang} ({(prob * 100):.1f}%)"
            except Exception as e:
                print(f"Error detecting language for track {idx}: {e}")
                results[idx] = "Error"
            finally:
                try: os.remove(temp_audio)
                except: pass

    # Cleanup the multi-track audio sample
    try: os.remove(sample_mkv)
    except: pass
    
    return results