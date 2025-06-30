import pytest

from src.game_logic import (
    get_cards_to_remove,
    evaluate_picks,
    should_advance,
    calculate_max_possible_score,
)
from config import PICKS_PER_PACK, ADVANCE_THRESHOLD


def test_get_cards_to_remove():
    assert get_cards_to_remove(0) == 0
    assert get_cards_to_remove(1) == PICKS_PER_PACK
    assert get_cards_to_remove(3) == 3 * PICKS_PER_PACK


def test_evaluate_picks_all_correct():
    card_lookup = {1: {"Name": "A"}, 2: {"Name": "B"}, 3: {"Name": "C"}}
    winrate_order = [{"Name": "A"}, {"Name": "B"}, {"Name": "C"}]
    score, results = evaluate_picks([1, 2, 3], card_lookup, winrate_order)
    assert score == 3
    assert all(r[2] for r in results)


def test_evaluate_picks_some_incorrect():
    card_lookup = {1: {"Name": "A"}, 2: {"Name": "B"}, 3: {"Name": "C"}}
    winrate_order = [{"Name": "A"}, {"Name": "C"}, {"Name": "B"}]
    score, results = evaluate_picks([1, 2, 3], card_lookup, winrate_order)
    assert score == 1
    # results should include False entries with correct best name
    assert results[1][2] == False
    assert results[1][3] == "C"


def test_should_advance():
    assert should_advance(ADVANCE_THRESHOLD) is True
    assert should_advance(ADVANCE_THRESHOLD - 1) is False


def test_calculate_max_possible_score():
    assert calculate_max_possible_score(3) == 3 * PICKS_PER_PACK
