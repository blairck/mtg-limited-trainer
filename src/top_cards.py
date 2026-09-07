"""
Top Cards module - identifies the most valuable cards in a Magic set
based on a cumulative value threshold.
"""

import requests
from typing import List, Dict, Optional, Tuple
from config import CARD_COLOR

# Basic lands to exclude from results
EXCLUDED_CARDS = {
    "Swamp",
    "Mountain",
    "Island",
    "Plains",
    "Forest",
}


def fetch_cards_from_scryfall(set_code: str) -> List[Dict[str, any]]:
    """
    Fetch all cards from Scryfall API for the specified set.

    Args:
        set_code: Magic set identifier (e.g., 'sos', 'dft')

    Returns:
        List of card dictionaries from Scryfall API

    Raises:
        requests.RequestException: If the API request fails
    """
    headers = {"User-Agent": "MTG-Limited-Trainer/1.0 (+https://github.com/)"}

    url = f"https://api.scryfall.com/cards/search?q=set={set_code}&order=set"
    all_cards = []

    while url:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        all_cards.extend(data.get("data", []))

        # Handle pagination
        url = data.get("next_page")

    seen = {}
    filtered_cards = []
    for card in all_cards:
        if card["name"] not in seen:
            seen[card["name"]] = True
            filtered_cards.append(card)

    return filtered_cards


def filter_cards_by_rarity(
    cards: List[Dict[str, any]], rarities: List[str]
) -> List[Dict[str, any]]:
    """
    Filter cards by one or more rarity levels.

    Args:
        cards: List of card dictionaries
        rarities: List of rarity codes (e.g., ['common', 'uncommon', 'rare', 'mythic'])

    Returns:
        Filtered list of cards
    """
    rarity_set = {r.lower() for r in rarities}
    return [card for card in cards if card.get("rarity", "").lower() in rarity_set]


def filter_excluded_cards(cards: List[Dict[str, any]]) -> List[Dict[str, any]]:
    """
    Filter out excluded cards (e.g., basic lands).

    Args:
        cards: List of card dictionaries

    Returns:
        Filtered list without excluded cards
    """
    return [card for card in cards if card.get("name") not in EXCLUDED_CARDS]


def get_card_price(card: Dict[str, any]) -> float:
    """
    Extract the price from a card dictionary.
    Prefers USD pricing, falls back to other currencies.

    Args:
        card: Card dictionary from Scryfall

    Returns:
        Price as float, or 0.0 if not available
    """
    prices = card.get("prices", {})

    # Try USD first
    if prices.get("usd"):
        try:
            return float(prices["usd"])
        except (ValueError, TypeError):
            pass

    # Try other price sources
    for key in ["usd_foil", "eur", "eur_foil"]:
        if prices.get(key):
            try:
                return float(prices[key])
            except (ValueError, TypeError):
                pass

    return 0.0


def get_color_from_card(card: Dict[str, any]) -> str:
    """
    Extract the primary color from a card.

    Args:
        card: Card dictionary from Scryfall

    Returns:
        Single character color code (W, U, B, R, G) or 'L' for colorless/lands
    """
    colors = card.get("colors", [])

    if not colors:
        return "L"  # Colorless/Lands

    # Return the first color if multiple
    color_map = {"W": "W", "U": "U", "B": "B", "R": "R", "G": "G"}
    first_color = colors[0]

    return color_map.get(first_color, "L")


def find_top_cards_by_threshold(
    cards: List[Dict[str, any]], threshold_percent: float
) -> Tuple[List[Dict[str, any]], float]:
    """
    Find the minimum set of cards needed to meet or exceed the cumulative value threshold.

    Args:
        cards: List of card dictionaries with price data
        threshold_percent: Target percentage (0-100) of total value to reach

    Returns:
        Tuple of (selected cards sorted by price, total value of selected cards)
    """
    # Filter out cards with no price
    priced_cards = [c for c in cards if get_card_price(c) > 0]

    if not priced_cards:
        return [], 0.0

    # Calculate total value
    total_value = sum(get_card_price(card) for card in priced_cards)

    if total_value == 0:
        return [], 0.0

    # Convert threshold from percentage to absolute value
    threshold_value = (threshold_percent / 100.0) * total_value

    # Sort cards by price (highest to lowest)
    sorted_cards = sorted(priced_cards, key=lambda c: get_card_price(c), reverse=True)

    # Find minimum set of cards to meet threshold
    selected_cards = []
    cumulative_value = 0.0

    for card in sorted_cards:
        selected_cards.append(card)
        cumulative_value += get_card_price(card)

        if cumulative_value >= threshold_value:
            break

    return selected_cards, cumulative_value


def sort_by_color(cards: List[Dict[str, any]]) -> List[Dict[str, any]]:
    """
    Sort cards by color in standard MTG order: W, U, B, R, G, L (colorless/lands).

    Args:
        cards: List of card dictionaries

    Returns:
        Sorted list of cards
    """
    color_order = {"W": 0, "U": 1, "B": 2, "R": 3, "G": 4, "L": 5}

    return sorted(
        cards,
        key=lambda c: (color_order.get(get_color_from_card(c), 5), -get_card_price(c)),
    )


def format_output(
    cards: List[Dict[str, any]],
    total_value: float,
    threshold_percent: float,
    total_cards_considered: int = 0,
) -> str:
    """
    Format the output for display, sorted by color.

    Args:
        cards: List of selected card dictionaries
        total_value: Total cumulative value of selected cards
        threshold_percent: The threshold percentage that was used
        total_cards_considered: Total number of cards considered before selection

    Returns:
        Formatted string for display
    """
    sorted_cards = sort_by_color(cards)

    output = []
    output.append(
        f"\n{'='*70}\n"
        f"Top Cards (Cumulative Value: ${total_value:.2f})\n"
        f"{'='*70}\n"
    )

    current_color = None
    color_names = {
        "W": "White",
        "U": "Blue",
        "B": "Black",
        "R": "Red",
        "G": "Green",
        "L": "Colorless/Lands",
    }

    for card in sorted_cards:
        color = get_color_from_card(card)

        if color != current_color:
            if current_color is not None:
                output.append("")
            output.append(f"\n{color_names.get(color, color)}:")
            current_color = color

        price = get_card_price(card)
        name = card.get("name", "Unknown")
        rarity = card.get("rarity", "unknown").capitalize()
        output.append(f"  {name:<40} ${price:>7.2f} ({rarity})")

    output.append(f"\n{'='*70}")

    # Calculate and add card volume reduction metric
    if total_cards_considered > 0:
        reduction_percent = (1 - len(cards) / total_cards_considered) * 100
        output.append(f"\nReduced card volume by {reduction_percent:.1f}%")

    return "\n".join(output)


def get_top_cards(
    set_code: str, rarities: List[str], threshold_percent: float
) -> Tuple[List[Dict[str, any]], float, int]:
    """
    Main entry point to get top cards by cumulative value threshold.

    Args:
        set_code: Magic set identifier (e.g., 'sos', 'dft')
        rarities: List of rarity levels to include (e.g., ['common', 'uncommon'])
        threshold_percent: Target percentage (0-100) of total value

    Returns:
        Tuple of (selected cards sorted by color, total cumulative value, total cards considered)

    Raises:
        requests.RequestException: If API fetch fails
        ValueError: If invalid parameters provided
    """
    if not 0 <= threshold_percent <= 100:
        raise ValueError("Threshold percentage must be between 0 and 100")

    if not rarities:
        raise ValueError("At least one rarity level must be specified")

    # Fetch cards from Scryfall
    all_cards = fetch_cards_from_scryfall(set_code)

    # Filter by rarity
    filtered_cards = filter_cards_by_rarity(all_cards, rarities)

    # Exclude basic lands and other unwanted cards
    filtered_cards = filter_excluded_cards(filtered_cards)

    if not filtered_cards:
        raise ValueError(
            f"No cards found for set '{set_code}' with rarities {rarities}"
        )

    # Store count of cards considered before threshold selection
    total_cards_considered = len(filtered_cards)

    # Find cards meeting threshold
    selected_cards, total_value = find_top_cards_by_threshold(
        filtered_cards, threshold_percent
    )

    # Sort by color
    sorted_cards = sort_by_color(selected_cards)

    return sorted_cards, total_value, total_cards_considered
