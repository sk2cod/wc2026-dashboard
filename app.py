import streamlit as st
from data.api_client import get_standings, get_todays_and_tomorrows_matches, get_recent_results
from data.wildcard import calculate_wildcard
from data.odds_client import get_wc_odds, parse_implied_probability

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

# ── Section 1: Headline numbers ───────────────────────────────
finished = recent_results
goals = sum(
    (m["score"]["fullTime"]["home"] or 0) + (m["score"]["fullTime"]["away"] or 0)
    for m in finished
)
upsets = 0
for m in finished:
    odds_match = next(
        (o for o in odds
         if m["homeTeam"]["name"] in o["home"] or
         m["awayTeam"]["name"] in o["away"]), None
    )
    if odds_match:
        score = m["score"]["fullTime"]
        if score["home"] > score["away"] and odds_match["home_prob"] < 40:
            upsets += 1
        elif score["away"] > score["home"] and odds_match["away_prob"] < 40:
            upsets += 1

m1, m2, m3, m4 = st.columns(4)
m1.metric("Matches Played", len(finished))
m2.metric("Goals Scored", goals)
m3.metric("Avg Goals/Match", f"{goals / len(finished):.1f}" if finished else "—")
m4.metric("Matches Today & Tomorrow", len(todays_matches))

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
            briefing = get_pundit_briefing(selected_team, context)
            st.markdown(briefing)