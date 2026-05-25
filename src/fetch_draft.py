"""
Fetch draft picks and game results from 17Lands for a given draft ID.

Usage:
    python -m src.fetch_draft <draft_id> [<draft_id> ...] [--output-dir PATH]

Each draft is saved as {output_dir}/{draft_id}.json.
Draft IDs are found in the 17Lands URL, e.g.:
    https://www.17lands.com/draft/b2fe067a99b84c13a754449cc0a52f11
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""

import argparse
import json
import os
import sys

import requests

from config import DRAFT_DATA_DIR

BASE_URL = "https://www.17lands.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch_draft_picks(draft_id: str) -> dict:
    """
    Fetch picks from the draft stream endpoint.
    Returns the raw payload dict with 'expansion' and 'picks'.
    """
    url = f"{BASE_URL}/data/draft/stream"
    resp = requests.get(url, params={"draft_id": draft_id}, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    raw = resp.text
    if raw.startswith("data: "):
        raw = raw[6:]
    return json.loads(raw)["payload"]


def fetch_draft_details(draft_id: str) -> dict:
    """
    Fetch game results and metadata from the details endpoint.
    Returns the response dict with 'format', 'wins', 'losses', etc.
    """
    url = f"{BASE_URL}/data/details"
    resp = requests.get(url, params={"draft_id": draft_id}, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def build_draft_json(draft_id: str, picks_payload: dict, details: dict) -> dict:
    """Combine API responses into the output schema."""
    picks = []
    for p in picks_payload["picks"]:
        picked_name = p["pick"]["name"]
        available = [
            {"name": card["name"], "picked": card["name"] == picked_name}
            for card in p["available"]
        ]
        picks.append(
            {
                "pack": p["pack_number"] + 1,
                "pick": p["pick_number"] + 1,
                "available": available,
            }
        )

    return {
        "draft_id": draft_id,
        "expansion": details["expansion"],
        "format": details["format"],
        "wins": details["wins"],
        "losses": details["losses"],
        "picks": picks,
    }


def save_draft(output_dir: str, draft_data: dict) -> str:
    """Write draft data to {output_dir}/{draft_id}.json. Returns the file path."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{draft_data['draft_id']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(draft_data, f, indent=2)
    return path


def process_draft(draft_id: str, output_dir: str) -> None:
    out_path = os.path.join(output_dir, f"{draft_id}.json")

    if os.path.exists(out_path):
        print(f"[skip]  {draft_id} — already saved at {out_path}")
        return

    print(f"[fetch] {draft_id}")
    try:
        picks_payload = fetch_draft_picks(draft_id)
        details = fetch_draft_details(draft_id)
    except requests.HTTPError as e:
        print(f"[error] {draft_id} — HTTP {e.response.status_code}", file=sys.stderr)
        return
    except requests.RequestException as e:
        print(f"[error] {draft_id} — {e}", file=sys.stderr)
        return

    draft_data = build_draft_json(draft_id, picks_payload, details)
    saved_path = save_draft(output_dir, draft_data)
    print(
        f"[saved] {saved_path}  "
        f"({draft_data['expansion']} {draft_data['format']}, "
        f"{draft_data['wins']}-{draft_data['losses']}, "
        f"{len(draft_data['picks'])} picks)"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch 17Lands draft data for one or more draft IDs."
    )
    parser.add_argument(
        "draft_ids",
        nargs="+",
        metavar="DRAFT_ID",
        help="One or more 17Lands draft IDs (from the URL).",
    )
    parser.add_argument(
        "--output-dir",
        default=DRAFT_DATA_DIR,
        metavar="PATH",
        help=f"Directory to save JSON files (default: {DRAFT_DATA_DIR}).",
    )
    args = parser.parse_args()

    for draft_id in args.draft_ids:
        process_draft(draft_id, args.output_dir)


if __name__ == "__main__":
    main()
