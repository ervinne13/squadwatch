import os
from dotenv import load_dotenv

load_dotenv()

TEAMS_TO_CHECK_JSON = os.getenv("TEAMS_TO_CHECK_JSON")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/116.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

