"""Tests for src/draft_analysis.py"""

import json
import os
import tempfile
from collections import Counter

import pytest

from src.draft_analysis import (
    classify_pick,
    evaluate_pick,
    find_biggest_misses,
    find_lane_signals,
    format_analysis_report,
    load_card_ratings_lookup,
    load_draft_log,
    normalize_card_name,
    summarize_pack,
    update_pool_state,
)


# ---------------------------------------------------------------------------
# Fixtures
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
    "Multi Color": {
        "rating": 57.0,
        "color": "WU",
        "rarity": "U",
        "alsa": 3.0,
        "ata": 3.5,
        "iih": "2.0pp",
    },
}

# Pack where Card A is the clear best and Card B is picked (rank 2, gap 5.0)
PICK_MISS = {
    "pack": 1,
    "pick": 2,
    "available": [
        {"name": "Card A", "picked": False},
        {"name": "Card B", "picked": True},
        {"name": "Card C", "picked": False},
    ],
}

# Pack where Card A is picked (rank 1, gap 0.0)
PICK_BEST = {
    "pack": 1,
    "pick": 1,
    "available": [
        {"name": "Card A", "picked": True},
        {"name": "Card B", "picked": False},
        {"name": "Card C", "picked": False},
    ],
}

# Pack where the chosen card has no entry in ratings
PICK_UNRATED = {
    "pack": 1,
    "pick": 3,
    "available": [
        {"name": "Unknown Card", "picked": True},
        {"name": "Card B", "picked": False},
    ],
}

# Late pick (pick 7) with a strong card left in the pack
PICK_LATE_SIGNAL = {
    "pack": 1,
    "pick": 7,
    "available": [
        {"name": "Card C", "picked": True},
        {"name": "Card A", "picked": False},  # 60.0% left late
    ],
}


# ---------------------------------------------------------------------------
# normalize_card_name
# ---------------------------------------------------------------------------


def test_normalize_card_name_strips_whitespace():
    assert normalize_card_name("  Card A  ") == "Card A"


def test_normalize_card_name_unchanged():
    assert normalize_card_name("Ajani's Response") == "Ajani's Response"


# ---------------------------------------------------------------------------
# classify_pick
# ---------------------------------------------------------------------------


def test_classify_pick_none_is_unrated():
    assert classify_pick(None) == "unrated"


def test_classify_pick_zero_is_best():
    assert classify_pick(0.0) == "best"


def test_classify_pick_defensible():
    assert classify_pick(0.9) == "defensible"
    assert classify_pick(1.0) == "defensible"


def test_classify_pick_speculative():
    assert classify_pick(1.1) == "speculative"
    assert classify_pick(3.0) == "speculative"


def test_classify_pick_costly_miss():
    assert classify_pick(3.1) == "costly miss"
    assert classify_pick(10.0) == "costly miss"


# ---------------------------------------------------------------------------
# evaluate_pick
# ---------------------------------------------------------------------------


def test_evaluate_pick_best():
    ev = evaluate_pick(PICK_BEST, MOCK_RATINGS)
    assert ev["chosen_name"] == "Card A"
    assert ev["rank"] == 1
    assert ev["gap"] == 0.0
    assert ev["classification"] == "best"
    assert ev["best_name"] == "Card A"


def test_evaluate_pick_miss():
    ev = evaluate_pick(PICK_MISS, MOCK_RATINGS)
    assert ev["chosen_name"] == "Card B"
    assert ev["rank"] == 2
    assert ev["gap"] == pytest.approx(5.0)
    assert ev["classification"] == "costly miss"
    assert ev["best_name"] == "Card A"


def test_evaluate_pick_unrated():
    ev = evaluate_pick(PICK_UNRATED, MOCK_RATINGS)
    assert ev["chosen_name"] == "Unknown Card"
    assert ev["rank"] is None
    assert ev["gap"] is None
    assert ev["classification"] == "unrated"
    assert ev["best_name"] == "Card B"


def test_evaluate_pick_pool_size():
    ev = evaluate_pick(PICK_BEST, MOCK_RATINGS)
    assert ev["pool_size"] == 3


def test_evaluate_pick_top3_order():
    ev = evaluate_pick(PICK_MISS, MOCK_RATINGS)
    ratings = [c["rating"] for c in ev["top3"]]
    assert ratings == sorted(ratings, reverse=True)


# ---------------------------------------------------------------------------
# update_pool_state
# ---------------------------------------------------------------------------


def test_update_pool_state_single_color():
    pool = Counter()
    update_pool_state(pool, {"color": "W", "rating": 55.0})
    assert pool["W"] == 1


def test_update_pool_state_multicolor():
    pool = Counter()
    update_pool_state(pool, {"color": "WU", "rating": 55.0})
    assert pool["W"] == 1
    assert pool["U"] == 1


def test_update_pool_state_colorless():
    pool = Counter()
    update_pool_state(pool, {"color": "", "rating": 55.0})
    assert sum(pool.values()) == 0


def test_update_pool_state_none_meta():
    pool = Counter({"W": 2})
    result = update_pool_state(pool, None)
    assert result["W"] == 2  # unchanged


# ---------------------------------------------------------------------------
# find_lane_signals
# ---------------------------------------------------------------------------


def test_find_lane_signals_detects_strong_late_card():
    # PICK_LATE_SIGNAL: pick 7, Card A (60.0%) is available but not taken
    ev = evaluate_pick(PICK_LATE_SIGNAL, MOCK_RATINGS)
    signals = find_lane_signals([ev])
    names = [s["name"] for s in signals]
    assert "Card A" in names


def test_find_lane_signals_ignores_early_picks():
    ev = evaluate_pick(PICK_MISS, MOCK_RATINGS)  # pick 2, early
    signals = find_lane_signals([ev])
    assert signals == []


def test_find_lane_signals_excludes_chosen_card():
    # Card A is the strong card and IS taken here
    ev = evaluate_pick(PICK_BEST, MOCK_RATINGS)
    # Manually force pick_num to 7 to make it "late"
    ev = {**ev, "pick_num": 7}
    signals = find_lane_signals([ev])
    # Card A was taken, so only Cards B and C could signal; B=55%, C=50% — both below 55.0 threshold
    assert all(s["name"] != "Card A" for s in signals)


# ---------------------------------------------------------------------------
# find_biggest_misses
# ---------------------------------------------------------------------------


def test_find_biggest_misses_order():
    ev_miss = evaluate_pick(PICK_MISS, MOCK_RATINGS)  # gap 5.0
    ev_best = evaluate_pick(PICK_BEST, MOCK_RATINGS)  # gap 0.0
    misses = find_biggest_misses([ev_miss, ev_best], top_n=5)
    # ev_best has gap 0.0 and is excluded (gap > 0 filter)
    assert len(misses) == 1
    assert misses[0]["chosen_name"] == "Card B"


def test_find_biggest_misses_top_n():
    # Build several misses of different sizes
    picks = [
        {
            "pack": 1,
            "pick": i,
            "available": [
                {"name": "Card A", "picked": False},
                {"name": "Card C", "picked": True},  # gap 10.0 every time
            ],
        }
        for i in range(1, 10)
    ]
    evals = [evaluate_pick(p, MOCK_RATINGS) for p in picks]
    misses = find_biggest_misses(evals, top_n=3)
    assert len(misses) == 3


# ---------------------------------------------------------------------------
# summarize_pack
# ---------------------------------------------------------------------------


def test_summarize_pack_counts():
    ev_best = evaluate_pick(PICK_BEST, MOCK_RATINGS)
    ev_miss = evaluate_pick(PICK_MISS, MOCK_RATINGS)
    ev_unrated = evaluate_pick(PICK_UNRATED, MOCK_RATINGS)
    summary = summarize_pack([ev_best, ev_miss, ev_unrated])
    assert summary["best"] == 1
    assert summary["costly_miss"] == 1
    assert summary["unrated"] == 1
    assert summary["rated"] == 2


def test_summarize_pack_avg_gap():
    ev_best = evaluate_pick(PICK_BEST, MOCK_RATINGS)  # gap 0.0
    ev_miss = evaluate_pick(PICK_MISS, MOCK_RATINGS)  # gap 5.0
    summary = summarize_pack([ev_best, ev_miss])
    assert summary["avg_gap"] == pytest.approx(2.5)


# ---------------------------------------------------------------------------
# load_draft_log
# ---------------------------------------------------------------------------


def test_load_draft_log_roundtrip():
    data = {
        "draft_id": "abc123",
        "expansion": "SOS",
        "wins": 3,
        "losses": 2,
        "picks": [],
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        tmp = f.name
    try:
        loaded = load_draft_log(tmp)
        assert loaded["draft_id"] == "abc123"
        assert loaded["wins"] == 3
    finally:
        os.unlink(tmp)


# ---------------------------------------------------------------------------
# load_card_ratings_lookup
# ---------------------------------------------------------------------------


def test_load_card_ratings_lookup_basic():
    csv_content = (
        "Name,Color,Rarity,# Seen,ALSA,# Picked,ATA,# GP,% GP,GP WR,# OH,OH WR,# GD,GD WR,# GIH,GIH WR,# GNS,GNS WR,IIH\n"
        "Test Card,W,C,1000,4.5,500,5.0,800,80%,55%,400,57.5%,300,58%,700,57.8%,100,53%,2.5pp\n"
    )
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, encoding="utf-8"
    ) as f:
        f.write(csv_content)
        tmp = f.name
    try:
        lookup = load_card_ratings_lookup(tmp, "OH WR")
        assert "Test Card" in lookup
        assert lookup["Test Card"]["rating"] == pytest.approx(57.5)
        assert lookup["Test Card"]["color"] == "W"
        assert lookup["Test Card"]["rarity"] == "C"
    finally:
        os.unlink(tmp)


def test_load_card_ratings_lookup_missing_rating_is_none():
    csv_content = (
        "Name,Color,Rarity,# Seen,ALSA,# Picked,ATA,# GP,% GP,GP WR,# OH,OH WR,# GD,GD WR,# GIH,GIH WR,# GNS,GNS WR,IIH\n"
        "No Data Card,W,C,,,,,,,,,,,,,,,\n"
    )
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, encoding="utf-8"
    ) as f:
        f.write(csv_content)
        tmp = f.name
    try:
        lookup = load_card_ratings_lookup(tmp, "OH WR")
        assert lookup["No Data Card"]["rating"] is None
    finally:
        os.unlink(tmp)


# ---------------------------------------------------------------------------
# format_analysis_report
# ---------------------------------------------------------------------------


def _make_draft():
    return {
        "draft_id": "test123",
        "expansion": "SOS",
        "format": "PremierDraft",
        "wins": 4,
        "losses": 3,
        "picks": [PICK_BEST, PICK_MISS, PICK_UNRATED],
    }


def test_format_analysis_report_contains_sections():
    draft = _make_draft()
    evals = [evaluate_pick(p, MOCK_RATINGS) for p in draft["picks"]]
    pack_summaries = [summarize_pack(evals)]
    signals = find_lane_signals(evals)
    report = format_analysis_report(draft, evals, pack_summaries, signals)

    for section in [
        "DRAFT ANALYSIS",
        "OVERALL STATS",
        "DRAFT ARC",
        "POOL / LANE TIMELINE",
        "SIGNAL SUMMARY BY COLOR",
        "PICK CLASSIFICATION",
        "LANE SIGNALS",
        "PACK SUMMARIES",
        "BIGGEST MISSES",
    ]:
        assert section in report, f"Missing section: {section}"


def test_format_analysis_report_contains_draft_id():
    draft = _make_draft()
    evals = [evaluate_pick(p, MOCK_RATINGS) for p in draft["picks"]]
    report = format_analysis_report(draft, evals, [summarize_pack(evals)], [])
    assert "test123" in report


def test_format_analysis_report_contains_record():
    draft = _make_draft()
    evals = [evaluate_pick(p, MOCK_RATINGS) for p in draft["picks"]]
    report = format_analysis_report(draft, evals, [summarize_pack(evals)], [])
    assert "4-3" in report


def test_format_analysis_report_contains_deterministic_core_details():
    draft = _make_draft()
    evals = [evaluate_pick(p, MOCK_RATINGS) for p in draft["picks"]]
    signals = find_lane_signals([evaluate_pick(PICK_LATE_SIGNAL, MOCK_RATINGS)])
    report = format_analysis_report(draft, evals, [summarize_pack(evals)], signals)

    assert "Early lane" in report
    assert "Takeaway: strongest late signals pointed to W" in report
    assert "KEY DECISION POINTS" not in report


def test_format_analysis_report_biggest_misses_use_negative_pp():
    draft = _make_draft()
    evals = [evaluate_pick(p, MOCK_RATINGS) for p in draft["picks"]]
    report = format_analysis_report(draft, evals, [summarize_pack(evals)], [])

    assert "(U, -5.0pp)" in report
