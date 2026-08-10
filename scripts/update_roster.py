import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


TEAM_ID = 143

API_BASE = "https://statsapi.mlb.com/api/v1"

OUTPUT_FILE = Path("players.json")


def get_json(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Phillies-Daily/1.0"
        }
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def get_roster(roster_type):
    url = (
        f"{API_BASE}/teams/{TEAM_ID}/roster"
        f"?rosterType={roster_type}"
    )

    data = get_json(url)

    return data.get("roster", [])


def normalize_position(position):
    if not position:
        return "Other"

    code = position.get("code", "")
    name = position.get("name", "")

    if code == "P" or name == "Pitcher":
        return "Pitchers"

    if code == "C" or name == "Catcher":
        return "Catchers"

    if code in ["1B", "2B", "3B", "SS"] or name == "Infielder":
        return "Infielders"

    if code in ["LF", "CF", "RF", "OF"] or name == "Outfielder":
        return "Outfielders"

    if name == "Designated Hitter":
        return "Infielders"

    return "Other"


def get_status(entry, is_active):
    status = entry.get("status", {})

    code = status.get("code", "")
    description = status.get("description", "")

    # IL
    if "IL" in code.upper() or "injured" in description.lower():
        return "IL"

    # Active roster
    if is_active:
        return "ACTIVE"

    # 40-man but not active
    return "40-MAN"


def main():

    print("Fetching Phillies roster...")

    active_roster = get_roster("active")
    forty_roster = get_roster("40Man")

    active_ids = {
        entry["person"]["id"]
        for entry in active_roster
        if entry.get("person")
    }

    players = {}

    for entry in forty_roster:

        person = entry.get("person", {})

        player_id = person.get("id")

        if not player_id:
            continue

        position = entry.get("position", {})

        player = {
            "id": player_id,
            "name": person.get("fullName", ""),
            "number": entry.get("jerseyNumber"),
            "position": normalize_position(position),
            "status": get_status(
                entry,
                player_id in active_ids
            ),
            "mlb_url": (
                f"https://www.mlb.com/player/"
                f"{player_id}"
            )
        }

        players[player_id] = player

    # ---------------------------------------------------------
    # 40-Manに存在する選手を基本にする
    # ---------------------------------------------------------

    result = list(players.values())

    # ---------------------------------------------------------
    # 並び順
    # Pitchers → Catchers → Infielders → Outfielders → Other
    # ---------------------------------------------------------

    order = {
        "Pitchers": 1,
        "Catchers": 2,
        "Infielders": 3,
        "Outfielders": 4,
        "Other": 5
    }

    result.sort(
        key=lambda player: (
            order.get(player["position"], 99),
            player["name"]
        )
    )

    output = {
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "source": "MLB Stats API",

        "source_url": (
            "https://statsapi.mlb.com/"
            "api/v1/teams/143/roster"
        ),

        "team": "Philadelphia Phillies",

        "team_id": TEAM_ID,

        "players": result
    }

    OUTPUT_FILE.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print(
        f"Updated {len(result)} players."
    )


if __name__ == "__main__":
    main()
