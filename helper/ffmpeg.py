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








# --- PARTIAL DOWNLOAD & DETECTION ---

# --- SIMPLE 10% PARTIAL DOWNLOAD & LANGUAGE DETECTION ---

async def detect_languages_first_10_percent(
    client,
    message,
    ms=None,              # message to edit for progress (optional)
    clip_seconds: int = 30
):
    """
    Simple strategy:
      - Download only the first 10% of the file (by size).
      - Use that partial file as a valid MKV/MP4 (it contains header).
      - For each audio track:
          - Cut a short `clip_seconds` clip from the *start* of partial.
          - Run ai_detect_audio_language() on that clip.
      - Show progress + elapsed time via `ms.edit(...)`.

    Returns:
        dict[int, str] -> {audio_track_index: language_name}
    """
    temp_dir = "downloads"
    os.makedirs(temp_dir, exist_ok=True)

    media = message.video or message.document or message.audio
    if not media:
        print("❌ No media in message.")
        return {}

    duration = getattr(media, "duration", None)
    file_size = getattr(media, "file_size", None)

    if not file_size or file_size <= 0:
        print("⚠️ No valid file_size from Telegram.")
        return {}

    # Decide extension (just for filename)
    ext = os.path.splitext(getattr(media, "file_name", "") or "")[1] or ".mkv"
    message_id = message.id
    partial_file = os.path.join(temp_dir, f"partial_{message_id}{ext}")

    # --- Download bytes that roughly cover 1–10 minutes ---
    if not duration or duration <= 0:
        # Fallback: if no duration, keep old 10% behaviour
        seconds_to_cover = 10 * 60
        bytes_per_second = file_size / float(seconds_to_cover)
    else:
        # Cover up to first 10 minutes or the whole movie if < 10 min
        seconds_to_cover = min(duration, 10 * 60)
        bytes_per_second = file_size / float(duration)

    limit_bytes = int(bytes_per_second * seconds_to_cover)

    # Safety: at least 10MB, at most full file
    min_bytes = 10 * 1024 * 1024
    if limit_bytes < min_bytes and file_size > min_bytes:
        limit_bytes = min_bytes
    if limit_bytes > file_size:
        limit_bytes = file_size

    # (optional) store approx covered duration for later use
    approx_covered_seconds = limit_bytes / bytes_per_second


    print(f"📥 10% partial download: file_size={file_size}, limit_bytes={limit_bytes}")

    start_time = time.time()
    downloaded = 0
    last_percent = -1

    try:
        with open(partial_file, "wb") as f:
            async for chunk in client.stream_media(message, limit=limit_bytes):
                f.write(chunk)
                downloaded += len(chunk)

                if ms:
                    # progress relative to planned 10% chunk
                    percent = int(downloaded * 100 / limit_bytes)
                    # Update every ~5% to avoid flood
                    if percent >= last_percent + 5:
                        elapsed = int(time.time() - start_time)
                        try:
                            await ms.edit(
                                f"<b>📥 Downloading first 10% for language detection...</b>\n\n"
                                f"Progress: <b>{percent}%</b>\n"
                                f"Downloaded: <code>{downloaded / 1024 / 1024:.1f} MB"
                                f" / {limit_bytes / 1024 / 1024:.1f} MB</code>\n"
                                f"⏱ Elapsed: <b>{elapsed}s</b>"
                            )
                        except Exception:
                            pass
                        last_percent = percent

                if downloaded >= limit_bytes:
                    break

        print(f"✅ 10% partial downloaded: {downloaded / 1024 / 1024:.2f} MB -> {partial_file}")

        if not os.path.exists(partial_file):
            print("❌ Partial file not created.")
            return {}

        if ms:
            elapsed = int(time.time() - start_time)
            try:
                await ms.edit(
                    f"<b>✅ Download complete. Extracting & detecting languages...</b>\n\n"
                    f"⏱ Elapsed so far: <b>{elapsed}s</b>"
                )
            except Exception:
                pass

        # --- Probe audio streams in partial file ---
        cmd_probe = [
            "ffprobe", "-v", "error",
            "-show_entries", "stream=index,codec_type",
            "-of", "csv=p=0",
            partial_file
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd_probe,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        probe_out = stdout.decode().strip()

        audio_tracks = []
        if probe_out:
            for line in probe_out.splitlines():
                try:
                    idx, codec_type = line.strip().split(",")
                    if codec_type == "audio":
                        audio_tracks.append(int(idx))
                except ValueError:
                    continue

        print(f"🎧 Audio streams found (by ffprobe): {audio_tracks}")

        if not audio_tracks:
            print("❌ No audio streams in partial file.")
            return {}


        results = {}
        total_tracks = len(audio_tracks)

        # Approx duration actually covered by partial (we stored above)
        try:
            effective_duration = approx_covered_seconds
        except NameError:
            # fallback: assume we covered at least 10 minutes
            effective_duration = 10 * 60

        # For each audio track, take multiple 30s clips between 1–10 min
        for audio_pos, global_idx in enumerate(audio_tracks):
            langs_for_track = []
            print(f"🔍 Processing audio track {audio_pos} (ffprobe index={global_idx})")

            # Candidate start times (in seconds) inside 1–10 min region
            candidate_offsets = [120, 180, 300, 420, 540]  # 2m, 3m, 5m, 7m, 9m

            for offset in candidate_offsets:
                # Do not seek beyond what we actually downloaded
                if offset + clip_seconds > effective_duration:
                    print(f"⚠️ Skipping offset {offset}s (beyond partial duration ~{effective_duration:.1f}s)")
                    continue

                sample_path = os.path.join(
                    temp_dir, f"sample_{message_id}_a{audio_pos}_{offset}.aac"
                )

                cmd_extract = [
                    "ffmpeg", "-y",
                    "-ss", str(offset),
                    "-i", partial_file,
                    "-map", f"0:a:{audio_pos}",
                    "-t", str(clip_seconds),
                    "-c:a", "copy",          # keep original audio
                    sample_path
                ]

                print(f"🎧 Extracting 30s sample for track {audio_pos} at {offset}s -> {sample_path}")
                proc = await asyncio.create_subprocess_exec(
                    *cmd_extract,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()

                if not os.path.exists(sample_path) or os.path.getsize(sample_path) < 1024:
                    print(f"❌ Failed or too small sample at {offset}s for track {audio_pos}")
                    try:
                        os.remove(sample_path)
                    except Exception:
                        pass
                    continue

                # Detect language for this 30s sample
                lang = await ai_detect_audio_language(sample_path)
                lang = lang or "Unknown"
                print(f"🌐 Track {audio_pos} @ {offset}s -> {lang}")

                # Treat non-Unknown as a successful detection
                if lang != "Unknown":
                    langs_for_track.append(lang)

                # Cleanup sample
                try:
                    os.remove(sample_path)
                except Exception:
                    pass

                # Stop after 5 successful detections for this track
                if len(langs_for_track) >= 5:
                    break

            # Decide final language for this track
            if not langs_for_track:
                final_lang = "Unknown"
            else:
                from collections import Counter
                counts = Counter(langs_for_track)
                final_lang = counts.most_common(1)[0][0]

            results[audio_pos] = final_lang
            print(f"✅ Final language for track {audio_pos}: {final_lang} (votes={langs_for_track})")

            # Progress update per track
            if ms:
                elapsed = int(time.time() - start_time)
                try:
                    await ms.edit(
                        f"<b>🎧 Detecting languages from ~1–10 min window...</b>\n\n"
                        f"Tracks analyzed: <b>{audio_pos + 1}/{total_tracks}</b>\n"
                        f"Last track: <b>{final_lang}</b>\n"
                        f"⏱ Elapsed: <b>{elapsed}s</b>"
                    )
                except Exception:
                    pass

            print(f"🌐 Final language for track {audio_pos}: {lang}")

            # Progress update per track
            if ms:
                elapsed = int(time.time() - start_time)
                try:
                    await ms.edit(
                        f"<b>🎧 Detecting languages from first 10%...</b>\n\n"
                        f"Tracks analyzed: <b>{audio_pos + 1}/{total_tracks}</b>\n"
                        f"Last track: <b>{lang}</b>\n"
                        f"⏱ Elapsed: <b>{elapsed}s</b>"
                    )
                except Exception:
                    pass

            # Cleanup sample
            try:
                os.remove(sample_path)
            except Exception:
                pass

        return lang

    except Exception as e:
        print(f"❌ Error in detect_languages_first_10_percent: {e}")
        return {}
    finally:
        # Cleanup partial file
        if os.path.exists(partial_file):
            try:
                os.remove(partial_file)
            except Exception:
                pass
