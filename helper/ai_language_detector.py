# helper/ai_language_detector.py

from faster_whisper import WhisperModel
import asyncio
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
# "tiny" is the fastest. Use "base" if you need slightly more accuracy.
# "int8" is crucial for speed on CPU/Low-RAM environments.
MODEL_SIZE = "base"
DEVICE = "cpu"
COMPUTE_TYPE = "int8"

# Load model globally once to avoid reloading overhead
print(f"⚡ Loading Faster-Whisper model ({MODEL_SIZE}) on {DEVICE}...")
try:
    model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
    print("✅ Faster-Whisper model loaded successfully!")
except Exception as e:
    print(f"❌ Failed to load Faster-Whisper model: {e}")
    model = None

async def ai_detect_audio_language(audio_path: str) -> str:
    """
    Detects the spoken language of an audio file using Faster-Whisper.
    Returns the full language name (e.g., 'English', 'Hindi').
    """
    if not model:
        print("⚠️ Model not initialized. Skipping detection.")
        return None

    if not os.path.exists(audio_path):
        print(f"❌ Audio file not found: {audio_path}")
        return None

    print(f"🎙 Detecting language for: {audio_path}")

    try:
        # Run synchronous blocking model code in a separate thread
        loop = asyncio.get_running_loop()
        
        # We process only the first 30 seconds for language detection (handled internally by transcribe default)
        def process():
            # faster-whisper returns a generator for segments and an info object
            # We don't need to iterate over segments, 'info' contains the language detection result immediately
            segments, info = model.transcribe(audio_path, beam_size=1)
            return info

        info = await loop.run_in_executor(None, process)

        lang_code = info.language
        probability = info.language_probability

        # Map 2-letter codes to readable names
        LANG_MAP = {
            "en": "English", "hi": "Hindi", "bn": "Bengali", "ta": "Tamil",
            "te": "Telugu", "ml": "Malayalam", "or": "Odia", "pa": "Punjabi",
            "kn": "Kannada", "gu": "Gujarati", "mr": "Marathi", "ur": "Urdu",
            "zh": "Chinese", "ko": "Korean", "ja": "Japanese", "ar": "Arabic",
            "es": "Spanish", "fr": "French", "ru": "Russian", "pt": "Portuguese",
            "id": "Indonesian", "de": "German", "it": "Italian", "tr": "Turkish"
        }

        detected_language = LANG_MAP.get(lang_code, lang_code.title())
        
        print(f"✅ Detected: {detected_language} (Code: {lang_code}, Prob: {probability:.2f})")
        return detected_language, float(probability)

    except Exception as e:
        print(f"❌ ERROR detecting language: {e}")
        return "Unknown", 0.0
