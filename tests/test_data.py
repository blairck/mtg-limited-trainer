import glob
import pytest

from src.data import (
    find_most_recent_csv,
    load_exclude_list,
    convert_ohwr_to_float,
    load_card_data,
)
from src.config import CARD_OHWR


def test_find_most_recent_csv():
    # Should find the most recent CSV in resources/sets/fin
    path = find_most_recent_csv("fin")
    assert path.endswith("resources/sets/fin/card-ratings-2025-06-24.csv")


def test_find_most_recent_csv_no_files(monkeypatch):
    # Simulate no files found
    monkeypatch.setattr(glob, "glob", lambda pattern: [])
    with pytest.raises(FileNotFoundError):
        find_most_recent_csv("unknown")


def test_load_exclude_list():
    exclude = load_exclude_list("fin")
    assert isinstance(exclude, set)
    # Known item from exclude.csv
    assert "Baron, Airship Kingdom" in exclude
    assert len(exclude) >= 1


def test_convert_ohwr_to_float():
    cards = [{CARD_OHWR: "50%"}, {CARD_OHWR: "abc"}, {CARD_OHWR: None}]
    convert_ohwr_to_float(cards)
    assert isinstance(cards[0][CARD_OHWR], float) and cards[0][CARD_OHWR] == 50.0
    assert cards[1][CARD_OHWR] == "abc"
    assert cards[2][CARD_OHWR] is None


def test_load_card_data(monkeypatch, tmp_path):
    # Create a temporary CSV file
    tmpfile = tmp_path / "temp.csv"
    lines = ["Name,Color,Rarity,OH WR\n", "Foo,Green,Common,23.5\n", "Bar,Red,Rare,\n"]
    tmpfile.write_text("".join(lines), encoding="utf-8")
    import src.data as data_mod

    monkeypatch.setattr(data_mod, "find_most_recent_csv", lambda s: str(tmpfile))

    cards = load_card_data("fin")
    assert isinstance(cards, list)
    # Only one card has non-empty OH WR
    assert len(cards) == 1
    assert cards[0]["Name"] == "Foo"
