#!/usr/bin/env python3
"""
Build script for NFL Key Numbers widget.

Pulls latest games.csv from nflverse-data 'schedules' release,
processes into compact JSON, and injects into the HTML template
to produce a single self-contained index.html.

Run locally:  python build.py
Run in CI:    triggered by the GitHub Action in .github/workflows/update-data.yml
"""
import json
import sys
import urllib.request
from pathlib import Path

NFLVERSE_URL = "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv"
ROOT = Path(__file__).parent
TEMPLATE_PATH = ROOT / "template.html"
OUTPUT_PATH = ROOT / "index.html"
DATA_PATH = ROOT / "games_data.json"


def fetch_games_csv() -> str:
    """Download the latest games.csv from nflverse releases."""
    print(f"Fetching {NFLVERSE_URL} ...")
    req = urllib.request.Request(
        NFLVERSE_URL,
        headers={"User-Agent": "nfl-key-numbers-build/1.0"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def parse_csv(csv_text: str) -> list[list]:
    """
    Parse the games CSV into compact records.
    Each record: [season, game_type_code, abs_margin, total_points, abs_spread]
    where game_type_code: 0 = REG, 1 = postseason (WC/DIV/CON/SB)
    """
    import csv
    from io import StringIO

    reader = csv.DictReader(StringIO(csv_text))
    records = []
    skipped = 0
    for row in reader:
        try:
            away = row["away_score"].strip()
            home = row["home_score"].strip()
            spread_line = row["spread_line"].strip()
            # Skip games without final scores (future games)
            if not away or not home or away == "NA" or home == "NA":
                skipped += 1
                continue
            away_score = int(float(away))
            home_score = int(float(home))
            season = int(row["season"])
            gt_raw = row["game_type"].strip()
            gt = 0 if gt_raw == "REG" else 1
            margin = abs(home_score - away_score)
            total = away_score + home_score
            # Spread may be missing for some games — default to 0 if blank
            if spread_line and spread_line != "NA":
                spread = abs(float(spread_line))
                spread = round(spread * 2) / 2
            else:
                spread = 0.0
            records.append([season, gt, margin, total, spread])
        except (ValueError, KeyError) as e:
            skipped += 1
            continue
    print(f"Parsed {len(records)} completed games (skipped {skipped})")
    return records


def write_json(records: list, path: Path) -> None:
    with path.open("w") as f:
        json.dump(records, f, separators=(",", ":"))
    size_kb = path.stat().st_size / 1024
    print(f"Wrote {path.name}: {size_kb:.1f} KB")


def inject_template(records: list) -> None:
    """Inject data array into template.html and write index.html."""
    if not TEMPLATE_PATH.exists():
        print(f"ERROR: {TEMPLATE_PATH} not found", file=sys.stderr)
        sys.exit(1)
    template = TEMPLATE_PATH.read_text()
    placeholder = "__DATA_PLACEHOLDER__"
    if placeholder not in template:
        print(f"ERROR: placeholder '{placeholder}' not in template", file=sys.stderr)
        sys.exit(1)
    data_json = json.dumps(records, separators=(",", ":"))
    data_block = f"const EMBEDDED_DATA = {data_json};"
    output = template.replace(placeholder, data_block)
    OUTPUT_PATH.write_text(output)
    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"Wrote {OUTPUT_PATH.name}: {size_kb:.1f} KB ({len(records)} games)")


def main() -> int:
    try:
        csv_text = fetch_games_csv()
    except Exception as e:
        print(f"ERROR: failed to fetch nflverse data: {e}", file=sys.stderr)
        return 1

    records = parse_csv(csv_text)
    if len(records) < 5000:
        print(f"WARNING: only {len(records)} games parsed — refusing to update", file=sys.stderr)
        return 1

    write_json(records, DATA_PATH)
    inject_template(records)
    seasons = sorted({r[0] for r in records})
    print(f"Season coverage: {seasons[0]}–{seasons[-1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
