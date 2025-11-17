# # database\GiminiAI.py
# import google.generativeai as genai
# import json
# import os
# import asyncio
# import base64
# from config import GEMINI_API_KEY


# if GEMINI_API_KEY:
#     genai.configure(api_key=GEMINI_API_KEY)
#     model = genai.GenerativeModel(
#         model_name="models/gemini-2.5-flash",
#         generation_config={"temperature": 0}  # 🔒 lock randomness
#     )
# else:
#     print("⚠️ Gemini API key not set, model disabled.")
#     model = None

# PROMPT_TEMPLATE = """
# Analyze the following media filename **and its caption** together to extract metadata.
# Respond with ONLY a valid JSON object following this structure, using null for missing values:
# {{
#   "type": "movie" or "series",
#   "title": "Clean Title",
#   "subtitle": "Extra Title Info (like guest names, episode titles)" or null,
#   "year": integer or null,
#   "quality": "string" or null,
#   "languages": ["language1", "language2"],
#   "season": integer or null,
#   "episode_start": integer or null,
#   "episode_end": integer or null,
#   "is_full_season": boolean,
#   "part": "string" or null,
#   "is_multi_audio": boolean,
#   "tags": ["tag1", "tag2"]
# }}

# ⚠️ Special parsing rules:
# 1. Title Cleaning:
#    - Remove junk uploader tags (e.g., MCU, TGMovies, @username, OTT_Downloader_Bot).
#    - Keep only the clean official title.
#    - If extra descriptors like actor/guest names ("Aamir Khan", "Salman Khan") or special episode titles are present, move them into "subtitle".
#    - If both filename and caption contain titles, prefer the caption (usually more accurate).
# 2. Year:
#    - Extract 19xx or 20xx if present, else null.
# 3. Quality:
#    - Extract only resolution + source (e.g., 240p, 360p, 480p, ,540p, 720p, 1080p, 2160p, 4k, BluRay, WEB-DL, WebRip).
#    - Ignore AAC, H.264, DD5.1, etc.
# 4. Episodes & Seasons:
#    - SxxEyy → Season=xx, Episode=yy
#    - E01-13 → Episode start=1, end=13
#    - "Completed" / "Full Season" → is_full_season=true
#    - Pxx → interpret as `"part": "Part xx"` (NOT episode).
#    - If both filename & caption differ, prefer caption data.
# 5. Languages:
#    - Extract spoken languages (e.g., "Dual Audio Hindi English" → ["Hindi", "English"]).
#    - "Hindi DD5.1" → ["Hindi"].
#    - Else [].
# 6. Multi-Audio:
#    - If contains "multi", "dual", "dual audio", or "multilingual", set is_multi_audio=true.
#    - Else false.
# 7. Tags:
#    - Capture extra descriptors like: ULLU, Netflix, Hotstar, JioCinema, JioHS, Zee5, Voot, Adult, 18+, Unrated, Combined, Complete.
#    - If none found, return [].

# Filename: "{filename}"
# Caption: "{caption}"
# """

# # Template for audio language detection
# AUDIO_PROMPT_TEMPLATE = """
# You are an AI assistant. Detect the primary spoken language(s) in the given audio file.
# Respond with only a single language name (like "English", "Hindi" etc).

# The audio file has been encoded as base64: {audio_base64}
# """

# async def ai_detect_audio_language(audio_file_path: str):
#     """
#     Sends audio file to Gemini AI to detect spoken language.
#     Returns the detected language as a string.
#     """
#     if not model:
#         print("⚠️ Gemini AI model not configured.")
#         return None

#     try:
#         # Read audio and convert to base64
#         with open(audio_file_path, "rb") as f:
#             audio_bytes = f.read()
#         audio_b64 = base64.b64encode(audio_bytes).decode()

#         prompt = AUDIO_PROMPT_TEMPLATE.format(audio_base64=audio_b64)

#         # Send async request to Gemini
#         response = await model.generate_content_async(prompt)
#         detected_language = response.text.strip()

#         # Clean response if necessary
#         detected_language = detected_language.strip().strip('"').strip("'")

#         print(f"🌐 Detected language for {os.path.basename(audio_file_path)}: {detected_language}")
#         return detected_language

#     except Exception as e:
#         print(f"❌ ERROR detecting audio language: {type(e).__name__} - {e}")
#         return None


# async def get_metadata_from_gemini(filename: str, caption: str):
#     if not model:
#         print("⚠️ Gemini AI model not configured.")
#         return None

#     try:
#         prompt = PROMPT_TEMPLATE.format(filename=filename, caption=caption)
#         response = await model.generate_content_async(prompt)
#         raw_text = response.text.strip().replace("```json", "").replace("```", "").strip()
#         try:
#             data = json.loads(raw_text)
#         except json.JSONDecodeError:
#             print("⚠️ Invalid JSON from Gemini:", raw_text)
#             return None
        
#         print(f"\n📝 Gemini Input -> Filename: {filename} \n Caption: {caption}\n")
#         print(json.dumps(data, indent=2))
#         return data
#     except Exception as e:
#         print(f"❌ ERROR: {type(e).__name__} - {e}")
#         return None

# async def main():
#     while True:
#         filename = input("\nEnter a filename to analyze (or type 'exit' to quit): ").strip()
#         if filename.lower() in ["exit", "quit"]:
#             break
#         caption = input("Enter caption (or leave blank): ").strip()
#         await get_metadata_from_gemini(filename, caption)



# # This Code can be run alonefor testing purpose, run "python Gimini.py"
# if __name__ == "__main__":
#     try:
#       asyncio.run(main())
#     except KeyboardInterrupt:
#         print("Exiting, Bye👋")
