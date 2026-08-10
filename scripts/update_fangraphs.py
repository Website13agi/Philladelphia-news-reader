import json
import os
import sys
import time
import unicodedata
from datetime import datetime, timezone

import pandas as pd

try:
    from pybaseball import batting_stats, pitching_stats
except ImportError:
    print("ERROR: pybaseball is not installed.")
    sys.exit(1)


# =========================================================
# CONFIG
# =========================================================

SEASON = 2026

TEAM_NAME = "Philadelphia Phillies"
TEAM_CODE = "PHI"

ROSTER_FILE = "players.json"
OUTPUT_FILE = "fangraphs_stats.json"


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def normalize_name(name):
    """
    Normalize player names so that MLB roster names and
    FanGraphs names can be matched safely.
    """

    if name is None:
        return ""

    value = str(name)

    value = unicodedata.normalize(
        "NFKD",
        value
    )

    value = "".join(
        char
        for char in value
        if not unicodedata.combining(char)
    )

    value = value.lower()

    value = (
        value
        .replace(".", "")
        .replace("'", "")
        .replace("-", " ")
    )

    value = " ".join(
        value.split()
    )

    return value


# =========================================================
# SAFE VALUE
# =========================================================

def clean_value(value):

    if pd.isna(value):
        return None

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


# =========================================================
# COLUMN HELPER
# =========================================================

def get_value(row, *columns):

    for column in columns:

        if column in row.index:

            value = row[column]

            if not pd.isna(value):
                return clean_value(value)

    return None


# =========================================================
# LOAD ROSTER
# =========================================================

def load_roster():

    if not os.path.exists(
        ROSTER_FILE
    ):

        raise FileNotFoundError(
            f"{ROSTER_FILE} was not found."
        )

    with open(
        ROSTER_FILE,
        "r",
        encoding="utf-8"
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
            "Invalid players.json format."
        )

    return players


# =========================================================
# FETCH FANGRAPHS BATTING
# =========================================================

def fetch_batting():

    print(
        f"Fetching FanGraphs batting data for {SEASON}..."
    )

    last_error = None

    for attempt in range(1, 4):

        try:

            data = batting_stats(
                SEASON,
                SEASON,
                qual=0
            )

            if data is None:
                raise RuntimeError(
                    "FanGraphs batting data is empty."
                )

            print(
                f"Batting rows received: {len(data)}"
            )

            return data

        except Exception as error:

            last_error = error

            print(
                f"Batting attempt {attempt} failed: {error}"
            )

            if attempt < 3:
                time.sleep(5)

    raise RuntimeError(
        f"Unable to fetch FanGraphs batting data: {last_error}"
    )


# =========================================================
# FETCH FANGRAPHS PITCHING
# =========================================================

def fetch_pitching():

    print(
        f"Fetching FanGraphs pitching data for {SEASON}..."
    )

    last_error = None

    for attempt in range(1, 4):

        try:

            data = pitching_stats(
                SEASON,
                SEASON,
                qual=0
            )

            if data is None:
                raise RuntimeError(
                    "FanGraphs pitching data is empty."
                )

            print(
                f"Pitching rows received: {len(data)}"
            )

            return data

        except Exception as error:

            last_error = error

            print(
                f"Pitching attempt {attempt} failed: {error}"
            )

            if attempt < 3:
                time.sleep(5)

    raise RuntimeError(
        f"Unable to fetch FanGraphs pitching data: {last_error}"
    )


# =========================================================
# FILTER PHILLIES
# =========================================================

def filter_team(data):

    if "Team" not in data.columns:

        raise RuntimeError(
            "FanGraphs data does not contain Team column."
        )

    result = data[
        data["Team"]
        .astype(str)
        .str.upper()
        .eq(TEAM_CODE)
    ].copy()

    return result


# =========================================================
# BATTER RECORD
# =========================================================

def build_batter_record(row):

    return {

        # Identification
        "name":
            get_value(
                row,
                "Name"
            ),

        "fangraphsId":
            get_value(
                row,
                "IDfg",
                "playerid"
            ),

        "team":
            TEAM_CODE,

        "season":
            SEASON,

        # Basic
        "G":
            get_value(row, "G"),

        "PA":
            get_value(row, "PA"),

        "AB":
            get_value(row, "AB"),

        "H":
            get_value(row, "H"),

        "2B":
            get_value(row, "2B"),

        "3B":
            get_value(row, "3B"),

        "HR":
            get_value(row, "HR"),

        "R":
            get_value(row, "R"),

        "RBI":
            get_value(row, "RBI"),

        "BB":
            get_value(row, "BB"),

        "SO":
            get_value(row, "SO"),

        "SB":
            get_value(row, "SB"),

        "CS":
            get_value(row, "CS"),

        # Slash line
        "AVG":
            get_value(row, "AVG"),

        "OBP":
            get_value(row, "OBP"),

        "SLG":
            get_value(row, "SLG"),

        "OPS":
            get_value(row, "OPS"),

        # Advanced offense
        "wOBA":
            get_value(row, "wOBA"),

        "wRC+":
            get_value(row, "wRC+"),

        "BB%":
            get_value(row, "BB%"),

        "K%":
            get_value(row, "K%"),

        "ISO":
            get_value(row, "ISO"),

        "BABIP":
            get_value(row, "BABIP"),

        # Value
        "BsR":
            get_value(row, "BsR"),

        "Off":
            get_value(row, "Off"),

        "Def":
            get_value(row, "Def"),

        "WAR":
            get_value(row, "WAR"),

        # FanGraphs identifier
        "source":
            "FanGraphs"
    }


# =========================================================
# PITCHER RECORD
# =========================================================

def build_pitcher_record(row):

    return {

        # Identification
        "name":
            get_value(
                row,
                "Name"
            ),

        "fangraphsId":
            get_value(
                row,
                "IDfg",
                "playerid"
            ),

        "team":
            TEAM_CODE,

        "season":
            SEASON,

        # Basic
        "G":
            get_value(row, "G"),

        "GS":
            get_value(row, "GS"),

        "IP":
            get_value(row, "IP"),

        "W":
            get_value(row, "W"),

        "L":
            get_value(row, "L"),

        "SV":
            get_value(row, "SV"),

        "SO":
            get_value(row, "SO"),

        "BB":
            get_value(row, "BB"),

        "HR":
            get_value(row, "HR"),

        # Traditional
        "ERA":
            get_value(row, "ERA"),

        "WHIP":
            get_value(row, "WHIP"),

        # Advanced
        "FIP":
            get_value(row, "FIP"),

        "xFIP":
            get_value(row, "xFIP"),

        "K/9":
            get_value(row, "K/9"),

        "BB/9":
            get_value(row, "BB/9"),

        "HR/9":
            get_value(row, "HR/9"),

        "K%":
            get_value(row, "K%"),

        "BB%":
            get_value(row, "BB%"),

        "K-BB%":
            get_value(
                row,
                "K-BB%"
            ),

        # Value
        "WAR":
            get_value(row, "WAR"),

        "RA9-WAR":
            get_value(
                row,
                "RA9-WAR"
            ),

        # FanGraphs identifier
        "source":
            "FanGraphs"
    }


# =========================================================
# MATCH ROSTER
# =========================================================

def build_player_index(players):

    index = {}

    for player in players:

        name = normalize_name(
            player.get("name", "")
        )

        if not name:
            continue

        index[name] = player

    return index


# =========================================================
# BUILD STATS
# =========================================================

def build_stats(
    roster,
    batting,
    pitching
):

    roster_index = build_player_index(
        roster
    )

    result = {}

    # -----------------------------------------------------
    # BATTING
    # -----------------------------------------------------

    for _, row in batting.iterrows():

        name = get_value(
            row,
            "Name"
        )

        normalized = normalize_name(
            name
        )

        if normalized not in roster_index:
            continue

        player = roster_index[
            normalized
        ]

        player_id = str(
            player.get("id")
        )

        result.setdefault(
            player_id,
            {
                "mlbId":
                    player.get("id"),

                "name":
                    player.get("name"),

                "batting":
                    None,

                "pitching":
                    None
            }
        )

        result[
            player_id
        ]["batting"] = build_batter_record(
            row
        )

    # -----------------------------------------------------
    # PITCHING
    # -----------------------------------------------------

    for _, row in pitching.iterrows():

        name = get_value(
            row,
            "Name"
        )

        normalized = normalize_name(
            name
        )

        if normalized not in roster_index:
            continue

        player = roster_index[
            normalized
        ]

        player_id = str(
            player.get("id")
        )

        result.setdefault(
            player_id,
            {
                "mlbId":
                    player.get("id"),

                "name":
                    player.get("name"),

                "batting":
                    None,

                "pitching":
                    None
            }
        )

        result[
            player_id
        ]["pitching"] = build_pitcher_record(
            row
        )

    return result


# =========================================================
# SAVE
# =========================================================

def save_data(
    stats,
    batting_count,
    pitching_count
):

    output = {

        "updatedAt":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "season":
            SEASON,

        "team": {

            "id":
                143,

            "name":
                TEAM_NAME,

            "abbreviation":
                TEAM_CODE
        },

        "source":
            "FanGraphs",

        "description":
            "Philadelphia Phillies player statistics sourced from FanGraphs.",

        "counts": {

            "batting":
                batting_count,

            "pitching":
                pitching_count,

            "matchedPlayers":
                len(stats)
        },

        "players":
            stats
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2
        )

    print()
    print(
        f"Saved FanGraphs statistics for {len(stats)} players."
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 60)

    print(
        "Phillies FanGraphs Statistics Updater"
    )

    print(
        f"Season: {SEASON}"
    )

    print("=" * 60)

    roster = load_roster()

    print(
        f"Roster players loaded: {len(roster)}"
    )

    batting_all = fetch_batting()

    pitching_all = fetch_pitching()

    batting = filter_team(
        batting_all
    )

    pitching = filter_team(
        pitching_all
    )

    print(
        f"Phillies batting rows: {len(batting)}"
    )

    print(
        f"Phillies pitching rows: {len(pitching)}"
    )

    stats = build_stats(
        roster,
        batting,
        pitching
    )

    if not stats:

        raise RuntimeError(
            "No Phillies players could be matched with FanGraphs data."
        )

    save_data(
        stats,
        len(batting),
        len(pitching)
    )

    print()
    print(
        "FanGraphs statistics update completed successfully."
    )


if __name__ == "__main__":
    main()
