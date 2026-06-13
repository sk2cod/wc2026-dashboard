import streamlit as st
from data.api_client import get_standings, get_todays_and_tomorrows_matches, get_recent_results
from data.wildcard import calculate_wildcard
from data.odds_client import get_wc_odds, parse_implied_probability
from components.haiku_pundit import get_match_narrative
from data.buzz_client import get_buzz_stories

st.set_page_config(
    page_title="WC 2026 Dashboard",
    page_icon="⚽",
    layout="wide"
)

# ── Cache data ────────────────────────────────────────────────
@st.cache_data(ttl=600)
def load_standings():
    return get_standings()

@st.cache_data(ttl=600)
def load_fixtures():
    return get_todays_and_tomorrows_matches()

@st.cache_data(ttl=600)
def load_results():
    return get_recent_results()

@st.cache_data(ttl=1800)
def load_odds():
    raw = get_wc_odds()
    return parse_implied_probability(raw)

@st.cache_data(ttl=3600*12)
def load_buzz(n=5):
    return get_buzz_stories(max_results=n)

# ── Load data ─────────────────────────────────────────────────
standings = load_standings()
all_groups, wildcard_df = calculate_wildcard(standings)
todays_matches = load_fixtures()
recent_results = load_results()
odds = load_odds()

# ── Header ────────────────────────────────────────────────────
col_title, col_refresh = st.columns([6, 1])
with col_title:
    st.title("⚽ World Cup 2026")
    st.caption("Morning briefing — live group stage data")
with col_refresh:
    st.write("")
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()

# ── Section 1: Completed match highlights ────────────────────


finished = recent_results

st.subheader("Recent Results")

if finished:
    # Show last 8 results max
    for match in finished[-8:]:
        home = match["homeTeam"]["name"]
        away = match["awayTeam"]["name"]
        score = match["score"]["fullTime"]
        home_score = score["home"] or 0
        away_score = score["away"] or 0
        group = match.get("group", "").replace(
            "GROUP_", "Grp ").replace("_", " ").title()
        match_date = match["utcDate"][:10]

        # Determine result indicator
        if home_score > away_score:
            result = f"🏆 {home} win"
        elif away_score > home_score:
            result = f"🏆 {away} win"
        else:
            result = "🤝 Draw"

        # Get one-line narrative from Haiku
        narrative = get_match_narrative(
            match["id"], home, away, home_score, away_score
        )

        st.markdown(
            f"<div style='padding:8px 0;border-bottom:0.5px solid #eee;'>"
            f"<div style='display:flex;align-items:flex-start;gap:16px;'>"
            f"<div style='min-width:280px;'>"
            f"<div style='font-size:14px;font-weight:600;'>{home} {home_score}–{away_score} {away}</div>"
            f"<div style='font-size:14px;color:#888;margin-top:2px;'>{group} · {match_date}</div>"
            f"</div>"
            f"<span style='font-size:13px;color:#555;min-width:140px;'>{result}</span>"
            f"<span style='font-size:13px;color:#444;font-style:italic;flex:1;'>{narrative}</span>"
            f"</div></div>",
            unsafe_allow_html=True
        )
else:
    st.info("No completed matches yet.")

st.divider()
from datetime import datetime, timezone, timedelta
aest = timezone(timedelta(hours=10))
last_updated = datetime.now(aest).strftime("%d %b %Y %I:%M %p AEST")
st.caption(f"Last updated: {last_updated}")

st.divider()

# ── Section 1.5: Bracket ──────────────────────────────────────
st.subheader("Tournament Bracket")
st.caption("Live group standings feeding into the knockout path")
from components.bracket import render_bracket
render_bracket(all_groups, wildcard_df)

st.divider()

# ── Section 2: Groups + Wildcard ──────────────────────────────
st.subheader("Group Standings")

def status_badge(pos, pts, played):
    if played == 0:
        return "⬜"
    if pos <= 2:
        return "🟢"
    elif pos == 3:
        return "🟡"
    return "🔴"

cols = st.columns(4)
for i, group_df in enumerate(all_groups):
    col = cols[i % 4]
    with col:
        raw = group_df["group"].iloc[0]
        group_name = raw.replace("GROUP_", "Group ").replace("_", " ").title()
        st.markdown(f"**{group_name}**")
        for _, row in group_df.iterrows():
            badge = status_badge(row["position"], row["points"], row["played"])
            st.markdown(
                f"{badge} {row['team']} — "
                f"**{row['points']}pts** "
                f"(GD: {row['gd']:+d})",
                unsafe_allow_html=True
            )
        st.write("")

st.divider()

# ── Section 3: Wildcard ladder ────────────────────────────────
st.subheader("Wildcard Ladder — Best 8 Third-Place Teams")
st.caption("Top 8 of 12 third-place teams advance to Round of 32")

if not wildcard_df.empty:
    for _, row in wildcard_df.iterrows():
        rank = int(row["wildcard_rank"])
        is_cutoff = rank == 9
        if is_cutoff:
            st.markdown("---  ✂️ *cut-off line — below this does not advance* ---")

        status_color = "🟢" if row["status"] == "IN" else "🔴"
        col_r, col_t, col_p, col_gd, col_s = st.columns([1, 4, 1, 1, 2])
        col_r.write(f"**{rank}**")
        col_t.write(f"{row['team']}")
        col_p.write(f"{int(row['points'])}pts")
        col_gd.write(f"GD {row['gd']:+d}")
        col_s.write(f"{status_color} {row['status']}")

st.divider()

# ── Section 4: Today's matches + hype bar ────────────────────
from datetime import datetime, timezone, timedelta

aest = timezone(timedelta(hours=10))

def utc_to_aest(utc_str):
    utc_dt = datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%SZ")
    utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    aest_dt = utc_dt.astimezone(aest)
    return aest_dt.strftime("%d %b %I:%M %p AEST"), aest_dt.strftime("%Y-%m-%d"), aest_dt.strftime("%A %d %B")

st.subheader("Today & Tomorrow's Matches")

if todays_matches:
    # Group matches by date
    from collections import defaultdict
    grouped = defaultdict(list)
    date_labels = {}
    for match in todays_matches:
        _, date_key, date_label = utc_to_aest(match["utcDate"])
        grouped[date_key].append(match)
        date_labels[date_key] = date_label

    sorted_dates = sorted(grouped.keys())[:2]

    if len(sorted_dates) == 1:
        # Only one day — single column
        cols = [st.container()]
        date_cols = {sorted_dates[0]: cols[0]}
    else:
        # Two days — two columns
        col1, col2 = st.columns(2)
        date_cols = {
            sorted_dates[0]: col1,
            sorted_dates[1]: col2
        }

    for date_key in sorted_dates:
        matches = grouped[date_key]
        container = date_cols[date_key]
        with container:
            st.markdown(f"**{date_labels[date_key]}**")
            for match in matches:
                home = match["homeTeam"]["name"]
                away = match["awayTeam"]["name"]
                kickoff, _, _ = utc_to_aest(match["utcDate"])
                status = match["status"]
                group = match.get("group", "").replace(
                    "GROUP_", "Grp ").replace("_", " ").title()

                odds_match = next(
                    (o for o in odds
                     if home in o["home"] or away in o["away"]), None
                )

                with st.container():
                    # Match title line
                    if status == "FINISHED":
                        score = match["score"]["fullTime"]
                        st.markdown(
                            f"**{home}** {score['home']}–"
                            f"{score['away']} **{away}** ✅"
                        )
                    else:
                        st.markdown(f"**{home}** vs **{away}**")

                        # Meta line — group, time, status
                        st.markdown(
                            f"<div style='font-size:13px;color:#444;margin-bottom:2px;'>"
                            f"{group} &nbsp;·&nbsp; {kickoff} &nbsp;·&nbsp; {status.replace('_', ' ').title()}"
                            f"</div>",
                            unsafe_allow_html=True
                        )

                    # Odds + hype bar line
                    if odds_match and status != "FINISHED":
                        hp = odds_match["home_prob"]
                        dp = odds_match["draw_prob"]
                        ap = odds_match["away_prob"]
                        favorite_prob = max(hp, ap)

                        if favorite_prob > 70:
                            bar_color = "#E24B4A"
                            label = "🔴 Hot favorite"
                        elif favorite_prob > 55:
                            bar_color = "#EF9F27"
                            label = "🟠 Likely winner"
                        else:
                            bar_color = "#1D9E75"
                            label = "🟢 Coin flip"

                        st.markdown(
                            f"<div style='margin:2px 0 8px;'>"
                            f"<div style='font-size:13px;color:#444;margin-bottom:2px;'>"
                            f"{home} {hp}% | Draw {dp}% | {away} {ap}% &nbsp;·&nbsp; {label}"
                            f"</div>"
                            f"<div style='background:#eee;border-radius:4px;height:6px;width:100%;'>"
                            f"<div style='background:{bar_color};width:{favorite_prob:.0f}%;height:6px;border-radius:4px;'>"
                            f"</div></div></div>",
                            unsafe_allow_html=True
                        )
                    # Betting insight button
                    if odds_match and status != "FINISHED":
                        if st.button(f"💡 Match insight", key=f"insight_{match['id']}"):
                            from components.haiku_pundit import get_betting_insight
                            from data.api_client import get_team_match_history
                            with st.spinner("Analysing..."):
                                home_history = ""
                                away_history = ""
                                for m in get_team_match_history(home):
                                    home_history += f"- vs {m['opponent']}: {m['team_goals']}-{m['opp_goals']} ({m['outcome']})\n"
                                for m in get_team_match_history(away):
                                    away_history += f"- vs {m['opponent']}: {m['team_goals']}-{m['opp_goals']} ({m['outcome']})\n"
                                insight = get_betting_insight(
                                    home, away,
                                    odds_match["home_prob"],
                                    odds_match["draw_prob"],
                                    odds_match["away_prob"],
                                    home_history,
                                    away_history
                                )
                            st.markdown(insight)
                    st.write("")
else:
    st.info("No matches scheduled today or tomorrow.")

st.divider()

# ── Section 5: Haiku pundit ───────────────────────────────────
st.subheader("Haiku Pundit")
st.caption("Select a team for an AI-powered 3-bullet briefing")

all_teams = sorted(set(
    row["team"]
    for group_df in all_groups
    for _, row in group_df.iterrows()
))

selected_team = st.selectbox("Choose a team", ["— select —"] + all_teams)

if selected_team and selected_team != "— select —":
    team_group = next(
        (group_df for group_df in all_groups
         if selected_team in group_df["team"].values), None
    )
    team_row = None
    if team_group is not None:
        team_row = team_group[team_group["team"] == selected_team].iloc[0]

    if st.button(f"Brief me on {selected_team} ↗"):
        from components.haiku_pundit import get_pundit_briefing
        from data.api_client import get_team_match_history

        with st.spinner("Consulting the Haiku Pundit..."):
            context = ""
            if team_row is not None:
                context = (
                    f"Team: {selected_team}\n"
                    f"Group: {team_row['group']}\n"
                    f"Position: {int(team_row['position'])}\n"
                    f"Points: {int(team_row['points'])}\n"
                    f"Played: {int(team_row['played'])}\n"
                    f"Goal difference: {team_row['gd']:+d}\n"
                    f"Goals for: {int(team_row['gf'])}\n"
                    f"Goals against: {int(team_row['ga'])}\n"
                )

            history = get_team_match_history(selected_team)
            match_history = ""
            for m in history:
                match_history += (
                    f"- {m['venue']} vs {m['opponent']}: "
                    f"{m['team_goals']}-{m['opp_goals']} ({m['outcome']})\n"
                )

            briefing = get_pundit_briefing(selected_team, context, match_history)
            st.markdown(briefing)

# ── Section 6: Buzz ───────────────────────────────────────────
st.divider()
st.subheader("🔥 Buzz")
st.caption("Trending stories, fun facts and off-the-pitch drama")

if "buzz_count" not in st.session_state:
    st.session_state.buzz_count = 5
if "buzz_stories" not in st.session_state:
    st.session_state.buzz_stories = None


if st.session_state.buzz_stories is None:
    st.session_state.buzz_stories = get_buzz_stories(5)
buzz_stories = st.session_state.buzz_stories

for i, story in enumerate(buzz_stories):


    read_more = f"· <a href='{story['url']}' target='_blank'>Read more</a>" if story['url'] else ""
    with st.container():
        st.markdown(
            f"<div style='padding:8px 0;border-bottom:0.5px solid #eee;'>"
            f"<div style='display:flex;align-items:flex-start;gap:10px;'>"
            f"<span style='font-size:20px;'>{story['icon']}</span>"
            f"<div style='flex:1;'>"
            f"<div style='font-size:14px;font-weight:600;color:#222;'>{story['title']}</div>"
            f"<div style='font-size:13px;color:#444;margin-top:2px;'>{story['content']}</div>"
            f"<div style='font-size:11px;color:#888;margin-top:4px;'>"
            f"via {story['source']} "
            f"{read_more}"
            f"</div>"
            f"</div>"
            f"</div></div>",
            unsafe_allow_html=True
        )



if st.button("Load 5 more ↓"):
    with st.spinner("Fetching more stories..."):
        existing_urls = {s["url"] for s in st.session_state.buzz_stories}
        from data.buzz_client import get_buzz_stories_uncached
        new_stories = get_buzz_stories_uncached(5)
        unique_new = [s for s in new_stories if s["url"] not in existing_urls]
        if unique_new:
            st.session_state.buzz_stories = st.session_state.buzz_stories + unique_new
        else:
            st.warning("No new stories found — check back later.")
    st.rerun()