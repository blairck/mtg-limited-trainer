"""
Game logic for scoring, evaluation, and game flow.
"""

from typing import List, Dict, Tuple

from config import CARD_NAME, PICKS_PER_PACK, ADVANCE_THRESHOLD


def get_cards_to_remove(pack_number: int) -> int:
    """Calculate how many top cards to remove based on pack number."""
    return 0 if pack_number == 0 else pack_number * PICKS_PER_PACK


def evaluate_picks(
    parsed_input: List[int],
    card_lookup_by_pack_sort: Dict[int, Dict[str, str]],
    winrate_order: List[Dict[str, str]],
) -> Tuple[int, List[Tuple]]:
    """
    Evaluate user picks against the optimal winrate order.
    Returns the score and detailed pick results.
    """
    user_score = 0
    pick_results = []

    for j, pick in enumerate(parsed_input):
        user_card = card_lookup_by_pack_sort.get(pick)
        winrate_card = winrate_order[j] if j < len(winrate_order) else None

        if (
            user_card
            and winrate_card
            and user_card[CARD_NAME] == winrate_card[CARD_NAME]
        ):
            user_score += 1
            pick_results.append((j + 1, user_card[CARD_NAME], True))
        else:
            user_name = user_card[CARD_NAME] if user_card else None
            winrate_name = winrate_card[CARD_NAME] if winrate_card else None
            pick_results.append((j + 1, user_name, False, winrate_name))

    return user_score, pick_results


def should_advance(score: int) -> bool:
    """Determine if the player should advance based on their score."""
    return score >= ADVANCE_THRESHOLD


def calculate_max_possible_score(total_packs: int) -> int:
    """Calculate the maximum possible score for the game."""
    return total_packs * PICKS_PER_PACK
