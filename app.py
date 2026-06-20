import streamlit as st
from data.api_client import get_standings, get_todays_and_tomorrows_matches, get_recent_results, get_top_scorers, get_fixtures
from data.wildcard import calculate_wildcard
from data.odds_client import get_wc_odds, parse_implied_probability
from components.haiku_pundit import get_match_narrative
from components.haiku_pundit import get_match_narrative, get_daily_storylines
from data.flags import get_flag, get_flag_img
from datetime import datetime, timezone, timedelta

aest = timezone(timedelta(hours=10))

def utc_to_aest(utc_str):
    utc_dt = datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%SZ")
    utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    aest_dt = utc_dt.astimezone(aest)
    return aest_dt.strftime("%d %b %I:%M %p AEST"), aest_dt.strftime("%Y-%m-%d"), aest_dt.strftime("%A %d %B")


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

@st.cache_data(ttl=600)
def load_all_fixtures():
    return get_fixtures()

@st.cache_data(ttl=1800)
def load_odds():
    raw = get_wc_odds()
    return parse_implied_probability(raw)


@st.cache_data(ttl=600)
def load_scorers():
    return get_top_scorers(limit=10)

# ── Load data ─────────────────────────────────────────────────
standings = load_standings()
all_groups, wildcard_df = calculate_wildcard(standings)
todays_matches = load_fixtures()
all_fixtures = load_all_fixtures()
recent_results = load_results()
odds = load_odds()
top_scorers = load_scorers()

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
import re
finished = recent_results

st.subheader("Recent Results")

date_filter = st.radio(
    "Show results from",
    ["Today", "Yesterday", "Last 3 days", "All"],
    horizontal=True,
    index=0
)

from datetime import datetime, timezone, timedelta as td
aest = timezone(td(hours=10))
now_aest = datetime.now(aest)

def match_aest_date(match):
    utc_dt = datetime.strptime(match["utcDate"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(aest).date()

today_date = now_aest.date()
yesterday_date = today_date - td(days=1)
three_days_ago = today_date - td(days=3)

if date_filter == "Today":
    filtered = [m for m in finished if match_aest_date(m) == today_date]
elif date_filter == "Yesterday":
    filtered = [m for m in finished if match_aest_date(m) == yesterday_date]
elif date_filter == "Last 3 days":
    filtered = [m for m in finished if match_aest_date(m) >= three_days_ago]
else:
    filtered = finished

if filtered:
    for match in filtered:
        home = match["homeTeam"]["name"]
        away = match["awayTeam"]["name"]
        score = match["score"]["fullTime"]
        home_score = score["home"] or 0
        away_score = score["away"] or 0
        group = match.get("group", "").replace(
            "GROUP_", "Grp ").replace("_", " ").title()
        match_date = match_aest_date(match).strftime("%Y-%m-%d")
        match_id = match["id"]

        if home_score > away_score:
            result = f"🏆 {home} win"
        elif away_score > home_score:
            result = f"🏆 {away} win"
        else:
            result = "🤝 Draw"

        col_info, col_btn = st.columns([6, 2])
        with col_info:
            st.markdown(
                f"<div style='padding:6px 0;'>"
                f"<div style='font-size:14px;font-weight:600;color:var(--color-text-primary);'>{home} {home_score}–{away_score} {away}</div>"
                f"<div style='font-size:12px;color:var(--color-text-tertiary);margin-top:2px;'>{group} · {match_date} · {result}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        with col_btn:
            analysis_clicked = st.button("📖 Analysis", key=f"analysis_{match_id}")

        if analysis_clicked:
            with st.spinner("Generating analysis..."):
                narrative_raw = get_match_narrative(
                    match_id, home, away, home_score, away_score
                )
                bullets = re.split(r'\n[•\-\*]|\n\n', narrative_raw.strip())
                bullets = [b.strip().lstrip("•-* ") for b in bullets if b.strip()]
                for bullet in bullets:
                    st.markdown(f"• {bullet}")

        st.markdown("<div style='border-bottom:0.5px solid #eee;margin:4px 0;'></div>", unsafe_allow_html=True)
else:
    st.info(f"No completed matches for: {date_filter}")

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
        group_key = "GROUP_" + raw.split()[-1]
        group_name = raw.replace("GROUP_", "Group ").replace("_", " ").title()
        matches_played = int(group_df["played"].sum() // 2)
        st.markdown(f"**{group_name}** (MP-{matches_played})")
        for _, row in group_df.iterrows():
            badge = status_badge(row["position"], row["points"], row["played"])
            st.markdown(
                f"{badge} {row['team']} {get_flag_img(row['team'])} — "
                f"**{row['points']}pts** "
                f"(GD: {row['gd']:+d}, GF: {int(row['gf'])}, MP-{int(row['played'])})",
                unsafe_allow_html=True
            )

        played = sorted(
            (m for m in all_fixtures if m.get("group") == group_key and m.get("status") == "FINISHED"),
            key=lambda m: m.get("utcDate", "")
        )
        if played:
            lines = ""
            for m in played:
                home = m["homeTeam"]["name"]
                away = m["awayTeam"]["name"]
                score = m["score"]["fullTime"]
                home_goals, away_goals = score["home"], score["away"]
                if home_goals > away_goals:
                    result = f"{home} win {home_goals}-{away_goals} 🏆"
                elif away_goals > home_goals:
                    result = f"{away} win {away_goals}-{home_goals} 🏆"
                else:
                    result = f"Draw {home_goals}-{away_goals} 🤝"
                lines += (
                    f"<div style='font-size:12px;color:var(--color-text-secondary);'>"
                    f"{home} vs {away} - {result}</div>"
                )
            st.markdown(
                "<div style='font-size:14px;font-weight:600;color:var(--color-text-tertiary);"
                "margin-top:6px;'>Results</div>" + lines,
                unsafe_allow_html=True
            )

        upcoming = sorted(
            (m for m in all_fixtures if m.get("group") == group_key and m.get("status") != "FINISHED"),
            key=lambda m: m.get("utcDate", "")
        )
        if upcoming:
            lines = ""
            for m in upcoming:
                home = m["homeTeam"]["name"]
                away = m["awayTeam"]["name"]
                kickoff, _, _ = utc_to_aest(m["utcDate"])
                lines += (
                    f"<div style='font-size:12px;color:var(--color-text-secondary);'>"
                    f"{home} vs {away} &nbsp;·&nbsp; {kickoff}</div>"
                )
            st.markdown(
                "<div style='font-size:14px;font-weight:600;color:var(--color-text-tertiary);"
                "margin-top:6px;'>Upcoming</div>" + lines,
                unsafe_allow_html=True
            )
        st.write("")

st.divider()

# ── Section 3: Wildcard ladder ────────────────────────────────
st.subheader("Wildcard Ladder — Best 8 Third-Place Teams")
st.caption("Top 8 of 12 third-place teams advance to Round of 32")

if not wildcard_df.empty:
    rows_html = ""
    for _, row in wildcard_df.iterrows():
        rank = int(row["wildcard_rank"])
        if rank == 9:
            rows_html += f"""
            <tr>
                <td colspan='5' style='padding:4px 8px;font-size:11px;
                color:var(--color-text-tertiary);border-top:1.5px dashed #888;
                text-align:center;'>✂️ cut-off — below this does not advance</td>
            </tr>"""

        status_color = "#1D9E75" if row["status"] == "IN" else "#E24B4A"
        status_text = row["status"]
        flag = get_flag_img(row["team"])

        rows_html += f"""
        <tr>
            <td style='padding:6px 8px;font-size:13px;font-weight:600;
            color:var(--color-text-secondary);'>#{rank}</td>
            <td style='padding:6px 8px;font-size:13px;
            color:var(--color-text-primary);'>{flag}{row['team']}</td>
            <td style='padding:6px 8px;font-size:13px;
            color:var(--color-text-secondary);text-align:center;'>{int(row['points'])}pts</td>
            <td style='padding:6px 8px;font-size:13px;
            color:var(--color-text-secondary);text-align:center;'>GD {row['gd']:+d}</td>
            <td style='padding:6px 8px;font-size:13px;font-weight:600;
            color:{status_color};text-align:center;'>{status_text}</td>
        </tr>"""

    st.markdown(
        f"""<table style='width:100%;border-collapse:collapse;'>
        <thead>
            <tr style='border-bottom:1px solid var(--color-border-tertiary);'>
                <th style='padding:6px 8px;font-size:11px;color:var(--color-text-tertiary);
                text-align:left;font-weight:500;'>#</th>
                <th style='padding:6px 8px;font-size:11px;color:var(--color-text-tertiary);
                text-align:left;font-weight:500;'>Team</th>
                <th style='padding:6px 8px;font-size:11px;color:var(--color-text-tertiary);
                text-align:center;font-weight:500;'>Pts</th>
                <th style='padding:6px 8px;font-size:11px;color:var(--color-text-tertiary);
                text-align:center;font-weight:500;'>GD</th>
                <th style='padding:6px 8px;font-size:11px;color:var(--color-text-tertiary);
                text-align:center;font-weight:500;'>Status</th>
            </tr>
        </thead>
        <tbody>{rows_html}</tbody>
        </table>""",
        unsafe_allow_html=True
    )

st.divider()
# ── Section 3.5: Top Scorers ──────────────────────────────────
st.subheader("Top Scorers")
st.caption("Golden Boot leaderboard — most goals in the tournament")

if top_scorers:
    for i, s in enumerate(top_scorers):
        player = s.get("player", {})
        team = s.get("team", {})
        goals = s.get("goals", 0)
        assists = s.get("assists", 0)
        penalties = s.get("penalties", 0)
        name = player.get("name", "")
        team_name = team.get("name", "")
        nationality = player.get("nationality", "")

        st.markdown(
            f"<div style='padding:6px 0;border-bottom:0.5px solid #eee;display:flex;align-items:center;gap:12px;'>"
            f"<span style='font-size:13px;font-weight:600;color:#888;min-width:24px;'>#{i+1}</span>"
            f"<span style='font-size:14px;font-weight:600;color:var(--color-text-primary);flex:1;'>{name}</span>"
            f"<span style='font-size:13px;color:var(--color-text-secondary);min-width:160px;'>{get_flag(team_name)} {team_name}</span>"
            f"<span style='font-size:13px;color:var(--color-text-secondary);min-width:80px;'>⚽ {goals} goal{'s' if goals != 1 else ''}</span>"
            f"<span style='font-size:12px;color:#888;min-width:80px;'>{'🅿 ' + str(penalties) + ' pen' if penalties else ''}</span>"
            f"</div>",
            unsafe_allow_html=True
        )
else:
    st.info("No goals scored yet.")

st.divider()

# ── Section 4: Today's matches + hype bar ────────────────────

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
st.caption("Select a team or group for an AI-powered briefing")

pundit_mode = st.radio("Analyse by", ["Team", "Group"], horizontal=True)

selected_team = "— select —"
selected_group = "— select —"

if pundit_mode == "Team":
    all_teams = sorted(set(
        row["team"]
        for group_df in all_groups
        for _, row in group_df.iterrows()
    ))
    selected_team = st.selectbox("Choose a team", ["— select —"] + all_teams)
else:
    all_group_names = [g["group"].iloc[0] for g in all_groups if not g.empty]
    selected_group = st.selectbox("Choose a group", ["— select —"] + sorted(all_group_names))

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
if pundit_mode == "Group" and selected_group and selected_group != "— select —":
    if st.button(f"Brief me on {selected_group} ↗"):
        from components.haiku_pundit import get_group_briefing
        from data.api_client import get_group_remaining_fixtures
        with st.spinner("Consulting the Haiku Pundit..."):
            group_df = next(
                (g for g in all_groups if g["group"].iloc[0] == selected_group), None
            )
            teams_data = ""
            if group_df is not None:
                for _, row in group_df.iterrows():
                    teams_data += (
                        f"- {row['team']}: Position {int(row['position'])}, "
                        f"{int(row['points'])}pts, Played {int(row['played'])}, "
                        f"GD {row['gd']:+d}, GF {int(row['gf'])}\n"
                    )

            remaining = get_group_remaining_fixtures(selected_group)
            remaining_text = "\n".join(f"- {r}" for r in remaining)

            briefing = get_group_briefing(selected_group, teams_data, remaining_text)
            st.markdown(briefing)


# ── Section 6: Today's Storylines ────────────────────────────
st.divider()
st.subheader("📋 Today's Storylines")
st.caption("AI-generated briefing based on today's fixtures and live standings")

from datetime import datetime, timezone, timedelta
aest = timezone(timedelta(hours=10))
today_str = datetime.now(aest).strftime("%A %d %B %Y")

if todays_matches:
    # Build fixtures context
    fixtures_data = ""
    for m in todays_matches:
        if m["status"] == "FINISHED":
            continue
        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]
        group = m.get("group", "").replace("GROUP_", "Group ").replace("_", " ").title()
        kickoff, _, _ = utc_to_aest(m["utcDate"])
        fixtures_data += f"- {group}: {home} vs {away} at {kickoff}\n"

    # Build standings context for relevant groups
    relevant_groups = set(
        m.get("group", "").replace("GROUP_", "Group ").replace("_", " ").title()
        for m in todays_matches
        if m["status"] != "FINISHED"
    )

    standings_data = ""
    for group_df in all_groups:
        group_name = group_df["group"].iloc[0]
        if group_name not in relevant_groups:
            continue
        standings_data += f"\n{group_name}:\n"
        for _, row in group_df.iterrows():
            standings_data += (
                f"  {int(row['position'])}. {row['team']} — "
                f"{int(row['points'])}pts, GD {row['gd']:+d}, "
                f"GF {int(row['gf'])}, Played {int(row['played'])}\n"
            )

    if fixtures_data:
        with st.spinner("Generating today's storylines..."):
            storylines = get_daily_storylines(fixtures_data, standings_data, today_str)
        st.markdown(storylines)
    else:
        st.info("All matches today are finished — check back tomorrow for new storylines.")
else:
    st.info("No matches scheduled today.")
