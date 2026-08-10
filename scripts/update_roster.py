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


# =========================================================
# HTTP
# =========================================================

def get_json(url):

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent":
                "Phillies-Daily/1.0"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:

        return json.loads(
            response
            .read()
            .decode("utf-8")
        )


# =========================================================
# MLB ROSTER
# =========================================================

def get_roster(roster_type):

    url = (
        f"{API_BASE}/teams/"
        f"{TEAM_ID}/roster"
        f"?rosterType={roster_type}"
    )

    print(
        f"Fetching {roster_type} roster..."
    )

    data = get_json(url)

    return data.get(
        "roster",
        []
    )


# =========================================================
# POSITION
# =========================================================

def normalize_position(position):

    if not position:
        return "Other"

    code = (
        position.get("code")
        or ""
    )

    name = (
        position.get("name")
        or ""
    )

    code = code.upper()
    name = name.lower()


    # Pitcher

    if (
        code == "P"
        or "pitcher" in name
    ):
        return "Pitchers"


    # Catcher

    if (
        code == "C"
        or "catcher" in name
    ):
        return "Catchers"


    # Infield

    if code in [
        "1B",
        "2B",
        "3B",
        "SS"
    ]:

        return "Infielders"


    if (
        "infielder" in name
        or "designated hitter" in name
    ):

        return "Infielders"


    # Outfield

    if code in [
        "LF",
        "CF",
        "RF",
        "OF"
    ]:

        return "Outfielders"


    if "outfielder" in name:

        return "Outfielders"


    return "Other"


# =========================================================
# STATUS
# =========================================================

def detect_status(
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
    # Injured List
    # -----------------------------------------------------

    il_keywords = [
        "injured",
        "injured list",
        "60-day",
        "15-day",
        "7-day",
        "10-day"
    ]

    if (
        "IL" in code
        or any(
            word in description
            for word in il_keywords
        )
    ):

        return "IL"


    # -----------------------------------------------------
    # Active roster
    # -----------------------------------------------------

    player_id = (
        entry
        .get("person", {})
        .get("id")
    )

    if player_id in active_ids:

        return "ACTIVE"


    # -----------------------------------------------------
    # 40-man roster
    # -----------------------------------------------------

    return "40-MAN"


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "======================================"
    )

    print(
        "Phillies roster update"
    )

    print(
        "======================================"
    )


    # -----------------------------------------------------
    # Active roster
    # -----------------------------------------------------

    active_roster = get_roster(
        "active"
    )


    # -----------------------------------------------------
    # 40-man roster
    # -----------------------------------------------------

    forty_roster = get_roster(
        "40Man"
    )


    # -----------------------------------------------------
    # Active player IDs
    # -----------------------------------------------------

    active_ids = {

        entry["person"]["id"]

        for entry in active_roster

        if entry.get("person")
        and entry["person"].get("id")

    }


    print(
        f"Active roster: "
        f"{len(active_ids)}"
    )

    print(
        f"40-man roster: "
        f"{len(forty_roster)}"
    )


    # -----------------------------------------------------
    # Build players
    # -----------------------------------------------------

    players = {}


    for entry in forty_roster:

        person = entry.get(
            "person",
            {}
        )

        player_id = person.get(
            "id"
        )


        if not player_id:

            continue


        position = entry.get(
            "position",
            {}
        )


        player = {

            "id":
                player_id,

            "name":
                person.get(
                    "fullName",
                    ""
                ),

            "number":
                entry.get(
                    "jerseyNumber"
                ),

            "position":
                normalize_position(
                    position
                ),

            "status":
                detect_status(
                    entry,
                    active_ids
                ),

            "mlb_url":
                (
                    "https://www.mlb.com/player/"
                    f"{player_id}"
                )

        }


        players[
            player_id
        ] = player


    # -----------------------------------------------------
    # Convert dictionary
    # -----------------------------------------------------

    result = list(
        players.values()
    )


    # -----------------------------------------------------
    # Position order
    # -----------------------------------------------------

    position_order = {

        "Pitchers": 1,

        "Catchers": 2,

        "Infielders": 3,

        "Outfielders": 4,

        "Other": 5

    }


    # -----------------------------------------------------
    # Status order
    # -----------------------------------------------------

    status_order = {

        "ACTIVE": 1,

        "IL": 2,

        "40-MAN": 3

    }


    result.sort(

        key=lambda player: (

            position_order.get(
                player["position"],
                99
            ),

            status_order.get(
                player["status"],
                99
            ),

            player["name"]

        )

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

        "roster_type":

            "40Man",

        "active_count":

            len(active_ids),

        "players_count":

            len(result),

        "players":

            result

    }


    # -----------------------------------------------------
    # Write players.json
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
        "--------------------------------------"
    )

    print(
        f"Updated players: "
        f"{len(result)}"
    )

    print(
        f"Output: "
        f"{OUTPUT_FILE}"
    )

    print(
        "--------------------------------------"
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()
