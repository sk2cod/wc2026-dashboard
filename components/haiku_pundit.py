import os
import anthropic
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

import streamlit as st
client = anthropic.Anthropic(api_key=st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))


@st.cache_data(ttl=3600*6, show_spinner=False)
def get_pundit_briefing(team_name: str, context: str, match_history: str) -> str:
    aest = timezone(timedelta(hours=10))
    today = datetime.now(aest).strftime("%Y-%m-%d")
    _ = today

    prompt = f"""You are a sharp, witty football pundit covering the 2026 World Cup.
Given the following team data and match history, give exactly 3 bullet points.
Be punchy, specific, and realistic. No fluff.

{context}

Match history:
{match_history if match_history else "No matches played yet."}

Return exactly this format:
🎯 **Hopes:** [realistic chance of advancing based on form and upcoming fixtures]
🟨 **Cards:** [suspension risks — who is one yellow from missing a knockout match]
⚠️ **Risk:** [biggest threat or weakness based on actual match performance]"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

@st.cache_data(ttl=3600*12, show_spinner=False)
def get_match_narrative(match_id: int, home: str, away: str,
                         home_score: int, away_score: int) -> str:
    prompt = f"""You are a sharp football pundit covering the 2026 World Cup.
    Give exactly 2 bullet points about this completed match. No filler, no preamble.

    Match: {home} {home_score} - {away_score} {away}

    Return exactly this format:
    - [How the match unfolded — who dominated, key moment, any drama]
    - [What this result means for the group — standings impact, who is under pressure]

    2 bullets only. Be specific and punchy. No extra text."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text.strip()

@st.cache_data(ttl=3600*6, show_spinner=False)
def get_betting_insight(home: str, away: str, home_prob: float,
                         draw_prob: float, away_prob: float,
                         home_history: str, away_history: str) -> str:
    prompt = f"""You are a sharp football analyst covering the 2026 World Cup.
    Analyse this upcoming match and give exactly 3 bullet points.
    No filler, no preamble.

    Match: {home} vs {away}
    Market implied probabilities: {home} {home_prob}% | Draw {draw_prob}% | {away} {away_prob}%

    {home} recent form:
    {home_history if home_history else "No matches played yet."}

    {away} recent form:
    {away_history if away_history else "No matches played yet."}

    Return exactly this format:
    📊 **Form vs Market:** [does the market reflect actual form — is one team over or underrated based on results]
    🚨 **Watch out:** [flag any trap game, upset potential, or key factor the odds might be ignoring]
    🎲 **Bet on:** [one specific call — result market or side market like cards/goals/corners — with brief reasoning]

    3 bullets only. Be specific. No generic statements."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

@st.cache_data(ttl=3600*6, show_spinner=False)
def get_group_briefing(group_name: str, teams_data: str, remaining_fixtures: str) -> str:
    prompt = f"""You are a sharp football analyst covering the 2026 World Cup.
Analyse the current situation in {group_name} and give exactly 4 bullet points.
No filler, no preamble.

Current standings:
{teams_data}

Remaining fixtures in this group:
{remaining_fixtures if remaining_fixtures else "All matches completed."}

Return exactly this format:
✅ **Through:** [which team(s) are virtually safe and why]
🎯 **Still alive:** [which teams are still fighting and what they need]
⚠️ **In trouble:** [which team(s) face elimination and what must happen]
🔥 **Watch for:** [the key remaining fixture that will decide this group]

4 bullets only. Be specific with numbers and scenarios."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text


@st.cache_data(ttl=3600*6, show_spinner=False)
def get_daily_storylines(fixtures_data: str, standings_data: str, today_str: str) -> str:
    prompt = f"""You are a sharp football analyst covering the 2026 World Cup.
Today is {today_str}. Based on today's fixtures and current group standings, 
give exactly 4 punchy storylines — things worth watching today.

Today's fixtures:
{fixtures_data}

Relevant group standings:
{standings_data}

Return exactly this format:
🔥 [storyline 1 — who needs what result and why it matters]
⚡ [storyline 2 — interesting tactical or form-based angle]
👀 [storyline 3 — group drama, wildcard implications, or upset potential]
🎯 [storyline 4 — one team or player to watch closely today]

4 bullets only. Be specific with team names, points, and scenarios. No filler."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text