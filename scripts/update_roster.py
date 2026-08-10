import json
import requests
from datetime import datetime, timezone
from pathlib import Path


# =========================================================
# SETTINGS
# =========================================================

TEAM_ID = 143
TEAM_NAME = "Philadelphia Phillies"

API_BASE = "https://statsapi.mlb.com/api/v1"

ROOT_DIR = Path(__file__).resolve().parent.parent

OUTPUT_FILE = ROOT_DIR / "players.json"


HEADERS = {
    "User-Agent":
        "Phillies-Daily-Roster/1.0"
}


# =========================================================
# API
# =========================================================

def get_json(url, params=None):

    response = requests.get(
        url,
        params=params,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# GET ROSTER
# =========================================================

def get_roster(roster_type):

    url = (
        f"{API_BASE}/teams/"
        f"{TEAM_ID}/roster"
    )

    data = get_json(
        url,
        {
            "rosterType": roster_type
        }
    )

    return data.get(
        "roster",
        []
    )


# =========================================================
# GET PLAYER PROFILE
# =========================================================

def get_player(player_id):

    url = (
        f"{API_BASE}/people/"
        f"{player_id}"
    )

    data = get_json(url)

    people =
        data.get(
            "people",
            []
        )

    if not people:
        return {}

    return people[0]


# =========================================================
# POSITION GROUP
# =========================================================

def get_position_group(position_code):

    code =
        str(position_code or "")
        .upper()


    if code in {
        "P",
        "SP",
        "RP"
    }:
        return "pitcher"


    if code == "C":
        return "catcher"


    if code in {
        "1B",
        "2B",
        "3B",
        "SS"
    }:
        return "infielder"


    if code in {
        "LF",
        "CF",
        "RF",
        "OF"
    }:
        return "outfielder"


    # DHは野手として扱う
    if code == "DH":
        return "infielder"


    return "infielder"


# =========================================================
# POSITION LABEL
# =========================================================

def get_position_label(
    profile,
    roster_entry
):

    primary_position =
        profile.get(
            "primaryPosition",
            {}
        )


    code =
        primary_position.get(
            "abbreviation"
        )


    if not code:

        code =
            (
                roster_entry
                .get("position", {})
                .get("abbreviation")
            )


    if code:
        return code


    return "—"


# =========================================================
# STATUS
# =========================================================

def get_status(
    player_id,
    active_ids,
    roster40_entry
):

    if player_id in active_ids:
        return "Active"


    status =
        roster40_entry.get(
            "status",
            {}
        )


    description =
        str(
            status.get(
                "description",
                ""
            )
        ).lower()


    code =
        str(
            status.get(
                "code",
                ""
            )
        ).lower()


    combined =
        f"{description} {code}"


    if (
        "injured" in combined
        or "injury" in combined
        or "10-day" in combined
        or "15-day" in combined
        or "60-day" in combined
        or "7-day" in combined
        or "il" in combined
    ):

        return "IL"


    return "40-Man"


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "Fetching Phillies MLB roster..."
    )


    active_roster =
        get_roster(
            "active"
        )


    roster40 =
        get_roster(
            "40Man"
        )


    active_ids = {
        int(
            item["person"]["id"]
        )
        for item in active_roster
        if item.get("person", {}).get("id")
    }


    roster40_by_id = {
        int(
            item["person"]["id"]
        ): item
        for item in roster40
        if item.get("person", {}).get("id")
    }


    print(
        f"Active roster: {len(active_roster)}"
    )

    print(
        f"40-man roster: {len(roster40)}"
    )


    players = []


    for roster_entry in roster40:

        person =
            roster_entry.get(
                "person",
                {}
            )


        player_id =
            person.get("id")


        if not player_id:
            continue


        print(
            "Fetching:",
            person.get("fullName"),
            player_id
        )


        try:

            profile =
                get_player(
                    player_id
                )

        except Exception as error:

            print(
                "Profile error:",
                error
            )

            profile = {}


        position =
            get_position_label(
                profile,
                roster_entry
            )


        group =
            get_position_group(
                position
            )


        bat_side =
            profile.get(
                "batSide",
                {}
            )


        pitch_hand =
            profile.get(
                "pitchHand",
                {}
            )


        bats =
            bat_side.get(
                "code"
            )


        throws =
            pitch_hand.get(
                "code"
            )


        number =
            (
                profile.get(
                    "primaryNumber"
                )
                or roster_entry.get(
                    "jerseyNumber"
                )
                or ""
            )


        status =
            get_status(
                int(player_id),
                active_ids,
                roster_entry
            )


        players.append({

            "id":
                int(player_id),

            "name":
                profile.get(
                    "fullName"
                )
                or person.get(
                    "fullName"
                ),

            "number":
                str(number),

            "group":
                group,

            "position":
                position,

            "bats":
                bats or "",

            "throws":
                throws or "",

            "status":
                status,

            "roster40":
                True,

            "mlbUrl":
                (
                    "https://www.mlb.com/"
                    "player/"
                    f"{player_id}"
                )

        })


    # =====================================================
    # SORT BY JERSEY NUMBER
    # =====================================================

    def sort_key(player):

        try:
            return int(
                player["number"]
            )

        except (
            ValueError,
            TypeError
        ):
            return 999


    players.sort(
        key=sort_key
    )


    # =====================================================
    # OUTPUT
    # =====================================================

    output = {

        "team": TEAM_NAME,

        "teamId": TEAM_ID,

        "source":
            "MLB Stats API",

        "updatedAt":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "players":
            players

    }


    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2
        )


    print()
    print(
        "===================================="
    )

    print(
        f"Saved {len(players)} players"
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )

    print(
        "===================================="
    )


if __name__ == "__main__":
    main()
