"""
MTG Limited Trainer - Card Rating Quiz with difficulty selection
"""
from src.display import format_card_line, get_color_code, cprint
from src.cards import filter_cards_by_rarity
from src.data import load_card_data, load_exclude_list, convert_keys_to_float
from src.top_cards import get_top_cards, format_output
from config import (
    MAGIC_SET,
    QUIZ_RARITIES,
    QUIZ_RATING_KEY,
    DRAFT_RATING_KEY,
    DRAFT_RAW_OUTPUT_DIR,
    DRAFT_HTML_OUTPUT_DIR,
    CARDS_IN_QUIZ,
    CARD_COLOR,
)
import argparse
import random
import os
import sys

from dotenv import load_dotenv

load_dotenv()




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


def get_arguments():
    parser = argparse.ArgumentParser(description="MTG Limited Trainer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ── quiz subcommand ──────────────────────────────────────────────────────
    quiz_parser = subparsers.add_parser("play/quiz", help="Run a card rating quiz")
    quiz_parser.add_argument(
        "--rarities",
        nargs="+",
        default=QUIZ_RARITIES,
        help="Card rarities to include (e.g. C U)",
    )
    quiz_parser.add_argument(
        "--rating-key",
        default=QUIZ_RATING_KEY,
        help="Rating field to quiz on (e.g. 'OH WR')",
    )
    quiz_parser.add_argument(
        "--num-questions",
        type=int,
        default=CARDS_IN_QUIZ,
        help="Number of questions in the quiz",
    )
    quiz_parser.add_argument(
        "--difficulty",
        choices=["easy", "medium", "hard"],
        default="medium",
        help="Difficulty: easy=tertiles, medium=quartiles, hard=quintiles",
    )

    # ── analyze subcommand ───────────────────────────────────────────────────
    analyze_parser = subparsers.add_parser(
        "play/analyze", help="Fetch a 17Lands draft log and immediately analyze it"
    )
    analyze_parser.add_argument(
        "draft_ids",
        nargs="+",
        metavar="DRAFT_ID",
        help="One or more 17Lands draft IDs (from the URL).",
    )
    analyze_parser.add_argument(
        "--rating-key",
        default=DRAFT_RATING_KEY,
        help=f"Rating column to rank picks by (default: '{DRAFT_RATING_KEY}')",
    )

    # ── top-cards subcommand ─────────────────────────────────────────────────
    top_cards_parser = subparsers.add_parser(
        "collection/top-cards",
        help="Find the most valuable cards in a set by cumulative value threshold",
    )
    top_cards_parser.add_argument(
        "--set",
        default=MAGIC_SET,
        help="Magic set code (e.g., 'sos', 'dft')",
    )
    top_cards_parser.add_argument(
        "--rarities",
        nargs="+",
        default=["C"],
        help="Card rarities to include (e.g. C U)",
    )
    top_cards_parser.add_argument(
        "--threshold",
        type=float,
        default=25.0,
        help="Cumulative value threshold as a percentage (0-100, default: 25)",
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
    if num_questions > len(quiz_cards):
        raise ValueError(
            f"Requested {num_questions} quiz questions, but only "
            f"{len(quiz_cards)} cards are available after filtering."
        )
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


def run_fetch(args) -> None:
    """Fetch one or more draft logs from 17Lands then analyze each one."""
    import argparse as _argparse
    from src.fetch_draft import process_draft

    for draft_id in args.draft_ids:
        process_draft(draft_id, DRAFT_RAW_OUTPUT_DIR)
        draft_log_path = os.path.join(DRAFT_RAW_OUTPUT_DIR, f"{draft_id}.json")
        if os.path.exists(draft_log_path):
            analyze_args = _argparse.Namespace(
                draft_log=draft_log_path,
                rating_key=args.rating_key,
            )
            _run_analyze(analyze_args)
        else:
            print(f"[skip analysis] {draft_id} — no local file found")


def _run_analyze(args) -> None:
    """Load a draft log, run pick analysis, and write an HTML report."""
    from collections import Counter

    from src.draft_analysis import (
        load_draft_log,
        load_card_ratings_lookup,
        evaluate_pick,
        update_pool_state,
        find_lane_signals,
        summarize_pack,
    )
    from src.html_report import format_analysis_html
    from src.data import find_most_recent_csv

    draft = load_draft_log(args.draft_log)
    set_code = draft["expansion"].lower()
    try:
        csv_path = find_most_recent_csv(set_code)
    except FileNotFoundError:
        print(f"No ratings CSV found for set '{draft['expansion']}' ({set_code}).")
        print(f"Expected ratings files under: {DRAFT_RAW_OUTPUT_DIR}")
        print(
            "Please download/fetch the set ratings data first, then rerun draft analysis."
        )
        return

    ratings = load_card_ratings_lookup(csv_path, args.rating_key)

    evaluations = [evaluate_pick(p, ratings, args.rating_key) for p in draft["picks"]]

    pool_state: Counter = Counter()
    for ev in evaluations:
        update_pool_state(pool_state, ev["chosen_meta"])

    packs = sorted({e["pack"] for e in evaluations})
    pack_summaries = [
        summarize_pack([e for e in evaluations if e["pack"] == p]) for p in packs
    ]

    lane_signals = find_lane_signals(evaluations)

    report = format_analysis_html(
        draft, evaluations, pack_summaries, lane_signals, args.rating_key
    )

    os.makedirs(DRAFT_HTML_OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(
        DRAFT_HTML_OUTPUT_DIR, f"{draft['draft_id']}_analysis.html"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Draft ID : {draft['draft_id']}")
    print(
        f"Set      : {draft['expansion']}  |  Format: {draft['format']}  |  Record: {draft['wins']}-{draft['losses']}"
    )
    print(f"Metric   : {args.rating_key}")
    print(f"Report saved to: {output_path}")

    bucket = os.environ.get("S3_BUCKET_NAME")
    if not bucket:
        print("[s3] S3_BUCKET_NAME not set — skipping upload")
        return
    import boto3

    s3_key = f"drafts/html/{draft['draft_id']}_analysis.html"
    session = boto3.session.Session()
    region = session.region_name or "us-east-1"
    session.client("s3").upload_file(
        output_path,
        bucket,
        s3_key,
        ExtraArgs={"ContentType": "text/html"},
    )
    public_url = f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"
    print(f"[s3] Uploaded: {public_url}")


def run_top_cards(args) -> None:
    """Find and display the top valuable cards in a set by cumulative threshold."""
    rarities = []
    for rarity in args.rarities:
        if rarity.lower() in ("c", "common") and "common" not in rarities:
            rarities.append("common")
        elif rarity.lower() in ("u", "uncommon") and "uncommon" not in rarities:
            rarities.append("uncommon")
        elif rarity.lower() in ("r", "rare") and "rare" not in rarities:
            rarities.append("rare")
        elif rarity.lower() in ("m", "mythic") and "mythic" not in rarities:
            rarities.append("mythic")
        else:
            print(f"Unknown rarity {rarity}, skipping")

    try:
        selected_cards, cumulative_value, total_value, total_considered = get_top_cards(
            args.set, rarities, args.threshold
        )

        # Display results
        output = format_output(
            selected_cards, cumulative_value, args.threshold, total_considered
        )
        print(output)

        # Print summary statistics
        print(
            f"\nSelected {len(selected_cards)} card(s) to reach {args.threshold}% threshold"
        )
        print(f"Selected value: ${cumulative_value:.2f}, Total value: ${total_value:0.2f}")
        print(f"Rarities included: {', '.join(rarities)}")

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error fetching cards from Scryfall: {e}")
        sys.exit(1)


def main():
    args = get_arguments()

    if args.command == "play/quiz":
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
    elif args.command == "play/analyze":
        run_fetch(args)
    elif args.command == "collection/top-cards":
        run_top_cards(args)


if __name__ == "__main__":
    main()
