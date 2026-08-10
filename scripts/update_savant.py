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
# JSON
# =========================================================

def load_json(path):
    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


# =========================================================
# HTTP
# =========================================================

def download_csv(url):

    print("")
    print("Downloading Baseball Savant:")
    print(url)
    print("")

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/csv,text/plain,*/*",
            "Referer": "https://baseballsavant.mlb.com/",
        }
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=120
        ) as response:

            data = response.read()

    except Exception as error:

        raise RuntimeError(
            "Baseball Savantへの接続に失敗しました: "
            + repr(error)
        )

    if not data:
        raise RuntimeError(
            "Baseball Savantから空のレスポンスが返されました。"
        )

    text = data.decode(
        "utf-8-sig",
        errors="replace"
    )

    if not text.strip():
        raise RuntimeError(
            "Baseball Savantから空のCSVが返されました。"
        )

    return text


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

        key = str(name).strip().lower()

        if key not in normalized:
            continue

        value = normalized[key]

        if value is None:
            continue

        value = str(value).strip()

        if value in (
            "",
            "-",
            "—",
            "N/A",
            "NA",
            "null",
            "NULL",
        ):
            continue

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
        "NULL",
    ):
        return None

    value = value.replace("%", "")

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
        "id"
    )

    if value is None:
        return None

    try:
        return int(float(value))
    except (
        ValueError,
        TypeError
    ):
        return None


# =========================================================
# PLAYERS.JSON
# =========================================================

def load_player_ids():

    data = load_json(
        PLAYERS_FILE
    )

    if isinstance(data, dict):

        players = data.get(
            "players",
            []
        )

    elif isinstance(data, list):

        players = data

    else:

        raise RuntimeError(
            "players.jsonの形式が正しくありません。"
        )

    if not isinstance(players, list):

        raise RuntimeError(
            "players.jsonのplayersが配列ではありません。"
        )

    player_ids = set()

    for player in players:

        if not isinstance(player, dict):
            continue

        value = (
            player.get("id")
            if player.get("id") is not None
            else player.get("player_id")
        )

        if value is None:
            value = player.get("playerId")

        if value is None:
            continue

        try:

            player_ids.add(
                int(value)
            )

        except (
            ValueError,
            TypeError
        ):

            continue

    if not player_ids:

        raise RuntimeError(
            "players.jsonから選手IDを取得できませんでした。"
        )

    print(
        "players.json players:",
        len(players)
    )

    print(
        "players.json player IDs:",
        len(player_ids)
    )

    return player_ids


# =========================================================
# SAVANT URL
# =========================================================

def make_url(
    player_type,
    selections
):

    params = [
        ("year", str(SEASON)),
        ("type", player_type),
        ("filter", "team=" + TEAM),
        ("min", "q"),
        (
            "selections",
            ",".join(selections)
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
        + urllib.parse.urlencode(
            params
        )
    )


# =========================================================
# FETCH SAVANT
# =========================================================

def fetch_savant(
    player_type,
    selections
):

    url = make_url(
        player_type,
        selections
    )

    text = download_csv(
        url
    )

    reader = csv.DictReader(
        io.StringIO(text)
    )

    if reader.fieldnames is None:

        raise RuntimeError(
            "Baseball SavantのCSVヘッダーを取得できませんでした。"
        )

    print(
        "CSV columns:",
        ", ".join(reader.fieldnames)
    )

    rows = list(reader)

    print(
        player_type,
        "rows:",
        len(rows)
    )

    if not rows:

        raise RuntimeError(
            "Baseball Savantから"
            + player_type
            + "データを取得できませんでした。"
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
                "player"
            ),

        "year":
            SEASON,

        "stats": {

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

            "rbi":
                to_number(
                    get_field(row, "rbi")
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
                        "k"
                    )
                ),

            "sb":
                to_number(
                    get_field(row, "sb")
                ),

            "cs":
                to_number(
                    get_field(row, "cs")
                ),

            "avg":
                to_number(
                    get_field(
                        row,
                        "avg",
                        "ba"
                    )
                ),

            "obp":
                to_number(
                    get_field(row, "obp")
                ),

            "slg":
                to_number(
                    get_field(row, "slg")
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

            "woba":
                to_number(
                    get_field(row, "woba")
                ),

            "xba":
                to_number(
                    get_field(row, "xba")
                ),

            "xslg":
                to_number(
                    get_field(row, "xslg")
                ),

            "xwoba":
                to_number(
                    get_field(row, "xwoba")
                ),

            "xobp":
                to_number(
                    get_field(row, "xobp")
                ),

            "xiso":
                to_number(
                    get_field(row, "xiso")
                ),

            "wobacon":
                to_number(
                    get_field(row, "wobacon")
                ),

            "xwobacon":
                to_number(
                    get_field(row, "xwobacon")
                ),

            "exit_velocity":
                to_number(
                    get_field(
                        row,
                        "exit_velocity_avg"
                    )
                ),

            "max_ev":
                to_number(
                    get_field(
                        row,
                        "exit_velocity_max",
                        "max_exit_velocity"
                    )
                ),

            "launch_angle":
                to_number(
                    get_field(
                        row,
                        "launch_angle_avg"
                    )
                ),

            "barrels":
                to_number(
                    get_field(
                        row,
                        "barrels",
                        "brl"
                    )
                ),

            "barrel_percent":
                to_number(
                    get_field(
                        row,
                        "barrel_batted_rate"
                    )
                ),

            "hard_hit_percent":
                to_number(
                    get_field(
                        row,
                        "hard_hit_percent"
                    )
                ),

            "whiff_percent":
                to_number(
                    get_field(
                        row,
                        "whiff_percent"
                    )
                ),

            "sprint_speed":
                to_number(
                    get_field(
                        row,
                        "sprint_speed"
                    )
                ),

            "oaa":
                to_number(
                    get_field(
                        row,
                        "oaa"
                    )
                ),
        }
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
                "player"
            ),

        "year":
            SEASON,

        "stats": {

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
                        "saves"
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
                        "k"
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

            "woba":
                to_number(
                    get_field(row, "woba")
                ),

            "xba":
                to_number(
                    get_field(row, "xba")
                ),

            "xslg":
                to_number(
                    get_field(row, "xslg")
                ),

            "xwoba":
                to_number(
                    get_field(row, "xwoba")
                ),

            "xobp":
                to_number(
                    get_field(row, "xobp")
                ),

            "xiso":
                to_number(
                    get_field(row, "xiso")
                ),

            "exit_velocity":
                to_number(
                    get_field(
                        row,
                        "exit_velocity_avg"
                    )
                ),

            "max_ev":
                to_number(
                    get_field(
                        row,
                        "exit_velocity_max",
                        "max_exit_velocity"
                    )
                ),

            "launch_angle":
                to_number(
                    get_field(
                        row,
                        "launch_angle_avg"
                    )
                ),

            "barrels":
                to_number(
                    get_field(
                        row,
                        "barrels",
                        "brl"
                    )
                ),

            "barrel_percent":
                to_number(
                    get_field(
                        row,
                        "barrel_batted_rate"
                    )
                ),

            "hard_hit_percent":
                to_number(
                    get_field(
                        row,
                        "hard_hit_percent"
                    )
                ),

            "whiff_percent":
                to_number(
                    get_field(
                        row,
                        "whiff_percent"
                    )
                ),

            "k_percent":
                to_number(
                    get_field(
                        row,
                        "k_percent"
                    )
                ),

            "bb_percent":
                to_number(
                    get_field(
                        row,
                        "bb_percent"
                    )
                ),

            "xera":
                to_number(
                    get_field(
                        row,
                        "xera"
                    )
                ),
        }
    }


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 60)
    print("PHILADELPHIA PHILLIES")
    print("BASEBALL SAVANT STATISTICS UPDATE")
    print("=" * 60)

    # -----------------------------------------------------
    # players.json
    # -----------------------------------------------------

    player_ids = load_player_ids()

    # -----------------------------------------------------
    # Savant selections
    # -----------------------------------------------------

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
        "bb",
        "so",
        "sb",
        "cs",

        "avg",
        "obp",
        "slg",
        "ops",
        "iso",
        "babip",

        "woba",
        "xba",
        "xslg",
        "xwoba",
        "xobp",
        "xiso",
        "wobacon",
        "xwobacon",

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

        "woba",
        "xba",
        "xslg",
        "xwoba",
        "xobp",
        "xiso",

        "exit_velocity_avg",
        "exit_velocity_max",
        "launch_angle_avg",
        "barrels",
        "barrel_batted_rate",
        "hard_hit_percent",
        "whiff_percent",

        "k_percent",
        "bb_percent",

        "xera",
    ]

    # -----------------------------------------------------
    # Download
    # -----------------------------------------------------

    batter_rows = fetch_savant(
        "batter",
        batter_selections
    )

    pitcher_rows = fetch_savant(
        "pitcher",
        pitcher_selections
    )

    # -----------------------------------------------------
    # Parse batters
    # -----------------------------------------------------

    batters = []

    for row in batter_rows:

        player = parse_batter(row)

        if player is None:
            continue

        if player["player_id"] in player_ids:

            batters.append(
                player
            )

    # -----------------------------------------------------
    # Parse pitchers
    # -----------------------------------------------------

    pitchers = []

    for row in pitcher_rows:

        player = parse_pitcher(row)

        if player is None:
            continue

        if player["player_id"] in player_ids:

            pitchers.append(
                player
            )

    # -----------------------------------------------------
    # Validation
    # -----------------------------------------------------

    print("")
    print("Matched Phillies batters:", len(batters))
    print("Matched Phillies pitchers:", len(pitchers))

    if not batters and not pitchers:

        raise RuntimeError(
            "Baseball SavantからPhillies選手の成績を"
            "1件も照合できませんでした。"
            "savant.jsonは更新しません。"
        )

    # -----------------------------------------------------
    # Sort
    # -----------------------------------------------------

    batters.sort(
        key=lambda x: (
            x.get("player_name") or ""
        )
    )

    pitchers.sort(
        key=lambda x: (
            x.get("player_name") or ""
        )
    )

    # -----------------------------------------------------
    # Output
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

    # -----------------------------------------------------
    # Write savant.json
    # -----------------------------------------------------

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=2
        )

        f.write("\n")

    # -----------------------------------------------------
    # Finished
    # -----------------------------------------------------

    print("")
    print("=" * 60)
    print("SAVANT UPDATE SUCCESS")
    print("=" * 60)
    print("Output:", OUTPUT_FILE)
    print("Batters:", len(batters))
    print("Pitchers:", len(pitchers))
    print("Updated:", output["updatedAt"])
    print("=" * 60)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()
