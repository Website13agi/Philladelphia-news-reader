import csv
import io
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone


# =========================================================
# CONFIG
# =========================================================

TEAM_ABBR = "PHI"
SEASON = datetime.now(timezone.utc).year

PLAYERS_FILE = "players.json"
OUTPUT_FILE = "player_stats.json"

SAVANT_BASE = (
    "https://baseballsavant.mlb.com/"
    "leaderboard/custom.csv"
)

USER_AGENT = (
    "Mozilla/5.0 "
    "(Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)


# =========================================================
# HTTP
# =========================================================

def download_csv(url):

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/csv,text/plain,*/*",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=90,
    ) as response:

        raw = response.read()

    return raw.decode(
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

def number(value):

    if value is None:
        return None

    value = str(value).strip()

    if value in (
        "",
        "-",
        "—",
        "N/A",
        "NA",
        "null",
    ):
        return None

    value = value.replace(
        "%",
        "",
    )

    try:

        result = float(value)

        if result.is_integer():

            return int(result)

        return result

    except ValueError:

        return value


# =========================================================
# FIELD
# =========================================================

def field(row, *names):

    normalized = {
        str(key).strip().lower():
        value

        for key, value
        in row.items()
    }

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
# SAVANT URL
# =========================================================

def make_url(
    player_type,
    selections,
):

    params = {

        "year":
            str(SEASON),

        "type":
            player_type,

        "filter":
            f"team={TEAM_ABBR}",

        "min":
            "q",

        "selections":
            ",".join(selections),

        "chart":
            "false",

        "x":
            "pa",

        "y":
            "pa",

        "r":
            "no",

        "chartType":
            "beeswarm",

        "sort":
            "pa",

        "sortDir":
            "desc",
    }

    return (
        SAVANT_BASE
        + "?"
        + urllib.parse.urlencode(
            params
        )
    )


# =========================================================
# DOWNLOAD SAVANT
# =========================================================

def fetch(
    player_type,
    selections,
):

    url = make_url(
        player_type,
        selections,
    )

    print()
    print(
        "Downloading:",
        player_type,
    )

    print(url)

    text = download_csv(
        url
    )

    reader = csv.DictReader(
        io.StringIO(text)
    )

    rows = list(reader)

    print(
        "Rows:",
        len(rows),
    )

    return rows


# =========================================================
# PLAYER ID
# =========================================================

def player_id(row):

    value = field(
        row,
        "player_id",
        "playerid",
    )

    if value is None:
        return None

    try:

        return int(
            float(value)
        )

    except ValueError:

        return None


# =========================================================
# BATTER
# =========================================================

def parse_batter(row):

    pid = player_id(row)

    if pid is None:
        return None

    stats = {

        # BASIC

        "G":
            number(field(row, "g")),

        "AB":
            number(field(row, "ab")),

        "PA":
            number(field(row, "pa")),

        "H":
            number(field(row, "h")),

        "1B":
            number(field(row, "1b")),

        "2B":
            number(field(row, "2b")),

        "3B":
            number(field(row, "3b")),

        "HR":
            number(field(row, "hr")),

        "RBI":
            number(field(row, "rbi")),

        "R":
            number(field(row, "r")),

        "BB":
            number(field(row, "bb")),

        "SO":
            number(field(row, "so")),

        "HBP":
            number(field(row, "hbp")),

        "SB":
            number(field(row, "sb")),

        "CS":
            number(field(row, "cs")),

        "AVG":
            number(field(row, "avg")),

        "OBP":
            number(field(row, "obp")),

        "SLG":
            number(field(row, "slg")),

        "OPS":
            number(field(row, "ops")),

        "ISO":
            number(field(row, "iso")),

        "BABIP":
            number(field(row, "babip")),

        # SAVANT / STATCAST

        "xBA":
            number(field(row, "xba")),

        "xSLG":
            number(field(row, "xslg")),

        "xwOBA":
            number(field(row, "xwoba")),

        "xOBP":
            number(field(row, "xobp")),

        "xISO":
            number(field(row, "xiso")),

        "wOBA":
            number(field(row, "woba")),

        "wOBAcon":
            number(field(row, "wobacon")),

        "xwOBAcon":
            number(field(row, "xwobacon")),

        "EV":
            number(
                field(
                    row,
                    "exit_velocity_avg",
                )
            ),

        "Launch Angle":
            number(
                field(
                    row,
                    "launch_angle_avg",
                )
            ),

        "Barrel%":
            number(
                field(
                    row,
                    "barrel_batted_rate",
                )
            ),

        "Hard-Hit%":
            number(
                field(
                    row,
                    "hard_hit_percent",
                )
            ),

        "K%":
            number(
                field(
                    row,
                    "k_percent",
                )
            ),

        "BB%":
            number(
                field(
                    row,
                    "bb_percent",
                )
            ),

        "Whiff%":
            number(
                field(
                    row,
                    "whiff_percent",
                )
            ),

        "Chase%":
            number(
                field(
                    row,
                    "chase_percent",
                )
            ),

        "Sprint Speed":
            number(
                field(
                    row,
                    "sprint_speed",
                )
            ),

        "OAA":
            number(
                field(
                    row,
                    "oaa",
                )
            ),
    }

    return {
        "playerId": pid,
        "type": "batter",
        "stats": stats,
    }


# =========================================================
# PITCHER
# =========================================================

def parse_pitcher(row):

    pid = player_id(row)

    if pid is None:
        return None

    stats = {

        # BASIC

        "G":
            number(field(row, "g")),

        "GS":
            number(field(row, "gs")),

        "IP":
            number(field(row, "ip")),

        "W":
            number(field(row, "w")),

        "L":
            number(field(row, "l")),

        "SV":
            number(field(row, "sv")),

        "H":
            number(field(row, "h")),

        "ER":
            number(field(row, "er")),

        "HR":
            number(field(row, "hr")),

        "BB":
            number(field(row, "bb")),

        "SO":
            number(field(row, "so")),

        "ERA":
            number(field(row, "era")),

        "WHIP":
            number(field(row, "whip")),

        "K%":
            number(
                field(
                    row,
                    "k_percent",
                )
            ),

        "BB%":
            number(
                field(
                    row,
                    "bb_percent",
                )
            ),

        # SAVANT / STATCAST

        "xERA":
            number(
                field(
                    row,
                    "xera",
                )
            ),

        "xBA":
            number(
                field(
                    row,
                    "xba",
                )
            ),

        "xSLG":
            number(
                field(
                    row,
                    "xslg",
                )
            ),

        "xwOBA":
            number(
                field(
                    row,
                    "xwoba",
                )
            ),

        "xOBP":
            number(
                field(
                    row,
                    "xobp",
                )
            ),

        "EV":
            number(
                field(
                    row,
                    "exit_velocity_avg",
                )
            ),

        "Launch Angle":
            number(
                field(
                    row,
                    "launch_angle_avg",
                )
            ),

        "Barrel%":
            number(
                field(
                    row,
                    "barrel_batted_rate",
                )
            ),

        "Hard-Hit%":
            number(
                field(
                    row,
                    "hard_hit_percent",
                )
            ),

        "Whiff%":
            number(
                field(
                    row,
                    "whiff_percent",
                )
            ),

        "CSW%":
            number(
                field(
                    row,
                    "csw_percent",
                )
            ),

        "Spin Rate":
            number(
                field(
                    row,
                    "avg_spin_rate",
                    "spin_rate",
                )
            ),

        "Velocity":
            number(
                field(
                    row,
                    "velocity",
                    "release_speed",
                )
            ),

        "Extension":
            number(
                field(
                    row,
                    "release_extension",
                )
            ),
    }

    return {
        "playerId": pid,
        "type": "pitcher",
        "stats": stats,
    }


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
        "Season:",
        SEASON,
    )

    roster_data = load_json(
        PLAYERS_FILE
    )

    players = roster_data.get(
        "players",
        []
    )

    roster = {}

    for player in players:

        try:

            pid = int(
                player["id"]
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ):

            continue

        roster[pid] = player

    print(
        "Roster players:",
        len(roster),
    )

    # =====================================================
    # BATTER
    # =====================================================

    batter_selections = [

        "g",
        "ab",
        "pa",
        "h",
        "1b",
        "2b",
        "3b",
        "hr",
        "rbi",
        "r",
        "bb",
        "so",
        "hbp",
        "sb",
        "cs",

        "avg",
        "obp",
        "slg",
        "ops",
        "iso",
        "babip",

        "xba",
        "xslg",
        "xwoba",
        "xobp",
        "xiso",

        "woba",
        "wobacon",
        "xwobacon",

        "exit_velocity_avg",
        "launch_angle_avg",
        "barrel_batted_rate",
        "hard_hit_percent",

        "k_percent",
        "bb_percent",
        "whiff_percent",
        "chase_percent",

        "sprint_speed",
        "oaa",
    ]

    # =====================================================
    # PITCHER
    # =====================================================

    pitcher_selections = [

        "g",
        "gs",
        "ip",
        "w",
        "l",
        "sv",
        "h",
        "er",
        "hr",
        "bb",
        "so",

        "era",
        "whip",

        "k_percent",
        "bb_percent",

        "xera",
        "xba",
        "xslg",
        "xwoba",
        "xobp",

        "exit_velocity_avg",
        "launch_angle_avg",
        "barrel_batted_rate",
        "hard_hit_percent",

        "whiff_percent",
        "csw_percent",

        "avg_spin_rate",
        "velocity",
        "release_speed",
        "release_extension",
    ]

    records = {}

    # =====================================================
    # FETCH BATTERS
    # =====================================================

    try:

        rows = fetch(
            "batter",
            batter_selections,
        )

        for row in rows:

            parsed = parse_batter(
                row
            )

            if parsed is None:
                continue

            pid = parsed[
                "playerId"
            ]

            if pid in roster:

                records[pid] = parsed

    except Exception as error:

        print(
            "BATTER ERROR:",
            repr(error),
        )

    # =====================================================
    # FETCH PITCHERS
    # =====================================================

    try:

        rows = fetch(
            "pitcher",
            pitcher_selections,
        )

        for row in rows:

            parsed = parse_pitcher(
                row
            )

            if parsed is None:
                continue

            pid = parsed[
                "playerId"
            ]

            if pid in roster:

                records[pid] = parsed

    except Exception as error:

        print(
            "PITCHER ERROR:",
            repr(error),
        )

    # =====================================================
    # KEEP EVERY ROSTER PLAYER
    # =====================================================

    output_players = []

    for pid, player in roster.items():

        record = records.get(
            pid
        )

        if record is None:

            record = {

                "playerId":
                    pid,

                "type":
                    (
                        "pitcher"
                        if player.get(
                            "group"
                        ) == "Pitcher"
                        else "batter"
                    ),

                "stats": {},
            }

        record["name"] = player.get(
            "name",
            "",
        )

        record["number"] = player.get(
            "number",
            "",
        )

        record["position"] = player.get(
            "position",
            "",
        )

        record["group"] = player.get(
            "group",
            "",
        )

        output_players.append(
            record
        )

    # =====================================================
    # OUTPUT
    # =====================================================

    output = {

        "updatedAt":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "source":
            "Baseball Savant",

        "season":
            SEASON,

        "team":
            "PHI",

        "players":
            output_players,
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

    print()
    print(
        "=========================================="
    )

    print(
        "SUCCESS"
    )

    print(
        "Players written:",
        len(output_players),
    )

    print(
        "Output:",
        OUTPUT_FILE,
    )

    print(
        "=========================================="
    )


if __name__ == "__main__":

    main()
