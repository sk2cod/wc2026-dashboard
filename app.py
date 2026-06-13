import streamlit as st
from data.api_client import get_standings, get_todays_and_tomorrows_matches, get_recent_results, get_top_scorers
from data.wildcard import calculate_wildcard
from data.odds_client import get_wc_odds, parse_implied_probability
from components.haiku_pundit import get_match_narrative
from data.buzz_client import get_buzz_stories
from data.flags import get_flag, get_flag_img


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

@st.cache_data(ttl=600)
def load_scorers():
    return get_top_scorers(limit=10)

# ── Load data ─────────────────────────────────────────────────
standings = load_standings()
all_groups, wildcard_df = calculate_wildcard(standings)
todays_matches = load_fixtures()
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

if finished:
    for match in finished[-8:]:
        home = match["homeTeam"]["name"]
        away = match["awayTeam"]["name"]
        score = match["score"]["fullTime"]
        home_score = score["home"] or 0
        away_score = score["away"] or 0
        group = match.get("group", "").replace(
            "GROUP_", "Grp ").replace("_", " ").title()
        match_date = match["utcDate"][:10]
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
    st.info("No completed matches yet.")

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
                f"{badge} {row['team']} {get_flag_img(row['team'])} — "
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
            f"<div style='font-size:14px;font-weight:600;color:var(--color-text-primary);'>{story['title']}</div>"
            f"<div style='font-size:13px;color:var(--color-text-secondary);margin-top:2px;'>{story['content']}</div>"
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