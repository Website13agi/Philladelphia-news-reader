import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path


# =========================================================
# CONFIG
# =========================================================

TEAM_ID = 143
API_BASE = "https://statsapi.mlb.com/api/v1"

OUTPUT_FILE = Path("players.json")

USER_AGENT = "Phillies-Daily/2.0"


# =========================================================
# HTTP
# =========================================================

def get_json(url):
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
            timeout=30
        ) as response:

            raw = response.read().decode("utf-8")

            return json.loads(raw)

    except urllib.error.HTTPError as error:

        raise RuntimeError(
            f"MLB API HTTP error: "
            f"{error.code} {url}"
        ) from error

    except urllib.error.URLError as error:

        raise RuntimeError(
            f"MLB API connection error: "
            f"{error.reason}"
        ) from error


# =========================================================
# MLB API
# =========================================================

def get_team_roster(roster_type):
    url = (
        f"{API_BASE}/teams/{TEAM_ID}/roster"
        f"?rosterType={roster_type}"
    )

    data = get_json(url)

    roster = data.get("roster")

    if not isinstance(roster, list):
        raise RuntimeError(
            f"Invalid roster response: {roster_type}"
        )

    return roster


def get_person(player_id):
    url = (
        f"{API_BASE}/people/"
        f"{player_id}"
        f"?hydrate=transactions"
    )

    data = get_json(url)

    people = data.get("people", [])

    if not people:
        return {}

    return people[0]


# =========================================================
# POSITION
# =========================================================

def normalize_position(position):
    if not position:
        return {
            "group": "Other",
            "detail": ""
        }

    code = str(
        position.get("code", "")
    ).upper()

    name = str(
        position.get("name", "")
    )

    # Pitcher
    if code == "P" or name == "Pitcher":

        return {
            "group": "Pitchers",
            "detail": "P"
        }

    # Catcher
    if code == "C" or name == "Catcher":

        return {
            "group": "Catchers",
            "detail": "C"
        }

    # Infield
    infield = {
        "1B",
        "2B",
        "3B",
        "SS"
    }

    if code in infield:

        return {
            "group": "Infielders",
            "detail": code
        }

    # Outfield
    outfield = {
        "LF",
        "CF",
        "RF",
        "OF"
    }

    if code in outfield:

        return {
            "group": "Outfielders",
            "detail": code
        }

    # DH
    if (
        code == "DH"
        or name == "Designated Hitter"
    ):

        return {
            "group": "Infielders",
            "detail": "DH"
        }

    return {
        "group": "Other",
        "detail": code or name
    }


# =========================================================
# IL DETECTION
# =========================================================

def is_il_status(status):
    if not status:
        return False

    code = str(
        status.get("code", "")
    ).upper()

    description = str(
        status.get("description", "")
    ).lower()

    keywords = [
        "injured",
        "injured list",
        "il",
        "10-day",
        "15-day",
        "60-day",
    ]

    if "IL" in code:
        return True

    for keyword in keywords:

        if keyword in description:
            return True

    return False


# =========================================================
# TRANSACTION / IL INFORMATION
# =========================================================

def extract_il_transaction(person):
    transactions = person.get(
        "transactions",
        []
    )

    if not isinstance(
        transactions,
        list
    ):
        return None

    il_transactions = []

    for transaction in transactions:

        description = str(
            transaction.get(
                "description",
                ""
            )
        )

        lower_description = (
            description.lower()
        )

        if (
            "injured list"
            in lower_description
        ):

            effective_date = (
                transaction.get(
                    "effectiveDate"
                )
                or transaction.get(
                    "date"
                )
            )

            il_transactions.append(
                {
                    "date": effective_date,
                    "description": description
                }
            )

    if not il_transactions:
        return None

    # 最新のIL関連トランザクション
    il_transactions.sort(
        key=lambda item:
            item.get("date") or "",
        reverse=True
    )

    latest = il_transactions[0]

    return {
        "date": latest.get("date"),
        "description":
            latest.get(
                "description",
                ""
            )
    }


# =========================================================
# IL DAYS
# =========================================================

def calculate_il_days(start_date):

    if not start_date:
        return None

    try:

        start = datetime.fromisoformat(
            start_date.replace(
                "Z",
                "+00:00"
            )
        )

        now = datetime.now(
            timezone.utc
        )

        days = (
            now.date()
            -
            start.date()
        ).days

        if days < 0:
            return 0

        return days

    except Exception:

        return None


# =========================================================
# STATUS
# =========================================================

def determine_status(
    player_id,
    active_ids,
    forty_ids,
    il_ids
):

    if player_id in il_ids:

        return "IL"

    if player_id in active_ids:

        return "ACTIVE"

    if player_id in forty_ids:

        return "40-MAN"

    return "OTHER"


# =========================================================
# PLAYER CREATION
# =========================================================

def build_player(
    entry,
    active_ids,
    forty_ids,
    il_ids
):

    person = entry.get(
        "person",
        {}
    )

    player_id = person.get("id")

    if not player_id:
        return None

    position_data = (
        entry.get("position")
        or {}
    )

    normalized = normalize_position(
        position_data
    )

    status = determine_status(
        player_id,
        active_ids,
        forty_ids,
        il_ids
    )

    # -----------------------------------------------------
    # Person information
    # -----------------------------------------------------

    full_person = {}

    try:
        full_person = get_person(
            player_id
        )
    except Exception as error:

        print(
            f"Warning: "
            f"person lookup failed for "
            f"{player_id}: {error}"
        )

    # -----------------------------------------------------
    # Bat / Throw
    # -----------------------------------------------------

    bat_side = (
        full_person
        .get("batSide", {})
        .get("description")
    )

    throw_side = (
        full_person
        .get("pitchHand", {})
        .get("description")
    )

    # Fallback
    if not bat_side:

        bat_side = (
            person
            .get("batSide", {})
            .get("description")
        )

    if not throw_side:

        throw_side = (
            person
            .get("pitchHand", {})
            .get("description")
        )

    # -----------------------------------------------------
    # IL
    # -----------------------------------------------------

    il_transaction = (
        extract_il_transaction(
            full_person
        )
    )

    il_start_date = None
    il_days = None
    il_description = ""

    if status == "IL":

        if il_transaction:

            il_start_date = (
                il_transaction.get(
                    "date"
                )
            )

            il_description = (
                il_transaction.get(
                    "description",
                    ""
                )
            )

            il_days = calculate_il_days(
                il_start_date
            )

    # -----------------------------------------------------
    # Player
    # -----------------------------------------------------

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
            normalized["group"],

        "position_detail":
            normalized["detail"],

        "bat_side":
            bat_side or "",

        "throw_side":
            throw_side or "",

        "status":
            status,

        "il_start_date":
            il_start_date,

        "il_days":
            il_days,

        "il_description":
            il_description,

        "mlb_url":
            (
                "https://www.mlb.com/player/"
                f"{player_id}"
            )
    }

    return player


# =========================================================
# SORT
# =========================================================

POSITION_ORDER = {

    "Pitchers": 1,

    "Catchers": 2,

    "Infielders": 3,

    "Outfielders": 4,

    "Other": 5
}


def number_value(number):

    if number is None:
        return 9999

    try:

        return int(
            str(number).strip()
        )

    except Exception:

        return 9999


def sort_players(players):

    return sorted(
        players,
        key=lambda player: (
            POSITION_ORDER.get(
                player.get(
                    "position"
                ),
                99
            ),

            number_value(
                player.get(
                    "number"
                )
            ),

            player.get(
                "name",
                ""
            )
        )
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "===================================="
    )

    print(
        "Phillies roster updater"
    )

    print(
        "Source: MLB Stats API"
    )

    print(
        "===================================="
    )

    # -----------------------------------------------------
    # Fetch rosters
    # -----------------------------------------------------

    print(
        "Fetching active roster..."
    )

    active_roster = get_team_roster(
        "active"
    )

    print(
        f"Active roster: "
        f"{len(active_roster)}"
    )

    print(
        "Fetching 40-man roster..."
    )

    forty_roster = get_team_roster(
        "40Man"
    )

    print(
        f"40-man roster: "
        f"{len(forty_roster)}"
    )

    print(
        "Fetching full roster..."
    )

    full_roster = get_team_roster(
        "fullRoster"
    )

    print(
        f"Full roster: "
        f"{len(full_roster)}"
    )

    # -----------------------------------------------------
    # IDs
    # -----------------------------------------------------

    active_ids = {
        entry["person"]["id"]
        for entry in active_roster
        if entry.get("person")
        and entry["person"].get("id")
    }

    forty_ids = {
        entry["person"]["id"]
        for entry in forty_roster
        if entry.get("person")
        and entry["person"].get("id")
    }

    # -----------------------------------------------------
    # Start with 40-man + full roster
    # -----------------------------------------------------

    entries = {}

    for entry in forty_roster:

        person = entry.get(
            "person",
            {}
        )

        player_id = person.get("id")

        if player_id:

            entries[player_id] = entry

    for entry in full_roster:

        person = entry.get(
            "person",
            {}
        )

        player_id = person.get("id")

        if player_id:

            entries.setdefault(
                player_id,
                entry
            )

    # -----------------------------------------------------
    # Find IL players
    # -----------------------------------------------------

    il_ids = set()

    print(
        "Checking injured-list status..."
    )

    for player_id in list(entries.keys()):

        entry = entries[player_id]

        status = entry.get(
            "status",
            {}
        )

        if is_il_status(status):

            il_ids.add(
                player_id
            )

    # -----------------------------------------------------
    # Build players
    # -----------------------------------------------------

    players = {}

    total = len(entries)

    print(
        f"Processing "
        f"{total} players..."
    )

    for index, entry in enumerate(
        entries.values(),
        start=1
    ):

        person = entry.get(
            "person",
            {}
        )

        player_id = person.get(
            "id"
        )

        print(
            f"[{index}/{total}] "
            f"{person.get('fullName', '')}"
        )

        player = build_player(
            entry,
            active_ids,
            forty_ids,
            il_ids
        )

        if player:

            players[
                player["id"]
            ] = player

    result = sort_players(
        list(
            players.values()
        )
    )

    # -----------------------------------------------------
    # Safety check
    # -----------------------------------------------------

    if not result:

        raise RuntimeError(
            "Roster update returned "
            "zero players. "
            "Existing players.json "
            "will NOT be overwritten."
        )

    # -----------------------------------------------------
    # Counts
    # -----------------------------------------------------

    active_count = sum(
        1
        for player in result
        if player["status"]
        == "ACTIVE"
    )

    forty_count = sum(
        1
        for player in result
        if player["status"]
        == "40-MAN"
    )

    il_count = sum(
        1
        for player in result
        if player["status"]
        == "IL"
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
                len(result),

            "active":
                active_count,

            "forty_man":
                forty_count,

            "il":
                il_count
        },

        "players":
            result
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

    print()
    print(
        "===================================="
    )

    print(
        "Roster update completed"
    )

    print(
        f"Total: {len(result)}"
    )

    print(
        f"Active: {active_count}"
    )

    print(
        f"40-Man: {forty_count}"
    )

    print(
        f"IL: {il_count}"
    )

    print(
        "===================================="
    )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()
