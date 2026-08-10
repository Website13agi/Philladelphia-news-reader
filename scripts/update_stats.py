import json
import math
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from pybaseball import (
    batting_stats,
    pitching_stats,
    statcast_batter_expected_stats,
    statcast_pitcher_expected_stats,
    statcast_batter_exitvelo_barrels,
    statcast_pitcher_exitvelo_barrels,
    statcast_outs_above_average,
)


# =========================================================
# SETTINGS
# =========================================================

SEASON = 2026
TEAM = "PHI"

ROOT_DIR = Path(__file__).resolve().parent.parent

PLAYERS_FILE = ROOT_DIR / "players.json"
OUTPUT_FILE = ROOT_DIR / "player_stats.json"


# =========================================================
# HELPERS
# =========================================================

def clean_name(value):
    """
    選手名を比較用に正規化する。
    """

    if value is None:
        return ""

    value = str(value)

    value = unicodedata.normalize(
        "NFKD",
        value
    )

    value = value.lower()

    value = re.sub(
        r"[^a-z0-9 ]",
        "",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


def clean_number(value):

    if value is None:
        return None

    try:

        if pd.isna(value):
            return None

    except Exception:
        pass

    try:

        number = float(value)

        if math.isnan(number):
            return None

        return number

    except Exception:

        return value


def find_column(df, candidates):

    if df is None or df.empty:
        return None

    columns = {
        str(column).strip().lower():
        column
        for column in df.columns
    }

    for candidate in candidates:

        key = candidate.lower()

        if key in columns:
            return columns[key]

    return None


def get_value(row, candidates):

    for candidate in candidates:

        if candidate in row.index:

            value = row[candidate]

            if value is not None:

                try:

                    if pd.isna(value):
                        continue

                except Exception:
                    pass

                return clean_number(value)

    return None


def get_player_name(row):

    candidates = [
        "Name",
        "name",
        "player_name",
        "Player",
        "player"
    ]

    for candidate in candidates:

        if candidate in row.index:

            value = row[candidate]

            if value is not None:

                return str(value).strip()

    return ""


# =========================================================
# LOAD PLAYERS
# =========================================================

def load_players():

    if not PLAYERS_FILE.exists():

        raise FileNotFoundError(
            f"{PLAYERS_FILE} was not found."
        )

    with open(
        PLAYERS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)


    # -----------------------------------------------------
    # Support several possible players.json structures
    # -----------------------------------------------------

    if isinstance(data, list):

        players = data

    elif isinstance(data, dict):

        if isinstance(
            data.get("players"),
            list
        ):

            players = data["players"]

        elif isinstance(
            data.get("roster"),
            list
        ):

            players = data["roster"]

        elif isinstance(
            data.get("active"),
            list
        ):

            players = data["active"]

        else:

            players = []

            for value in data.values():

                if isinstance(value, list):

                    players.extend(value)


    else:

        players = []


    if not players:

        raise RuntimeError(
            "No players were found in players.json."
        )


    print(
        f"Loaded {len(players)} players."
    )

    return players


# =========================================================
# FAN GRAPHS BATTING
# =========================================================

def load_fangraphs_batting():

    print()
    print(
        "Downloading FanGraphs batting stats..."
    )


    df = batting_stats(
        SEASON,
        SEASON,
        qual=0
    )


    if df is None or df.empty:

        raise RuntimeError(
            "FanGraphs batting data is empty."
        )


    print(
        f"FanGraphs batting rows: {len(df)}"
    )


    return df


# =========================================================
# FAN GRAPHS PITCHING
# =========================================================

def load_fangraphs_pitching():

    print()
    print(
        "Downloading FanGraphs pitching stats..."
    )


    df = pitching_stats(
        SEASON,
        SEASON,
        qual=0
    )


    if df is None or df.empty:

        raise RuntimeError(
            "FanGraphs pitching data is empty."
        )


    print(
        f"FanGraphs pitching rows: {len(df)}"
    )


    return df


# =========================================================
# SAVANT EXPECTED BATTING
# =========================================================

def load_savant_batting():

    print()
    print(
        "Downloading Baseball Savant expected batting stats..."
    )


    df = statcast_batter_expected_stats(
        SEASON,
        minPA=0
    )


    if df is None or df.empty:

        print(
            "Savant batting expected stats unavailable."
        )

        return pd.DataFrame()


    print(
        f"Savant batting rows: {len(df)}"
    )


    return df


# =========================================================
# SAVANT EXPECTED PITCHING
# =========================================================

def load_savant_pitching():

    print()
    print(
        "Downloading Baseball Savant expected pitching stats..."
    )


    df = statcast_pitcher_expected_stats(
        SEASON,
        minPA=0
    )


    if df is None or df.empty:

        print(
            "Savant pitching expected stats unavailable."
        )

        return pd.DataFrame()


    print(
        f"Savant pitching rows: {len(df)}"
    )


    return df


# =========================================================
# SAVANT BATTING CONTACT
# =========================================================

def load_savant_batting_contact():

    print()
    print(
        "Downloading Baseball Savant batting contact stats..."
    )


    df = statcast_batter_exitvelo_barrels(
        SEASON,
        minBBE=0
    )


    if df is None or df.empty:

        print(
            "Savant batting contact data unavailable."
        )

        return pd.DataFrame()


    print(
        f"Savant batting contact rows: {len(df)}"
    )


    return df


# =========================================================
# SAVANT PITCHING CONTACT
# =========================================================

def load_savant_pitching_contact():

    print()
    print(
        "Downloading Baseball Savant pitching contact stats..."
    )


    df = statcast_pitcher_exitvelo_barrels(
        SEASON,
        minBBE=0
    )


    if df is None or df.empty:

        print(
            "Savant pitching contact data unavailable."
        )

        return pd.DataFrame()


    print(
        f"Savant pitching contact rows: {len(df)}"
    )


    return df


# =========================================================
# SAVANT OAA
# =========================================================

def load_oaa():

    print()
    print(
        "Downloading Baseball Savant OAA..."
    )


    results = []


    # -----------------------------------------------------
    # Position mapping
    # 3 = 1B
    # 4 = 2B
    # 5 = 3B
    # 6 = SS
    # 7 = LF
    # 8 = CF
    # 9 = RF
    # -----------------------------------------------------

    for position in [
        3,
        4,
        5,
        6,
        7,
        8,
        9
    ]:

        try:

            df = statcast_outs_above_average(
                SEASON,
                position,
                min_att=0
            )

            if df is not None and not df.empty:

                results.append(df)

        except Exception as error:

            print(
                f"OAA position {position} failed:"
            )

            print(error)


    if not results:

        print(
            "OAA unavailable."
        )

        return pd.DataFrame()


    combined = pd.concat(
        results,
        ignore_index=True
    )


    print(
        f"OAA rows: {len(combined)}"
    )


    return combined


# =========================================================
# BUILD FAN GRAPHS MAP
# =========================================================

def build_fangraphs_map(df):

    result = {}


    if df is None or df.empty:

        return result


    for _, row in df.iterrows():

        name = get_player_name(row)

        key = clean_name(name)


        if not key:
            continue


        result[key] = row


    return result


# =========================================================
# BUILD SAVANT MAP
# =========================================================

def build_savant_map(df):

    result = {}


    if df is None or df.empty:

        return result


    for _, row in df.iterrows():

        name = get_player_name(row)

        key = clean_name(name)


        if not key:
            continue


        result[key] = row


    return result


# =========================================================
# EXTRACT BATTING FAN GRAPHS
# =========================================================

def extract_batting_fangraphs(row):

    if row is None:
        return {}


    return {

        "G":
            get_value(
                row,
                ["G"]
            ),

        "PA":
            get_value(
                row,
                ["PA"]
            ),

        "HR":
            get_value(
                row,
                ["HR"]
            ),

        "R":
            get_value(
                row,
                ["R"]
            ),

        "RBI":
            get_value(
                row,
                ["RBI"]
            ),

        "SB":
            get_value(
                row,
                ["SB"]
            ),

        "BB":
            get_value(
                row,
                ["BB"]
            ),

        "SO":
            get_value(
                row,
                ["SO"]
            ),

        "AVG":
            get_value(
                row,
                ["AVG"]
            ),

        "OBP":
            get_value(
                row,
                ["OBP"]
            ),

        "SLG":
            get_value(
                row,
                ["SLG"]
            ),

        "OPS":
            get_value(
                row,
                ["OPS"]
            ),

        "wOBA":
            get_value(
                row,
                ["wOBA"]
            ),

        "wRC+":
            get_value(
                row,
                ["wRC+"]
            ),

        "WAR":
            get_value(
                row,
                ["WAR"]
            )
    }


# =========================================================
# EXTRACT PITCHING FAN GRAPHS
# =========================================================

def extract_pitching_fangraphs(row):

    if row is None:
        return {}


    return {

        "G":
            get_value(
                row,
                ["G"]
            ),

        "GS":
            get_value(
                row,
                ["GS"]
            ),

        "IP":
            get_value(
                row,
                ["IP"]
            ),

        "W":
            get_value(
                row,
                ["W"]
            ),

        "L":
            get_value(
                row,
                ["L"]
            ),

        "SV":
            get_value(
                row,
                ["SV"]
            ),

        "ERA":
            get_value(
                row,
                ["ERA"]
            ),

        "FIP":
            get_value(
                row,
                ["FIP"]
            ),

        "WHIP":
            get_value(
                row,
                ["WHIP"]
            ),

        "SO":
            get_value(
                row,
                ["SO"]
            ),

        "BB":
            get_value(
                row,
                ["BB"]
            ),

        "HR":
            get_value(
                row,
                ["HR"]
            ),

        "K%":
            get_value(
                row,
                ["K%"]
            ),

        "BB%":
            get_value(
                row,
                ["BB%"]
            ),

        "WAR":
            get_value(
                row,
                ["WAR"]
            )
    }


# =========================================================
# EXTRACT SAVANT BATTING
# =========================================================

def extract_savant_batting(
    expected_row,
    contact_row
):

    result = {}


    if expected_row is not None:

        result.update({

            "xBA":
                get_value(
                    expected_row,
                    [
                        "xBA",
                        "xba"
                    ]
                ),

            "xSLG":
                get_value(
                    expected_row,
                    [
                        "xSLG",
                        "xslg"
                    ]
                ),

            "xwOBA":
                get_value(
                    expected_row,
                    [
                        "xwOBA",
                        "xwoba"
                    ]
                )

        })


    if contact_row is not None:

        result.update({

            "EV":
                get_value(
                    contact_row,
                    [
                        "avg_hit_speed",
                        "launch_speed",
                        "EV"
                    ]
                ),

            "MaxEV":
                get_value(
                    contact_row,
                    [
                        "max_hit_speed",
                        "maxEV",
                        "max_ev"
                    ]
                ),

            "HardHit%":
                get_value(
                    contact_row,
                    [
                        "hard_hit_percent",
                        "HardHit%"
                    ]
                ),

            "Barrel%":
                get_value(
                    contact_row,
                    [
                        "barrels_percent",
                        "Barrel%"
                    ]
                ),

            "Barrels":
                get_value(
                    contact_row,
                    [
                        "barrels",
                        "Barrels"
                    ]
                )

        })


    return result


# =========================================================
# EXTRACT SAVANT PITCHING
# =========================================================

def extract_savant_pitching(
    expected_row,
    contact_row
):

    result = {}


    if expected_row is not None:

        result.update({

            "xBA":
                get_value(
                    expected_row,
                    [
                        "xBA",
                        "xba"
                    ]
                ),

            "xSLG":
                get_value(
                    expected_row,
                    [
                        "xSLG",
                        "xslg"
                    ]
                ),

            "xwOBA":
                get_value(
                    expected_row,
                    [
                        "xwOBA",
                        "xwoba"
                    ]
                ),

            "xERA":
                get_value(
                    expected_row,
                    [
                        "xERA",
                        "xera"
                    ]
                )

        })


    if contact_row is not None:

        result.update({

            "EV":
                get_value(
                    contact_row,
                    [
                        "avg_hit_speed",
                        "launch_speed",
                        "EV"
                    ]
                ),

            "HardHit%":
                get_value(
                    contact_row,
                    [
                        "hard_hit_percent",
                        "HardHit%"
                    ]
                ),

            "Barrel%":
                get_value(
                    contact_row,
                    [
                        "barrels_percent",
                        "Barrel%"
                    ]
                ),

            "Barrels":
                get_value(
                    contact_row,
                    [
                        "barrels",
                        "Barrels"
                    ]
                )

        })


    return result


# =========================================================
# OAA MAP
# =========================================================

def build_oaa_map(df):

    result = {}


    if df is None or df.empty:

        return result


    for _, row in df.iterrows():

        name = get_player_name(row)

        key = clean_name(name)


        if not key:
            continue


        value = get_value(
            row,
            [
                "OAA",
                "oaa"
            ]
        )


        if value is None:
            continue


        # If the player appears at multiple positions,
        # add the position values together.
        if key in result:

            old = result[key]

            if old is not None:

                result[key] = old + value

        else:

            result[key] = value


    return result


# =========================================================
# TEAM FILTER
# =========================================================

def belongs_to_phillies(row):

    if row is None:
        return False


    team_column = find_column(
        row.to_frame().T,
        [
            "Team",
            "team",
            "team_name_abbr"
        ]
    )


    if team_column is None:
        return True


    value = str(
        row[team_column]
    ).upper()


    # FanGraphs may display:
    # PHI
    # Philadelphia
    # Phillies
    return (
        "PHI" in value
        or "PHILADELPHIA" in value
        or "PHILLIES" in value
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print(
        "=============================================="
    )

    print(
        "Phillies Player Statistics Updater"
    )

    print(
        f"Season: {SEASON}"
    )

    print(
        "=============================================="
    )


    # -----------------------------------------------------
    # PLAYERS
    # -----------------------------------------------------

    players = load_players()


    # -----------------------------------------------------
    # FAN GRAPHS
    # -----------------------------------------------------

    fg_batting = load_fangraphs_batting()

    fg_pitching = load_fangraphs_pitching()


    # Only Phillies rows
    fg_batting = fg_batting[
        fg_batting["Team"].astype(str).str.contains(
            "PHI|Philadelphia|Phillies",
            case=False,
            regex=True,
            na=False
        )
    ].copy()


    fg_pitching = fg_pitching[
        fg_pitching["Team"].astype(str).str.contains(
            "PHI|Philadelphia|Phillies",
            case=False,
            regex=True,
            na=False
        )
    ].copy()


    # -----------------------------------------------------
    # SAVANT
    # -----------------------------------------------------

    savant_batting = (
        load_savant_batting()
    )

    savant_pitching = (
        load_savant_pitching()
    )

    savant_batting_contact = (
        load_savant_batting_contact()
    )

    savant_pitching_contact = (
        load_savant_pitching_contact()
    )

    oaa = load_oaa()


    # -----------------------------------------------------
    # MAPS
    # -----------------------------------------------------

    fg_batting_map = build_fangraphs_map(
        fg_batting
    )

    fg_pitching_map = build_fangraphs_map(
        fg_pitching
    )

    savant_batting_map = build_savant_map(
        savant_batting
    )

    savant_pitching_map = build_savant_map(
        savant_pitching
    )

    savant_batting_contact_map = (
        build_savant_map(
            savant_batting_contact
        )
    )

    savant_pitching_contact_map = (
        build_savant_map(
            savant_pitching_contact
        )
    )

    oaa_map = build_oaa_map(
        oaa
    )


    # -----------------------------------------------------
    # BUILD OUTPUT
    # -----------------------------------------------------

    output_batting = []

    output_pitching = []

    matched = 0

    unmatched = []


    for player in players:

        # -----------------------------------------------
        # PLAYER NAME
        # -----------------------------------------------

        name = (
            player.get("name")
            or player.get("fullName")
            or player.get("player_name")
            or player.get("playerName")
            or ""
        )


        if not name:
            continue


        key = clean_name(name)


        # -----------------------------------------------
        # PLAYER ID
        # -----------------------------------------------

        player_id = (
            player.get("playerId")
            or player.get("player_id")
            or player.get("mlbam_id")
            or player.get("id")
        )


        # -----------------------------------------------
        # POSITION
        # -----------------------------------------------

        position = (
            player.get("position")
            or player.get("pos")
            or ""
        )


        position_upper = str(
            position
        ).upper()


        # -----------------------------------------------
        # PITCHER
        # -----------------------------------------------

        is_pitcher = (
            position_upper == "P"
            or position_upper == "PITCHER"
        )


        # -----------------------------------------------
        # COMMON OBJECT
        # -----------------------------------------------

        record = {

            "playerId":
                player_id,

            "name":
                name,

            "position":
                position,

            "season":
                SEASON
        }


        # =================================================
        # PITCHER
        # =================================================

        if is_pitcher:

            fg_row = (
                fg_pitching_map.get(key)
            )

            savant_row = (
                savant_pitching_map.get(key)
            )

            contact_row = (
                savant_pitching_contact_map.get(key)
            )


            fangraphs_data = (
                extract_pitching_fangraphs(
                    fg_row
                )
            )


            savant_data = (
                extract_savant_pitching(
                    savant_row,
                    contact_row
                )
            )


            record["type"] = "pitcher"

            record["fangraphs"] = (
                fangraphs_data
            )

            record["savant"] = (
                savant_data
            )


            if fg_row is not None:

                matched += 1

            else:

                unmatched.append(name)


            output_pitching.append(
                record
            )


        # =================================================
        # HITTER
        # =================================================

        else:

            fg_row = (
                fg_batting_map.get(key)
            )

            savant_row = (
                savant_batting_map.get(key)
            )

            contact_row = (
                savant_batting_contact_map.get(key)
            )


            fangraphs_data = (
                extract_batting_fangraphs(
                    fg_row
                )
            )


            savant_data = (
                extract_savant_batting(
                    savant_row,
                    contact_row
                )
            )


            record["type"] = "batter"

            record["fangraphs"] = (
                fangraphs_data
            )

            record["savant"] = (
                savant_data
            )


            if fg_row is not None:

                matched += 1

            else:

                unmatched.append(name)


            output_batting.append(
                record
            )


    # -----------------------------------------------------
    # OUTPUT
    # -----------------------------------------------------

    output = {

        "team":
            "Philadelphia Phillies",

        "teamAbbreviation":
            TEAM,

        "season":
            SEASON,

        "updatedAt":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "sources": {

            "fangraphs":
                "https://www.fangraphs.com/",

            "baseballSavant":
                "https://baseballsavant.mlb.com/",

            "mlb":
                "https://www.mlb.com/"
        },

        "batters":
            output_batting,

        "pitchers":
            output_pitching,

        "summary": {

            "players":
                len(
                    output_batting
                )
                +
                len(
                    output_pitching
                ),

            "matched":
                matched,

            "unmatched":
                unmatched
        }
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
        "=============================================="
    )

    print(
        f"Batters: {len(output_batting)}"
    )

    print(
        f"Pitchers: {len(output_pitching)}"
    )

    print(
        f"Matched: {matched}"
    )

    print(
        f"Unmatched: {len(unmatched)}"
    )

    if unmatched:

        print()
        print(
            "Unmatched players:"
        )

        for name in unmatched:

            print(
                f" - {name}"
            )


    print()
    print(
        f"Output: {OUTPUT_FILE}"
    )

    print(
        "=============================================="
    )


if __name__ == "__main__":

    main()
