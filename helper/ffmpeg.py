# helper\ffmpeg.py
import time
import os
import asyncio
from PIL import Image
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

import json
import subprocess
# from .geminiAI import get_metadata_from_gemini
from config import LOG_CHANNEL
from .ai_language_detector import ai_detect_audio_language

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


        # Step 1: probe all streams
        cmd_probe = [
            "ffprobe", "-v", "error",
            "-show_entries", "stream=index,codec_type",
            "-of", "csv=p=0",
            file_path
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd_probe, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()

        streams = []
        for line in stdout.decode().splitlines():
            index, codec_type = line.strip().split(",")
            if codec_type == "audio":
                streams.append(int(index))

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
