"""
MTG Limited Trainer - Multiple-Choice Rating Quiz (main_v2.py)

This entry point implements the quiz described in design.md: 
- A set of multiple-choice questions on card ratings
- Repeats wrong questions until all are correct
"""
import argparse
import random
import time

from config import (
    MAGIC_SET,
    QUIZ_RARITIES,
    QUIZ_RATING_KEY,
    COMMONS_PER_PACK,
    UNCOMMONS_PER_PACK,
    CARD_COLOR,
    QUIZ_ANSWER_DELAY,
)
from src.data import load_card_data, load_exclude_list, convert_ohwr_to_float
from src.cards import filter_cards_by_rarity
from src.display import format_card_line, get_color_code, cprint
from src.quiz import generate_questions, Question


def ask_question(q: Question, idx: int, low_th: float, high_th: float) -> bool:
    """Display one question and return True if the user answers correctly."""
    card = q.card
    # Show question header
    cprint(f"{idx}. {format_card_line(card, False)}", get_color_code(card[CARD_COLOR]))
    # Pause after showing card before options
    time.sleep(QUIZ_ANSWER_DELAY)
    # Show options with color based on value
    for i, opt in enumerate(q.options):
        letter = chr(ord("a") + i)
        # choose color by global tertile thresholds
        if opt < low_th:
            col = "red"
        elif opt < high_th:
            col = "yellow"
        else:
            col = "green"
        cprint(f"  {letter}) {opt}", col)

    # Prompt until valid
    valid_letters = [chr(ord("a") + i) for i in range(len(q.options))]
    while True:
        ans = input(f"Your answer ({'/'.join(valid_letters)}): ").strip().lower()
        if ans in valid_letters:
            chosen = ord(ans) - ord("a")
            is_correct = chosen in q.correct_indices
            return is_correct, chosen
        print("Invalid choice, please try again.")


def main():
    parser = argparse.ArgumentParser(
        description="Run a multiple-choice rating quiz on MTG cards"
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
        default=COMMONS_PER_PACK + UNCOMMONS_PER_PACK,
        help="Number of questions in the quiz",
    )
    parser.add_argument(
        "--difficulty",
        choices=["easy", "medium", "hard"],
        default="medium",
        help="Difficulty level: easy rounds to nearest 2.0, medium to nearest 1.0, hard to nearest 0.5",
    )
    args = parser.parse_args()
    # Determine rounding step based on difficulty
    difficulty_map = {"easy": 2.0, "medium": 1.0, "hard": 0.5}
    step = difficulty_map[args.difficulty]

    # Load and prepare cards
    cards = load_card_data(MAGIC_SET)
    convert_ohwr_to_float(cards)
    exclude = load_exclude_list(MAGIC_SET)
    # Filter by rarity and exclude list
    quiz_cards = []
    for r in args.rarities:
        quiz_cards.extend(filter_cards_by_rarity(cards, r))
    quiz_cards = [c for c in quiz_cards if c["Name"] not in exclude]

    # Determine rating bounds
    values = [float(c[args.rating_key]) for c in quiz_cards]
    min_val, max_val = min(values), max(values)
    # Compute global tertile thresholds based on overall ratings
    sorted_vals = sorted(values)
    n_vals = len(sorted_vals)
    low_idx = n_vals // 3
    high_idx = (2 * n_vals) // 3
    low_th = sorted_vals[low_idx]
    high_th = sorted_vals[high_idx]

    # Generate initial question set
    questions = generate_questions(
        quiz_cards,
        args.rating_key,
        min_val,
        max_val,
        args.num_questions,
        step=step,
    )

    round_num = 1
    remaining = questions
    while remaining:
        print(f"\n--- Round {round_num}: {len(remaining)} question(s) ---")
        wrong = []
        for i, q in enumerate(remaining, start=1):
            correct, chosen = ask_question(q, i, low_th, high_th)
            if correct:
                # Immediate positive feedback
                cprint("Correct", "green")
            else:
                # Immediate negative feedback and prepare for next round
                cprint("Wrong", "red")
                # Remove the chosen wrong option for next round
                new_opts = q.options.copy()
                new_opts.pop(chosen)
                # Recompute correct indices based on remaining options
                true_val = float(q.card[args.rating_key])
                new_correct_indices = [
                    i for i, opt in enumerate(new_opts) if abs(opt - true_val) < step
                ]
                wrong.append(
                    Question(
                        card=q.card,
                        options=new_opts,
                        correct_indices=new_correct_indices,
                    )
                )
        num = len(remaining)
        correct_count = num - len(wrong)
        print(f"You answered {correct_count}/{num} correct this round.")
        if wrong:
            print("Repeating wrong questions...\n")
            random.shuffle(wrong)
            remaining = wrong
            round_num += 1
        else:
            break

    print("\nQuiz complete! You got all questions correct.")


if __name__ == "__main__":
    main()
