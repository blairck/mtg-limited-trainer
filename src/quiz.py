"""
Quiz generation and orchestration for MTG rating quiz.
"""
import random
from dataclasses import dataclass
from typing import List, Dict

# Default number of choices per question
DEFAULT_NUM_CHOICES = 5


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
    num_choices: int = DEFAULT_NUM_CHOICES,
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
    # Guarantee at least one wrong answer within one step of the correct answer
    neighbors = [p for p in (true_rounded - step, true_rounded + step) if p in others]
    total_wrongs = min(len(others), num_choices - 1)
    # Chance to include a neighbor within one step; otherwise sample wrongs normally
    if neighbors and random.random() < 0.67:
        wrong = []
        near = random.choice(neighbors)
        wrong.append(near)
        remaining = total_wrongs - 1
        if remaining > 0:
            other_candidates = [p for p in others if p != near]
            wrong.extend(random.sample(other_candidates, remaining))
    else:
        wrong = random.sample(others, total_wrongs)
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
