"""
Tests for the top_cards module.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.top_cards import (
    fetch_cards_from_scryfall,
    filter_cards_by_rarity,
    filter_excluded_cards,
    format_output,
    get_card_price,
    get_color_from_card,
    find_top_cards_by_threshold,
    sort_by_color,
    get_top_cards,
)


@pytest.fixture
def sample_cards():
    """Sample cards for testing."""
    return [
        {
            "name": "Card One",
            "rarity": "common",
            "colors": ["W"],
            "prices": {"usd": "0.10"},
        },
        {
            "name": "Card Two",
            "rarity": "uncommon",
            "colors": ["U"],
            "prices": {"usd": "0.40"},
        },
        {
            "name": "Card Three",
            "rarity": "rare",
            "colors": ["B"],
            "prices": {"usd": "0.30"},
        },
        {
            "name": "Card Four",
            "rarity": "rare",
            "colors": ["R"],
            "prices": {"usd": "0.20"},
        },
        {
            "name": "Card Five",
            "rarity": "mythic",
            "colors": ["G"],
            "prices": {"usd": "0.25"},
        },
        {
            "name": "Colorless Card",
            "rarity": "common",
            "colors": [],
            "prices": {"usd": "0.05"},
        },
    ]


class TestGetCardPrice:
    """Tests for get_card_price function."""

    def test_get_card_price_usd(self):
        """Test extracting USD price."""
        card = {"prices": {"usd": "1.50"}}
        assert get_card_price(card) == 1.50

    def test_get_card_price_fallback_usd_foil(self):
        """Test fallback to USD foil."""
        card = {"prices": {"usd_foil": "2.00"}}
        assert get_card_price(card) == 2.00

    def test_get_card_price_no_price(self):
        """Test card with no price."""
        card = {"prices": {}}
        assert get_card_price(card) == 0.0

    def test_get_card_price_invalid_price(self):
        """Test card with invalid price string."""
        card = {"prices": {"usd": "invalid"}}
        assert get_card_price(card) == 0.0

    def test_get_card_price_missing_prices(self):
        """Test card without prices key."""
        card = {}
        assert get_card_price(card) == 0.0


class TestGetColorFromCard:
    """Tests for get_color_from_card function."""

    def test_white_card(self):
        """Test white card color."""
        card = {"colors": ["W"]}
        assert get_color_from_card(card) == "W"

    def test_blue_card(self):
        """Test blue card color."""
        card = {"colors": ["U"]}
        assert get_color_from_card(card) == "U"

    def test_black_card(self):
        """Test black card color."""
        card = {"colors": ["B"]}
        assert get_color_from_card(card) == "B"

    def test_red_card(self):
        """Test red card color."""
        card = {"colors": ["R"]}
        assert get_color_from_card(card) == "R"

    def test_green_card(self):
        """Test green card color."""
        card = {"colors": ["G"]}
        assert get_color_from_card(card) == "G"

    def test_colorless_card(self):
        """Test colorless card."""
        card = {"colors": []}
        assert get_color_from_card(card) == "L"

    def test_multicolor_card(self):
        """Test multicolor card (returns first color)."""
        card = {"colors": ["W", "U"]}
        assert get_color_from_card(card) == "M"

    def test_unknown_card(self):
        """Test unknown card color."""
        card = {"colors": ["Q"]}
        assert get_color_from_card(card) == "O"

    def test_missing_colors(self):
        """Test card without colors key."""
        card = {}
        assert get_color_from_card(card) == "L"


class TestFilterCardsByRarity:
    """Tests for filter_cards_by_rarity function."""

    def test_filter_single_rarity(self, sample_cards):
        """Test filtering by single rarity."""
        filtered = filter_cards_by_rarity(sample_cards, ["common"])
        assert len(filtered) == 2
        assert all(c["rarity"] == "common" for c in filtered)

    def test_filter_multiple_rarities(self, sample_cards):
        """Test filtering by multiple rarities."""
        filtered = filter_cards_by_rarity(sample_cards, ["rare", "mythic"])
        assert len(filtered) == 3
        assert all(c["rarity"] in ["rare", "mythic"] for c in filtered)

    def test_filter_case_insensitive(self, sample_cards):
        """Test that filtering is case-insensitive."""
        filtered = filter_cards_by_rarity(sample_cards, ["COMMON", "Uncommon"])
        assert len(filtered) == 3

    def test_filter_no_matches(self, sample_cards):
        """Test filtering with no matching cards."""
        filtered = filter_cards_by_rarity(sample_cards, ["special"])
        assert len(filtered) == 0


class TestFilterExcludedCards:
    """Tests for filter_excluded_cards function."""

    def test_exclude_basic_lands(self):
        """Test that basic lands are excluded."""
        cards = [
            {"name": "Swamp", "prices": {"usd": "0.10"}},
            {"name": "Mountain", "prices": {"usd": "0.10"}},
            {"name": "Island", "prices": {"usd": "0.10"}},
            {"name": "Plains", "prices": {"usd": "0.10"}},
            {"name": "Forest", "prices": {"usd": "0.10"}},
            {"name": "Lightning Bolt", "prices": {"usd": "5.00"}},
        ]
        filtered = filter_excluded_cards(cards)
        assert len(filtered) == 1
        assert filtered[0]["name"] == "Lightning Bolt"

    def test_exclude_partial_match(self):
        """Test that partial matches are not excluded."""
        cards = [
            {"name": "Swamp", "prices": {"usd": "0.10"}},
            {"name": "Swampland", "prices": {"usd": "0.50"}},
        ]
        filtered = filter_excluded_cards(cards)
        assert len(filtered) == 1
        assert filtered[0]["name"] == "Swampland"

    def test_include_non_excluded_cards(self, sample_cards):
        """Test that non-excluded cards are preserved."""
        filtered = filter_excluded_cards(sample_cards)
        assert len(filtered) == len(sample_cards)


class TestFindTopCardsByThreshold:
    """Tests for find_top_cards_by_threshold function."""

    def test_50_percent_threshold(self, sample_cards):
        """Test finding top cards at 50% threshold."""
        selected, cumulative_value, _ = find_top_cards_by_threshold(sample_cards, 50.0)

        # Total value is 1.30, 50% is 0.65
        # Cards sorted by price: 0.40, 0.30, 0.25, 0.20, 0.10, 0.05
        # Selected: 0.40 + 0.30 = 0.70 (meets 0.65 threshold)
        assert len(selected) == 2
        assert abs(cumulative_value - 0.70) < 0.01

    def test_100_percent_threshold(self, sample_cards):
        """Test 100% threshold selects all cards."""
        selected, cumulative_value, _ = find_top_cards_by_threshold(sample_cards, 100.0)
        assert len(selected) == len(sample_cards)
        assert abs(cumulative_value - 1.30) < 0.01

    def test_0_percent_threshold(self, sample_cards):
        """Test 0% threshold selects just the highest card."""
        selected, cumulative_value, _ = find_top_cards_by_threshold(sample_cards, 0.0)
        assert len(selected) == 1
        assert abs(cumulative_value - 0.40) < 0.01

    def test_threshold_no_priced_cards(self):
        """Test with cards that have no prices."""
        cards = [
            {"name": "Card A", "prices": {}},
            {"name": "Card B", "prices": {}},
        ]
        selected, total_value = find_top_cards_by_threshold(cards, 50.0)
        assert len(selected) == 0
        assert total_value == 0.0


class TestSortByColor:
    """Tests for sort_by_color function."""

    def test_sort_by_color_order(self, sample_cards):
        """Test that cards are sorted in correct color order."""
        sorted_cards = sort_by_color(sample_cards)
        colors = [get_color_from_card(c) for c in sorted_cards]

        # Expected order: W, U, B, R, G, L
        assert colors == ["W", "U", "B", "R", "G", "L"]

    def test_sort_within_color_by_price(self):
        """Test that cards within same color are sorted by price (descending)."""
        cards = [
            {"name": "White1", "colors": ["W"], "prices": {"usd": "0.10"}},
            {"name": "White2", "colors": ["W"], "prices": {"usd": "0.30"}},
            {"name": "White3", "colors": ["W"], "prices": {"usd": "0.20"}},
        ]
        sorted_cards = sort_by_color(cards)
        names = [c["name"] for c in sorted_cards]
        assert names == ["White2", "White3", "White1"]


class TestGetTopCards:
    """Tests for the main get_top_cards function."""

    @patch("src.top_cards.fetch_cards_from_scryfall")
    def test_get_top_cards_success(self, mock_fetch, sample_cards):
        """Test successful top cards retrieval."""
        mock_fetch.return_value = sample_cards

        selected, cumulative, _, count = get_top_cards("sos", ["common"], 50.0)

        assert len(selected) > 0
        assert cumulative > 0
        assert count > 0
        mock_fetch.assert_called_once_with("sos")

    @patch("src.top_cards.fetch_cards_from_scryfall")
    def test_get_top_cards_no_matching_cards(self, mock_fetch, sample_cards):
        """Test when no cards match the criteria."""
        mock_fetch.return_value = sample_cards

        with pytest.raises(ValueError, match="No cards found"):
            get_top_cards("sos", ["special"], 50.0)

    def test_get_top_cards_invalid_threshold(self):
        """Test with invalid threshold value."""
        with pytest.raises(ValueError, match="(?i)threshold percentage"):
            get_top_cards("sos", ["common"], 150.0)

    def test_get_top_cards_no_rarities(self):
        """Test with empty rarities list."""
        with pytest.raises(ValueError, match="At least one rarity"):
            get_top_cards("sos", [], 50.0)


@patch("src.top_cards.requests.get")
def test_fetch_cards_from_scryfall(mock_get):
    """Test fetching cards from Scryfall API."""
    # Mock first page with next_page
    first_page = {
        "data": [{"name": "Card 1"}, {"name": "Card 2"}],
        "next_page": "https://api.scryfall.com/page2",
    }
    # Mock second page without next_page
    second_page = {
        "data": [{"name": "Card 3"}],
    }

    mock_response_1 = MagicMock()
    mock_response_1.json.return_value = first_page
    mock_response_2 = MagicMock()
    mock_response_2.json.return_value = second_page

    mock_get.side_effect = [mock_response_1, mock_response_2]

    cards = fetch_cards_from_scryfall("sos")

    assert len(cards) == 3
    assert cards[0]["name"] == "Card 1"
    assert cards[2]["name"] == "Card 3"


class TestFormatOutput:
    """Tests for format_output function."""

    def test_format_output_includes_card_volume_reduction(self, sample_cards):
        """Test that format_output includes card volume reduction metric."""
        # 2 cards selected out of 6 considered = 66.7% reduction
        output = format_output(sample_cards[:2], 0.50, 50.0, total_cards_considered=6)

        assert "Reduced card volume by" in output
        assert "66.7%" in output

    def test_format_output_no_reduction_metric_without_count(self, sample_cards):
        """Test that format_output doesn't include metric if count is 0."""
        output = format_output(sample_cards[:2], 0.50, 50.0, total_cards_considered=0)

        assert "Reduced card volume by" not in output

    def test_format_output_100_percent_reduction(self):
        """Test format output with 100% of cards selected."""
        cards = [{"name": "Card1", "colors": ["W"], "prices": {"usd": "1.0"}}]
        output = format_output(cards, 1.0, 50.0, total_cards_considered=1)

        # 1 out of 1 = 0% reduction
        assert "Reduced card volume by 0.0%" in output

    def test_format_output_shows_all_colors(self):
        """Test that output shows all color categories."""
        cards = [
            {"name": "White", "colors": ["W"], "prices": {"usd": "1.0"}},
            {"name": "Blue", "colors": ["U"], "prices": {"usd": "1.0"}},
            {"name": "Black", "colors": ["B"], "prices": {"usd": "1.0"}},
            {"name": "Red", "colors": ["R"], "prices": {"usd": "1.0"}},
            {"name": "Green", "colors": ["G"], "prices": {"usd": "1.0"}},
            {"name": "Land", "colors": [], "prices": {"usd": "1.0"}},
        ]
        output = format_output(cards, 6.0, 100.0, total_cards_considered=10)

        assert "White:" in output
        assert "Blue:" in output
        assert "Black:" in output
        assert "Red:" in output
        assert "Green:" in output
        assert "Colorless/Lands:" in output
        assert "Reduced card volume by 40.0%" in output
