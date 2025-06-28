import pytest

from src.cards import (
    filter_cards_by_rarity,
    draw_pack,
    remove_top_n_by_winrate,
    get_winrate_order,
)
from src.config import (
    CARD_NAME,
    CARD_RARITY,
    CARD_OHWR,
    COMMONS_PER_PACK,
    UNCOMMONS_PER_PACK,
)


def make_card(name, rarity, winrate):
    """Helper to create a card dict."""
    return {CARD_NAME: name, CARD_RARITY: rarity, CARD_OHWR: winrate}


def test_filter_cards_by_rarity():
    cards = [
        make_card("A", "Common", 0.1),
        make_card("B", "Uncommon", 0.2),
        make_card("C", "Common", 0.3),
    ]
    common_cards = filter_cards_by_rarity(cards, "Common")
    assert common_cards == [cards[0], cards[2]]

    rare_cards = filter_cards_by_rarity(cards, "Rare")
    assert rare_cards == []


def test_draw_pack_without_exclude(monkeypatch):
    # Disable shuffle for deterministic results
    import src.cards as cards_mod

    monkeypatch.setattr(cards_mod, "shuffle", lambda x: None)

    common_cards = [make_card(f"C{i}", "Common", 0.1) for i in range(15)]
    uncommon_cards = [make_card(f"U{i}", "Uncommon", 0.2) for i in range(10)]

    pack = cards_mod.draw_pack(common_cards.copy(), uncommon_cards.copy())
    # Expect exactly COMMONS_PER_PACK + UNCOMMONS_PER_PACK cards
    assert len(pack) == COMMONS_PER_PACK + UNCOMMONS_PER_PACK
    # First commons come from common_cards in order
    assert pack[:COMMONS_PER_PACK] == common_cards[:COMMONS_PER_PACK]
    # Then uncommons
    assert pack[COMMONS_PER_PACK:] == uncommon_cards[:UNCOMMONS_PER_PACK]


def test_draw_pack_with_exclude(monkeypatch):
    # Disable shuffle for deterministic results
    import src.cards as cards_mod

    monkeypatch.setattr(cards_mod, "shuffle", lambda x: None)

    # Setup smaller card pools
    common_cards = [make_card(f"C{i}", "Common", 0.1) for i in range(5)]
    uncommon_cards = [make_card(f"U{i}", "Uncommon", 0.2) for i in range(5)]
    # Exclude some common and uncommon cards
    exclude = {"C0", "C1", "U0"}

    pack = cards_mod.draw_pack(common_cards.copy(), uncommon_cards.copy(), exclude)
    # Excluded cards should not be in pack
    assert all(card[CARD_NAME] not in exclude for card in pack)
    # Since only 3 commons available and 4 uncommons, total pack size should be 7
    assert len(pack) == 3 + 4


def test_remove_top_n_by_winrate():
    cards = [
        make_card("A", "Common", 0.1),
        make_card("B", "Common", 0.5),
        make_card("C", "Common", 0.3),
    ]
    # Remove top 1 by winrate (B)
    result = remove_top_n_by_winrate(cards.copy(), 1)
    # Remaining should be sorted by descending winrate: C(0.3), A(0.1)
    assert [c[CARD_OHWR] for c in result] == [0.3, 0.1]

    # If cards_to_remove is zero, original list is returned
    result_zero = remove_top_n_by_winrate(cards.copy(), 0)
    assert result_zero == cards


def test_get_winrate_order():
    cards = [
        make_card("X", "Common", 0.2),
        make_card("Y", "Common", 0.8),
        make_card("Z", "Common", 0.5),
    ]
    ordered = get_winrate_order(cards)
    # Expect descending order: Y(0.8), Z(0.5), X(0.2)
    assert [c[CARD_OHWR] for c in ordered] == [0.8, 0.5, 0.2]
