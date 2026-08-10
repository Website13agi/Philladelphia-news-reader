import csv
import io
import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import urlencode

import pandas as pd
import requests


# =========================================================
# CONFIG
# =========================================================

SEASON = 2026

TEAM_NAME = "Philadelphia Phillies"
TEAM_CODE = "PHI"
TEAM_ID = 143

ROSTER_FILE = "roster.json"
OUTPUT_FILE = "savant_stats.json"

BASE_URL = "https://baseballsavant.mlb.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/126.0 Safari/537.36"
    ),
    "Accept": "text/csv,application/csv,text/plain,*/*",
}


# =========================================================
# HTTP
# =========================================================

def download_csv(url):
    print()
    print("GET:")
    print(url)

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=60,
    )

    response.raise_for_status()

    content = response.content.decode(
        "utf-8-sig",
        errors="replace",
    )

    if not content.strip():
        raise RuntimeError(
            "Baseball Savant returned an empty CSV."
        )

    # HTML error page detection
    first_line = content.lstrip()[:200].lower()

    if "<html" in first_line or "<!doctype" in first_line:
        raise RuntimeError(
            "Baseball Savant returned HTML instead of CSV."
        )

    return pd.read_csv(
        io.StringIO(content)
    )


# =========================================================
# ROSTER
# =========================================================

def load_roster():

    if not os.path.exists(ROSTER_FILE):
        raise FileNotFoundError(
            f"{ROSTER_FILE} was not found."
        )

    with open(
        ROSTER_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    if isinstance(data, dict):

        players = data.get(
            "players",
            []
        )

    elif isinstance(data, list):

        players = data

    else:

        raise ValueError(
            "Invalid roster.json format."
        )

    if not players:
        raise RuntimeError(
            "No players were found in roster.json."
        )

    print(
        f"Roster players loaded: {len(players)}"
    )

    return players


# =========================================================
# SAFE VALUES
# =========================================================

def clean_value(value):

    if value is None:
        return None

    try:

        if pd.isna(value):
            return None

    except Exception:
        pass

    if hasattr(value, "item"):

        try:
            value = value.item()
        except Exception:
            pass

    if isinstance(value, float):

        if value != value:
            return None

        return round(value, 6)

    return value


def get_value(row, *columns):

    for column in columns:

        if column in row.index:

            value = clean_value(
                row[column]
            )

            if value is not None:
                return value

    return None


# =========================================================
# PLAYER ID
# =========================================================

def get_player_id(player):

    possible_keys = [
        "id",
        "playerId",
        "player_id",
        "mlbId",
        "mlb_id",
    ]

    for key in possible_keys:

        value = player.get(key)

        if value is not None and str(value).strip():

            try:
                return int(value)
            except Exception:
                return str(value)

    return None


# =========================================================
# SAVANT URLs
# =========================================================

def build_batter_url():

    params = {
        "type": "batter",
        "year": SEASON,
        "position": "",
        "team": TEAM_ID,
        "min": "q",
        "csv": "true",
    }

    return (
        f"{BASE_URL}/leaderboard/expected_statistics?"
        f"{urlencode(params)}"
    )


def build_pitcher_url():

    params = {
        "type": "pitcher",
        "year": SEASON,
        "position": "",
        "team": TEAM_ID,
        "min": "q",
        "csv": "true",
    }

    return (
        f"{BASE_URL}/leaderboard/expected_statistics?"
        f"{urlencode(params)}"
    )


def build_custom_batter_url():

    selections = ",".join([
        "pa",
        "ab",
        "h",
        "single",
        "double",
        "triple",
        "home_run",
        "rbi",
        "bb",
        "so",
        "avg",
        "obp",
        "slg",
        "ops",
        "iso",
        "babip",
        "k_percent",
        "bb_percent",
        "woba",
        "xwoba",
        "xba",
        "xslg",
        "barrel_batted_rate",
        "hard_hit_percent",
        "exit_velocity_avg",
        "launch_angle_avg",
        "whiff_percent",
        "swing_percent",
    ])

    params = {
        "year": SEASON,
        "type": "batter",
        "filter": "",
        "min": "q",
        "selections": selections,
        "chart": "false",
        "x": "pa",
        "y": "pa",
        "r": "no",
        "chartType": "beeswarm",
        "sort": "pa",
        "sortDir": "desc",
        "csv": "true",
    }

    return (
        f"{BASE_URL}/leaderboard/custom?"
        f"{urlencode(params)}"
    )


def build_custom_pitcher_url():

    selections = ",".join([
        "pa",
        "era",
        "whiff_percent",
        "k_percent",
        "bb_percent",
        "xera",
        "xwoba",
        "exit_velocity_avg",
        "hard_hit_percent",
        "barrel_batted_rate",
    ])

    params = {
        "year": SEASON,
        "type": "pitcher",
        "filter": "",
        "min": "q",
        "selections": selections,
        "chart": "false",
        "x": "pa",
        "y": "pa",
        "r": "no",
        "chartType": "beeswarm",
        "sort": "pa",
        "sortDir": "desc",
        "csv": "true",
    }

    return (
        f"{BASE_URL}/leaderboard/custom?"
        f"{urlencode(params)}"
    )


# =========================================================
# FETCH
# =========================================================

def fetch_batting():

    print()
    print("Fetching Baseball Savant batting data...")

    try:

        data = download_csv(
            build_custom_batter_url()
        )

        print(
            f"Custom batting rows: {len(data)}"
        )

        return data

    except Exception as error:

        print(
            "Custom batting leaderboard failed:"
        )
        print(error)

        print(
            "Trying expected statistics leaderboard..."
        )

        data = download_csv(
            build_batter_url()
        )

        print(
            f"Expected batting rows: {len(data)}"
        )

        return data


def fetch_pitching():

    print()
    print("Fetching Baseball Savant pitching data...")

    try:

        data = download_csv(
            build_custom_pitcher_url()
        )

        print(
            f"Custom pitching rows: {len(data)}"
        )

        return data

    except Exception as error:

        print(
            "Custom pitching leaderboard failed:"
        )
        print(error)

        print(
            "Trying expected statistics leaderboard..."
        )

        data = download_csv(
            build_pitcher_url()
        )

        print(
            f"Expected pitching rows: {len(data)}"
        )

        return data


# =========================================================
# COLUMN DETECTION
# =========================================================

def find_column(data, *names):

    normalized = {
        str(column).strip().lower(): column
        for column in data.columns
    }

    for name in names:

        key = name.lower()

        if key in normalized:
            return normalized[key]

    return None


def detect_player_id_column(data):

    return find_column(
        data,
        "player_id",
        "playerid",
        "id",
        "mlb_id",
    )


def detect_name_column(data):

    return find_column(
        data,
        "player_name",
        "name",
        "last_name, first_name",
    )


# =========================================================
# ROSTER INDEX
# =========================================================

def build_roster_index(players):

    index = {}

    for player in players:

        player_id = get_player_id(player)

        if player_id is None:
            continue

        index[str(player_id)] = player

    return index


# =========================================================
# RECORD BUILDERS
# =========================================================

def build_batter_record(row):

    return {

        "source": "Baseball Savant",

        "season": SEASON,

        "G":
            get_value(row, "G", "games"),

        "PA":
            get_value(row, "PA", "pa"),

        "AB":
            get_value(row, "AB", "ab"),

        "H":
            get_value(row, "H", "h"),

        "1B":
            get_value(
                row,
                "1B",
                "single",
                "singles",
            ),

        "2B":
            get_value(
                row,
                "2B",
                "double",
                "doubles",
            ),

        "3B":
            get_value(
                row,
                "3B",
                "triple",
                "triples",
            ),

        "HR":
            get_value(
                row,
                "HR",
                "home_run",
                "home_runs",
            ),

        "RBI":
            get_value(row, "RBI", "rbi"),

        "BB":
            get_value(row, "BB", "bb"),

        "SO":
            get_value(
                row,
                "SO",
                "so",
            ),

        "SB":
            get_value(
                row,
                "SB",
                "sb",
                "stolen_bases",
            ),

        "AVG":
            get_value(
                row,
                "AVG",
                "avg",
            ),

        "OBP":
            get_value(
                row,
                "OBP",
                "obp",
            ),

        "SLG":
            get_value(
                row,
                "SLG",
                "slg",
            ),

        "OPS":
            get_value(
                row,
                "OPS",
                "ops",
            ),

        "ISO":
            get_value(
                row,
                "ISO",
                "iso",
            ),

        "BABIP":
            get_value(
                row,
                "BABIP",
                "babip",
            ),

        "K%":
            get_value(
                row,
                "K%",
                "k_percent",
            ),

        "BB%":
            get_value(
                row,
                "BB%",
                "bb_percent",
            ),

        "wOBA":
            get_value(
                row,
                "wOBA",
                "woba",
            ),

        "xBA":
            get_value(
                row,
                "xBA",
                "xba",
            ),

        "xSLG":
            get_value(
                row,
                "xSLG",
                "xslg",
            ),

        "xwOBA":
            get_value(
                row,
                "xwOBA",
                "xwoba",
            ),

        "EV":
            get_value(
                row,
                "EV",
                "exit_velocity_avg",
            ),

        "LaunchAngle":
            get_value(
                row,
                "LA",
                "launch_angle_avg",
            ),

        "Barrel%":
            get_value(
                row,
                "Barrel%",
                "barrel_batted_rate",
            ),

        "HardHit%":
            get_value(
                row,
                "HardHit%",
                "hard_hit_percent",
            ),

        "Whiff%":
            get_value(
                row,
                "Whiff%",
                "whiff_percent",
            ),

        "Swing%":
            get_value(
                row,
                "Swing%",
                "swing_percent",
            ),
    }


def build_pitcher_record(row):

    return {

        "source": "Baseball Savant",

        "season": SEASON,

        "G":
            get_value(row, "G", "games"),

        "GS":
            get_value(row, "GS", "games_started"),

        "IP":
            get_value(
                row,
                "IP",
                "ip",
            ),

        "W":
            get_value(row, "W", "wins"),

        "L":
            get_value(row, "L", "losses"),

        "SV":
            get_value(
                row,
                "SV",
                "saves",
            ),

        "ERA":
            get_value(
                row,
                "ERA",
                "era",
            ),

        "WHIP":
            get_value(
                row,
                "WHIP",
                "whip",
            ),

        "SO":
            get_value(
                row,
                "SO",
                "so",
            ),

        "BB":
            get_value(
                row,
                "BB",
                "bb",
            ),

        "HR":
            get_value(
                row,
                "HR",
                "home_run",
                "home_runs",
            ),

        "K%":
            get_value(
                row,
                "K%",
                "k_percent",
            ),

        "BB%":
            get_value(
                row,
                "BB%",
                "bb_percent",
            ),

        "K-BB%":
            get_value(
                row,
                "K-BB%",
                "k_minus_bb_percent",
            ),

        "xERA":
            get_value(
                row,
                "xERA",
                "xera",
            ),

        "xwOBA":
            get_value(
                row,
                "xwOBA",
                "xwoba",
            ),

        "EV":
            get_value(
                row,
                "EV",
                "exit_velocity_avg",
            ),

        "HardHit%":
            get_value(
                row,
                "HardHit%",
                "hard_hit_percent",
            ),

        "Barrel%":
            get_value(
                row,
                "Barrel%",
                "barrel_batted_rate",
            ),

        "Whiff%":
            get_value(
                row,
                "Whiff%",
                "whiff_percent",
            ),
    }


# =========================================================
# MATCH DATA
# =========================================================

def build_stats(
    roster,
    batting,
    pitching,
):

    roster_index = build_roster_index(
        roster
    )

    result = {}

    batting_id_column = detect_player_id_column(
        batting
    )

    pitching_id_column = detect_player_id_column(
        pitching
    )

    batting_name_column = detect_name_column(
        batting
    )

    pitching_name_column = detect_name_column(
        pitching
    )

    print()
    print(
        "Batting player ID column:",
        batting_id_column,
    )

    print(
        "Pitching player ID column:",
        pitching_id_column,
    )

    # -----------------------------------------------------
    # Create every roster player first
    # -----------------------------------------------------

    for player in roster:

        player_id = get_player_id(player)

        if player_id is None:
            continue

        key = str(player_id)

        result[key] = {

            "mlbId":
                player_id,

            "name":
                player.get("name"),

            "batting":
                None,

            "pitching":
                None,
        }

    # -----------------------------------------------------
    # Batting
    # -----------------------------------------------------

    for _, row in batting.iterrows():

        player_id = None

        if batting_id_column:

            player_id = clean_value(
                row[batting_id_column]
            )

        if player_id is None:

            continue

        key = str(
            int(player_id)
            if str(player_id).isdigit()
            else player_id
        )

        if key not in result:

            continue

        result[key]["batting"] = (
            build_batter_record(row)
        )

    # -----------------------------------------------------
    # Pitching
    # -----------------------------------------------------

    for _, row in pitching.iterrows():

        player_id = None

        if pitching_id_column:

            player_id = clean_value(
                row[pitching_id_column]
            )

        if player_id is None:

            continue

        key = str(
            int(player_id)
            if str(player_id).isdigit()
            else player_id
        )

        if key not in result:

            continue

        result[key]["pitching"] = (
            build_pitcher_record(row)
        )

    return result


# =========================================================
# SAVE
# =========================================================

def save_data(stats):

    output = {

        "updatedAt":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "season":
            SEASON,

        "team": {

            "id":
                TEAM_ID,

            "name":
                TEAM_NAME,

            "abbreviation":
                TEAM_CODE,
        },

        "source":
            "Baseball Savant",

        "description":
            (
                "Philadelphia Phillies "
                "player statistics sourced "
                "directly from Baseball Savant."
            ),

        "players":
            stats,
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2,
        )

    batting_count = sum(
        1
        for player in stats.values()
        if player["batting"] is not None
    )

    pitching_count = sum(
        1
        for player in stats.values()
        if player["pitching"] is not None
    )

    print()
    print("=" * 60)
    print(
        "Baseball Savant statistics saved."
    )
    print(
        f"Roster players: {len(stats)}"
    )
    print(
        f"Players with batting data: {batting_count}"
    )
    print(
        f"Players with pitching data: {pitching_count}"
    )
    print(
        f"Output: {OUTPUT_FILE}"
    )
    print("=" * 60)


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 60)
    print(
        "Phillies Baseball Savant Statistics Updater"
    )
    print(
        f"Season: {SEASON}"
    )
    print("=" * 60)

    roster = load_roster()

    batting = fetch_batting()

    pitching = fetch_pitching()

    stats = build_stats(
        roster,
        batting,
        pitching,
    )

    if not stats:

        raise RuntimeError(
            "No roster players were found."
        )

    save_data(stats)

    print()
    print(
        "Baseball Savant update completed successfully."
    )


if __name__ == "__main__":
    main()
