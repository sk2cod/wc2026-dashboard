import os
import anthropic
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


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