import pytest

from src.game_logic import (
    evaluate_picks,
)


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
