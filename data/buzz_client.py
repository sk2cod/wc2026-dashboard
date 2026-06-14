import os
import streamlit as st
from tavily import TavilyClient

def get_tavily_client():
    api_key = st.secrets.get("TAVILY_API_KEY") or os.getenv("TAVILY_API_KEY")
    return TavilyClient(api_key=api_key)


CATEGORY_ICONS = {
    "music": "🎵",
    "venue": "🏟️",
    "player": "⚽",
    "team": "👥",
    "social": "📱",
    "record": "📊",
    "culture": "🌍",
    "default": "🔥"
}


def categorise(title: str) -> str:
    title_lower = title.lower()
    if any(w in title_lower for w in ["song", "music", "anthem", "singer", "album"]):
        return "music"
    elif any(w in title_lower for w in ["stadium", "venue", "altitude", "pitch", "ground"]):
        return "venue"
    elif any(w in title_lower for w in ["goal", "scored", "player", "striker", "keeper"]):
        return "player"
    elif any(w in title_lower for w in ["team", "squad", "manager", "coach", "nation"]):
        return "team"
    elif any(w in title_lower for w in ["trending", "viral", "social", "tiktok", "twitter", "instagram"]):
        return "social"
    elif any(w in title_lower for w in ["record", "stat", "history", "first", "most"]):
        return "record"
    else:
        return "default"


@st.cache_data(ttl=3600*12, show_spinner=False)
def get_buzz_stories(max_results: int = 5) -> list:
    """Fetches and filters fresh FIFA World Cup 2026 buzz stories via Tavily + Haiku."""
    try:
        from datetime import datetime, timezone, timedelta
        aest = timezone(timedelta(hours=10))
        today_str = datetime.now(aest).strftime("%B %d %Y")

        client = get_tavily_client()

        import random
        all_queries = [
            "FIFA World Cup 2026 fun facts unusual stories viral",
            "FIFA World Cup 2026 trending social media players teams",
            "World Cup 2026 venue altitude weather surprising facts",
            "World Cup 2026 player controversy drama off pitch",
            "World Cup 2026 fan culture celebrations host cities",
            "FIFA World Cup 2026 records history first time",
            "World Cup 2026 underdog stories surprising results",
            "FIFA 2026 celebrity fans music entertainment",
        ]
        queries = random.sample(all_queries, 3)

        raw_results = []
        for query in queries:
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=4,
                include_answer=False,
                days=2
            )
            raw_results.extend(response.get("results", []))

        raw_text = ""
        url_map = {}
        for i, r in enumerate(raw_results):
            title = r.get("title", "").strip()
            content = r.get("content", "").strip()[:300]
            url = r.get("url", "")
            source = url.split("/")[2].replace("www.", "") if url else ""
            raw_text += f"[{i}] {title}: {content} (source: {source}, url: {url})\n\n"
            url_map[i] = {"url": url, "source": source}

        import anthropic
        import os
        llm_client = anthropic.Anthropic(
            api_key=st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        )

        prompt = f"""You are a football buzz editor for a daily World Cup 2026 briefing.
Today's date is {today_str}. From the raw search results below, 
pick the {max_results} most interesting "did you know" style facts or stories.

STRONGLY PREFER:
- Specific facts about a venue, stadium, city, or weather for upcoming/recent matches
- A surprising stat, record, or moment tied to a specific team or player
- Recent reactions, controversies, or fan culture moments from actual matches played
- Anything with a specific number, name, date, or place that feels like trivia

STRONGLY AVOID:
- Match results, scores, or summaries of who won/lost/drew — this is covered elsewhere
- Anything starting with team names followed by a score or "defeated", "won", "drew"
- Generic statements about "48 teams", "104 matches", tournament format/history that apply to the whole event with no specific team, player, venue, or date attached
- Vague marketing-style statements about "biggest ever" or "record-breaking" with no specific detail
- Pre-tournament announcements about songs, ceremonies, or events that already happened days ago
- Generic news, junk social media captions, non-English content, boring previews

For each picked story, return ONLY this JSON format, nothing else:
[
  {{"index": <original index number>, "icon": "<single emoji>", "headline": "<punchy 8 word headline>", "summary": "<1-2 sentences, specific and surprising, no filler>"}},
  ...
]

Raw results:
{raw_text}

Return valid JSON array only. No preamble, no markdown backticks."""

        message = llm_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=min(150 * max_results, 1500),
            messages=[{"role": "user", "content": prompt}]
        )

        import json
        response_text = message.content[0].text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        picked = json.loads(response_text)

        stories = []
        for item in picked:
            idx = item.get("index", 0)
            url_info = url_map.get(idx, {"url": "", "source": ""})
            stories.append({
                "icon": item.get("icon", "🔥"),
                "title": item.get("headline", ""),
                "content": item.get("summary", ""),
                "url": url_info["url"],
                "source": url_info["source"]
            })

        return stories

    except Exception as e:
        return [{"title": "Buzz unavailable", "content": str(e),
                 "url": "", "source": "", "icon": "⚠️"}]

def get_buzz_stories_uncached(max_results: int = 5) -> list:
    """Same as get_buzz_stories but bypasses cache for Load more."""
    try:
        client = get_tavily_client()
        import random
        all_queries = [
            "FIFA World Cup 2026 fun facts unusual stories viral",
            "FIFA World Cup 2026 trending social media players teams",
            "World Cup 2026 venue altitude weather surprising facts",
            "World Cup 2026 player controversy drama off pitch",
            "World Cup 2026 fan culture celebrations host cities",
            "FIFA World Cup 2026 records history first time",
            "World Cup 2026 underdog stories surprising results",
            "FIFA 2026 celebrity fans music entertainment",
        ]
        # Pick 3 random queries different from the cached ones
        queries = random.sample(all_queries, 3)

        raw_results = []
        for query in queries:
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=4,
                include_answer=False,
                days=2
            )
            raw_results.extend(response.get("results", []))

        raw_text = ""
        url_map = {}
        for i, r in enumerate(raw_results):
            title = r.get("title", "").strip()
            content = r.get("content", "").strip()[:300]
            url = r.get("url", "")
            source = url.split("/")[2].replace("www.", "") if url else ""
            raw_text += f"[{i}] {title}: {content} (source: {source}, url: {url})\n\n"
            url_map[i] = {"url": url, "source": source}

        import anthropic
        import os
        llm_client = anthropic.Anthropic(
            api_key=st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        )

        prompt = f"""You are a football buzz editor. From the raw search results below, 
        pick the {max_results} most interesting, surprising, or fun stories about the 2026 World Cup.
        
STRONGLY PREFER:
- Specific facts about a venue, stadium, city, or weather tied to a recent or upcoming match
- A surprising stat, record, or moment tied to a specific team or player, dated recently
- Fan culture, atmosphere, or off-pitch moments from the last day or two
- Anything with a specific number, name, place, or date that feels like genuine trivia

 STRONGLY AVOID:
- Match results, scores, or summaries of who won/lost/drew — this is covered elsewhere
- Anything starting with team names followed by a score or "defeated", "won", "drew"
- Generic statements about "48 teams", "104 matches", tournament format/history that apply to the whole event with no specific team, player, venue, or date attached
- Vague marketing-style statements about "biggest ever" or "record-breaking" with no specific detail
- Pre-tournament announcements about songs, ceremonies, or events that already happened days ago
- Generic news, junk social media captions, non-English content, boring previews

KEEP: fun facts, viral moments, unusual stories, quirky player/team news, venue facts, cultural moments, weather/altitude trivia, fan culture, controversies unrelated to match scores — all tied to something specific and recent.
        For each picked story, return ONLY this JSON format, nothing else:
        [
          {{"index": <original index number>, "icon": "<single emoji>", "headline": "<punchy 8 word headline>", "summary": "<1-2 sentences, insightful and specific, no filler>"}},
          ...
        ]

        Raw results:
        {raw_text}

        Return valid JSON array only. No preamble, no markdown backticks."""

        message = llm_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=min(150 * max_results, 1500),
            messages=[{"role": "user", "content": prompt}]
        )

        import json
        response_text = message.content[0].text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        picked = json.loads(response_text)

        stories = []
        for item in picked:
            idx = item.get("index", 0)
            url_info = url_map.get(idx, {"url": "", "source": ""})
            stories.append({
                "icon": item.get("icon", "🔥"),
                "title": item.get("headline", ""),
                "content": item.get("summary", ""),
                "url": url_info["url"],
                "source": url_info["source"]
            })
        return stories

    except Exception as e:
        return [{"title": "Buzz unavailable", "content": str(e),
                 "url": "", "source": "", "icon": "⚠️"}]