# Note (requirements)
# pip install -U pyrogram tgcrypto python-dotenv

import os
import asyncio
from dotenv import load_dotenv

# --- Safe event loop setup (no deprecated policies) ---
# Ensure an event loop exists on MainThread before importing pyrogram.sync
try:
    loop = asyncio.get_event_loop()
    # On some setups get_event_loop() may return a closed loop, check and recreate if needed
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
except RuntimeError:
    # No current event loop for this thread — create and set a fresh one
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
# -------------------------------------------------------

# Now safe to import pyrogram
from pyrogram import Client

# Load environment variables from .env file if present
load_dotenv()


def get_input_or_env(variable_name: str, prompt: str) -> str:
    value = os.getenv(variable_name)
    if not value:
        value = input(prompt).strip()
    return value


def export_session_string():
    # Get API ID (string or int accepted by Pyrogram)
    API_ID = get_input_or_env("API_ID", "Enter your API ID: ")

    # Get API Hash
    API_HASH = get_input_or_env("API_HASH", "Enter your API Hash: ")

    # Get phone number (only needed for old phone-login flow)
    PHONE_NUMBER = os.getenv("PHONE_NUMBER")  # optional: do not force prompt
    if not PHONE_NUMBER:
        # Only prompt if user didn't provide in .env
        PHONE_NUMBER = input("Enter your phone number (with country code) or press Enter to use QR/login: ").strip() or None

    SESSION_STRING = "my_session"

    try:
        app = Client(
            name=SESSION_STRING,
            api_id=API_ID,
            api_hash=API_HASH,
            phone_number=PHONE_NUMBER
        )

        # Using context manager will handle start/stop
        with app:
            session_string = app.export_session_string()
            print("\nSession string generated successfully!\n")
            print(session_string)

        # Remove the temporary .session file if you don't want to keep it
        session_file = f"{SESSION_STRING}.session"
        if os.path.exists(session_file):
            try:
                os.remove(session_file)
                print(f"\nSession file '{session_file}' has been deleted.")
            except Exception as e:
                print(f"\nCould not delete '{session_file}': {e}")
        else:
            print(f"\nSession file '{session_file}' not found (maybe Pyrogram used a different storage).")

    except Exception as e:
        print(f"\nAn error occurred: {e}")


if __name__ == "__main__":
    export_session_string()
