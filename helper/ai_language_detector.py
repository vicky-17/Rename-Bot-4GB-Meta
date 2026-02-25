# helper/ai_language_detector.py

from faster_whisper import WhisperModel
import asyncio
import os
import logging
import platform

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_optimal_hardware_config():
    """Detects system hardware and returns the best Faster-Whisper configuration."""
    
    config = {
        "model_size": "base",
        "device": "cpu",
        "compute_type": "int8",
        "threads": 2,
        "env_name": "Unknown"
    }

    # 1. Check for GPU (CUDA)
    has_gpu = False
    try:
        import ctranslate2
        # If there is at least 1 CUDA device, we can use the GPU
        if ctranslate2.get_cuda_device_count() > 0:
            has_gpu = True
    except Exception:
        pass

    # 2. Check System RAM (in GB)
    total_ram_gb = 2.0  # Default assumption
    try:
        import psutil
        total_ram_gb = psutil.virtual_memory().total / (1024 ** 3)
    except ImportError:
        # Fallback for Linux environments (Heroku, Koyeb, Colab) if psutil is not installed
        if hasattr(os, 'sysconf'):
            try:
                ram_bytes = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
                total_ram_gb = ram_bytes / (1024 ** 3)
            except Exception:
                pass

    # 3. Check CPU Cores
    cpu_cores = os.cpu_count() or 2

    # --- DECISION LOGIC ---
    if has_gpu:
        config["env_name"] = "🚀 GPU Environment (Colab/Local PC)"
        config["device"] = "cuda"
        config["compute_type"] = "float16" # Lightning fast on GPU
        config["model_size"] = "small"     # Small/Medium is highly accurate for Indian languages
        config["threads"] = max(2, cpu_cores - 1)
        
    else:
        # CPU Only Environments
        config["device"] = "cpu"
        config["compute_type"] = "int8" # Int8 is best and fastest for CPU
        
        # Free Tier / Low Spec (Heroku, Koyeb Free, < 2GB RAM)
        if total_ram_gb <= 2.0 or os.environ.get("DYNO") or os.environ.get("KOYEB_SERVICE_ID"):
            config["env_name"] = "☁️ Low-RAM Cloud (Heroku/Koyeb Free)"
            config["model_size"] = "base"
            config["threads"] = 2
            
        # Standard Laptop / Medium Server (2GB - 8GB RAM)
        elif total_ram_gb <= 8.0:
            config["env_name"] = "💻 Standard CPU Environment"
            config["model_size"] = "base" 
            config["threads"] = max(2, cpu_cores // 2)
            
        # High-End CPU Server / Beefy Laptop (> 8GB RAM)
        else:
            config["env_name"] = "🖥️ High-RAM CPU Server"
            config["model_size"] = "small" # Safe to load smarter models
            config["threads"] = max(2, cpu_cores - 2)

    return config

# --- INITIALIZE SMART CONFIGURATION ---
hw_config = get_optimal_hardware_config()
print(f"\n{hw_config['env_name']}")
print(f"⚡ Loading Faster-Whisper [{hw_config['model_size']}] on [{hw_config['device'].upper()}] (Threads: {hw_config['threads']}, Compute: {hw_config['compute_type']})...\n")

try:
    model = WhisperModel(
        hw_config["model_size"], 
        device=hw_config["device"], 
        compute_type=hw_config["compute_type"], 
        cpu_threads=hw_config["threads"]
    )
    print("✅ Faster-Whisper model loaded successfully!")
    
except ValueError as e:
    # Graceful Fallback if GPU is detected but drivers are missing/corrupted
    if "cuda" in str(e).lower() or "gpu" in str(e).lower():
        print("⚠️ GPU drivers missing or failed! Falling back to safe CPU mode...")
        model = WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=2)
        print("✅ Faster-Whisper model loaded successfully on CPU!")
    else:
        print(f"❌ Failed to load model: {e}")
        model = None
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    model = None


async def ai_detect_audio_language(audio_path: str) -> str:
    """
    Detects the spoken language of an audio file using Faster-Whisper.
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
            segments, info = model.transcribe(audio_path, beam_size=1)
            return info

        info = await loop.run_in_executor(None, process)

        lang_code = info.language
        probability = info.language_probability

        LANG_MAP = {
            "en": "English", "hi": "Hindi", "bn": "Bengali", "ta": "Tamil",
            "te": "Telugu", "ml": "Malayalam", "or": "Odia", "pa": "Punjabi",
            "kn": "Kannada", "gu": "Gujarati", "mr": "Marathi", "ur": "Urdu",
            "zh": "Chinese", "ko": "Korean", "ja": "Japanese", "ar": "Arabic",
            "es": "Spanish", "fr": "French", "ru": "Russian", "pt": "Portuguese",
            "id": "Indonesian", "de": "German", "it": "Italian", "tr": "Turkish",
        }

        detected_language = LANG_MAP.get(lang_code, lang_code.title())
        
        print(f"✅ Detected: {detected_language} (Code: {lang_code}, Prob: {probability:.2f})")
        return detected_language, float(probability)

    except Exception as e:
        print(f"❌ ERROR detecting language: {e}")
        return "Unknown", 0.0