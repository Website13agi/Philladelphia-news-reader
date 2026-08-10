import csv
import io
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone


# =========================================================
# CONFIG
# =========================================================

TEAM_ID = 143
TEAM_ABBR = "PHI"
SEASON = datetime.now(timezone.utc).year

PLAYERS_FILE = "players.json"
OUTPUT_FILE = "player_stats.json"

USER_AGENT = "Phillies-Daily/1.0"

SAVANT_URL = "https://baseballsavant.mlb.com/leaderboard/custom.csv"


# =========================================================
# HTTP
# =========================================================

def get_text(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/csv,text/plain,*/*",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=60,
    ) as response:

        return response.read().decode(
            "utf-8-sig",
            errors="replace",
        )


# =========================================================
# JSON
# =========================================================

def load_json(path):
    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# =========================================================
# NUMBER
# =========================================================

def clean_number(value):

    if value is None:
        return None

    value = str(value).strip()

    if value in {
        "",
        "-",
        "—",
        "N/A",
        "null",
        "None",
    }:
        return None

    value = value.replace("%", "")

    try:
        number = float(value)

        if number.is_integer():
            return int(number)

        return number

    except Exception:
        return value


# =========================================================
# FIELD
# =========================================================

def first_value(row, *names):

    normalized = {}

    for key, value in row.items():

        normalized[
            str(key).strip().lower()
        ] = value

    for name in names:

        value = normalized.get(
            name.lower()
        )

        if value not in (
            None,
            "",
        ):
            return value

    return None


# =========================================================
# SAVANT CSV
# =========================================================

def fetch_savant(
    player_type,
    selections,
):

    params = {
        "year": SEASON,
        "type": player_type,
        "filter": f"team={TEAM_ABBR}",
        "min": "q",
        "selections": ",".join(selections),
        "chart": "false",
        "x": "pa",
        "y": "pa",
        "r": "no",
        "chartType": "beeswarm",
        "sort": "pa",
        "sortDir": "desc",
    }

    url = (
        SAVANT_URL
        + "?"
        + urllib.parse.urlencode(
            params
        )
    )

    print()
    print(
        f"Downloading Savant {player_type} data..."
    )
    print(url)

    text = get_text(url)

    reader = csv.DictReader(
        io.StringIO(text)
    )

    rows = list(reader)

    print(
        f"Savant returned {len(rows)} rows."
    )

    return rows


# =========================================================
# PLAYER ID
# =========================================================

def get_player_id(row):

    value = first_value(
        row,
        "player_id",
        "playerid",
        "mlb_id",
        "id",
    )

    if value is None:
        return None

    try:
        return int(
            float(value)
        )

    except Exception:
        return None


# =========================================================
# PLAYER NAME
# =========================================================

def get_player_name(row):

    return first_value(
        row,
        "last_name, first_name",
        "player_name",
        "name",
        "player",
    )


# =========================================================
# NORMALIZE SAVANT ROW
# =========================================================

def normalize_row(
    row,
    player_type,
):

    player_id = get_player_id(
        row
    )

    if not player_id:
        return None

    name = get_player_name(
        row
    )

    if player_type == "batter":

        stats = {

            "PA":
                clean_number(
                    first_value(
                        row,
                        "pa",
                    )
                ),

            "AB":
                clean_number(
                    first_value(
                        row,
                        "ab",
                    )
                ),

            "H":
                clean_number(
                    first_value(
                        row,
                        "h",
                    )
                ),

            "HR":
                clean_number(
                    first_value(
                        row,
                        "home_run",
                        "hr",
                    )
                ),

            "RBI":
                clean_number(
                    first_value(
                        row,
                        "rbi",
                    )
                ),

            "BB":
                clean_number(
                    first_value(
                        row,
                        "bb",
                    )
                ),

            "SO":
                clean_number(
                    first_value(
                        row,
                        "k",
                        "so",
                    )
                ),

            "SB":
                clean_number(
                    first_value(
                        row,
                        "sb",
                    )
                ),

            "AVG":
                clean_number(
                    first_value(
                        row,
                        "ba",
                        "avg",
                    )
                ),

            "OBP":
                clean_number(
                    first_value(
                        row,
                        "obp",
                    )
                ),

            "SLG":
                clean_number(
                    first_value(
                        row,
                        "slg",
                    )
                ),

            "OPS":
                clean_number(
                    first_value(
                        row,
                        "ops",
                    )
                ),

            "wOBA":
                clean_number(
                    first_value(
                        row,
                        "woba",
                    )
                ),

            "xBA":
                clean_number(
                    first_value(
                        row,
                        "xba",
                    )
                ),

            "xSLG":
                clean_number(
                    first_value(
                        row,
                        "xslg",
                    )
                ),

            "xwOBA":
                clean_number(
                    first_value(
                        row,
                        "xwoba",
                    )
                ),

            "EV":
                clean_number(
                    first_value(
                        row,
                        "exit_velocity_avg",
                        "launch_speed",
                        "ev",
                    )
                ),

            "Barrel%":
                clean_number(
                    first_value(
                        row,
                        "barrel_batted_rate",
                        "barrel_percent",
                        "brl_percent",
                    )
                ),

            "HardHit%":
                clean_number(
                    first_value(
                        row,
                        "hard_hit_percent",
                    )
                ),

            "K%":
                clean_number(
                    first_value(
                        row,
                        "k_percent",
                    )
                ),

            "BB%":
                clean_number(
                    first_value(
                        row,
                        "bb_percent",
                    )
                ),

            "Whiff%":
                clean_number(
                    first_value(
                        row,
                        "whiff_percent",
                    )
                ),

            "Chase%":
                clean_number(
                    first_value(
                        row,
                        "chase_percent",
                    )
                ),

            "Sprint Speed":
                clean_number(
                    first_value(
                        row,
                        "sprint_speed",
                    )
                ),

            "OAA":
                clean_number(
                    first_value(
                        row,
                        "oaa",
                    )
                ),
        }

    else:

        stats = {

            "IP":
                clean_number(
                    first_value(
                        row,
                        "ip",
                    )
                ),

            "ERA":
                clean_number(
                    first_value(
                        row,
                        "era",
                    )
                ),

            "WHIP":
                clean_number(
                    first_value(
                        row,
                        "whip",
                    )
                ),

            "W":
                clean_number(
                    first_value(
                        row,
                        "w",
                    )
                ),

            "L":
                clean_number(
                    first_value(
                        row,
                        "l",
                    )
                ),

            "SV":
                clean_number(
                    first_value(
                        row,
                        "sv",
                        "saves",
                    )
                ),

            "SO":
                clean_number(
                    first_value(
                        row,
                        "so",
                        "k",
                    )
                ),

            "BB":
                clean_number(
                    first_value(
                        row,
                        "bb",
                    )
                ),

            "HR":
                clean_number(
                    first_value(
                        row,
                        "hr",
                    )
                ),

            "K%":
                clean_number(
                    first_value(
                        row,
                        "k_percent",
                    )
                ),

            "BB%":
                clean_number(
                    first_value(
                        row,
                        "bb_percent",
                    )
                ),

            "K-BB%":
                clean_number(
                    first_value(
                        row,
                        "k_minus_bb_percent",
                        "k_bb_percent",
                    )
                ),

            "xERA":
                clean_number(
                    first_value(
                        row,
                        "xera",
                    )
                ),

            "xBA":
                clean_number(
                    first_value(
                        row,
                        "xba",
                    )
                ),

            "xSLG":
                clean_number(
                    first_value(
                        row,
                        "xslg",
                    )
                ),

            "xwOBA":
                clean_number(
                    first_value(
                        row,
                        "xwoba",
                    )
                ),

            "EV":
                clean_number(
                    first_value(
                        row,
                        "exit_velocity_avg",
                        "ev",
                    )
                ),

            "HardHit%":
                clean_number(
                    first_value(
                        row,
                        "hard_hit_percent",
                    )
                ),

            "Barrel%":
                clean_number(
                    first_value(
                        row,
                        "barrel_batted_rate",
                        "barrel_percent",
                    )
                ),

            "Whiff%":
                clean_number(
                    first_value(
                        row,
                        "whiff_percent",
                    )
                ),

            "CSW%":
                clean_number(
                    first_value(
                        row,
                        "csw_percent",
                    )
                ),
        }

    return {
        "playerId":
            player_id,

        "name":
            name,

        "type":
            player_type,

        "season":
            SEASON,

        "stats":
            stats,
    }


# =========================================================
# BUILD
# =========================================================

def build_stats():

    players_data = load_json(
        PLAYERS_FILE
    )

    players = players_data.get(
        "players",
        [],
    )

    roster_ids = {
        int(player["id"])
        for player in players
        if player.get("id")
    }

    print(
        f"Roster contains {len(roster_ids)} players."
    )

    batter_selections = [
        "pa",
        "ab",
        "h",
        "home_run",
        "rbi",
        "bb",
        "k",
        "sb",
        "ba",
        "obp",
        "slg",
        "ops",
        "woba",
        "xba",
        "xslg",
        "xwoba",
        "exit_velocity_avg",
        "barrel_batted_rate",
        "hard_hit_percent",
        "k_percent",
        "bb_percent",
        "whiff_percent",
        "chase_percent",
        "sprint_speed",
        "oaa",
    ]

    pitcher_selections = [
        "ip",
        "era",
        "whip",
        "w",
        "l",
        "sv",
        "so",
        "bb",
        "hr",
        "k_percent",
        "bb_percent",
        "k_minus_bb_percent",
        "xera",
        "xba",
        "xslg",
        "xwoba",
        "exit_velocity_avg",
        "hard_hit_percent",
        "barrel_batted_rate",
        "whiff_percent",
        "csw_percent",
    ]

    all_stats = {}

    # -----------------------------------------------------
    # BATTERS
    # -----------------------------------------------------

    try:

        batter_rows = fetch_savant(
            "batter",
            batter_selections,
        )

        for row in batter_rows:

            player = normalize_row(
                row,
                "batter",
            )

            if not player:
                continue

            if (
                player["playerId"]
                not in roster_ids
            ):
                continue

            all_stats[
                player["playerId"]
            ] = player

    except Exception as error:

        print(
            "Batter download failed:",
            error,
        )

    # -----------------------------------------------------
    # PITCHERS
    # -----------------------------------------------------

    try:

        pitcher_rows = fetch_savant(
            "pitcher",
            pitcher_selections,
        )

        for row in pitcher_rows:

            player = normalize_row(
                row,
                "pitcher",
            )

            if not player:
                continue

            if (
                player["playerId"]
                not in roster_ids
            ):
                continue

            all_stats[
                player["playerId"]
            ] = player

    except Exception as error:

        print(
            "Pitcher download failed:",
            error,
        )

    # -----------------------------------------------------
    # ENSURE ALL ROSTER PLAYERS EXIST
    # -----------------------------------------------------

    for roster_player in players:

        try:

            player_id = int(
                roster_player["id"]
            )

        except Exception:
            continue

        if player_id not in all_stats:

            all_stats[player_id] = {

                "playerId":
                    player_id,

                "name":
                    roster_player.get(
                        "name",
                        "",
                    ),

                "type":
                    (
                        "pitcher"
                        if roster_player.get(
                            "group"
                        ) == "Pitcher"
                        else "batter"
                    ),

                "season":
                    SEASON,

                "stats":
                    {},
            }

    # -----------------------------------------------------
    # SORT
    # -----------------------------------------------------

    result_players = []

    for player in players:

        try:

            player_id = int(
                player["id"]
            )

        except Exception:
            continue

        stats = all_stats.get(
            player_id
        )

        if not stats:
            continue

        # Preserve roster identity.
        stats["name"] = player.get(
            "name",
            stats.get("name", ""),
        )

        stats["number"] = player.get(
            "number",
            "",
        )

        stats["group"] = player.get(
            "group",
            "",
        )

        stats["position"] = player.get(
            "position",
            "",
        )

        result_players.append(
            stats
        )

    # -----------------------------------------------------
    # OUTPUT
    # -----------------------------------------------------

    return {
        "updatedAt":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "source":
            "Baseball Savant",

        "season":
            SEASON,

        "team": {
            "id":
                TEAM_ID,

            "name":
                "Philadelphia Phillies",

            "abbreviation":
                TEAM_ABBR,
        },

        "players":
            result_players,
    }


# =========================================================
# SAVE
# =========================================================

def save_result(data):

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print(
        f"Saved {len(data['players'])} player records."
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "=========================================="
    )

    print(
        "Phillies Baseball Savant Stats Updater"
    )

    print(
        "=========================================="
    )

    print(
        f"Season: {SEASON}"
    )

    data = build_stats()

    if not data.get("players"):

        raise RuntimeError(
            "No player statistics were generated."
        )

    save_result(
        data
    )

    print()
    print(
        "Savant stats update completed successfully."
    )


if __name__ == "__main__":
    main()
