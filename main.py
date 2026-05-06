"""
MTG Limited Trainer - Card Rating Quiz with difficulty selection
"""
import argparse
import random
import os
import sys

from config import (
    MAGIC_SET,
    QUIZ_RARITIES,
    QUIZ_RATING_KEY,
    CARDS_IN_QUIZ,
    CARD_COLOR,
    CARD_RARITY,
)
from src.data import load_card_data, load_exclude_list, convert_keys_to_float
from src.cards import filter_cards_by_rarity
from src.display import format_card_line, get_color_code, cprint


def ask_question(
    card: dict,
    idx: int,
    thresholds: list[float],
    labels: list[str],
    colors: list[str],
    rating_key: str,
) -> tuple[bool, int]:
    """Display one question and return True if the user answers correctly."""
    # Show question header
    cprint(f"{idx}. {format_card_line(card, False)}", get_color_code(card[CARD_COLOR]))
    # Show options based on difficulty segments
    for i, label in enumerate(labels):
        cprint(f"  {i+1}) {label}", colors[i])

    # Prompt until valid
    valid = [str(i + 1) for i in range(len(labels))]
    while True:
        ans = input(f"Your answer ({'/'.join(valid)}): ").strip()
        if ans in valid:
            chosen = int(ans) - 1
            val = float(card[rating_key])
            # Determine correct segment
            correct_idx = len(thresholds)
            for i, th in enumerate(thresholds):
                if val < th:
                    correct_idx = i
                    break
            return chosen == correct_idx, chosen
        print("Invalid choice, please try again.")


def prepare_difficulty_thresholds(
    quiz_cards: list[dict],
    rating_key: str,
    difficulty: str,
) -> tuple[list[float], list[str], list[str]]:
    """Determine rating bounds and configure thresholds, labels, and colors for difficulty levels."""
    values = [float(c[rating_key]) for c in quiz_cards]
    sorted_vals = sorted(values)
    n_vals = len(sorted_vals)

    if difficulty == "easy":
        # tertiles
        idxs = [n_vals // 3, (2 * n_vals) // 3]
        labels = ["bad", "okay", "good"]
        colors = ["red", "yellow", "green"]
    elif difficulty == "medium":
        # quartiles
        idxs = [n_vals // 4, n_vals // 2, (3 * n_vals) // 4]
        labels = ["bad", "okay", "good", "great"]
        colors = ["red", "yellow", "green", "blue"]
    else:
        # hard quintiles
        idxs = [n_vals // 5, (2 * n_vals) // 5, (3 * n_vals) // 5, (4 * n_vals) // 5]
        labels = ["bad", "okay", "good", "great", "amazing"]
        colors = ["red", "yellow", "green", "blue", "magenta"]

    thresholds = [sorted_vals[i] for i in idxs]
    return thresholds, labels, colors


def load_and_filter_cards(
    rarities: list[str],
) -> list[dict]:
    """Load card data, convert keys to float, and filter by rarity and exclude list."""
    cards = load_card_data(MAGIC_SET)
    convert_keys_to_float(cards)
    exclude = load_exclude_list(MAGIC_SET)
    # Filter by rarity and exclude list
    quiz_cards = []
    for r in rarities:
        quiz_cards.extend(filter_cards_by_rarity(cards, r))
    quiz_cards = [c for c in quiz_cards if c["Name"] not in exclude]
    return quiz_cards


def print_rating_ranges(thresholds, labels, difficulty):
    """Print the rating ranges for each difficulty level."""
    print(f"Difficulty: {difficulty.capitalize()}")
    print("Rating ranges:")
    for th, label in zip(thresholds, labels):
        print(f"  {label}: < {th:.1f}")
    print(f"  {labels[-1]}: >= {thresholds[-1]:.1f}")


def apply_threshold_rating(card, rating_key, thresholds, labels):
    thresholdLabelMappings = []
    for threshold, label in zip(thresholds, labels):
        thresholdLabelMappings.append({"threshold": threshold, "label": label})

    for thresholdLabel in thresholdLabelMappings:
        if card[rating_key] < thresholdLabel["threshold"]:
            return thresholdLabel["label"]

    return labels[-1]


def get_arguments():
    parser = argparse.ArgumentParser(
        description="Run a rating quiz on MTG cards with adjustable difficulty ranges"
    )
    parser.add_argument(
        "--rarities",
        nargs="+",
        default=QUIZ_RARITIES,
        help="Card rarities to include (e.g. C U)",
    )
    parser.add_argument(
        "--rating-key",
        default=QUIZ_RATING_KEY,
        help="Rating field to quiz on (e.g. CARD_OHWR)",
    )
    parser.add_argument(
        "--num-questions",
        type=int,
        default=CARDS_IN_QUIZ,
        help="Number of questions in the quiz",
    )
    parser.add_argument(
        "--difficulty",
        choices=["easy", "medium", "hard"],
        default="medium",
        help="Difficulty: easy=tertiles, medium=quartiles, hard=quintiles",
    )
    return parser.parse_args()


def verify_resources():
    # Ensure resources directory exists
    resources_path = os.path.join(os.getcwd(), "resources", "sets", MAGIC_SET)
    if not os.path.isdir(resources_path):
        print(f"Error: Resource directory '{resources_path}' not found.")
        print(
            "Please follow the setup instructions in README.md to download the required data files."
        )
        sys.exit(1)


def run_quiz(quiz_cards, thresholds, labels, colors, rating_key, num_questions):
    # Generate initial question set by sampling cards and attaching full option lists
    questions = random.sample(quiz_cards, num_questions)
    # Each entry: (card, thresholds, labels, colors)
    remaining = [
        (
            card,
            thresholds.copy(),
            labels.copy(),
            colors.copy(),
        )
        for card in questions
    ]
    original_card_list = remaining
    while True:
        round_num = 1
        offer_retry = False
        while remaining:
            print(f"\n--- Round {round_num}: {len(remaining)} question(s) ---")
            wrong = []
            for i, (card, thr, lab, col) in enumerate(remaining, start=1):
                correct, chosen = ask_question(card, i, thr, lab, col, rating_key)
                if correct:
                    cprint("Correct", "green")
                else:
                    cprint("Wrong", "red")
                    # remove chosen wrong option for next round
                    new_thr = thr.copy()
                    new_lab = lab.copy()
                    new_col = col.copy()
                    # remove corresponding label/color and threshold
                    new_lab.pop(chosen)
                    new_col.pop(chosen)
                    if len(new_thr) > chosen:
                        new_thr.pop(chosen)
                    else:
                        # if removing last label, drop last threshold
                        new_thr.pop(-1)
                    wrong.append((card, new_thr, new_lab, new_col))
            num = len(remaining)
            correct_count = num - len(wrong)
            amount_correct = 100 * correct_count / num
            if amount_correct < 100:
                offer_retry = True
            print(f"You answered {amount_correct:.1f}% correct this round.")
            if wrong:
                print("Repeating wrong questions...\n")
                random.shuffle(wrong)
                remaining = wrong
                round_num += 1
            else:
                break

        print("\nQuiz complete!")
        if offer_retry:
            print("You scored below 100% in round 1.")
            retry = input("Would you like to retry the quiz? (y/n): ").strip().lower()
            if retry == "n":
                pass
            else:
                remaining = original_card_list.copy()
                random.shuffle(remaining)
                continue
        break


def main():
    args = get_arguments()

    verify_resources()

    quiz_cards = load_and_filter_cards(args.rarities)

    thresholds, labels, colors = prepare_difficulty_thresholds(
        quiz_cards, args.rating_key, args.difficulty
    )

    print_rating_ranges(thresholds, labels, args.difficulty)

    run_quiz(
        quiz_cards,
        thresholds,
        labels,
        colors,
        args.rating_key,
        args.num_questions,
    )


if __name__ == "__main__":
    main()
