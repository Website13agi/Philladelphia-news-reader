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

# 現在のシーズン
SEASON = 2026

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
            timeout=120
        ) as response:

            raw = response.read()

    except Exception as error:

        raise RuntimeError(
            "MLB APIへの接続に失敗しました: "
            + repr(error)
        )

    if not raw:

        raise RuntimeError(
            "MLB APIから空のレスポンスが返されました。"
        )

    try:

        return json.loads(
            raw.decode("utf-8")
        )

    except Exception as error:

        raise RuntimeError(
            "MLB APIのJSON解析に失敗しました: "
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
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    if not isinstance(
        data,
        dict
    ):

        raise RuntimeError(
            "players.jsonのルートがオブジェクトではありません。"
        )

    players = data.get(
        "players"
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

        # MLB ID
        player_id = player.get(
            "id"
        )

        if player_id is None:
            continue

        try:

            player_id = int(
                player_id
            )

        except (
            TypeError,
            ValueError
        ):

            continue

        # 40-Manだけ
        if player.get(
            "is40Man"
        ) is not True:

            continue

        result[player_id] = player

    if not result:

        raise RuntimeError(
            "40-Man選手をplayers.jsonから取得できませんでした。"
        )

    print(
        f"40-Man roster players: {len(result)}"
    )

    return result


# =========================================================
# MLB API
# =========================================================

def build_stats_url(group):

    params = {
        "stats": "season",
        "group": group,
        "season": str(SEASON),
        "teamId": str(TEAM_ID),
        "sportIds": "1",
        "gameType": "R",
        "limit": "5000",
    }

    return (
        BASE_URL
        + "?"
        + urllib.parse.urlencode(params)
    )


def get_stats(group):

    url = build_stats_url(
        group
    )

    print(
        f"Downloading MLB API {group}..."
    )

    data = fetch_json(
        url
    )

    blocks = data.get(
        "stats",
        []
    )

    if not isinstance(
        blocks,
        list
    ):

        raise RuntimeError(
            f"MLB API {group} のstatsが配列ではありません。"
        )

    result = []

    for block in blocks:

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
        f"{group}: {len(result)} records"
    )

    return result


# =========================================================
# NUMBER
# =========================================================

def number(value):

    if value is None:
        return None

    if isinstance(
        value,
        (int, float)
    ):

        return value

    text = str(
        value
    ).strip()

    if not text:
        return None

    try:

        if "." in text:
            return float(text)

        return int(text)

    except ValueError:

        return text


# =========================================================
# EMPTY STATS
# =========================================================

def empty_batting():

    return {
        "g": 0,
        "ab": 0,
        "pa": 0,
        "h": 0,
        "1b": 0,
        "2b": 0,
        "3b": 0,
        "hr": 0,
        "r": 0,
        "rbi": 0,
        "bb": 0,
        "so": 0,
        "sb": 0,
        "cs": 0,
        "avg": None,
        "obp": None,
        "slg": None,
        "ops": None,
        "tb": 0,
        "ibb": 0,
        "hbp": 0,
        "sf": 0,
        "sh": 0,
    }


def empty_pitching():

    return {
        "g": 0,
        "gs": 0,
        "ip": "0.0",
        "bf": 0,
        "w": 0,
        "l": 0,
        "sv": 0,
        "h": 0,
        "er": 0,
        "hr": 0,
        "bb": 0,
        "so": 0,
        "era": None,
        "whip": None,
        "h9": None,
        "hr9": None,
        "bb9": None,
        "k9": None,
        "kbb": None,
        "baa": None,
    }


# =========================================================
# PARSE BATTING
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

        "player_id":
            int(player_id),

        "player_name":
            player.get(
                "fullName"
            ),

        "stats": {

            "g": number(
                stat.get(
                    "gamesPlayed"
                )
            ),

            "ab": number(
                stat.get(
                    "atBats"
                )
            ),

            "pa": number(
                stat.get(
                    "plateAppearances"
                )
            ),

            "h": number(
                stat.get(
                    "hits"
                )
            ),

            "1b": number(
                stat.get(
                    "singles"
                )
            ),

            "2b": number(
                stat.get(
                    "doubles"
                )
            ),

            "3b": number(
                stat.get(
                    "triples"
                )
            ),

            "hr": number(
                stat.get(
                    "homeRuns"
                )
            ),

            "r": number(
                stat.get(
                    "runs"
                )
            ),

            "rbi": number(
                stat.get(
                    "rbi"
                )
            ),

            "bb": number(
                stat.get(
                    "baseOnBalls"
                )
            ),

            "so": number(
                stat.get(
                    "strikeOuts"
                )
            ),

            "sb": number(
                stat.get(
                    "stolenBases"
                )
            ),

            "cs": number(
                stat.get(
                    "caughtStealing"
                )
            ),

            "avg": number(
                stat.get(
                    "avg"
                )
            ),

            "obp": number(
                stat.get(
                    "obp"
                )
            ),

            "slg": number(
                stat.get(
                    "slg"
                )
            ),

            "ops": number(
                stat.get(
                    "ops"
                )
            ),

            "tb": number(
                stat.get(
                    "totalBases"
                )
            ),

            "ibb": number(
                stat.get(
                    "intentionalWalks"
                )
            ),

            "hbp": number(
                stat.get(
                    "hitByPitch"
                )
            ),

            "sf": number(
                stat.get(
                    "sacFlies"
                )
            ),

            "sh": number(
                stat.get(
                    "sacBunts"
                )
            ),
        }
    }


# =========================================================
# PARSE PITCHING
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

        "player_id":
            int(player_id),

        "player_name":
            player.get(
                "fullName"
            ),

        "stats": {

            "g": number(
                stat.get(
                    "gamesPlayed"
                )
            ),

            "gs": number(
                stat.get(
                    "gamesStarted"
                )
            ),

            "ip": stat.get(
                "inningsPitched",
                "0.0"
            ),

            "bf": number(
                stat.get(
                    "battersFaced"
                )
            ),

            "w": number(
                stat.get(
                    "wins"
                )
            ),

            "l": number(
                stat.get(
                    "losses"
                )
            ),

            "sv": number(
                stat.get(
                    "saves"
                )
            ),

            "h": number(
                stat.get(
                    "hits"
                )
            ),

            "er": number(
                stat.get(
                    "earnedRuns"
                )
            ),

            "hr": number(
                stat.get(
                    "homeRuns"
                )
            ),

            "bb": number(
                stat.get(
                    "baseOnBalls"
                )
            ),

            "so": number(
                stat.get(
                    "strikeOuts"
                )
            ),

            "era": number(
                stat.get(
                    "era"
                )
            ),

            "whip": number(
                stat.get(
                    "whip"
                )
            ),

            "h9": number(
                stat.get(
                    "hitsPer9Inn"
                )
            ),

            "hr9": number(
                stat.get(
                    "homeRunsPer9"
                )
            ),

            "bb9": number(
                stat.get(
                    "walksPer9Inn"
                )
            ),

            "k9": number(
                stat.get(
                    "strikeoutsPer9Inn"
                )
            ),

            "kbb": number(
                stat.get(
                    "strikeoutWalkRatio"
                )
            ),

            "baa": number(
                stat.get(
                    "avg"
                )
            ),
        }
    }


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 60)
    print("PHILLIES MLB STATISTICS")
    print(f"SEASON: {SEASON}")
    print("=" * 60)

    # -----------------------------------------------------
    # 40-Man
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
    # MLB API data -> ID map
    # -----------------------------------------------------

    batting_map = {}

    for split in batting_splits:

        player = parse_batter(
            split
        )

        if player is None:
            continue

        player_id = player[
            "player_id"
        ]

        if player_id in players:

            batting_map[
                player_id
            ] = player

    pitching_map = {}

    for split in pitching_splits:

        player = parse_pitcher(
            split
        )

        if player is None:
            continue

        player_id = player[
            "player_id"
        ]

        if player_id in players:

            pitching_map[
                player_id
            ] = player

    # -----------------------------------------------------
    # IMPORTANT
    #
    # MLB APIに成績が存在しない選手も
    # 40-Manから削除しない
    # -----------------------------------------------------

    batters = []
    pitchers = []

    no_batting_stats = []
    no_pitching_stats = []

    for player_id, player in players.items():

        name = player.get(
            "name",
            f"Player {player_id}"
        )

        position_code = player.get(
            "positionCode",
            ""
        )

        group = str(
            player.get(
                "group",
                ""
            )
        ).lower()

        # -------------------------------------------------
        # 投手
        # -------------------------------------------------

        if (
            position_code == "P"
            or group == "pitcher"
        ):

            if player_id in pitching_map:

                pitchers.append(
                    pitching_map[
                        player_id
                    ]
                )

            else:

                pitchers.append({

                    "player_id":
                        player_id,

                    "player_name":
                        name,

                    "stats":
                        empty_pitching()
                })

                no_pitching_stats.append(
                    name
                )

        # -------------------------------------------------
        # 野手
        # -------------------------------------------------

        else:

            if player_id in batting_map:

                batters.append(
                    batting_map[
                        player_id
                    ]
                )

            else:

                batters.append({

                    "player_id":
                        player_id,

                    "player_name":
                        name,

                    "stats":
                        empty_batting()
                })

                no_batting_stats.append(
                    name
                )

    # -----------------------------------------------------
    # SORT
    # -----------------------------------------------------

    batters.sort(
        key=lambda x:
            x.get(
                "player_name",
                ""
            )
    )

    pitchers.sort(
        key=lambda x:
            x.get(
                "player_name",
                ""
            )
    )

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    total = (
        len(batters)
        +
        len(pitchers)
    )

    print()
    print(
        "40-Man:",
        len(players)
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
        "Total:",
        total
    )

    print(
        "Batters with stats:",
        len(batting_map)
    )

    print(
        "Pitchers with stats:",
        len(pitching_map)
    )

    if no_batting_stats:

        print()
        print(
            "Batters without MLB stats:"
        )

        for name in no_batting_stats:

            print(
                " -",
                name
            )

    if no_pitching_stats:

        print()
        print(
            "Pitchers without MLB stats:"
        )

        for name in no_pitching_stats:

            print(
                " -",
                name
            )

    # -----------------------------------------------------
    # 絶対条件
    # -----------------------------------------------------

    if total != len(players):

        raise RuntimeError(
            "40-Man全員をsavant.jsonへ登録できませんでした。"
            f" 40-Man={len(players)}, "
            f"output={total}"
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
            pitchers
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
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=2
        )

        f.write(
            "\n"
        )

    os.replace(
        temp_file,
        OUTPUT_FILE
    )

    print()
    print("=" * 60)
    print("SUCCESS")
    print(
        f"{OUTPUT_FILE}: {total} players"
    )
    print("=" * 60)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    try:

        main()

    except Exception as error:

        print()
        print("=" * 60)
        print("UPDATE FAILED")
        print("=" * 60)
        print(
            repr(error)
        )
        print("=" * 60)

        sys.exit(1)
