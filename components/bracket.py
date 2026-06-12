import streamlit as st
import streamlit.components.v1 as components


def render_bracket(all_groups, wildcard_df):
    """Renders the 2026 World Cup wallchart bracket."""

    # Build team lookup by group
    group_data = {}
    for group_df in all_groups:
        if group_df.empty:
            continue
        group_name = group_df["group"].iloc[0]
        # Store under both formats to be safe
        short = group_name.replace("GROUP_", "").strip()
        group_name = group_name  # keep as-is e.g. "Group A"
        teams = []
        for _, row in group_df.iterrows():
            teams.append({
                "name": row["team"],
                "points": int(row["points"]),
                "gd": int(row["gd"]),
                "played": int(row["played"]),
                "position": int(row["position"]),
            })
        group_data[group_name] = teams  # e.g. "Group A"
        group_data[short] = teams  # e.g. "A"


    # Build wildcard lookup
    wildcard_teams = set()
    if not wildcard_df.empty:
        wildcard_teams = set(
            wildcard_df[wildcard_df["status"] == "IN"]["team"].tolist()
        )

    def team_box(team, pos):
        if not team:
            return f"""
            <div class="team-box empty">TBD</div>
            """
        pts = team["points"]
        played = team["played"]
        gd = team["gd"]

        if played == 0:
            status_class = "unplayed"
        elif pos <= 2:
            status_class = "advancing"
        elif team["name"] in wildcard_teams:
            status_class = "wildcard"
        else:
            status_class = "danger"

        gd_str = f"+{gd}" if gd > 0 else str(gd)
        return f"""
        <div class="team-box {status_class}" 
             title="{team['name']} — {pts}pts GD:{gd_str}">
            <span class="team-name">{team['name']}</span>
            <span class="team-pts">{pts}p</span>
        </div>
        """

    def group_card(letter):
        teams = group_data.get(letter, [])
        while len(teams) < 4:
            teams.append(None)
        html = f"""
        <div class="group-card">
            <div class="group-title">{letter}</div>
            {"".join(team_box(t, t["position"] if t else 99) for t in teams)}
        </div>
        """
        return html

    def ko_box(label="TBD", sublabel=""):
        return f"""
        <div class="ko-box">
            <div class="ko-team">{label}</div>
            {f'<div class="ko-sub">{sublabel}</div>' if sublabel else ''}
        </div>
        """

    def stage_col(title, boxes, extra_class=""):
        content = "".join(boxes)
        return f"""
        <div class="stage-col {extra_class}">
            <div class="stage-title">{title}</div>
            {content}
        </div>
        """

    # Left side groups A-F, Right side G-L
    left_groups = ["Group A", "Group B", "Group C", "Group D", "Group E", "Group F"]
    right_groups = ["Group G", "Group H", "Group I", "Group J", "Group K", "Group L"]

    left_group_html = "".join(group_card(g) for g in left_groups)
    right_group_html = "".join(group_card(g) for g in right_groups)

    r32_left = "".join(ko_box("R32") for _ in range(8))
    r32_right = "".join(ko_box("R32") for _ in range(8))
    r16_left = "".join(ko_box("R16") for _ in range(4))
    r16_right = "".join(ko_box("R16") for _ in range(4))
    qf_left = "".join(ko_box("QF") for _ in range(2))
    qf_right = "".join(ko_box("QF") for _ in range(2))
    sf_left = ko_box("SF")
    sf_right = ko_box("SF")
    final = ko_box("🏆", "Final")

    html = f"""
    <style>
        .bracket-wrap {{
            display: flex;
            align-items: flex-start;
            gap: 6px;
            font-family: sans-serif;
            overflow-x: auto;
            padding: 12px 4px;
        }}
        .stage-col {{
            display: flex;
            flex-direction: column;
            gap: 6px;
            min-width: 110px;
        }}
        .stage-title {{
            font-size: 10px;
            font-weight: 600;
            color: #888;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 4px;
            white-space: nowrap;
        }}
        .group-card {{
            background: #f8f8f8;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 6px 8px;
            min-width: 110px;
        }}
        .group-title {{
            font-size: 10px;
            font-weight: 600;
            color: #555;
            margin-bottom: 4px;
            text-transform: uppercase;
        }}
        .team-box {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 3px 5px;
            border-radius: 4px;
            margin-bottom: 2px;
            font-size: 11px;
            border-left: 3px solid transparent;
        }}
        .team-box.advancing {{
            border-left-color: #1D9E75;
            background: #f0faf6;
        }}
        .team-box.wildcard {{
            border-left-color: #EF9F27;
            background: #fffbf0;
        }}
        .team-box.danger {{
            border-left-color: #E24B4A;
            background: #fff5f5;
        }}
        .team-box.unplayed {{
            border-left-color: #ddd;
            background: #fafafa;
        }}
        .team-box.empty {{
            border-left-color: #eee;
            background: #fafafa;
            color: #bbb;
            font-style: italic;
        }}
        .team-name {{
            color: #333;
            font-size: 10px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 75px;
        }}
        .team-pts {{
            font-size: 10px;
            font-weight: 600;
            color: #666;
            margin-left: 4px;
        }}
        .ko-box {{
            background: #f0f0f0;
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 6px 8px;
            text-align: center;
            margin-bottom: 2px;
        }}
        .ko-team {{
            font-size: 11px;
            color: #999;
            font-style: italic;
        }}
        .ko-sub {{
            font-size: 9px;
            color: #aaa;
            margin-top: 2px;
        }}
        .final-col {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-width: 90px;
            gap: 6px;
        }}
        .final-box {{
            background: #fff8e1;
            border: 2px solid #EF9F27;
            border-radius: 8px;
            padding: 10px 12px;
            text-align: center;
        }}
        .final-box .ko-team {{
            font-size: 14px;
            color: #BA7517;
            font-style: normal;
            font-weight: 600;
        }}
        .legend {{
            display: flex;
            gap: 16px;
            margin-top: 10px;
            font-size: 11px;
            color: #666;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .legend-dot {{
            width: 10px;
            height: 10px;
            border-radius: 2px;
        }}
    </style>

    <div class="bracket-wrap">
        {stage_col("Groups A–F", [left_group_html], "groups-col")}
        {stage_col("Round of 32", [r32_left])}
        {stage_col("Round of 16", [r16_left])}
        {stage_col("Quarter-finals", [qf_left])}
        {stage_col("Semi-finals", [sf_left])}

        <div class="final-col">
            <div class="stage-title">Final</div>
            <div class="final-box">
                <div class="ko-team">🏆</div>
                <div class="ko-sub">19 Jul</div>
            </div>
        </div>

        {stage_col("Semi-finals", [sf_right])}
        {stage_col("Quarter-finals", [qf_right])}
        {stage_col("Round of 16", [r16_right])}
        {stage_col("Round of 32", [r32_right])}
        {stage_col("Groups G–L", [right_group_html], "groups-col")}
    </div>

    <div class="legend">
        <div class="legend-item">
            <div class="legend-dot" style="background:#1D9E75;"></div> Direct qualifier (1st/2nd)
        </div>
        <div class="legend-item">
            <div class="legend-dot" style="background:#EF9F27;"></div> Wildcard bubble (3rd)
        </div>
        <div class="legend-item">
            <div class="legend-dot" style="background:#E24B4A;"></div> Eliminated (4th)
        </div>
        <div class="legend-item">
            <div class="legend-dot" style="background:#ddd;"></div> Not played yet
        </div>
    </div>
    """

    components.html(html, height=750, scrolling=False)