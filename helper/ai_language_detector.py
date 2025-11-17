# helper\ai_language_detector.py

import whisper
import asyncio
import os
import warnings


# Suppress harmless FP16 CPU warning
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

# Load model once globally (to avoid reloading for every call)
model = whisper.load_model("base")

"""
Size	| Parameters	English-only model	Multilingual model	Required VRAM	Relative speed
--------|-----------    ------------------  ------------------  -------------   --------------
tiny	| 39 M	        tiny.en	            tiny	            ~1 GB	        ~10x
base	| 74 M	        base.en	            base	            ~1 GB	        ~7x
small	| 244 M	        small.en	        small	            ~2 GB	        ~4x
medium	| 769 M	        medium.en	        medium	            ~5 GB	        ~2x
large	| 1550 M	    N/A	                large	            ~10 GB	        1x
turbo	| 809 M	        N/A	                turbo	            ~6 GB	        ~8x

read whisper : https://github.com/openai/whisper
"""

async def ai_detect_audio_language(audio_path: str) -> str:
    """
    Detects the spoken language of an audio file using OpenAI Whisper.
    Returns the full language name (e.g., 'English', 'Hindi', 'Bengali').
    """

    try:
        if not os.path.exists(audio_path):
            print(f"❌ Audio file not found: {audio_path}\n Returning the default file pat name")
            return None

        print(f"🎙 Detecting language for: {audio_path}")

        # Run Whisper transcribe in a thread to avoid blocking asyncio loop
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, lambda: model.transcribe(audio_path))

        lang_code = result.get("language", "unknown")

        # Map Whisper's 2-letter codes to readable language names
        LANG_MAP = {
            "en": "English",
            "hi": "Hindi",
            "bn": "Bengali",
            "ta": "Tamil",
            "te": "Telugu",
            "ml": "Malayalam",
            "or": "Odia",
            "pa": "Punjabi",
            "kn": "Kannada",
            "gu": "Gujarati",
            "mr": "Marathi",
            "ur": "Urdu",
            "zh": "Chinese",
            "ko": "Korean",
            "ja": "Japanese",
            "ar": "Arabic",
            "es": "Spanish",
            "fr": "French",
            "ru": "Russian"
        }

        detected_language = LANG_MAP.get(lang_code, lang_code.title())
        print(f"✅ Detected spoken language: {detected_language}")

        return detected_language

    except Exception as e:
        print(f"❌ ERROR detecting audio language: {e}")
        return "Unknown"
