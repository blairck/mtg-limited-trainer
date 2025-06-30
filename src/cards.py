"""
Card operations including pack generation and filtering.
"""

from typing import List, Dict, Set, Optional
from random import shuffle

from config import (
    CARD_RARITY,
    CARD_NAME,
    CARD_OHWR,
    COMMONS_PER_PACK,
    UNCOMMONS_PER_PACK,
)


def filter_cards_by_rarity(
    cards: List[Dict[str, str]], rarity: str
) -> List[Dict[str, str]]:
    """Filter cards by rarity."""
    return [card for card in cards if card[CARD_RARITY] == rarity]


def draw_pack(
    common_cards: List[Dict[str, str]],
    uncommon_cards: List[Dict[str, str]],
    exclude: Optional[Set[str]] = None,
) -> List[Dict[str, str]]:
    """
    Draw a pack of cards with the specified number of commons and uncommons.
    Excludes cards in the exclude set if provided.
    """
    result = []
    seen = set()
    shuffle(common_cards)
    shuffle(uncommon_cards)

    # Add up to COMMONS_PER_PACK unique commons
    for card in common_cards:
        card_id = card.get(CARD_NAME)
        if card_id not in seen and (exclude is None or card_id not in exclude):
            result.append(card)
            seen.add(card_id)
        if len(result) == COMMONS_PER_PACK:
            break

    # Add up to UNCOMMONS_PER_PACK unique uncommons (not already in result)
    for card in uncommon_cards:
        card_id = card.get(CARD_NAME)
        if card_id not in seen and (exclude is None or card_id not in exclude):
            result.append(card)
            seen.add(card_id)
        if len(result) == COMMONS_PER_PACK + UNCOMMONS_PER_PACK:
            break

    return result


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
