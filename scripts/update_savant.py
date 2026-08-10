import csv
import io
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone


# =========================================================
# CONFIG
# =========================================================

ROSTER_FILE = "roster.json"
OUTPUT_FILE = "savant.json"

TEAM = "PHI"
SEASON = datetime.now(timezone.utc).year

BASE_URL = (
    "https://baseballsavant.mlb.com/leaderboard/custom.csv"
)

USER_AGENT = (
    "Mozilla/5.0 "
    "(Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/131.0 Safari/537.36"
)


# =========================================================
# HTTP
# =========================================================

def download_csv(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/csv,*/*",
            "Referer": "https://baseballsavant.mlb.com/",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=120,
    ) as response:

        data = response.read()

    return data.decode(
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
# CSV FIELD
# =========================================================

def get_field(row, *names):

    normalized = {}

    for key, value in row.items():

        if key is None:
            continue

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
            "-",
        ):
            return value

    return None


# =========================================================
# NUMBER
# =========================================================

def to_number(value):

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
        number = float(value)

        if number.is_integer():
            return int(number)

        return number

    except ValueError:
        return value


# =========================================================
# PLAYER ID
# =========================================================

def get_player_id(row):

    value = get_field(
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

    except (
        ValueError,
        TypeError,
    ):
        return None


# =========================================================
# SAVANT URL
# =========================================================

def make_url(
    player_type,
    selections,
):

    params = [
        ("year", str(SEASON)),
        ("type", player_type),
        ("filter", f"team={TEAM}"),
        ("min", "q"),
        (
            "selections",
            ",".join(selections),
        ),
        ("chart", "false"),
        ("x", "pa"),
        ("y", "pa"),
        ("r", "no"),
        ("chartType", "beeswarm"),
        ("sort", "pa"),
        ("sortDir", "desc"),
    ]

    return (
        BASE_URL
        + "?"
        + urllib.parse.urlencode(params)
    )


# =========================================================
# FETCH
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
        "Downloading Savant:",
        player_type,
    )

    print(url)

    text = download_csv(url)

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
# BATTER
# =========================================================

def parse_batter(row):

    player_id = get_player_id(row)

    if player_id is None:
        return None

    return {
        "player_id": player_id,

        "player_name": get_field(
            row,
            "last_name, first_name",
            "player_name",
            "player",
        ),

        "year": SEASON,

        "stats": {

            # BASIC
            "g": to_number(
                get_field(row, "g")
            ),

            "ab": to_number(
                get_field(row, "ab")
            ),

            "pa": to_number(
                get_field(row, "pa")
            ),

            "h": to_number(
                get_field(row, "h")
            ),

            "1b": to_number(
                get_field(row, "1b")
            ),

            "2b": to_number(
                get_field(row, "2b")
            ),

            "3b": to_number(
                get_field(row, "3b")
            ),

            "hr": to_number(
                get_field(row, "hr")
            ),

            "rbi": to_number(
                get_field(row, "rbi")
            ),

            "bb": to_number(
                get_field(row, "bb")
            ),

            "so": to_number(
                get_field(
                    row,
                    "so",
                    "k",
                )
            ),

            "sb": to_number(
                get_field(row, "sb")
            ),

            "cs": to_number(
                get_field(row, "cs")
            ),

            "avg": to_number(
                get_field(
                    row,
                    "avg",
                    "ba",
                )
            ),

            "obp": to_number(
                get_field(row, "obp")
            ),

            "slg": to_number(
                get_field(row, "slg")
            ),

            "ops": to_number(
                get_field(row, "ops")
            ),

            "iso": to_number(
                get_field(row, "iso")
            ),

            "babip": to_number(
                get_field(row, "babip")
            ),

            # STATCAST
            "xba": to_number(
                get_field(row, "xba")
            ),

            "xslg": to_number(
                get_field(row, "xslg")
            ),

            "xwoba": to_number(
                get_field(row, "xwoba")
            ),

            "xobp": to_number(
                get_field(row, "xobp")
            ),

            "xiso": to_number(
                get_field(row, "xiso")
            ),

            "woba": to_number(
                get_field(row, "woba")
            ),

            "wobacon": to_number(
                get_field(row, "wobacon")
            ),

            "xwobacon": to_number(
                get_field(row, "xwobacon")
            ),

            # CONTACT
            "exit_velocity": to_number(
                get_field(
                    row,
                    "exit_velocity_avg",
                )
            ),

            "max_ev": to_number(
                get_field(
                    row,
                    "exit_velocity_max",
                    "max_exit_velocity",
                )
            ),

            "launch_angle": to_number(
                get_field(
                    row,
                    "launch_angle_avg",
                )
            ),

            "barrels": to_number(
                get_field(
                    row,
                    "barrels",
                    "brl",
                )
            ),

            "barrel_percent": to_number(
                get_field(
                    row,
                    "barrel_batted_rate",
                )
            ),

            "hard_hit_percent": to_number(
                get_field(
                    row,
                    "hard_hit_percent",
                )
            ),

            "whiff_percent": to_number(
                get_field(
                    row,
                    "whiff_percent",
                )
            ),

            "sprint_speed": to_number(
                get_field(
                    row,
                    "sprint_speed",
                )
            ),

            "oaa": to_number(
                get_field(
                    row,
                    "oaa",
                )
            ),
        },
    }


# =========================================================
# PITCHER
# =========================================================

def parse_pitcher(row):

    player_id = get_player_id(row)

    if player_id is None:
        return None

    return {
        "player_id": player_id,

        "player_name": get_field(
            row,
            "last_name, first_name",
            "player_name",
            "player",
        ),

        "year": SEASON,

        "stats": {

            # BASIC
            "g": to_number(
                get_field(row, "g")
            ),

            "gs": to_number(
                get_field(row, "gs")
            ),

            "ip": to_number(
                get_field(row, "ip")
            ),

            "bf": to_number(
                get_field(row, "bf")
            ),

            "w": to_number(
                get_field(row, "w")
            ),

            "l": to_number(
                get_field(row, "l")
            ),

            "sv": to_number(
                get_field(
                    row,
                    "s",
                    "sv",
                    "saves",
                )
            ),

            "h": to_number(
                get_field(row, "h")
            ),

            "er": to_number(
                get_field(row, "er")
            ),

            "hr": to_number(
                get_field(row, "hr")
            ),

            "bb": to_number(
                get_field(row, "bb")
            ),

            "so": to_number(
                get_field(
                    row,
                    "so",
                    "k",
                )
            ),

            "era": to_number(
                get_field(row, "era")
            ),

            "whip": to_number(
                get_field(row, "whip")
            ),

            "baa": to_number(
                get_field(row, "baa")
            ),

            # STATCAST
            "xba": to_number(
                get_field(row, "xba")
            ),

            "xslg": to_number(
                get_field(row, "xslg")
            ),

            "xwoba": to_number(
                get_field(row, "xwoba")
            ),

            "xobp": to_number(
                get_field(row, "xobp")
            ),

            "xiso": to_number(
                get_field(row, "xiso")
            ),

            "woba": to_number(
                get_field(row, "woba")
            ),

            # CONTACT ALLOWED
            "exit_velocity": to_number(
                get_field(
                    row,
                    "exit_velocity_avg",
                )
            ),

            "max_ev": to_number(
                get_field(
                    row,
                    "exit_velocity_max",
                    "max_exit_velocity",
                )
            ),

            "launch_angle": to_number(
                get_field(
                    row,
                    "launch_angle_avg",
                )
            ),

            "barrels": to_number(
                get_field(
                    row,
                    "barrels",
                    "brl",
                )
            ),

            "barrel_percent": to_number(
                get_field(
                    row,
                    "barrel_batted_rate",
                )
            ),

            "hard_hit_percent": to_number(
                get_field(
                    row,
                    "hard_hit_percent",
                )
            ),

            "whiff_percent": to_number(
                get_field(
                    row,
                    "whiff_percent",
                )
            ),

            "k_percent": to_number(
                get_field(
                    row,
                    "k_percent",
                )
            ),

            "bb_percent": to_number(
                get_field(
                    row,
                    "bb_percent",
                )
            ),

            "xera": to_number(
                get_field(
                    row,
                    "xera",
                )
            ),
        },
    }


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "========================================"
    )

    print(
        "PHILLIES SAVANT UPDATE"
    )

    print(
        "========================================"
    )

    # -----------------------------------------------------
    # ROSTER
    # -----------------------------------------------------

    roster_data = load_json(
        ROSTER_FILE
    )

    # roster.json の構造に対応
    if isinstance(
        roster_data,
        dict
    ):

        roster_players = (
            roster_data.get(
                "players",
                []
            )
        )

    elif isinstance(
        roster_data,
        list
    ):

        roster_players = roster_data

    else:

        raise RuntimeError(
            "roster.json の形式を認識できません。"
        )

    roster_ids = set()

    for player in roster_players:

        value = (
            player.get("id")
            or player.get("player_id")
            or player.get("playerId")
        )

        if value is None:
            continue

        try:

            roster_ids.add(
                int(value)
            )

        except (
            ValueError,
            TypeError,
        ):

            pass

    print(
        "Roster IDs:",
        len(roster_ids),
    )

    # -----------------------------------------------------
    # BATTER SELECTIONS
    # -----------------------------------------------------

    batter_selections = [

        # Standard
        "g",
        "ab",
        "pa",
        "h",
        "1b",
        "2b",
        "3b",
        "hr",
        "so",
        "bb",
        "k_percent",
        "bb_percent",
        "avg",
        "slg",
        "obp",
        "ops",
        "iso",
        "babip",
        "rbi",
        "sb",
        "cs",

        # Statcast
        "xba",
        "xslg",
        "woba",
        "xwoba",
        "xobp",
        "xiso",
        "wobacon",
        "xwobacon",

        # Contact
        "exit_velocity_avg",
        "exit_velocity_max",
        "launch_angle_avg",
        "barrels",
        "barrel_batted_rate",
        "hard_hit_percent",

        # Other
        "whiff_percent",
        "sprint_speed",
        "oaa",
    ]

    # -----------------------------------------------------
    # PITCHER SELECTIONS
    # -----------------------------------------------------

    pitcher_selections = [

        # Standard
        "g",
        "gs",
        "ip",
        "bf",
        "h",
        "hr",
        "so",
        "bb",
        "era",
        "baa",
        "w",
        "l",
        "s",
        "er",
        "whip",

        # Statcast
        "xba",
        "xslg",
        "woba",
        "xwoba",
        "xobp",
        "xiso",

        # Contact
        "exit_velocity_avg",
        "exit_velocity_max",
        "launch_angle_avg",
        "barrels",
        "barrel_batted_rate",
        "hard_hit_percent",

        # Other
        "whiff_percent",
        "k_percent",
        "bb_percent",
        "xera",
    ]

    batters = []
    pitchers = []

    # -----------------------------------------------------
    # BATTERS
    # -----------------------------------------------------

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

            if (
                not roster_ids
                or parsed["player_id"]
                in roster_ids
            ):

                batters.append(
                    parsed
                )

    except Exception as error:

        print(
            "BATTER ERROR:",
            repr(error),
        )

    # -----------------------------------------------------
    # PITCHERS
    # -----------------------------------------------------

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

            if (
                not roster_ids
                or parsed["player_id"]
                in roster_ids
            ):

                pitchers.append(
                    parsed
                )

    except Exception as error:

        print(
            "PITCHER ERROR:",
            repr(error),
        )

    # -----------------------------------------------------
    # OUTPUT
    # -----------------------------------------------------

    output = {

        "team":
            "Philadelphia Phillies",

        "teamAbbreviation":
            "PHI",

        "season":
            SEASON,

        "source":
            "Baseball Savant",

        "sourceUrl":
            "https://baseballsavant.mlb.com/",

        "updatedAt":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "batters":
            batters,

        "pitchers":
            pitchers,
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
        "========================================"
    )

    print(
        "Savant update completed."
    )

    print(
        "Batters:",
        len(batters),
    )

    print(
        "Pitchers:",
        len(pitchers),
    )

    print(
        "Output:",
        OUTPUT_FILE,
    )

    print(
        "========================================"
    )


if __name__ == "__main__":
    main()
