"""
Data management utilities for loading and validating card data.
"""

import csv
import os
import glob
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Set

from config import QUIZ_RATING_KEY, STALE_DATA_CUTOFF_DAYS, CARD_OHWR
from .display import make_clickable_link


def find_most_recent_csv(set_name: str, testing=False) -> str:
    """Find the most recent card-ratings CSV file for the given set."""
    pattern = f"resources/sets/{set_name}/card-ratings-*.csv"
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(
            f"No CSV files found for set '{set_name}' in pattern: {pattern}"
        )

    # Sort by filename (which includes the date) in descending order
    files.sort(reverse=True)
    most_recent_file = files[0]

    # Extract date from filename and check if it's more than 1 week old
    filename = os.path.basename(most_recent_file)
    try:
        # Extract date from filename like 'card-ratings-2025-06-18.csv'
        date_str = filename.replace("card-ratings-", "").replace(".csv", "")
        file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        current_date = datetime.now().date()

        clickable_link = make_clickable_link(
            f"https://www.17lands.com/card_data?expansion={set_name}&format=PremierDraft&start=2025-06-10&view=table",
            "17lands.com",
        )

        if (current_date - file_date) > timedelta(
            days=STALE_DATA_CUTOFF_DAYS
        ) and not testing:
            print(
                f"Error: The most recent data file is from {file_date.strftime('%Y-%m-%d')}, "
                f"which is more than {STALE_DATA_CUTOFF_DAYS} days old."
                f"\nGo to {clickable_link} to retrieve the latest data file for {set_name}."
            )
            print(f"Please update the data files in resources/sets/{set_name}/")
            sys.exit(1)
    except ValueError:
        print(f"Error: Could not parse date from filename: {filename}")
        sys.exit(1)

    return most_recent_file


def load_card_data(set_name: str) -> List[Dict[str, str]]:
    """Load card data from the most recent CSV file for the given set."""
    csv_file_path = find_most_recent_csv(set_name)
    cards = []

    with open(csv_file_path, encoding="utf-8-sig") as csvfile:
        csvreader = csv.reader(csvfile, delimiter=",", quotechar='"')

        first = True
        for row in csvreader:
            if first:
                card_fields = row
                first = False
            else:
                new_card = {}
                for j in range(0, len(card_fields)):
                    new_card[card_fields[j]] = row[j]
                cards.append(new_card)

    # Filter out cards without OH WR data
    cards = [card for card in cards if card[QUIZ_RATING_KEY] != ""]
    return cards


def load_exclude_list(set_name: str) -> set:
    """Load a CSV file of card names to exclude for the given set."""
    path = f"resources/sets/{set_name}/exclude.csv"
    if not os.path.exists(path):
        return set()

    exclude = set()
    with open(path, encoding="utf-8") as f:
        next(f)  # skip header
        for line in f:
            name = line.strip()
            if name:
                exclude.add(name)
    return exclude


def convert_keys_to_float(cards: List[Dict[str, str]]) -> None:
    """Convert percentage strings to float values in place."""
    for card in cards:
        try:
            card[QUIZ_RATING_KEY] = float(card[QUIZ_RATING_KEY].replace("%", ""))
        except (AttributeError, ValueError):
            pass
