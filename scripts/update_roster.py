import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


# =========================================================
# PHILLIES ROSTER UPDATER
# MLB Stats API
# =========================================================

TEAM_ID = 143

API_BASE = "https://statsapi.mlb.com/api/v1"

OUTPUT_FILE = Path("players.json")

USER_AGENT = (
    "Mozilla/5.0 "
    "(compatible; PhilliesDailyRoster/2.0)"
)


# =========================================================
# HTTP
# =========================================================

def get_json(url):

    print(f"GET: {url}")

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:

        data = response.read()

    return json.loads(
        data.decode("utf-8")
    )


# =========================================================
# ROSTER
# =========================================================

def get_roster(roster_type):

    url = (
        f"{API_BASE}/teams/{TEAM_ID}/roster"
        f"?rosterType={roster_type}"
    )

    data = get_json(url)

    roster = data.get(
        "roster",
        []
    )

    if not isinstance(
        roster,
        list
    ):
        return []

    return roster


# =========================================================
# POSITION NORMALIZATION
#
# MLB Stats APIでは
#
# Pitcher:
#   P
#
# Catcher:
#   C
#
# First Base:
#   3
#
# Second Base:
#   4
#
# Third Base:
#   5
#
# Shortstop:
#   6
#
# Left Field:
#   7
#
# Center Field:
#   8
#
# Right Field:
#   9
#
# Designated Hitter:
#   10
#
# というコードが使用される場合がある。
# =========================================================

def normalize_position(position):

    if not position:
        return "Other"

    code = str(
        position.get(
            "code",
            ""
        )
    ).upper()

    name = str(
        position.get(
            "name",
            ""
        )
    ).strip().lower()

    # -----------------------------------------------------
    # Pitcher
    # -----------------------------------------------------

    if (
        code == "P"
        or name == "pitcher"
        or "pitcher" in name
    ):
        return "Pitchers"

    # -----------------------------------------------------
    # Catcher
    # -----------------------------------------------------

    if (
        code == "C"
        or name == "catcher"
        or "catcher" in name
    ):
        return "Catchers"

    # -----------------------------------------------------
    # Infield
    #
    # API may return:
    #
    # 1B / 2B / 3B / SS
    # 3 / 4 / 5 / 6
    #
    # or names such as:
    #
    # First Base
    # Second Base
    # Third Base
    # Shortstop
    # Infielder
    # -----------------------------------------------------

    infield_codes = {
        "1B",
        "2B",
        "3B",
        "SS",
        "3",
        "4",
        "5",
        "6",
    }

    infield_names = {
        "first base",
        "second base",
        "third base",
        "shortstop",
        "infielder",
        "infield",
    }

    if (
        code in infield_codes
        or name in infield_names
        or "infielder" in name
    ):
        return "Infielders"

    # -----------------------------------------------------
    # Outfield
    #
    # API may return:
    #
    # LF / CF / RF / OF
    # 7 / 8 / 9
    #
    # or names such as:
    #
    # Left Field
    # Center Field
    # Right Field
    # Outfielder
    # -----------------------------------------------------

    outfield_codes = {
        "LF",
        "CF",
        "RF",
        "OF",
        "7",
        "8",
        "9",
    }

    outfield_names = {
        "left field",
        "center field",
        "right field",
        "outfielder",
        "outfield",
    }

    if (
        code in outfield_codes
        or name in outfield_names
        or "outfielder" in name
    ):
        return "Outfielders"

    # -----------------------------------------------------
    # Designated Hitter
    #
    # UIでは野手として扱う
    # -----------------------------------------------------

    if (
        code == "DH"
        or code == "10"
        or name == "designated hitter"
        or "designated hitter" in name
    ):
        return "Infielders"

    # -----------------------------------------------------
    # Utility / Two-Way
    #
    # 野手として登録されている場合は
    # 名前から可能な限り判定
    # -----------------------------------------------------

    if (
        "utility" in name
        or "two-way" in name
    ):
        return "Infielders"

    return "Other"


# =========================================================
# STATUS
# =========================================================

def get_status(
    entry,
    active_ids
):

    status = entry.get(
        "status",
        {}
    )

    code = str(
        status.get(
            "code",
            ""
        )
    ).upper()

    description = str(
        status.get(
            "description",
            ""
        )
    ).lower()

    # -----------------------------------------------------
    # IL
    # -----------------------------------------------------

    if (
        "IL" in code
        or "INJURED" in code
        or "INJURED" in description.upper()
        or "injured" in description
        or "injury" in description
    ):
        return "IL"

    # -----------------------------------------------------
    # Active
    # -----------------------------------------------------

    person = entry.get(
        "person",
        {}
    )

    player_id = person.get(
        "id"
    )

    if player_id in active_ids:
        return "ACTIVE"

    # -----------------------------------------------------
    # 40-man only
    # -----------------------------------------------------

    return "40-MAN"


# =========================================================
# PLAYER
# =========================================================

def create_player(
    entry,
    active_ids
):

    person = entry.get(
        "person",
        {}
    )

    player_id = person.get(
        "id"
    )

    if not player_id:
        return None

    name = person.get(
        "fullName",
        ""
    )

    if not name:
        return None

    position_data = entry.get(
        "position",
        {}
    )

    number = entry.get(
        "jerseyNumber"
    )

    if number is None:
        number = ""

    number = str(
        number
    ).strip()

    position = normalize_position(
        position_data
    )

    status = get_status(
        entry,
        active_ids
    )

    return {

        "id":
            player_id,

        "name":
            name,

        "number":
            number,

        "position":
            position,

        "status":
            status,

        "mlb_url":
            (
                "https://www.mlb.com/player/"
                f"{player_id}"
            ),

    }


# =========================================================
# NUMBER SORT
# =========================================================

def number_sort_value(number):

    if number is None:
        return 9999

    number = str(
        number
    ).strip()

    if not number:
        return 9999

    try:

        return int(
            number
        )

    except ValueError:

        return 9999


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "=========================================="
    )

    print(
        "Philadelphia Phillies Roster Update"
    )

    print(
        "=========================================="
    )

    # -----------------------------------------------------
    # ACTIVE
    # -----------------------------------------------------

    active_roster = get_roster(
        "active"
    )

    print(
        f"Active roster: {len(active_roster)}"
    )

    active_ids = set()

    for entry in active_roster:

        person = entry.get(
            "person"
        )

        if not person:
            continue

        player_id = person.get(
            "id"
        )

        if player_id:
            active_ids.add(
                player_id
            )

    # -----------------------------------------------------
    # 40-MAN
    # -----------------------------------------------------

    forty_roster = get_roster(
        "40Man"
    )

    print(
        f"40-man roster: {len(forty_roster)}"
    )

    # -----------------------------------------------------
    # MERGE
    # -----------------------------------------------------

    players_by_id = {}

    for entry in forty_roster:

        player = create_player(
            entry,
            active_ids
        )

        if not player:
            continue

        players_by_id[
            player["id"]
        ] = player

    # -----------------------------------------------------
    # Safety
    # -----------------------------------------------------

    if not players_by_id:

        raise RuntimeError(
            "MLB Stats API returned "
            "zero Phillies players."
        )

    players = list(
        players_by_id.values()
    )

    # -----------------------------------------------------
    # POSITION ORDER
    # -----------------------------------------------------

    position_order = {

        "Pitchers": 1,

        "Catchers": 2,

        "Infielders": 3,

        "Outfielders": 4,

        "Other": 5,

    }

    # -----------------------------------------------------
    # SORT
    #
    # ① ポジション
    # ② 背番号
    # ③ 名前
    #
    # 背番号なしは最後
    # -----------------------------------------------------

    players.sort(

        key=lambda player: (

            position_order.get(
                player["position"],
                99
            ),

            number_sort_value(
                player["number"]
            ),

            player["name"].lower(),

        )

    )

    # -----------------------------------------------------
    # COUNTS
    # -----------------------------------------------------

    active_count = sum(

        1

        for player in players

        if player["status"] == "ACTIVE"

    )

    il_count = sum(

        1

        for player in players

        if player["status"] == "IL"

    )

    forty_count = sum(

        1

        for player in players

        if player["status"] == "40-MAN"

    )

    # -----------------------------------------------------
    # OUTPUT
    # -----------------------------------------------------

    output = {

        "updated_at":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "source":
            "MLB Stats API",

        "source_url":
            (
                "https://statsapi.mlb.com/"
                "api/v1/teams/143/roster"
            ),

        "team":
            "Philadelphia Phillies",

        "team_id":
            TEAM_ID,

        "counts": {

            "total":
                len(players),

            "active":
                active_count,

            "il":
                il_count,

            "forty_man":
                forty_count,

        },

        "players":
            players,

    }

    # -----------------------------------------------------
    # WRITE
    # -----------------------------------------------------

    OUTPUT_FILE.write_text(

        json.dumps(
            output,
            ensure_ascii=False,
            indent=2
        ),

        encoding="utf-8"

    )

    # -----------------------------------------------------
    # LOG
    # -----------------------------------------------------

    print(
        "------------------------------------------"
    )

    print(
        f"Total: {len(players)}"
    )

    print(
        f"Active: {active_count}"
    )

    print(
        f"IL: {il_count}"
    )

    print(
        f"40-Man only: {forty_count}"
    )

    print(
        "Roster update completed."
    )

    print(
        "------------------------------------------"
    )


if __name__ == "__main__":

    main()
