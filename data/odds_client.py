import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.the-odds-api.com/v4"
API_KEY = os.getenv("ODDS_API_KEY")


def get_wc_odds():
    """Returns upcoming World Cup match odds from all bookmakers."""
    r = requests.get(
        f"{BASE_URL}/sports/soccer_fifa_world_cup/odds",
        params={
            "apiKey": API_KEY,
            "regions": "uk",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }
    )
    if r.status_code == 404:
        return []
    r.raise_for_status()
    remaining = r.headers.get("x-requests-remaining")
    print(f"  Odds API requests remaining: {remaining}")
    return r.json()


def parse_implied_probability(odds_data):
    """
    Converts decimal odds to normalised implied probabilities.
    Returns list of dicts: {home, away, draw, home_prob, away_prob, draw_prob}
    """
    results = []
    for match in odds_data:
        home = match.get("home_team")
        away = match.get("away_team")
        bookmakers = match.get("bookmakers", [])
        if not bookmakers:
            continue

        # Use first available bookmaker
        markets = bookmakers[0].get("markets", [])
        if not markets:
            continue

        outcomes = {o["name"]: o["price"] for o in markets[0].get("outcomes", [])}

        home_odds = outcomes.get(home, 0)
        away_odds = outcomes.get(away, 0)
        draw_odds = outcomes.get("Draw", 0)

        if not all([home_odds, away_odds, draw_odds]):
            continue

        # Raw implied probabilities
        raw_home = 1 / home_odds
        raw_away = 1 / away_odds
        raw_draw = 1 / draw_odds

        # Normalise to remove bookmaker margin
        total = raw_home + raw_away + raw_draw
        results.append({
            "home": home,
            "away": away,
            "home_prob": round(raw_home / total * 100, 1),
            "away_prob": round(raw_away / total * 100, 1),
            "draw_prob": round(raw_draw / total * 100, 1),
        })
    return results