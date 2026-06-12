import os
from dotenv import load_dotenv
import requests

load_dotenv()

# ── Test 1: football-data.org ─────────────────────────────────
print("Testing football-data.org...")
try:
    r = requests.get(
        "https://api.football-data.org/v4/competitions/WC/standings",
        headers={"X-Auth-Token": os.getenv("FOOTBALLDATA_API_KEY")}
    )
    data = r.json()
    if r.status_code == 200:
        groups = data.get("standings", [])
        print(f"  OK: World Cup standings returned {len(groups)} groups")
    else:
        print(f"  ERROR {r.status_code}: {data.get('message')}")
except Exception as e:
    print(f"  FAILED: {e}")

# ── Test 2: The Odds API ──────────────────────────────────────
print("\nTesting The Odds API...")
try:
    r = requests.get(
        "https://api.the-odds-api.com/v4/sports",
        params={"apiKey": os.getenv("ODDS_API_KEY")}
    )
    data = r.json()
    if r.status_code == 200:
        remaining = r.headers.get("x-requests-remaining")
        soccer = [s for s in data if "soccer" in s.get("key", "")]
        print(f"  OK: {len(soccer)} soccer competitions available")
        print(f"  Requests remaining this month: {remaining}")
    else:
        print(f"  ERROR {r.status_code}: {data.get('message')}")
except Exception as e:
    print(f"  FAILED: {e}")

# ── Test 3: Anthropic ─────────────────────────────────────────
print("\nTesting Anthropic...")
try:
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=64,
        messages=[{"role": "user", "content": "Reply with exactly: Haiku online."}]
    )
    print(f"  OK: {message.content[0].text}")
except Exception as e:
    print(f"  FAILED: {e}")

print("\nPhase 0 complete. Ready for Phase 1.")