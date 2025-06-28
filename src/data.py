"""
Data management utilities for loading and validating card data.
"""

import csv
import os
import glob
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Set

from .config import MAGIC_SET, STALE_DATA_CUTOFF_DAYS, CARD_OHWR
from .display import make_clickable_link


def find_most_recent_csv(set_name: str) -> str:
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
            f"https://www.17lands.com/card_data?expansion={set_name}&format=PremierDraft&start=2025-06-10&view=table&columns=opening",
            "17lands.com",
        )

        if (current_date - file_date) > timedelta(days=STALE_DATA_CUTOFF_DAYS):
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
    cards = [card for card in cards if card[CARD_OHWR] != ""]
    return cards


def load_exclude_list(set_name: str) -> Set[str]:
    """Load the exclude list from exclude.csv if it exists."""
    exclude_file_path = f"resources/sets/{set_name}/exclude.csv"
    exclude_list = set()

    if os.path.exists(exclude_file_path):
        try:
            with open(exclude_file_path, encoding="utf-8-sig") as csvfile:
                csvreader = csv.reader(csvfile, delimiter=",", quotechar='"')
                first = True
                for row in csvreader:
                    if first:
                        first = False  # Skip header row
                    else:
                        if row and len(row) > 0:  # Check if row is not empty
                            # Add card name to exclude set
                            exclude_list.add(row[0])
        except Exception as e:
            print(f"Warning: Could not load exclude file {exclude_file_path}: {e}")

    return exclude_list


def convert_ohwr_to_float(cards: List[Dict[str, str]]) -> None:
    """Convert OH WR percentage strings to float values in place."""
    for card in cards:
        try:
            card[CARD_OHWR] = float(card[CARD_OHWR].replace("%", ""))
        except (AttributeError, ValueError):
            pass
