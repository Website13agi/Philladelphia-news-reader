import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


# =========================================================
# Phillies Roster Updater
# MLB Stats API
# =========================================================

TEAM_ID = 143

API_BASE = "https://statsapi.mlb.com/api/v1"

OUTPUT_FILE = Path("players.json")

USER_AGENT = (
    "Mozilla/5.0 "
    "(compatible; PhilliesDailyRoster/1.0)"
)


# =========================================================
# HTTP
# =========================================================

def get_json(url):

    print(f"GET {url}")

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

        raw = response.read()

    return json.loads(
        raw.decode("utf-8")
    )


# =========================================================
# MLB ROSTER
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
# POSITION
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
    ).lower()

    # Pitcher
    if (
        code == "P"
        or name == "pitcher"
    ):
        return "Pitchers"

    # Catcher
    if (
        code == "C"
        or name == "catcher"
    ):
        return "Catchers"

    # Infield
    if (
        code in {
            "1B",
            "2B",
            "3B",
            "SS"
        }
        or name == "infielder"
    ):
        return "Infielders"

    # Outfield
    if (
        code in {
            "LF",
            "CF",
            "RF",
            "OF"
        }
        or name == "outfielder"
    ):
        return "Outfielders"

    # Designated hitter
    if (
        code == "DH"
        or name == "designated hitter"
    ):
        return "Infielders"

    return "Other"


# =========================================================
# STATUS
# =========================================================

def normalize_status(
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

    il_words = [
        "injured",
        "injury",
        "10-day injured",
        "15-day injured",
        "60-day injured",
        "7-day injured",
        "il",
    ]

    if (
        "IL" in code
        or any(
            word in description
            for word in il_words
        )
    ):
        return "IL"

    # -----------------------------------------------------
    # Active roster
    # -----------------------------------------------------

    player = entry.get(
        "person",
        {}
    )

    player_id = player.get(
        "id"
    )

    if player_id in active_ids:
        return "ACTIVE"

    # -----------------------------------------------------
    # 40-man roster
    # -----------------------------------------------------

    return "40-MAN"


# =========================================================
# PLAYER
# =========================================================

def make_player(
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

    position = entry.get(
        "position",
        {}
    )

    status = normalize_status(
        entry,
        active_ids
    )

    jersey_number = entry.get(
        "jerseyNumber"
    )

    # jerseyNumber may be missing
    if jersey_number is None:
        jersey_number = ""

    player = {
        "id": player_id,

        "name": name,

        "number": str(
            jersey_number
        ),

        "position": normalize_position(
            position
        ),

        "status": status,

        "mlb_url": (
            "https://www.mlb.com/player/"
            f"{player_id}"
        ),
    }

    return player


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "========================================"
    )

    print(
        "Updating Philadelphia Phillies roster"
    )

    print(
        "========================================"
    )

    # -----------------------------------------------------
    # Active roster
    # -----------------------------------------------------

    active_roster = get_roster(
        "active"
    )

    print(
        f"Active roster: "
        f"{len(active_roster)}"
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
    # 40-man roster
    # -----------------------------------------------------

    forty_roster = get_roster(
        "40Man"
    )

    print(
        f"40-man roster: "
        f"{len(forty_roster)}"
    )

    # -----------------------------------------------------
    # Merge
    # -----------------------------------------------------

    players_by_id = {}

    for entry in forty_roster:

        player = make_player(
            entry,
            active_ids
        )

        if not player:
            continue

        players_by_id[
            player["id"]
        ] = player

    # -----------------------------------------------------
    # Safety check
    #
    # API failureなどで空データを
    # players.jsonに書き込まない
    # -----------------------------------------------------

    if len(players_by_id) == 0:

        raise RuntimeError(
            "No Phillies players were returned "
            "from MLB Stats API. "
            "Existing players.json was not overwritten."
        )

    # -----------------------------------------------------
    # Sort
    # -----------------------------------------------------

    position_order = {
        "Pitchers": 1,
        "Catchers": 2,
        "Infielders": 3,
        "Outfielders": 4,
        "Other": 5,
    }

    players = list(
        players_by_id.values()
    )

    players.sort(
        key=lambda player: (
            position_order.get(
                player["position"],
                99
            ),
            player["name"].lower()
        )
    )

    # -----------------------------------------------------
    # Statistics
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
    # Output
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
    # Write
    # -----------------------------------------------------

    OUTPUT_FILE.write_text(

        json.dumps(
            output,
            ensure_ascii=False,
            indent=2
        ),

        encoding="utf-8"
    )

    print(
        "----------------------------------------"
    )

    print(
        f"Players: {len(players)}"
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
        "players.json successfully updated."
    )

    print(
        "----------------------------------------"
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()
