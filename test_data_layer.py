from data.api_client import get_standings, get_todays_and_tomorrows_matches, get_recent_results
from data.wildcard import calculate_wildcard
from data.odds_client import get_wc_odds, parse_implied_probability

print("=" * 50)
print("Testing data layer")
print("=" * 50)

# Test 1: Standings
print("\n1. Standings...")
standings = get_standings()
print(f"   Got {len(standings)} groups")

# Test 2: Wildcard
print("\n2. Wildcard calculation...")
all_groups, wildcard_df = calculate_wildcard(standings)
print(f"   {len(all_groups)} group tables built")
if not wildcard_df.empty:
    print(f"   Top 3rd place teams:")
    for _, row in wildcard_df.head(3).iterrows():
        print(f"   {int(row['wildcard_rank'])}. {row['team']} ({row['points']}pts, GD:{row['gd']}) — {row['status']}")

# Test 3: Today's matches
print("\n3. Today's matches...")
todays = get_todays_and_tomorrows_matches()
if todays:
    for m in todays:
        home = m['homeTeam']['name']
        away = m['awayTeam']['name']
        time = m['utcDate'][11:16]
        print(f"   {home} vs {away} at {time} UTC")
else:
    print("   No matches today (or all finished)")

# Test 4: Recent results
print("\n4. Recent results...")
results = get_recent_results()
for m in results[-3:]:
    home = m['homeTeam']['name']
    away = m['awayTeam']['name']
    score = m['score']['fullTime']
    print(f"   {home} {score['home']} - {score['away']} {away}")

# Test 5: Odds
print("\n5. Odds...")
odds_raw = get_wc_odds()
if odds_raw:
    probs = parse_implied_probability(odds_raw)
    for p in probs[:3]:
        print(f"   {p['home']} {p['home_prob']}% | Draw {p['draw_prob']}% | {p['away']} {p['away_prob']}%")
else:
    print("   No upcoming odds available right now")

print("\nData layer ready.")

print("\n6. Top scorers...")
from data.api_client import get_top_scorers
scorers = get_top_scorers()
for s in scorers[:5]:
    player = s.get("player", {})
    team = s.get("team", {})
    print(f"   {player.get('name')} ({team.get('name')}) — {s.get('goals')} goals")