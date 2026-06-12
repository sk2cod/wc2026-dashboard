import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": os.getenv("FOOTBALLDATA_API_KEY")}


def get_standings():
    """Returns all 12 group standings as a list."""
    r = requests.get(f"{BASE_URL}/competitions/WC/standings", headers=HEADERS)
    r.raise_for_status()
    return r.json().get("standings", [])


def get_fixtures():
    """Returns all tournament fixtures including results."""
    r = requests.get(f"{BASE_URL}/competitions/WC/matches", headers=HEADERS)
    r.raise_for_status()
    return r.json().get("matches", [])


def get_todays_and_tomorrows_matches():
    """Returns today's and tomorrow's matches in AEST."""
    from datetime import datetime, timezone, timedelta

    aest = timezone(timedelta(hours=10))
    now_aest = datetime.now(aest)
    today_aest = now_aest.strftime("%Y-%m-%d")
    tomorrow_aest = (now_aest + timedelta(days=1)).strftime("%Y-%m-%d")

    all_matches = get_fixtures()
    return [
        m for m in all_matches
        if m.get("utcDate", "")[:10] in [today_aest, tomorrow_aest]
    ]


def get_recent_results():
    """Returns finished matches from the last 3 days."""
    all_matches = get_fixtures()
    return [
        m for m in all_matches
        if m.get("status") == "FINISHED"
    ]