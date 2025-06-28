"""
MTG Limited Trainer - Main application entry point.

This application helps train Magic: The Gathering limited format skills
by presenting simulated card packs and evaluating card pick decisions
against optimal win rate data.
"""

from random import shuffle

from src.config import MAGIC_SET, TOTAL_PACKS
from src.data import (
    load_card_data,
    load_exclude_list,
    convert_ohwr_to_float,
)
from src.cards import (
    filter_cards_by_rarity,
    draw_pack,
    remove_top_n_by_winrate,
    get_winrate_order,
)
from src.game_logic import (
    get_cards_to_remove,
    evaluate_picks,
    should_advance,
    calculate_max_possible_score,
)
from src.display import print_intro, print_pack, get_user_input, print_pick_summary


def initialize_game():
    """Initialize the game by loading card data and filtering by rarity."""
    cards = load_card_data(MAGIC_SET)
    common_cards = filter_cards_by_rarity(cards, "C")
    uncommon_cards = filter_cards_by_rarity(cards, "U")
    exclude_cards = load_exclude_list(MAGIC_SET)

    return common_cards, uncommon_cards, exclude_cards


def main():
    """Main game loop."""
    print_intro()

    # Initialize game data
    common_cards, uncommon_cards, exclude_cards = initialize_game()

    overall_score = 0
    pack = 0

    while True:
        cards_to_remove = get_cards_to_remove(pack)
        pack_cards = draw_pack(common_cards, uncommon_cards, exclude_cards)
        convert_ohwr_to_float(pack_cards)
        pack_cards = remove_top_n_by_winrate(pack_cards, cards_to_remove)
        shuffle(pack_cards)

        card_lookup_by_pack_sort = print_pack(pack_cards)
        print("- - - - - - - ")

        parsed_input = get_user_input(pack_cards)
        winrate_order = get_winrate_order(pack_cards)
        user_score, pick_results = evaluate_picks(
            parsed_input, card_lookup_by_pack_sort, winrate_order
        )

        print(f"\nYour pick accuracy score: {user_score}/5")
        print_pick_summary(pick_results, pack_cards)

        overall_score += user_score
        pack += 1

        if not should_advance(user_score):
            print(f"You did not match enough cards. Game over.")
            break
        if pack >= TOTAL_PACKS:
            break

    max_score = calculate_max_possible_score(TOTAL_PACKS)
    print(
        f"\nOverall score: {overall_score} points out of {max_score} possible points."
    )


if __name__ == "__main__":
    main()
