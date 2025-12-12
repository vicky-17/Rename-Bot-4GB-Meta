# config.py
import os
from dotenv import load_dotenv


#add this two buildpack to heroku in settings serially

# https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest
# heroku/python

# Load variables from .env file
load_dotenv()

# Required Variables Config
API_ID = int(os.environ.get("API_ID", "23884743"))
API_HASH = os.environ.get("API_HASH", "b8c26efa0bc0e98f306094ca676165d2")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8417112946:AAHwa2ma5KeDnVfRSTrVS_hkTfunHK49VxM")
ADMIN = int(os.environ.get("ADMIN", "6216066502"))

# Premium 4GB Renaming Client Config
STRING_SESSION = os.environ.get("STRING_SESSION", "BQFsc8cAbkTdlS-gWfK93hYO0cvxzeBHlcJ4lZdexPqZIjtrV670iRx8NA3sXwkMGZOofqcLb5HH7SoNWTRjMlYyMQRstFQNHXLUltcyPREqiit91Bs8ERkFlIUhANECog3zXH9j-CqJl8vY38f8EACDMUXkbzQCU6Mcc1Cggf5mhLflSZAz0B8iKArFClEC-ZyOslvKCFaEFFI0TQHfozAGPjSpqtu_-6Sy1tda0L37JuXDKjJC4_kKXuI8KDYIWxouHpg1aRk8HSBJcPFHoGiW9pdEq8cHLiQuM15AGUQ-zOukjvCO5i95pFh2Cyyafq-_NOGAzVtYX4YhIcqGaFwL7-RuugAAAAFygaXGAA")

# Log & Force Channel Config
FORCE_SUBS = int(os.environ.get("FORCE_SUBS", "-1002575243889"))
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "-1002681917761"))

# Mongo DB Database Config
DATABASE_URL = os.environ.get("DATABASE_URL", "mongodb+srv://debashis_telegram:jmlUuZAYI5tZ7pzX@cluster0.rpkocnf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DATABASE_NAME = "renameBot"

# Other Variables Config
START_PIC = os.environ.get("START_PIC", "https://ibb.co/mrfjj8KW")

# SHORTNER_URL = os.environ.get("SHORTNER_URL", "")
# SHORTNER_API = os.environ.get("SHORTNER_API", "")
# TOKEN_TIMEOUT = os.environ.get("TOKEN_TIMEOUT", "")
