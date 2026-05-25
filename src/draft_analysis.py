"""
Deterministic draft pick analysis helpers.

Produces a plain-text coaching report suitable for pasting into an LLM.

Analysis flow:
    ratings  = load_card_ratings_lookup(csv_path, rating_key)
    draft    = load_draft_log(path)
    evals    = [evaluate_pick(p, ratings) for p in draft["picks"]]
    signals  = find_lane_signals(evals)
    summaries = [summarize_pack([e for e in evals if e["pack"] == p]) for p in packs]
    report   = format_analysis_report(draft, evals, summaries, signals, rating_key)
"""

import csv
import json
from collections import Counter
from typing import Optional

from config import (
    PICK_DEFENSIBLE_THRESHOLD,
    PICK_COSTLY_THRESHOLD,
    LANE_SIGNAL_PICK_CUTOFF,
    LANE_SIGNAL_WR_THRESHOLD,
    DRAFT_RATING_KEY,
)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_draft_log(path: str) -> dict:
    """Load a saved draft log JSON file and return it as a dict."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_card_ratings_lookup(csv_path: str, rating_key: str = DRAFT_RATING_KEY) -> dict:
    """
    Read a 17Lands card-ratings CSV and return a dict keyed by card name.

    Each value contains:
        rating  – float value of the chosen rating_key column (e.g. OH WR stripped of %)
        color   – str (e.g. "W", "UB", "")
        rarity  – str (e.g. "C", "U", "R", "M")
        alsa    – float or None (average last-seen at)
        ata     – float or None (average taken at)
        iih     – str (improvement in hand, e.g. "3.2pp")
    """
    lookup: dict[str, dict] = {}

    def _pct(s: str) -> Optional[float]:
        s = s.strip()
        if not s:
            return None
        try:
            return float(s.rstrip("%"))
        except ValueError:
            return None

    def _float(s: str) -> Optional[float]:
        s = s.strip()
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None

    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["Name"]
            lookup[name] = {
                "rating": _pct(row.get(rating_key, "")),
                "color": row.get("Color", ""),
                "rarity": row.get("Rarity", ""),
                "alsa": _float(row.get("ALSA", "")),
                "ata": _float(row.get("ATA", "")),
                "iih": row.get("IIH", ""),
            }

    return lookup


def normalize_card_name(name: str) -> str:
    """Strip surrounding whitespace from a card name for lookup purposes."""
    return name.strip()


# ---------------------------------------------------------------------------
# Per-pick evaluation
# ---------------------------------------------------------------------------


def evaluate_pick(
    pick: dict, ratings: dict, rating_key: str = DRAFT_RATING_KEY
) -> dict:
    """
    Evaluate a single pick against the ratings lookup.

    Returns a dict with:
        pack, pick_num      – pack and pick number (1-indexed)
        chosen_name         – name of the card that was taken
        chosen_meta         – ratings entry for the chosen card (or None)
        best_name           – name of the highest-rated available card
        best_meta           – ratings entry for the best card
        rank                – 1-indexed rank of chosen card among rated options
        pool_size           – number of rated cards in the pack
        gap                 – rating gap between best and chosen (pp), or None if unrated
        classification      – "best" | "defensible" | "speculative" | "costly miss" | "unrated"
        top3                – top 3 rated cards in the pack
        available_rated     – all rated cards sorted by rating descending
        rating_key          – the metric used for comparison
    """
    available_rated: list[dict] = []
    chosen_name: Optional[str] = None
    chosen_meta: Optional[dict] = None

    for card in pick["available"]:
        name = card["name"]
        meta = ratings.get(normalize_card_name(name))

        if card["picked"]:
            chosen_name = name
            chosen_meta = meta

        if meta is not None and meta.get("rating") is not None:
            available_rated.append({"name": name, **meta})

    available_sorted = sorted(available_rated, key=lambda x: x["rating"], reverse=True)

    base = {
        "pack": pick["pack"],
        "pick_num": pick["pick"],
        "chosen_name": chosen_name,
        "chosen_meta": {"name": chosen_name, **(chosen_meta or {})},
        "pool_size": len(available_sorted),
        "top3": available_sorted[:3],
        "available_rated": available_sorted,
        "rating_key": rating_key,
    }

    # Chosen card has no rating → skip gap math
    if chosen_meta is None or chosen_meta.get("rating") is None:
        return {
            **base,
            "best_name": available_sorted[0]["name"] if available_sorted else None,
            "best_meta": available_sorted[0] if available_sorted else None,
            "rank": None,
            "gap": None,
            "classification": "unrated",
        }

    if not available_sorted:
        # No rated cards in the pack at all (shouldn't happen outside of edge cases)
        return {
            **base,
            "best_name": chosen_name,
            "best_meta": {"name": chosen_name, **chosen_meta},
            "rank": 1,
            "gap": 0.0,
            "classification": "best",
        }

    best = available_sorted[0]
    rank = next(
        (i + 1 for i, c in enumerate(available_sorted) if c["name"] == chosen_name),
        None,
    )
    gap = round(best["rating"] - chosen_meta["rating"], 2)

    return {
        **base,
        "best_name": best["name"],
        "best_meta": best,
        "rank": rank,
        "gap": gap,
        "classification": classify_pick(gap),
    }


def classify_pick(gap: Optional[float]) -> str:
    """
    Classify a pick by its rating gap from the best available card.

    Returns one of: "best", "defensible", "speculative", "costly miss", "unrated"
    """
    if gap is None:
        return "unrated"
    if gap == 0.0:
        return "best"
    if gap <= PICK_DEFENSIBLE_THRESHOLD:
        return "defensible"
    if gap <= PICK_COSTLY_THRESHOLD:
        return "speculative"
    return "costly miss"


# ---------------------------------------------------------------------------
# Pool state tracking
# ---------------------------------------------------------------------------


def update_pool_state(pool_state: Counter, chosen_meta: Optional[dict]) -> Counter:
    """
    Add the chosen card's color(s) to the running pool color counter.

    Multi-color cards (e.g. color="WU") each character is counted separately.
    Colorless/artifact cards (color="") contribute nothing.
    """
    if chosen_meta is None:
        return pool_state
    for ch in chosen_meta.get("color") or "":
        if ch in "WUBRG":
            pool_state[ch] += 1
    return pool_state


def extract_colors(color: str) -> list[str]:
    """Return the ordered list of mana colors in a card color string."""
    return [ch for ch in color if ch in "WUBRG"]


def format_color_identity(color: str) -> str:
    """Format an internal color string for human-readable report output."""
    return color or "C"


def summarize_pool_colors(evaluations: list[dict]) -> Counter:
    """Return total picked color counts across the whole draft."""
    pool_state: Counter = Counter()
    for ev in evaluations:
        update_pool_state(pool_state, ev["chosen_meta"])
    return pool_state


def top_colors(pool_state: Counter, limit: int = 2) -> list[tuple[str, int]]:
    """Return the most represented colors in deterministic order."""
    return sorted(
        ((color, count) for color, count in pool_state.items() if count > 0),
        key=lambda item: (-item[1], "WUBRG".index(item[0])),
    )[:limit]


def guess_lane(pool_state: Counter) -> str:
    """Return a short color-pair guess from the current pool colors."""
    leaders = top_colors(pool_state, limit=2)
    if not leaders:
        return "undetermined"
    if len(leaders) == 1:
        return leaders[0][0]
    if leaders[1][1] == 0:
        return leaders[0][0]
    return "".join(color for color, _ in leaders)


def format_pool_counts(pool_state: Counter) -> str:
    """Format colored pick counts for compact timeline output."""
    parts = [
        f"{color}:{pool_state[color]}" for color in "WUBRG" if pool_state[color] > 0
    ]
    return " ".join(parts) if parts else "none"


def summarize_lane_signals_by_color(lane_signals: list[dict]) -> list[dict]:
    """Group late passed signals by color for compact reporting."""
    grouped: dict[str, dict] = {}

    for signal in lane_signals:
        color = format_color_identity(signal["color"])
        bucket = grouped.setdefault(
            color,
            {"color": color, "count": 0, "best_rating": 0.0, "cards": Counter()},
        )
        bucket["count"] += 1
        bucket["best_rating"] = max(bucket["best_rating"], signal["rating"])
        bucket["cards"][signal["name"]] += 1

    summaries = []
    for bucket in grouped.values():
        top_cards = sorted(
            bucket["cards"].items(),
            key=lambda item: (-item[1], item[0]),
        )[:3]
        summaries.append(
            {
                "color": bucket["color"],
                "count": bucket["count"],
                "best_rating": bucket["best_rating"],
                "top_cards": top_cards,
            }
        )

    def _sort_key(item: dict) -> tuple[int, int]:
        color = item["color"]
        order = "WUBRGC"
        primary = order.index(color[0]) if color[0] in order else len(order)
        return (-item["count"], primary)

    return sorted(summaries, key=_sort_key)


def build_pool_timeline(evaluations: list[dict]) -> list[dict]:
    """Capture deterministic pool snapshots at key draft checkpoints."""
    checkpoints = [
        ("End Pack 1", lambda ev: ev["pack"] == 1 and ev["pick_num"] == 14),
        ("Mid Pack 2", lambda ev: ev["pack"] == 2 and ev["pick_num"] == 7),
        ("End Pack 2", lambda ev: ev["pack"] == 2 and ev["pick_num"] == 14),
        ("End Pack 3", lambda ev: ev["pack"] == 3 and ev["pick_num"] == 14),
    ]
    pool_state: Counter = Counter()
    timeline = []

    for ev in evaluations:
        update_pool_state(pool_state, ev["chosen_meta"])
        for label, predicate in checkpoints:
            if predicate(ev):
                timeline.append(
                    {
                        "label": label,
                        "pool_counts": format_pool_counts(pool_state),
                        "lane": guess_lane(pool_state),
                    }
                )
    return timeline


def summarize_draft_arc(
    evaluations: list[dict],
    lane_signals: list[dict],
    timeline: list[dict],
) -> dict:
    """Create a deterministic, rule-based summary of the draft's lane development."""
    early_pool = summarize_pool_colors(evaluations[:5])
    final_pool = summarize_pool_colors(evaluations)
    early_lane = guess_lane(early_pool)
    final_lane = guess_lane(final_pool)

    signal_by_color = summarize_lane_signals_by_color(lane_signals)
    strongest_signal = signal_by_color[0] if signal_by_color else None
    pivot_window = "none identified"
    if strongest_signal and strongest_signal["count"] >= 3:
        pivot_pick = next(
            (
                signal
                for signal in sorted(
                    lane_signals, key=lambda item: (item["pack"], item["pick_num"])
                )
                if format_color_identity(signal["color"]) == strongest_signal["color"]
            ),
            None,
        )
        if pivot_pick is not None:
            pivot_window = (
                f"P{pivot_pick['pack']}P{pivot_pick['pick_num']:02d}"
                f" toward {strongest_signal['color']}"
            )

    summary_parts = []
    if early_lane == "undetermined":
        summary_parts.append("early picks stayed open")
    else:
        summary_parts.append(f"early pool leaned {early_lane}")

    if strongest_signal and strongest_signal["count"] >= 3:
        summary_parts.append(
            f"late signals most strongly favored {strongest_signal['color']}"
        )
    else:
        summary_parts.append("late signals were mixed")

    if timeline:
        summary_parts.append(f"final pool finished {timeline[-1]['lane']}")
    else:
        summary_parts.append(f"final pool finished {final_lane}")

    return {
        "early_lane": early_lane,
        "pivot_window": pivot_window,
        "final_lane": final_lane,
        "summary": "; ".join(summary_parts),
    }


def find_key_decision_points(evaluations: list[dict], top_n: int = 5) -> list[dict]:
    """Return the most consequential deviations for focused review."""
    candidates = [e for e in evaluations if e["gap"] is not None and e["gap"] > 0.0]
    prioritized = sorted(
        candidates,
        key=lambda e: (
            -e["gap"],
            -(1 if e["pick_num"] >= LANE_SIGNAL_PICK_CUTOFF else 0),
            e["pack"],
            e["pick_num"],
        ),
    )
    return prioritized[:top_n]


# ---------------------------------------------------------------------------
# Signal and summary helpers
# ---------------------------------------------------------------------------


def find_lane_signals(evaluations: list[dict]) -> list[dict]:
    """
    Return strong cards that were seen late (pick >= LANE_SIGNAL_PICK_CUTOFF) but not taken.

    Cards above LANE_SIGNAL_WR_THRESHOLD that wheel or are passed late suggest
    that color is open at the table.

    Returns a list of dicts with: pack, pick_num, name, color, rating.
    """
    signals = []
    for ev in evaluations:
        if ev["pick_num"] < LANE_SIGNAL_PICK_CUTOFF:
            continue
        for card in ev["available_rated"]:
            if card["name"] == ev["chosen_name"]:
                continue
            if card["rating"] >= LANE_SIGNAL_WR_THRESHOLD:
                signals.append(
                    {
                        "pack": ev["pack"],
                        "pick_num": ev["pick_num"],
                        "name": card["name"],
                        "color": card["color"],
                        "rating": card["rating"],
                    }
                )
    return signals


def summarize_pack(pack_evals: list[dict]) -> dict:
    """
    Aggregate stats for a single pack.

    Returns: rated, avg_gap, best, defensible, speculative, costly_miss, unrated.
    """
    rated = [e for e in pack_evals if e["gap"] is not None]
    counts = Counter(e["classification"] for e in pack_evals)
    avg_gap = round(sum(e["gap"] for e in rated) / len(rated), 2) if rated else None
    return {
        "rated": len(rated),
        "avg_gap": avg_gap,
        "best": counts["best"],
        "defensible": counts["defensible"],
        "speculative": counts["speculative"],
        "costly_miss": counts["costly miss"],
        "unrated": counts["unrated"],
    }


def find_biggest_misses(evaluations: list[dict], top_n: int = 5) -> list[dict]:
    """Return the top_n picks with the largest rating gap (non-zero misses only)."""
    missed = [e for e in evaluations if e["gap"] is not None and e["gap"] > 0.0]
    return sorted(missed, key=lambda x: x["gap"], reverse=True)[:top_n]


# ---------------------------------------------------------------------------
# Report formatter
# ---------------------------------------------------------------------------


def _fmt_rating(val: Optional[float]) -> str:
    return f"{val:.1f}%" if val is not None else "N/A"


def format_analysis_report(
    draft: dict,
    evaluations: list[dict],
    pack_summaries: list[dict],
    lane_signals: list[dict],
    rating_key: str = DRAFT_RATING_KEY,
) -> str:
    """
    Assemble the full plain-text coaching report.

    The output is clean and LLM-friendly — paste it directly into a chat.
    """
    lines: list[str] = []

    # ── Header ──────────────────────────────────────────────────────────────
    lines.append("DRAFT ANALYSIS")
    lines.append("=" * 60)
    lines.append(f"Draft ID : {draft['draft_id']}")
    lines.append(
        f"Set      : {draft['expansion']}"
        f"  |  Format: {draft['format']}"
        f"  |  Record: {draft['wins']}-{draft['losses']}"
    )
    lines.append(f"Metric   : {rating_key}")
    lines.append("")

    # ── Overall stats ────────────────────────────────────────────────────────
    rated = [e for e in evaluations if e["gap"] is not None]
    total = len(evaluations)
    n_rated = len(rated)
    n_best = sum(1 for e in rated if e["classification"] == "best")
    n_top3 = sum(1 for e in rated if e.get("rank") is not None and e["rank"] <= 3)
    avg_rank_val = (
        sum(e["rank"] for e in rated if e.get("rank") is not None) / n_rated
        if n_rated
        else None
    )
    avg_gap_val = sum(e["gap"] for e in rated) / n_rated if n_rated else None
    timeline = build_pool_timeline(evaluations)
    draft_arc = summarize_draft_arc(evaluations, lane_signals, timeline)
    signal_summary = summarize_lane_signals_by_color(lane_signals)

    lines.append("OVERALL STATS")
    lines.append(f"  Rated picks    : {n_rated} / {total}")
    lines.append(
        f"  Best card taken: {n_best} / {n_rated}"
        + (f"  ({100 * n_best / n_rated:.1f}%)" if n_rated else "")
    )
    lines.append(
        f"  Top-3 pick     : {n_top3} / {n_rated}"
        + (f"  ({100 * n_top3 / n_rated:.1f}%)" if n_rated else "")
    )
    lines.append(
        f"  Avg pick rank  : {avg_rank_val:.1f}"
        if avg_rank_val is not None
        else "  Avg pick rank  : N/A"
    )
    lines.append(
        f"  Avg {rating_key} gap : -{avg_gap_val:.2f} pp"
        if avg_gap_val is not None
        else f"  Avg {rating_key} gap : N/A"
    )
    lines.append("")

    # ── Classification breakdown ─────────────────────────────────────────────
    counts = Counter(e["classification"] for e in evaluations)
    lines.append("PICK CLASSIFICATION")
    lines.append(f"  best          (0.0 pp)               : {counts['best']}")
    lines.append(
        f"  defensible    (<= {PICK_DEFENSIBLE_THRESHOLD:.1f} pp)            : {counts['defensible']}"
    )
    lines.append(
        f"  speculative   (<= {PICK_COSTLY_THRESHOLD:.1f} pp)            : {counts['speculative']}"
    )
    lines.append(
        f"  costly miss   (>  {PICK_COSTLY_THRESHOLD:.1f} pp)            : {counts['costly miss']}"
    )
    lines.append(f"  unrated                               : {counts['unrated']}")
    lines.append("")

    # ── Biggest misses ───────────────────────────────────────────────────────
    misses = find_biggest_misses(evaluations)
    lines.append("BIGGEST MISSES")
    if misses:
        for n, e in enumerate(misses, start=1):
            color = (e["chosen_meta"].get("color") or "C") if e["chosen_meta"] else "?"
            lines.append(
                f"  {n}. P{e['pack']}P{e['pick_num']:02d}"
                f"  {e['chosen_name']:<32} ({color}, {-e['gap']:.1f}pp)"
                f"  over  {e['best_name']:<32}"
            )
    else:
        lines.append("  (none)")
    lines.append("")

    # ── Pack summaries ───────────────────────────────────────────────────────
    lines.append("PACK SUMMARIES")
    for i, ps in enumerate(pack_summaries, start=1):
        avg_str = f"{ps['avg_gap']:.1f}pp" if ps["avg_gap"] is not None else "N/A"
        lines.append(
            f"  Pack {i}"
            f"  avg gap {avg_str:>6}"
            f"  |  best {ps['best']}"
            f"  |  defensible {ps['defensible']}"
            f"  |  speculative {ps['speculative']}"
            f"  |  costly {ps['costly_miss']}"
        )
    lines.append("")

    # ── Draft arc ───────────────────────────────────────────────────────────
    lines.append("DRAFT ARC")
    lines.append(f"  Early lane      : {draft_arc['early_lane']}")
    lines.append(f"  Pivot window    : {draft_arc['pivot_window']}")
    lines.append(f"  Final lane read : {draft_arc['final_lane']}")
    lines.append(f"  Summary         : {draft_arc['summary']}")
    lines.append("")

    # ── Pool / lane timeline ───────────────────────────────────────────────
    lines.append("POOL / LANE TIMELINE")
    if timeline:
        for snapshot in timeline:
            lines.append(
                f"  {snapshot['label']:<12}: picked colors {snapshot['pool_counts']}"
                f" | likely lane {snapshot['lane']}"
            )
    else:
        lines.append("  (none)")
    lines.append("")

    # ── Signal summary by color ────────────────────────────────────────────
    lines.append("SIGNAL SUMMARY BY COLOR")
    if signal_summary:
        for summary in signal_summary:
            key_cards = ", ".join(
                f"{name} x{count}" if count > 1 else name
                for name, count in summary["top_cards"]
            )
            lines.append(
                f"  {summary['color']:<2} : {summary['count']:>2} late signals"
                f" | best {_fmt_rating(summary['best_rating'])}"
                f" | key cards: {key_cards}"
            )
        lines.append(
            f"  Takeaway: strongest late signals pointed to {signal_summary[0]['color']}"
        )
    else:
        lines.append("  (none)")
    lines.append("")

    # ── Lane signals ─────────────────────────────────────────────────────────
    lines.append(
        f"LANE SIGNALS  "
        f"(strong cards seen at pick {LANE_SIGNAL_PICK_CUTOFF}+, not taken)"
    )
    if lane_signals:
        for s in sorted(lane_signals, key=lambda x: x["rating"], reverse=True)[:10]:
            color_str = s["color"] if s["color"] else "C"
            lines.append(
                f"  P{s['pack']}P{s['pick_num']:02d}"
                f"  {s['name']:<32}"
                f"  {color_str:>2}"
                f"  {_fmt_rating(s['rating'])}"
            )
    else:
        lines.append("  (none)")
    lines.append("")

    return "\n".join(lines) + "\n"
