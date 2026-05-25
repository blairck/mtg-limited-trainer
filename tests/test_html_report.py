"""Smoke tests for src/html_report.py"""

from src.draft_analysis import evaluate_pick, find_lane_signals, summarize_pack
from src.html_report import (
    format_analysis_html,
    _card_link,
    _pick_link,
    _linkify_picks,
    _card_css,
)

# ---------------------------------------------------------------------------
# Shared fixtures (mirrored from test_draft_analysis.py)
# ---------------------------------------------------------------------------

MOCK_RATINGS = {
    "Card A": {
        "rating": 60.0,
        "color": "W",
        "rarity": "R",
        "alsa": 1.5,
        "ata": 1.8,
        "iih": "5.0pp",
    },
    "Card B": {
        "rating": 55.0,
        "color": "U",
        "rarity": "C",
        "alsa": 4.0,
        "ata": 4.5,
        "iih": "3.0pp",
    },
    "Card C": {
        "rating": 50.0,
        "color": "R",
        "rarity": "C",
        "alsa": 7.0,
        "ata": 8.0,
        "iih": "1.0pp",
    },
}

PICKS = [
    {
        "pack": 1,
        "pick": 1,
        "available": [
            {"name": "Card A", "picked": True},
            {"name": "Card B", "picked": False},
        ],
    },
    {
        "pack": 1,
        "pick": 2,
        "available": [
            {"name": "Card A", "picked": False},
            {"name": "Card B", "picked": True},
        ],
    },
]

DRAFT = {
    "draft_id": "abc123def456",
    "expansion": "SOS",
    "format": "PremierDraft",
    "wins": 5,
    "losses": 2,
    "picks": PICKS,
}


def _make_report():
    evals = [evaluate_pick(p, MOCK_RATINGS) for p in DRAFT["picks"]]
    pack_summaries = [summarize_pack(evals)]
    signals = find_lane_signals(evals)
    return format_analysis_html(DRAFT, evals, pack_summaries, signals)


# ---------------------------------------------------------------------------
# _card_css
# ---------------------------------------------------------------------------


def test_card_css_single_colors():
    assert _card_css("W") == "#f5f5dc"
    assert _card_css("U") == "#4fc3f7"
    assert _card_css("B") == "#b0b0b0"
    assert _card_css("R") == "#ef5350"
    assert _card_css("G") == "#66bb6a"


def test_card_css_multicolor():
    assert _card_css("WU") == "#ffd600"
    assert _card_css("WBR") == "#ffd600"


def test_card_css_colorless():
    assert _card_css("") == "#ce93d8"
    assert _card_css("C") == "#ce93d8"


# ---------------------------------------------------------------------------
# _card_link
# ---------------------------------------------------------------------------


def test_card_link_contains_scryfall_url():
    link = _card_link("Rubble Rouser", "R")
    assert "scryfall.com/search" in link
    assert "Rubble+Rouser" in link


def test_card_link_contains_card_name_text():
    link = _card_link("Rubble Rouser", "R")
    assert "Rubble Rouser" in link


def test_card_link_color_applied():
    link = _card_link("Some Card", "U")
    assert "#4fc3f7" in link


# ---------------------------------------------------------------------------
# _pick_link
# ---------------------------------------------------------------------------


def test_pick_link_contains_17lands_url():
    link = _pick_link("abc123", 2, 1)
    assert "17lands.com/draft/abc123/2/1" in link


def test_pick_link_label():
    link = _pick_link("abc123", 2, 1)
    assert "P2P01" in link


def test_pick_link_zero_padded():
    link = _pick_link("abc123", 1, 6)
    assert "P1P06" in link


# ---------------------------------------------------------------------------
# _linkify_picks
# ---------------------------------------------------------------------------


def test_linkify_picks_replaces_pattern():
    result = _linkify_picks("Pivot at P1P06 toward R", "abc123")
    assert "17lands.com/draft/abc123/1/6" in result
    assert "P1P06" in result


def test_linkify_picks_multiple():
    result = _linkify_picks("P1P06 and P2P09", "abc123")
    assert "17lands.com/draft/abc123/1/6" in result
    assert "17lands.com/draft/abc123/2/9" in result


def test_linkify_picks_no_match():
    text = "No picks here"
    assert _linkify_picks(text, "abc123") == text


# ---------------------------------------------------------------------------
# format_analysis_html — structure
# ---------------------------------------------------------------------------


def test_html_report_is_valid_html():
    html = _make_report()
    assert html.strip().startswith("<!DOCTYPE html>")
    assert "</html>" in html


def test_html_report_contains_draft_id():
    html = _make_report()
    assert "abc123def456" in html


def test_html_report_contains_record():
    html = _make_report()
    assert "5-2" in html


def test_html_report_contains_all_sections():
    html = _make_report()
    for heading in [
        "Overall Stats",
        "Pick Classification",
        "Biggest Misses",
        "Pack Summaries",
        "Draft Arc",
        "Pool / Lane Timeline",
        "Signal Summary by Color",
        "Lane Signals",
    ]:
        assert heading in html, f"Missing section heading: {heading}"


def test_html_report_no_full_pick_log():
    html = _make_report()
    assert "FULL PICK LOG" not in html
    assert "Full Pick Log" not in html


def test_html_report_pick_links_use_17lands():
    html = _make_report()
    assert "17lands.com/draft/abc123def456" in html


def test_html_report_card_links_use_scryfall():
    html = _make_report()
    assert "scryfall.com/search" in html


def test_html_report_lane_signals_top5_per_pack():
    """Lane signals show top 5 per pack (up to 3 packs × 5 = 15 total)."""
    # Manufacture late-pick evaluations across all 3 packs to generate >5 signals per pack
    many_picks = [
        {
            "pack": pack_num,
            "pick": pick_num,
            "available": [
                {"name": "Card C", "picked": True},
                {"name": "Card A", "picked": False},
            ],
        }
        for pack_num in (1, 2, 3)
        for pick_num in range(6, 14)
    ]
    draft = {**DRAFT, "picks": many_picks}
    evals = [evaluate_pick(p, MOCK_RATINGS) for p in many_picks]
    pack_summaries = [summarize_pack(evals)]
    signals = find_lane_signals(evals)
    assert len(signals) > 5, "Need >5 signals per pack for this test to be meaningful"
    html = format_analysis_html(draft, evals, pack_summaries, signals)
    import re

    lane_section = re.search(r"Lane Signals.*?</section>", html, re.DOTALL)
    assert lane_section is not None
    # Each pack contributes at most 5 pick links → max 15 total
    links_in_section = re.findall(r"17lands\.com/draft", lane_section.group())
    assert len(links_in_section) <= 15
    # Verify all 3 pack subsections are present
    assert "Pack 1" in lane_section.group()
    assert "Pack 2" in lane_section.group()
    assert "Pack 3" in lane_section.group()
