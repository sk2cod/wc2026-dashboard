import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.football-data.org/v4"
import streamlit as st
HEADERS = {"X-Auth-Token": st.secrets.get("FOOTBALLDATA_API_KEY") or os.getenv("FOOTBALLDATA_API_KEY")}


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

def get_match_details(match_id):
    """Returns details for a specific match including goals."""
    r = requests.get(
        f"{BASE_URL}/matches/{match_id}",
        headers=HEADERS
    )
    r.raise_for_status()
    return r.json()

def get_team_match_history(team_name):
    """Returns all finished matches for a specific team."""
    all_matches = get_fixtures()
    team_matches = []
    for m in all_matches:
        if m["status"] != "FINISHED":
            continue
        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]
        if team_name not in [home, away]:
            continue
        score = m["score"]["fullTime"]
        is_home = home == team_name
        opponent = away if is_home else home
        team_goals = score["home"] if is_home else score["away"]
        opp_goals = score["away"] if is_home else score["home"]

        if team_goals > opp_goals:
            outcome = "Win"
        elif team_goals < opp_goals:
            outcome = "Loss"
        else:
            outcome = "Draw"

        team_matches.append({
            "opponent": opponent,
            "team_goals": team_goals,
            "opp_goals": opp_goals,
            "outcome": outcome,
            "venue": "Home" if is_home else "Away"
        })
    return team_matches

def get_top_scorers(limit: int = 10):
    """Returns top goal scorers for the tournament."""
    r = requests.get(
        f"{BASE_URL}/competitions/WC/scorers?limit={limit}",
        headers=HEADERS
    )
    r.raise_for_status()
    return r.json().get("scorers", [])