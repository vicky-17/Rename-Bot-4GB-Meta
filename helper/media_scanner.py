# helper/media_scanner.py
import os
import tempfile
from pymediainfo import MediaInfo

async def extract_media_info(client, message):
    print("📡 [Media Scanner] Starting media scan process...")
    if not message.media:
        print("❌ [Media Scanner] Error: No media found in the message.")
        return "❌ No media found to scan."

    # 5MB chunk is usually enough for MKV/MP4 headers
    CHUNK_LIMIT = 5 * 1024 * 1024 
    downloaded = 0
    temp_fd, temp_path = tempfile.mkstemp(suffix=".mkv")
    
    try:
        print(f"📥 [Media Scanner] Created temp file: {temp_path}. Streaming first 5MB...")
        with os.fdopen(temp_fd, 'wb') as f:
            async for chunk in client.stream_media(message):
                f.write(chunk)
                downloaded += len(chunk)
                if downloaded >= CHUNK_LIMIT:
                    print("✅ [Media Scanner] Reached 5MB chunk limit. Stopping stream.")
                    break
        
        print("🔍 [Media Scanner] Parsing media info using pymediainfo...")
        media_info = MediaInfo.parse(temp_path)
        
        audios = []
        subs = []
        
        for track in media_info.tracks:
            if track.track_type == "Audio":
                lang = getattr(track, 'language', 'Unknown') or 'Unknown'
                title = getattr(track, 'title', '')
                track_name = f"{lang}" + (f" ({title})" if title else "")
                audios.append(track_name)
                print(f"🎵 [Media Scanner] Found Audio Track: {track_name}")
            elif track.track_type == "Text":
                lang = getattr(track, 'language', 'Unknown') or 'Unknown'
                title = getattr(track, 'title', '')
                track_name = f"{lang}" + (f" ({title})" if title else "")
                subs.append(track_name)
                print(f"✏️ [Media Scanner] Found Subtitle Track: {track_name}")
        
        print("✅ [Media Scanner] Scan completed successfully. Formatting results...")
        
        text = "🎬 **Media Scan Results**\n\n"
        text += f"⭐ **Audio Tracks ({len(audios)}):** {', '.join(audios) if audios else 'None'}\n"
        text += f"✏️ **Subtitle Tracks ({len(subs)}):** {', '.join(subs) if subs else 'None'}\n\n"
        text += "📌 *All information is fetched directly from the file header API.*"
        
        return text

    except Exception as e:
        print(f"❌ [Media Scanner] Error during media scan: {e}")
        return f"❌ Error scanning file: {e}"
    finally:
        # ALWAYS clean up the temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            print(f"🗑️ [Media Scanner] Cleaned up temporary file: {temp_path}")