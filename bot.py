# Rename-Bot-4GB-Meta-main\bot.py
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
            text="✅ Bot started successfully on Heroku! Ready to rename files."
        )
        logging.info(f"Startup message sent to admin {ADMIN}")
    except Exception as e:
        logging.error(f"Failed to send startup message to admin {ADMIN}: {e}\n{traceback.format_exc()}")

def main():
    if STRING_SESSION:
        apps = [Client2, bot]
        for app in apps:
            try:
                app.start()
                logging.info(f"{app.name} started successfully")
            except Exception as e:
                logging.error(f"Failed to start {app.name}: {e}\n{traceback.format_exc()}")
                return
        logging.info("✅ All clients started successfully")

        bot.loop.run_until_complete(start_web_server(bot))
        bot.loop.run_until_complete(notify_admins())  # Send message to admins
        idle()
        for app in apps:
            app.stop()
        logging.info("🛑 All clients stopped gracefully")
    else:
        bot.run()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Bot crashed: {e}\n{traceback.format_exc()}")
