import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


# =========================================================
# SETTINGS
# =========================================================

TEAM = "PHI"
SEASON = 2026

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = ROOT_DIR / "savant.json"

HEADERS = {
    "User-Agent": "Phillies-Daily/1.0"
}


# =========================================================
# URLS
# =========================================================

BATTER_EXPECTED_URL = (
    "https://baseballsavant.mlb.com/leaderboard/"
    "expected_statistics"
)

PITCHER_EXPECTED_URL = (
    "https://baseballsavant.mlb.com/leaderboard/"
    "expected_statistics"
)

BATTER_PERCENTILE_URL = (
    "https://baseballsavant.mlb.com/leaderboard/"
    "percentile-rankings"
)

PITCHER_PERCENTILE_URL = (
    "https://baseballsavant.mlb.com/leaderboard/"
    "percentile-rankings"
)


# =========================================================
# HTTP
# =========================================================

def download_csv(url, params):
    print()
    print("Downloading:")
    print(url)

    response = requests.get(
        url,
        params=params,
        headers=HEADERS,
        timeout=60
    )

    response.raise_for_status()

    text = response.content.decode(
        "utf-8-sig",
        errors="replace"
    )

    if not text.strip():
        raise RuntimeError(
            "Baseball Savant returned an empty response."
        )

    return list(
        csv.DictReader(
            io.StringIO(text)
        )
    )


# =========================================================
# VALUE CONVERSION
# =========================================================

def clean_value(value):
    if value is None:
        return None

    value = str(value).strip()

    if value == "":
        return None

    return value


def number_or_string(value):
    value = clean_value(value)

    if value is None:
        return None

    try:
        if "." in value:
            return float(value)

        return int(value)

    except ValueError:
        return value


# =========================================================
# PLAYER ID
# =========================================================

def get_player_id(row):
    candidates = [
        "player_id",
        "mlbam_id",
        "playerid",
        "id"
    ]

    for key in candidates:
        value = row.get(key)

        if value:
            try:
                return int(value)
            except ValueError:
                pass

    return None


# =========================================================
# PLAYER NAME
# =========================================================

def get_player_name(row):
    name = row.get("player_name")

    if name:
        return name.strip()

    first = (
        row.get("first_name")
        or row.get("firstname")
        or ""
    ).strip()

    last = (
        row.get("last_name")
        or row.get("lastname")
        or ""
    ).strip()

    if first or last:
        return f"{first} {last}".strip()

    return ""


# =========================================================
# EXPECTED STATISTICS
# =========================================================

def fetch_expected_statistics(player_type):
    params = {
        "type": player_type,
        "year": SEASON,
        "position": "",
        "team": TEAM,
        "filterType": "pa",
        "min": "0",
        "csv": "true"
    }

    rows = download_csv(
        BATTER_EXPECTED_URL
        if player_type == "batter"
        else PITCHER_EXPECTED_URL,
        params
    )

    print(
        f"{player_type}: "
        f"{len(rows)} expected-stat rows"
    )

    return rows


# =========================================================
# PERCENTILE RANKINGS
# =========================================================

def fetch_percentile_rankings(player_type):
    params = {
        "type": player_type,
        "year": SEASON,
        "position": "",
        "team": TEAM,
        "csv": "true"
    }

    rows = download_csv(
        BATTER_PERCENTILE_URL
        if player_type == "batter"
        else PITCHER_PERCENTILE_URL,
        params
    )

    print(
        f"{player_type}: "
        f"{len(rows)} percentile rows"
    )

    return rows


# =========================================================
# NORMALIZE ROW
# =========================================================

def normalize_row(row):
    result = {}

    for key, value in row.items():

        if key is None:
            continue

        key = key.strip()

        if not key:
            continue

        result[key] = number_or_string(value)

    player_id = get_player_id(row)

    if player_id is not None:
        result["player_id"] = player_id

    name = get_player_name(row)

    if name:
        result["player_name"] = name

    return result


# =========================================================
# MERGE
# =========================================================

def merge_player_data(expected_rows, percentile_rows):
    players = {}

    for row in expected_rows:

        normalized = normalize_row(row)

        player_id = normalized.get(
            "player_id"
        )

        if player_id is None:
            continue

        players[player_id] = normalized


    for row in percentile_rows:

        normalized = normalize_row(row)

        player_id = normalized.get(
            "player_id"
        )

        if player_id is None:
            continue

        if player_id not in players:
            players[player_id] = {
                "player_id": player_id
            }

        players[player_id].update(
            normalized
        )


    return list(
        players.values()
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "=========================================="
    )

    print(
        "Phillies Baseball Savant updater"
    )

    print(
        f"Season: {SEASON}"
    )

    print(
        f"Team: {TEAM}"
    )

    print(
        "=========================================="
    )


    # -----------------------------------------------------
    # BATTERS
    # -----------------------------------------------------

    batter_expected = (
        fetch_expected_statistics(
            "batter"
        )
    )

    batter_percentile = (
        fetch_percentile_rankings(
            "batter"
        )
    )


    batters = merge_player_data(
        batter_expected,
        batter_percentile
    )


    # -----------------------------------------------------
    # PITCHERS
    # -----------------------------------------------------

    pitcher_expected = (
        fetch_expected_statistics(
            "pitcher"
        )
    )

    pitcher_percentile = (
        fetch_percentile_rankings(
            "pitcher"
        )
    )


    pitchers = merge_player_data(
        pitcher_expected,
        pitcher_percentile
    )


    # -----------------------------------------------------
    # OUTPUT
    # -----------------------------------------------------

    output = {

        "team": "Philadelphia Phillies",

        "teamAbbreviation": TEAM,

        "season": SEASON,

        "source": "Baseball Savant",

        "sourceUrl":
            "https://baseballsavant.mlb.com/",

        "updatedAt":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "batters":
            batters,

        "pitchers":
            pitchers
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
        "=========================================="
    )

    print(
        f"Batters: {len(batters)}"
    )

    print(
        f"Pitchers: {len(pitchers)}"
    )

    print(
        f"Saved: {OUTPUT_FILE}"
    )

    print(
        "=========================================="
    )


if __name__ == "__main__":
    main()
