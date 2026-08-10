import json
import re
import urllib.request
from datetime import datetime, timezone


# =========================================================
# CONFIG
# =========================================================

TEAM_ID = 143

ROSTER_URL = (
    f"https://statsapi.mlb.com/api/v1/teams/"
    f"{TEAM_ID}/roster?rosterType=40Man&hydrate=person"
)

OUTPUT_FILE = "players.json"


# =========================================================
# HTTP
# =========================================================

def get_json(url):

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Phillies-Daily/1.0"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=20
    ) as response:

        return json.loads(
            response.read().decode("utf-8")
        )


# =========================================================
# POSITION GROUP
# =========================================================

def position_group(position_name):

    if not position_name:
        return "Unknown"

    p = position_name.lower()

    # Pitchers
    if (
        p == "pitcher"
        or "pitcher" in p
    ):
        return "Pitcher"

    # Catchers
    if (
        p == "catcher"
        or "catcher" in p
    ):
        return "Catcher"

    # Outfielders
    if (
        p in [
            "left fielder",
            "center fielder",
            "right fielder",
            "outfielder"
        ]
        or "fielder" in p
    ):
        return "Outfielder"

    # Infielders
    if (
        p in [
            "first baseman",
            "second baseman",
            "third baseman",
            "shortstop",
            "infielder"
        ]
        or "baseman" in p
    ):
        return "Infielder"

    return "Unknown"


# =========================================================
# POSITION SHORT NAME
# =========================================================

def position_code(position_name):

    if not position_name:
        return ""

    mapping = {
        "Pitcher": "P",
        "Catcher": "C",
        "First Base": "1B",
        "Second Base": "2B",
        "Third Base": "3B",
        "Shortstop": "SS",
        "Left Field": "LF",
        "Center Field": "CF",
        "Right Field": "RF",
        "Outfield": "OF",
        "Designated Hitter": "DH",
        "Two-Way Player": "TWP"
    }

    return mapping.get(
        position_name,
        position_name
    )


# =========================================================
# SAFE INT
# =========================================================

def safe_int(value):

    try:
        return int(value)
    except Exception:
        return 9999


# =========================================================
# NORMALIZE
# =========================================================

def normalize_player(entry):

    person = entry.get(
        "person",
        {}
    )

    position = entry.get(
        "position",
        {}
    )

    jersey = (
        entry.get("jerseyNumber")
        or person.get("primaryNumber")
        or ""
    )

    position_name = position.get(
        "name",
        ""
    )

    group = position_group(
        position_name
    )

    # -----------------------------------------------------
    # B/T
    # -----------------------------------------------------

    bat_side = (
        person
        .get("batSide", {})
        .get("code", "")
    )

    pitch_hand = (
        person
        .get("pitchHand", {})
        .get("code", "")
    )

    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    status = (
        entry
        .get("status", {})
        .get("code", "")
    )

    status_description = (
        entry
        .get("status", {})
        .get("description", "")
    )

    # -----------------------------------------------------
    # ACTIVE
    # -----------------------------------------------------

    active = (
        status == "A"
        or entry.get("active") is True
    )

    # -----------------------------------------------------
    # IL
    # -----------------------------------------------------

    is_il = False

    status_text = (
        status_description or ""
    ).lower()

    if (
        "injured" in status_text
        or "injured list" in status_text
        or "il" in status_text
        or "disabled" in status_text
    ):
        is_il = True

    # Some MLB roster responses use rosterType /
    # roster status information instead of a simple
    # active flag.
    roster_status = (
        entry
        .get("status", {})
        .get("type", "")
    )

    if (
        "injured" in roster_status.lower()
        or "injured" in status_text
    ):
        is_il = True

    # -----------------------------------------------------
    # B/T display
    # -----------------------------------------------------

    bats = bat_side or "-"

    throws = pitch_hand or "-"

    bt = f"{bats}/{throws}"

    # -----------------------------------------------------
    # IL information
    # -----------------------------------------------------

    il_days = None
    il_start_date = None

    # MLB API does not consistently expose IL start date
    # directly inside every 40-man roster response.
    #
    # Therefore these fields are kept ready for future
    # transaction-based enrichment.

    if is_il:
        il_start_date = (
            entry.get("ilStartDate")
            or entry.get("injuredListStartDate")
        )

    if il_start_date:

        try:

            start = datetime.fromisoformat(
                il_start_date.replace(
                    "Z",
                    "+00:00"
                )
            )

            now = datetime.now(
                timezone.utc
            )

            il_days = max(
                1,
                (now.date() - start.date()).days + 1
            )

        except Exception:

            il_days = None

    # -----------------------------------------------------
    # RETURN
    # -----------------------------------------------------

    return {

        "id":
            person.get("id"),

        "name":
            person.get(
                "fullName",
                "Unknown"
            ),

        "firstName":
            person.get(
                "firstName",
                ""
            ),

        "lastName":
            person.get(
                "lastName",
                ""
            ),

        "number":
            str(jersey),

        "position":
            position_name,

        "positionCode":
            position_code(
                position_name
            ),

        "group":
            group,

        "bats":
            bats,

        "throws":
            throws,

        "bt":
            bt,

        "active":
            active,

        "is40Man":
            True,

        "isIL":
            is_il,

        "ilStartDate":
            il_start_date,

        "ilDays":
            il_days,

        "status":
            status,

        "statusDescription":
            status_description,

        "mlbUrl":
            (
                f"https://www.mlb.com/player/"
                f"{person.get('id')}"
            )

    }


# =========================================================
# SORT
# =========================================================

GROUP_ORDER = {

    "Pitcher": 1,

    "Catcher": 2,

    "Infielder": 3,

    "Outfielder": 4,

    "Unknown": 5
}


def sort_players(players):

    return sorted(
        players,
        key=lambda p: (

            GROUP_ORDER.get(
                p.get("group"),
                99
            ),

            safe_int(
                p.get("number")
            ),

            p.get(
                "lastName",
                ""
            ).lower()

        )
    )


# =========================================================
# FETCH
# =========================================================

def fetch_players():

    print(
        "Fetching Philadelphia Phillies 40-man roster..."
    )

    data = get_json(
        ROSTER_URL
    )

    roster = data.get(
        "roster",
        []
    )

    print(
        f"MLB API returned {len(roster)} players."
    )

    players = []

    for entry in roster:

        try:

            player = normalize_player(
                entry
            )

            if player["id"]:

                players.append(
                    player
                )

        except Exception as error:

            print(
                "Player processing error:",
                error
            )

    players = sort_players(
        players
    )

    return players


# =========================================================
# SAVE
# =========================================================

def save_players(players):

    result = {

        "updatedAt":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "team": {

            "id":
                TEAM_ID,

            "name":
                "Philadelphia Phillies"

        },

        "players":
            players

    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=2
        )

    print()
    print(
        f"Saved {len(players)} players."
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )


# =========================================================
# MAIN
# =========================================================

def main():

    try:

        players = fetch_players()

        if not players:

            raise RuntimeError(
                "No players were returned."
            )

        save_players(
            players
        )

        print()
        print(
            "Roster update completed successfully."
        )

    except Exception as error:

        print()
        print(
            "ERROR:",
            error
        )

        raise


if __name__ == "__main__":
    main()
