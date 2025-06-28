import pytest

from src.display import (
    make_clickable_link,
    get_color_code,
    get_card_url,
    format_card_line,
)
from src.config import CARD_NAME, CARD_COLOR, CARD_RARITY, CARD_OHWR


def test_make_clickable_link():
    url = "http://example.com"
    text = "example"
    link = make_clickable_link(url, text)
    # Should contain the URL and text and proper ANSI link sequences
    assert url in link
    assert text in link
    assert link.startswith(f"\033]8;;{url}\033\\")
    assert link.endswith("\033]8;;\033\\")


def test_get_color_code_primary_colors():
    assert get_color_code("G") == "green"
    assert get_color_code("W") == "white"
    assert get_color_code("U") == "blue"
    assert get_color_code("B") == "black"
    assert get_color_code("R") == "red"


def test_get_color_code_multicolor_and_default():
    # Multicolor (length >1)
    assert get_color_code("GW") == "yellow"
    # Colorless or unrecognized
    assert get_color_code("") == "magenta"
    assert get_color_code("X") == "magenta"


def test_get_card_url_and_format_card_line():
    name = "Test Card"
    card = {CARD_NAME: name, CARD_RARITY: "Rare", CARD_COLOR: "G", CARD_OHWR: "42%"}
    url = get_card_url(name)
    # Spaces should be replaced with '+'
    assert "+" in url and "Test+Card" in url

    # Test format without percent
    line = format_card_line(card.copy(), show_percent=False)
    assert name in line
    assert "Rare" in line
    assert "link" in line
    assert "42%" not in line

    # Test format with percent
    line_pct = format_card_line(card.copy(), show_percent=True)
    assert "42%" in line_pct
