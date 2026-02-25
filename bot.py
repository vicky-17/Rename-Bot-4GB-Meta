# Rename-Bot-4GB-Meta\bot.py
import logging
import traceback
from pyrogram import Client, idle
from plugins.cb_data import app as Client2
from config import *
import pyrogram.utils
from server import start_web_server

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

pyrogram.utils.MIN_CHAT_ID = -999999999999
pyrogram.utils.MIN_CHANNEL_ID = -100999999999999

bot = Client("ZRenamer", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH, plugins=dict(root='plugins'))

async def notify_admins():
    """Send startup message to admin(s)."""
    try:
        await bot.send_message(
            chat_id=ADMIN,
            text="✅ Bot & Stream Server started successfully! Ready to rename files."
        )
        logging.info(f"Startup message sent to admin {ADMIN}")
    except Exception as e:
        logging.error(f"Failed to send startup message to admin {ADMIN}: {e}")

def main():
    # 1. Start the main bot client
    bot.start()
    logging.info("✅ Main Bot started successfully")

    # 2. Start the premium string session client (if it exists)
    if STRING_SESSION:
        try:
            Client2.start()
            logging.info("✅ Premium Client started successfully")
        except Exception as e:
            logging.error(f"Failed to start Premium Client: {e}")

    # 3. Start the internal web server for FFmpeg streaming
    bot.loop.run_until_complete(start_web_server(bot))
    
    # 4. Notify Admins
    bot.loop.run_until_complete(notify_admins())
    
    # 5. Keep the bot alive and listening for messages
    idle()
    
    # 6. Stop everything gracefully when shutting down
    bot.stop()
    if STRING_SESSION:
        Client2.stop()
    logging.info("🛑 All clients stopped gracefully")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Bot crashed: {e}\n{traceback.format_exc()}")

    