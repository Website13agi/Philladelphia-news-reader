import csv
import io
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone


# =========================================================
# CONFIG
# =========================================================

PLAYERS_FILE = "players.json"
OUTPUT_FILE = "savant.json"

TEAM = "PHI"
SEASON = datetime.now(timezone.utc).year

BASE_URL = "https://baseballsavant.mlb.com/leaderboard/custom.csv"

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

    print("Downloading:")
    print(url)

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/csv,text/plain,*/*",
            "Referer": "https://baseballsavant.mlb.com/",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=120,
    ) as response:

        data = response.read()

    text = data.decode(
        "utf-8-sig",
        errors="replace",
    )

    if not text.strip():
        raise RuntimeError(
            "Baseball Savantから空のデータが返されました。"
        )

    return text


# =========================================================
# JSON
# =========================================================

def load_players():

    with open(
        PLAYERS_FILE,
        "r",
        encoding="utf-8",
    ) as f:

        data = json.load(f)

    if not isinstance(data, dict):
        raise RuntimeError(
            "players.jsonの形式が正しくありません。"
        )

    players = data.get(
        "players",
        []
    )

    if not isinstance(players, list):
        raise RuntimeError(
            "players.jsonのplayersが配列ではありません。"
        )

    return players


# =========================================================
# CSV
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

        key = str(name).strip().lower()

        if key in normalized:

            value = normalized[key]

            if value not in (
                None,
                "",
                "-",
                "—",
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
# URL
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
            f"team={TEAM}",

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
        BASE_URL
        + "?"
        + urllib.parse.urlencode(
            params
        )
    )


# =========================================================
# FETCH CSV
# =========================================================

def fetch(
    player_type,
    selections,
):

    url = make_url(
        player_type,
        selections,
    )

    text = download_csv(url)

    reader = csv.DictReader(
        io.StringIO(text)
    )

    rows = list(reader)

    if not rows:

        raise RuntimeError(
            f"Savantの{player_type}データを取得できませんでした。"
        )

    print(
        f"{player_type}: {len(rows)} players"
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

        "player_id":
            player_id,

        "player_name":
            get_field(
                row,
                "last_name, first_name",
                "player_name",
                "player",
            ),

        "year":
            SEASON,

        # -------------------------
        # BASIC
        # -------------------------

        "g":
            to_number(
                get_field(row, "g")
            ),

        "ab":
            to_number(
                get_field(row, "ab")
            ),

        "pa":
            to_number(
                get_field(row, "pa")
            ),

        "h":
            to_number(
                get_field(row, "h")
            ),

        "1b":
            to_number(
                get_field(row, "1b")
            ),

        "2b":
            to_number(
                get_field(row, "2b")
            ),

        "3b":
            to_number(
                get_field(row, "3b")
            ),

        "hr":
            to_number(
                get_field(row, "hr")
            ),

        "so":
            to_number(
                get_field(
                    row,
                    "so",
                    "k",
                )
            ),

        "bb":
            to_number(
                get_field(row, "bb")
            ),

        "k_percent":
            to_number(
                get_field(
                    row,
                    "k_percent",
                )
            ),

        "bb_percent":
            to_number(
                get_field(
                    row,
                    "bb_percent",
                )
            ),

        "avg":
            to_number(
                get_field(
                    row,
                    "avg",
                    "ba",
                )
            ),

        "slg":
            to_number(
                get_field(row, "slg")
            ),

        "obp":
            to_number(
                get_field(row, "obp")
            ),

        "ops":
            to_number(
                get_field(row, "ops")
            ),

        "iso":
            to_number(
                get_field(row, "iso")
            ),

        "babip":
            to_number(
                get_field(row, "babip")
            ),

        "rbi":
            to_number(
                get_field(row, "rbi")
            ),

        "sb":
            to_number(
                get_field(row, "sb")
            ),

        "cs":
            to_number(
                get_field(row, "cs")
            ),

        # -------------------------
        # SAVANT
        # -------------------------

        "xwoba":
            to_number(
                get_field(row, "xwoba")
            ),

        "xba":
            to_number(
                get_field(row, "xba")
            ),

        "xslg":
            to_number(
                get_field(row, "xslg")
            ),

        "xobp":
            to_number(
                get_field(row, "xobp")
            ),

        "xiso":
            to_number(
                get_field(row, "xiso")
            ),

        "woba":
            to_number(
                get_field(row, "woba")
            ),

        "exit_velocity":
            to_number(
                get_field(
                    row,
                    "exit_velocity_avg",
                )
            ),

        "max_ev":
            to_number(
                get_field(
                    row,
                    "exit_velocity_max",
                    "max_exit_velocity",
                )
            ),

        "launch_angle":
            to_number(
                get_field(
                    row,
                    "launch_angle_avg",
                )
            ),

        "barrels":
            to_number(
                get_field(
                    row,
                    "barrels",
                    "brl",
                )
            ),

        "barrel_percent":
            to_number(
                get_field(
                    row,
                    "barrel_batted_rate",
                )
            ),

        "hard_hit_percent":
            to_number(
                get_field(
                    row,
                    "hard_hit_percent",
                )
            ),

        "whiff_percent":
            to_number(
                get_field(
                    row,
                    "whiff_percent",
                )
            ),

        "sprint_speed":
            to_number(
                get_field(
                    row,
                    "sprint_speed",
                )
            ),

        "oaa":
            to_number(
                get_field(
                    row,
                    "oaa",
                )
            ),
    }


# =========================================================
# PITCHER
# =========================================================

def parse_pitcher(row):

    player_id = get_player_id(row)

    if player_id is None:
        return None

    return {

        "player_id":
            player_id,

        "player_name":
            get_field(
                row,
                "last_name, first_name",
                "player_name",
                "player",
            ),

        "year":
            SEASON,

        # -------------------------
        # BASIC
        # -------------------------

        "g":
            to_number(
                get_field(row, "g")
            ),

        "gs":
            to_number(
                get_field(row, "gs")
            ),

        "ip":
            to_number(
                get_field(row, "ip")
            ),

        "bf":
            to_number(
                get_field(row, "bf")
            ),

        "w":
            to_number(
                get_field(row, "w")
            ),

        "l":
            to_number(
                get_field(row, "l")
            ),

        "sv":
            to_number(
                get_field(
                    row,
                    "s",
                    "sv",
                    "saves",
                )
            ),

        "h":
            to_number(
                get_field(row, "h")
            ),

        "er":
            to_number(
                get_field(row, "er")
            ),

        "hr":
            to_number(
                get_field(row, "hr")
            ),

        "bb":
            to_number(
                get_field(row, "bb")
            ),

        "so":
            to_number(
                get_field(
                    row,
                    "so",
                    "k",
                )
            ),

        "era":
            to_number(
                get_field(row, "era")
            ),

        "whip":
            to_number(
                get_field(row, "whip")
            ),

        "baa":
            to_number(
                get_field(row, "baa")
            ),

        # -------------------------
        # SAVANT
        # -------------------------

        "xwoba":
            to_number(
                get_field(row, "xwoba")
            ),

        "xba":
            to_number(
                get_field(row, "xba")
            ),

        "xslg":
            to_number(
                get_field(row, "xslg")
            ),

        "xobp":
            to_number(
                get_field(row, "xobp")
            ),

        "xiso":
            to_number(
                get_field(row, "xiso")
            ),

        "woba":
            to_number(
                get_field(row, "woba")
            ),

        "exit_velocity":
            to_number(
                get_field(
                    row,
                    "exit_velocity_avg",
                )
            ),

        "max_ev":
            to_number(
                get_field(
                    row,
                    "exit_velocity_max",
                    "max_exit_velocity",
                )
            ),

        "launch_angle":
            to_number(
                get_field(
                    row,
                    "launch_angle_avg",
                )
            ),

        "barrels":
            to_number(
                get_field(
                    row,
                    "barrels",
                    "brl",
                )
            ),

        "barrel_percent":
            to_number(
                get_field(
                    row,
                    "barrel_batted_rate",
                )
            ),

        "hard_hit_percent":
            to_number(
                get_field(
                    row,
                    "hard_hit_percent",
                )
            ),

        "whiff_percent":
            to_number(
                get_field(
                    row,
                    "whiff_percent",
                )
            ),

        "k_percent":
            to_number(
                get_field(
                    row,
                    "k_percent",
                )
            ),

        "bb_percent":
            to_number(
                get_field(
                    row,
                    "bb_percent",
                )
            ),

        "xera":
            to_number(
                get_field(
                    row,
                    "xera",
                )
            ),

        "fb_velocity":
            to_number(
                get_field(
                    row,
                    "release_speed",
                    "fb_velocity",
                )
            ),

        "fb_spin":
            to_number(
                get_field(
                    row,
                    "release_spin_rate",
                    "avg_spin_rate",
                    "fb_spin",
                )
            ),
    }


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "========================================"
    )

    print(
        "PHILLIES BASEBALL SAVANT UPDATE"
    )

    print(
        "========================================"
    )

    # =====================================================
    # PLAYERS.JSON
    # =====================================================

    players = load_players()

    roster_ids = set()

    for player in players:

        player_id = player.get("id")

        if player_id is None:
            continue

        try:

            roster_ids.add(
                int(player_id)
            )

        except (
            ValueError,
            TypeError,
        ):

            continue

    print(
        "Players in players.json:",
        len(players),
    )

    print(
        "Player IDs:",
        len(roster_ids),
    )

    if not roster_ids:

        raise RuntimeError(
            "players.jsonから選手IDを取得できませんでした。"
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

        "woba",
        "xwoba",
        "xba",
        "xslg",
        "xobp",
        "xiso",

        "exit_velocity_avg",
        "exit_velocity_max",
        "launch_angle_avg",
        "barrels",
        "barrel_batted_rate",
        "hard_hit_percent",
        "whiff_percent",

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
        "bf",
        "w",
        "l",
        "s",
        "h",
        "er",
        "hr",
        "bb",
        "so",
        "era",
        "whip",
        "baa",

        "k_percent",
        "bb_percent",

        "woba",
        "xwoba",
        "xba",
        "xslg",
        "xobp",
        "xiso",

        "exit_velocity_avg",
        "exit_velocity_max",
        "launch_angle_avg",
        "barrels",
        "barrel_batted_rate",
        "hard_hit_percent",
        "whiff_percent",

        "xera",

        "release_speed",
        "release_spin_rate",
    ]

    # =====================================================
    # DOWNLOAD
    # =====================================================

    batter_rows = fetch(
        "batter",
        batter_selections,
    )

    pitcher_rows = fetch(
        "pitcher",
        pitcher_selections,
    )

    # =====================================================
    # PARSE
    # =====================================================

    batters = []

    for row in batter_rows:

        player = parse_batter(row)

        if player is None:
            continue

        if player["player_id"] not in roster_ids:
            continue

        batters.append(
            player
        )

    pitchers = []

    for row in pitcher_rows:

        player = parse_pitcher(row)

        if player is None:
            continue

        if player["player_id"] not in roster_ids:
            continue

        pitchers.append(
            player
        )

    # =====================================================
    # SORT
    # =====================================================

    batters.sort(
        key=lambda x: x["player_name"] or ""
    )

    pitchers.sort(
        key=lambda x: x["player_name"] or ""
    )

    # =====================================================
    # SAFETY CHECK
    # =====================================================

    if not batters and not pitchers:

        raise RuntimeError(
            "SavantからPhillies選手の成績を1人も取得できませんでした。"
        )

    print(
        "Batters:",
        len(batters),
    )

    print(
        "Pitchers:",
        len(pitchers),
    )

    # =====================================================
    # OUTPUT
    # =====================================================

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

    # =====================================================
    # WRITE savant.json
    # =====================================================

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print(
        "========================================"
    )

    print(
        "SUCCESS"
    )

    print(
        "Output:",
        OUTPUT_FILE,
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
        "========================================"
    )


if __name__ == "__main__":
    main()
