# helper/ai_language_detector.py

from faster_whisper import WhisperModel
import asyncio
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- SMART CONFIGURATION ---
# Auto-detect if we are running on Heroku (Heroku automatically sets the "DYNO" environment variable)
if os.environ.get("DYNO"):
    print("☁️ Heroku Environment Detected! Applying Low-RAM CPU optimizations...")
    # 🔴 HEROKU SETTINGS (Low RAM, Weak CPU)
    MODEL_SIZE = "base"    # "base" is the safest for 512MB RAM. 
    DEVICE = "cpu"         # Heroku does not have GPUs
    COMPUTE_TYPE = "int8"  # Squeezes the model size by 50% to prevent memory crashes
    THREADS = 2            # Limits CPU cores so Heroku doesn't freeze/timeout
else:
    print("🚀 Google Colab / Local Environment Detected! Applying GPU optimizations...")
    # 🟢 GOOGLE COLAB SETTINGS (High RAM, Powerful GPU)
    MODEL_SIZE = "small"   # "small" or "medium" for flawless Indian language accuracy
    DEVICE = "cuda"        # Forces the use of the Nvidia GPU
    COMPUTE_TYPE = "float16" # float16 is lightning fast on modern GPUs
    THREADS = 4            # More threads for faster pre-processing

print(f"⚡ Loading Faster-Whisper model ({MODEL_SIZE}) on {DEVICE}...")

try:
    # Attempt to load the model with the ideal settings
    model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE, cpu_threads=THREADS)
    print("✅ Faster-Whisper model loaded successfully!")
    
except ValueError as e:
    # Fallback: If Colab is set to CPU-only instead of T4 GPU, it will catch the error and fallback gracefully
    if "cuda" in str(e).lower() or "gpu" in str(e).lower():
        print("⚠️ CUDA GPU not found! Falling back to fast CPU settings...")
        DEVICE = "cpu"
        COMPUTE_TYPE = "int8"
        model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE, cpu_threads=THREADS)
        print("✅ Faster-Whisper model loaded successfully on CPU!")
    else:
        print(f"❌ Failed to load Faster-Whisper model: {e}")
        model = None
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
        loop = asyncio.get_running_loop()
        
        def process():
            # Beam size 1 is the absolute fastest way to transcribe. 
            # It disables deep searching and just returns the most likely language instantly.
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