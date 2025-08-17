"""
Card operations including pack generation and filtering.
"""

from typing import List, Dict, Set, Optional
from random import shuffle

from config import (
    CARD_RARITY,
    CARD_OHWR,
)


def filter_cards_by_rarity(
    cards: List[Dict[str, str]], rarity: str
) -> List[Dict[str, str]]:
    """Filter cards by rarity."""
    return [card for card in cards if card[CARD_RARITY] == rarity]


def remove_top_n_by_winrate(
    pack_cards: List[Dict[str, str]], cards_to_remove: int
) -> List[Dict[str, str]]:
    """Remove the top N cards by win rate from the pack."""
    if cards_to_remove > 0:
        pack_cards = sorted(pack_cards, key=lambda x: x[CARD_OHWR], reverse=True)[
            cards_to_remove:
        ]
    return pack_cards


def get_winrate_order(pack_cards: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Get cards sorted by win rate in descending order."""
    return sorted(pack_cards, key=lambda x: x[CARD_OHWR], reverse=True)
