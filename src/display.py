"""
Display and formatting utilities for the MTG Limited Trainer.
"""

from typing import Dict, List, Tuple
from termcolor import cprint

from config import CARD_NAME, CARD_COLOR, CARD_RARITY, CARD_OHWR


def make_clickable_link(url: str, text: str = "link") -> str:
    """Create a clickable terminal link."""
    return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"


def get_color_code(card_color: str) -> str:
    """Get the terminal color code for a card color."""
    if card_color == "G":
        return "green"
    elif card_color == "W":
        return "white"
    elif card_color == "U":
        return "blue"
    elif card_color == "B":
        return "black"
    elif card_color == "R":
        return "red"
    elif len(card_color) > 1:
        return "yellow"
    # For colorless cards or any other case, use a string color name
    # that termcolor supports instead of an RGB tuple
    return "magenta"


def get_card_url(card_name: str) -> str:
    """Generate a Scryfall search URL for the given card name."""
    return f"https://scryfall.com/search?q={card_name.replace(' ', '+')}"


def format_card_line(card: Dict[str, str], show_percent: bool = False) -> str:
    """
    Format a card line with name, rarity, and clickable link.
    Optionally includes the win rate percentage.
    """
    name = card[CARD_NAME]
    rarity = card[CARD_RARITY]
    url = get_card_url(name)
    link = make_clickable_link(url, "link")

    if show_percent:
        percent = card[CARD_OHWR]
        return f"{name} ({rarity}) - {link} - {percent}"
    return f"{name} ({rarity}) - {link}"


def print_intro() -> None:
    """Print the game introduction."""
    print("Welcome to the MTG Card Selection Game!")
    print("You will be presented with 3 packs of cards.")
    print(
        "For each pack, you will select 5 cards based on their Win Rate Order (OH WR)."
    )
    print(
        "Your goal is to match the top 5 cards by Win Rate Order as closely as possible."
    )
    print("Let's begin!\n")


def print_pack(pack_cards: List[Dict[str, str]]) -> Dict[int, Dict[str, str]]:
    """Print the cards in a pack and return a lookup dictionary."""
    card_lookup_by_pack_sort = {}
    for index, card in enumerate(pack_cards):
        line_text = f"{index+1}. {format_card_line(card)}"
        card["PackIndex"] = index + 1
        card_lookup_by_pack_sort[index + 1] = card
        cprint(line_text, get_color_code(card[CARD_COLOR]))
    return card_lookup_by_pack_sort


def get_user_input(pack_cards: List[Dict[str, str]]) -> List[int]:
    """Get user input for card selection."""
    while True:
        try:
            user_input = input(
                f"Please enter your selection as comma separated numbers (1-{len(pack_cards)}): "
            )
            parsed_input = list(int(i) for i in user_input.split(","))
            if len(parsed_input) == 5 and all(
                1 <= i <= len(pack_cards) for i in parsed_input
            ):
                return parsed_input
            else:
                print(
                    f"Invalid input. Please enter exactly 5 numbers between 1 and {len(pack_cards)}."
                )
        except ValueError:
            print("Invalid input. Please enter valid integers.")


def print_pick_summary(
    pick_results: List[Tuple], pack_cards: List[Dict[str, str]]
) -> None:
    """Print a summary of the user's picks."""
    print("Pick summary:")
    for result in pick_results:
        pick_num = result[0]

        if result[2] == True:
            card = next((c for c in pack_cards if c[CARD_NAME] == result[1]), None)
            card_text = format_card_line(card, True)
            cprint(
                f"Pick {pick_num}: {card_text} - Correct",
                get_color_code(card[CARD_COLOR]),
            )
        elif result[1] is not None:
            user_card = next((c for c in pack_cards if c[CARD_NAME] == result[1]), None)
            best_card = next((c for c in pack_cards if c[CARD_NAME] == result[3]), None)

            # Print user pick
            if user_card:
                user_str = format_card_line(user_card, True)
                cprint(
                    f"Pick {pick_num}: {user_str}",
                    get_color_code(user_card[CARD_COLOR]),
                )
            else:
                print(f"Pick {pick_num}: {result[1]}")

            # Print best pick
            if best_card:
                best_str = format_card_line(best_card, True)
                cprint(
                    f"\t - Wrong, best pick is: {best_str}",
                    get_color_code(best_card[CARD_COLOR]),
                )
            else:
                print(f"\t - Wrong, best pick is: {result[3]}")
        else:
            print(f"Pick {pick_num}: Invalid selection")
