import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone


# =========================================================
# CONFIG
# =========================================================

TEAM_ID = 143
TEAM_ABBR = "PHI"
TEAM_NAME = "Philadelphia Phillies"

SEASON = datetime.now(timezone.utc).year

OUTPUT_FILE = "savant.json"
PLAYERS_FILE = "players.json"

BASE_URL = "https://statsapi.mlb.com/api/v1/stats"

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

def fetch_json(url):

    print()
    print("GET:")
    print(url)
    print()

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=120,
        ) as response:

            raw = response.read()

    except Exception as error:

        raise RuntimeError(
            "MLB公式Stats APIへの接続に失敗しました: "
            + repr(error)
        )

    if not raw:

        raise RuntimeError(
            "MLB公式Stats APIから空のレスポンスが返されました。"
        )

    try:

        return json.loads(
            raw.decode(
                "utf-8"
            )
        )

    except Exception as error:

        raise RuntimeError(
            "MLB公式Stats APIのJSONを解析できませんでした: "
            + repr(error)
        )


# =========================================================
# players.json
# =========================================================

def load_players():

    if not os.path.exists(
        PLAYERS_FILE
    ):

        raise RuntimeError(
            "players.jsonが見つかりません。"
        )

    with open(
        PLAYERS_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    if isinstance(
        data,
        dict
    ):

        players = data.get(
            "players",
            []
        )

    elif isinstance(
        data,
        list
    ):

        players = data

    else:

        raise RuntimeError(
            "players.jsonの形式が不正です。"
        )

    if not isinstance(
        players,
        list
    ):

        raise RuntimeError(
            "players.jsonのplayersが配列ではありません。"
        )

    result = {}

    for player in players:

        if not isinstance(
            player,
            dict
        ):
            continue

        player_id = (
            player.get("id")
            or player.get("player_id")
            or player.get("playerId")
        )

        if player_id is None:
            continue

        try:

            player_id = int(
                player_id
            )

        except (
            ValueError,
            TypeError,
        ):

            continue

        result[player_id] = player

    if not result:

        raise RuntimeError(
            "players.jsonから選手IDを取得できませんでした。"
        )

    print(
        "players.json players:",
        len(result)
    )

    return result


# =========================================================
# MLB STATS API
# =========================================================

def build_stats_url(
    group
):

    params = {
        "stats": "season",
        "group": group,
        "season": str(SEASON),
        "teamId": str(TEAM_ID),
        "sportIds": "1",
        "gameType": "R",
    }

    return (
        BASE_URL
        + "?"
        + urllib.parse.urlencode(
            params
        )
    )


def get_stats(
    group
):

    url = build_stats_url(
        group
    )

    data = fetch_json(
        url
    )

    stats = data.get(
        "stats"
    )

    if not isinstance(
        stats,
        list
    ):

        raise RuntimeError(
            f"MLB APIの{group}データ形式が不正です。"
        )

    result = []

    for block in stats:

        if not isinstance(
            block,
            dict
        ):
            continue

        splits = block.get(
            "splits",
            []
        )

        if not isinstance(
            splits,
            list
        ):
            continue

        result.extend(
            splits
        )

    print(
        group,
        "records:",
        len(result)
    )

    return result


# =========================================================
# VALUE
# =========================================================

def number(
    value
):

    if value is None:
        return None

    if isinstance(
        value,
        bool
    ):
        return value

    if isinstance(
        value,
        (int, float)
    ):
        return value

    text = str(
        value
    ).strip()

    if text == "":
        return None

    try:

        if "." in text:

            return float(
                text
            )

        return int(
            text
        )

    except ValueError:

        return text


# =========================================================
# BATTING
# =========================================================

def parse_batter(
    split
):

    player = split.get(
        "player",
        {}
    )

    stat = split.get(
        "stat",
        {}
    )

    player_id = player.get(
        "id"
    )

    if player_id is None:
        return None

    return {
        "player_id": int(
            player_id
        ),

        "player_name":
            player.get(
                "fullName"
            ),

        "stats": {

            "g": number(
                stat.get("gamesPlayed")
            ),

            "ab": number(
                stat.get("atBats")
            ),

            "pa": number(
                stat.get("plateAppearances")
            ),

            "h": number(
                stat.get("hits")
            ),

            "1b": number(
                stat.get("singles")
            ),

            "2b": number(
                stat.get("doubles")
            ),

            "3b": number(
                stat.get("triples")
            ),

            "hr": number(
                stat.get("homeRuns")
            ),

            "rbi": number(
                stat.get("rbi")
            ),

            "bb": number(
                stat.get("baseOnBalls")
            ),

            "so": number(
                stat.get("strikeOuts")
            ),

            "sb": number(
                stat.get("stolenBases")
            ),

            "cs": number(
                stat.get("caughtStealing")
            ),

            "avg": number(
                stat.get("avg")
            ),

            "obp": number(
                stat.get("obp")
            ),

            "slg": number(
                stat.get("slg")
            ),

            "ops": number(
                stat.get("ops")
            ),

            "r": number(
                stat.get("runs")
            ),

            "tb": number(
                stat.get("totalBases")
            ),

            "ibb": number(
                stat.get("intentionalWalks")
            ),

            "hbp": number(
                stat.get("hitByPitch")
            ),

            "sf": number(
                stat.get("sacFlies")
            ),

            "sh": number(
                stat.get("sacBunts")
            ),
        },
    }


# =========================================================
# PITCHING
# =========================================================

def parse_pitcher(
    split
):

    player = split.get(
        "player",
        {}
    )

    stat = split.get(
        "stat",
        {}
    )

    player_id = player.get(
        "id"
    )

    if player_id is None:
        return None

    return {
        "player_id": int(
            player_id
        ),

        "player_name":
            player.get(
                "fullName"
            ),

        "stats": {

            "g": number(
                stat.get("gamesPlayed")
            ),

            "gs": number(
                stat.get("gamesStarted")
            ),

            "ip": number(
                stat.get("inningsPitched")
            ),

            "bf": number(
                stat.get("battersFaced")
            ),

            "w": number(
                stat.get("wins")
            ),

            "l": number(
                stat.get("losses")
            ),

            "sv": number(
                stat.get("saves")
            ),

            "h": number(
                stat.get("hits")
            ),

            "er": number(
                stat.get("earnedRuns")
            ),

            "hr": number(
                stat.get("homeRuns")
            ),

            "bb": number(
                stat.get("baseOnBalls")
            ),

            "so": number(
                stat.get("strikeOuts")
            ),

            "era": number(
                stat.get("era")
            ),

            "whip": number(
                stat.get("whip")
            ),

            "h9": number(
                stat.get("hitsPer9Inn")
            ),

            "hr9": number(
                stat.get("homeRunsPer9")
            ),

            "bb9": number(
                stat.get("walksPer9Inn")
            ),

            "k9": number(
                stat.get("strikeoutsPer9Inn")
            ),

            "kbb": number(
                stat.get("strikeoutWalkRatio")
            ),

            "baa": number(
                stat.get("avg")
            ),
        },
    }


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "=" * 70
    )

    print(
        "PHILADELPHIA PHILLIES"
    )

    print(
        "MLB OFFICIAL STATS API UPDATE"
    )

    print(
        "=" * 70
    )

    # -----------------------------------------------------
    # players.json
    # -----------------------------------------------------

    players = load_players()

    # -----------------------------------------------------
    # MLB API
    # -----------------------------------------------------

    batting_splits = get_stats(
        "hitting"
    )

    pitching_splits = get_stats(
        "pitching"
    )

    # -----------------------------------------------------
    # BATTERS
    # -----------------------------------------------------

    batters = []

    seen_batters = set()

    for split in batting_splits:

        player = parse_batter(
            split
        )

        if player is None:
            continue

        player_id = player[
            "player_id"
        ]

        if player_id not in players:
            continue

        if player_id in seen_batters:
            continue

        seen_batters.add(
            player_id
        )

        batters.append(
            player
        )

    # -----------------------------------------------------
    # PITCHERS
    # -----------------------------------------------------

    pitchers = []

    seen_pitchers = set()

    for split in pitching_splits:

        player = parse_pitcher(
            split
        )

        if player is None:
            continue

        player_id = player[
            "player_id"
        ]

        if player_id not in players:
            continue

        if player_id in seen_pitchers:
            continue

        seen_pitchers.add(
            player_id
        )

        pitchers.append(
            player
        )

    # -----------------------------------------------------
    # Sort
    # -----------------------------------------------------

    batters.sort(
        key=lambda x: (
            x.get(
                "player_name"
            )
            or ""
        )
    )

    pitchers.sort(
        key=lambda x: (
            x.get(
                "player_name"
            )
            or ""
        )
    )

    # -----------------------------------------------------
    # Validation
    # -----------------------------------------------------

    total = (
        len(batters)
        + len(pitchers)
    )

    print()
    print(
        "Matched batters:",
        len(batters)
    )

    print(
        "Matched pitchers:",
        len(pitchers)
    )

    print(
        "Total:",
        total
    )

    if total == 0:

        raise RuntimeError(
            "MLB公式APIからPhillies選手の成績を"
            "1件も取得できませんでした。"
        )

    # -----------------------------------------------------
    # OUTPUT
    # -----------------------------------------------------

    output = {

        "team":
            TEAM_NAME,

        "teamAbbreviation":
            TEAM_ABBR,

        "teamId":
            TEAM_ID,

        "season":
            SEASON,

        "gameType":
            "R",

        "source":
            "MLB Official Stats API",

        "sourceUrl":
            "https://statsapi.mlb.com/",

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
    # Atomic write
    # -----------------------------------------------------

    temp_file = (
        OUTPUT_FILE
        + ".tmp"
    )

    with open(
        temp_file,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2,
        )

        file.write(
            "\n"
        )

    os.replace(
        temp_file,
        OUTPUT_FILE
    )

    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------

    print()
    print(
        "=" * 70
    )

    print(
        "SUCCESS"
    )

    print(
        "Output:",
        OUTPUT_FILE
    )

    print(
        "Batters:",
        len(batters)
    )

    print(
        "Pitchers:",
        len(pitchers)
    )

    print(
        "Updated:",
        output["updatedAt"]
    )

    print(
        "=" * 70
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    try:

        main()

    except Exception as error:

        print()
        print(
            "=" * 70
        )

        print(
            "UPDATE FAILED"
        )

        print(
            repr(error)
        )

        print(
            "=" * 70
        )

        sys.exit(1)
