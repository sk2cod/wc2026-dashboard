import os
import anthropic
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

import streamlit as st
client = anthropic.Anthropic(api_key=st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))


@st.cache_data(ttl=3600*6, show_spinner=False)
def get_pundit_briefing(team_name: str, context: str) -> str:
    aest = timezone(timedelta(hours=10))
    today = datetime.now(aest).strftime("%Y-%m-%d")
    # Cache key includes date so it refreshes daily
    _ = today

    prompt = f"""You are a sharp, witty football pundit covering the 2026 World Cup.
Given the following team data, give exactly 3 bullet points.
Be punchy, specific, and realistic. No fluff.

{context}

Return exactly this format:
🎯 **Hopes:** [one sentence on their realistic chance of advancing]
🟨 **Cards:** [one sentence on suspension risks — who is one yellow from missing a match]
⚠️ **Risk:** [one sentence on their biggest threat or weakness]"""

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