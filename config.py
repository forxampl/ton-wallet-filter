import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TONAPI_KEY", "")
BASE_URL = "https://tonapi.io/v2"
DELAY = 0.35
TX_LIMIT = 100
DB = "cache.db"
EXCHANGES_FILE = "known_addresses.json"
OUT = "result.txt"
