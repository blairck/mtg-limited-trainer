"""
Quiz generation and orchestration for MTG rating quiz.
"""
import random
from config import QUIZ_NUM_CHOICES
from dataclasses import dataclass
from typing import List, Dict


def round_to_increment(value: float, step: float) -> float:
    """Round a float to nearest step."""
    return round(value / step) * step


@dataclass
class Question:
    card: Dict[str, any]
    options: List[float]
    correct_indices: List[int]


def round_to_half(value: float) -> float:
    """Round a float to nearest 0.5 (legacy)"""
    return round_to_increment(value, 0.5)


def make_question(
    card: Dict[str, any],
    rating_key: str,
    min_val: float,
    max_val: float,
    step: float = 0.5,
) -> Question:
    """
    Build a multiple-choice question for a single card.
    Choices are rounded to step increments, clamped within [min_val, max_val].
    Correct options are those within step of the true rating.
    """
    true_val = float(card[rating_key])
    true_rounded = round_to_increment(true_val, step)
    # Compute all possible rounded values within [min_val, max_val]
    # Determine index range around true_rounded
    low_i = int((min_val - true_rounded) // step)
    high_i = int((max_val - true_rounded) // step)
    # Build candidate list
    possible = []
    for i in range(low_i, high_i + 1):
        candidate = round_to_increment(true_rounded + i * step, step)
        # Include only within bounds
        if min_val <= candidate <= max_val:
            possible.append(candidate)
    # Ensure uniqueness and include true value
    possible = sorted(set(possible))
    # Select wrong options excluding the true one
    others = [p for p in possible if p != true_rounded]
    # Sample up to num_choices-1 wrong options
    wrong = random.sample(others, min(len(others), QUIZ_NUM_CHOICES - 1))
    # Build final options, always include true_rounded
    options = wrong + [true_rounded]
    random.shuffle(options)
    correct_indices = [i for i, opt in enumerate(options) if abs(opt - true_val) < step]
    return Question(card=card, options=options, correct_indices=correct_indices)


def generate_questions(
    cards: List[Dict[str, any]],
    rating_key: str,
    min_val: float,
    max_val: float,
    num_questions: int,
    step: float = 0.5,
) -> List[Question]:
    """
    Sample a set of cards and generate a Question for each.
    """
    sampled = random.sample(cards, num_questions)
    return [
        make_question(card, rating_key, min_val, max_val, step=step) for card in sampled
    ]
