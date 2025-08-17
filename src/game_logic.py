"""
Game logic for scoring, evaluation, and game flow.
"""

from typing import List, Dict, Tuple

from config import CARD_NAME


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
