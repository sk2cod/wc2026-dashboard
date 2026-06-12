import pandas as pd


def calculate_wildcard(standings):
    """
    Takes raw standings from football-data.org and returns:
    1. all_groups — list of group DataFrames
    2. wildcard_df — sorted third-place teams, top 8 advance
    """
    all_groups = []
    third_place_teams = []

    for group in standings:
        group_name = group.get("group", "")
        table = group.get("table", [])

        rows = []
        for entry in table:
            team = entry.get("team", {})
            rows.append({
                "group": group_name,
                "position": entry.get("position"),
                "team": team.get("name", ""),
                "crest": team.get("crest", ""),
                "played": entry.get("playedGames"),
                "won": entry.get("won"),
                "draw": entry.get("draw"),
                "lost": entry.get("lost"),
                "gf": entry.get("goalsFor"),
                "ga": entry.get("goalsAgainst"),
                "gd": entry.get("goalDifference"),
                "points": entry.get("points"),
            })

        df = pd.DataFrame(rows)
        all_groups.append(df)

        # Extract 3rd place team only if they have played
        third = df[(df["position"] == 3) & (df["played"] > 0)]
        if not third.empty:
            third_place_teams.append(third.iloc[0])

    # Build wildcard table
    if third_place_teams:
        wildcard_df = pd.DataFrame(third_place_teams)
        wildcard_df = wildcard_df.sort_values(
            by=["points", "gd", "gf"],
            ascending=False
        ).reset_index(drop=True)
        wildcard_df["wildcard_rank"] = wildcard_df.index + 1
        wildcard_df["status"] = wildcard_df["wildcard_rank"].apply(
            lambda r: "IN" if r <= 8 else "OUT"
        )
    else:
        wildcard_df = pd.DataFrame()

    return all_groups, wildcard_df