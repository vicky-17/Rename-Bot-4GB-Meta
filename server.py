# server.py
import math
import re
from aiohttp import web
from pyrogram import Client
from config import LOG_CHANNEL, PORT

routes = web.RouteTableDef()
tg_client = None  # We will pass the pyrogram bot here when starting

async def yield_file(client, message, start, end):
    """Mathematically translates byte ranges into Telegram 1MB chunks to skip downloads"""
    chunk_size = 1024 * 1024  # Pyrogram standard 1MB chunks
    offset = start // chunk_size
    skip_bytes = start % chunk_size
    
    limit = math.ceil((end - start + skip_bytes + 1) / chunk_size)
    
    downloaded = 0
    target_bytes = end - start + 1
    
    async for chunk in client.stream_media(message, limit=limit, offset=offset):
        if skip_bytes > 0:
            chunk = chunk[skip_bytes:]
            skip_bytes = 0
        
        if downloaded + len(chunk) > target_bytes:
            chunk = chunk[:target_bytes - downloaded]
            
        yield chunk
        downloaded += len(chunk)
        if downloaded >= target_bytes:
            break

@routes.get('/{chat_id}/{message_id}')
async def stream_handler(request):
    try:
        chat_id = int(request.match_info['chat_id'])
        message_id = int(request.match_info['message_id'])
        
        # 1. Fetch message directly from the provided chat
        message = await tg_client.get_messages(chat_id, message_id)

        if not message or message.empty:
            return web.Response(status=404, text="Message not found")

        media = message.video or message.document or message.audio
        if not media:
            return web.Response(status=404, text="No media found")

        file_size = getattr(media, "file_size", 0)
        
        # 2. Handle Range Header (FFmpeg needs this to skip the middle of the 4GB file)
        range_header = request.headers.get('Range', '')
        start = 0
        end = file_size - 1

        if range_header:
            match = re.search(r'bytes=(\d+)-(\d*)', range_header)
            if match:
                start = int(match.group(1))
                end_str = match.group(2)
                if end_str:
                    end = int(end_str)
        
        if start >= file_size or end >= file_size:
            return web.Response(status=416, text="Requested Range Not Satisfiable")

        chunk_size = end - start + 1
        
        headers = {
            'Content-Type': getattr(media, "mime_type", 'application/octet-stream'),
            'Accept-Ranges': 'bytes',
            'Content-Range': f'bytes {start}-{end}/{file_size}',
            'Content-Length': str(chunk_size),
        }

        response = web.StreamResponse(status=206 if range_header else 200, headers=headers)
        await response.prepare(request)

        # 3. Stream the specific bytes directly to FFmpeg
        async for chunk in yield_file(tg_client, message, start, end):
            await response.write(chunk)
            
        return response
        
    except Exception as e:
        print(f"Stream Server Error: {e}")
        return web.Response(status=500, text="Internal Server Error")

async def start_web_server(client: Client):
    global tg_client
    tg_client = client
    
    app = web.Application()
    app.add_routes(routes)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print(f"✅ Minimal Stream Server running internally on port {PORT}")