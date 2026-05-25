"""
HTML draft analysis report generator.

Produces a self-contained HTML file from the same data used by
format_analysis_report in draft_analysis.py.

Public API:
    format_analysis_html(draft, evaluations, pack_summaries, lane_signals, rating_key)
        → str  (complete HTML document)
"""

import re
from collections import Counter
from html import escape
from typing import Optional
from urllib.parse import quote_plus

from config import (
    PICK_DEFENSIBLE_THRESHOLD,
    PICK_COSTLY_THRESHOLD,
    LANE_SIGNAL_PICK_CUTOFF,
    DRAFT_RATING_KEY,
)
from src.draft_analysis import (
    find_biggest_misses,
    build_pool_timeline,
    summarize_draft_arc,
    summarize_lane_signals_by_color,
    _fmt_rating,
)

# ---------------------------------------------------------------------------
# CSS color map: MTG color identity → CSS hex value
# ---------------------------------------------------------------------------

_COLOR_CSS: dict[str, str] = {
    "W": "#f5f5dc",  # wheat  (white cards)
    "U": "#4fc3f7",  # light blue
    # light gray (black cards; true black invisible on dark bg)
    "B": "#b0b0b0",
    "R": "#ef5350",  # red
    "G": "#66bb6a",  # green
}

# Fallback for multi-color and colorless
_MULTI_CSS = "#ffd600"  # gold
_COLORLESS_CSS = "#ce93d8"  # lavender / purple

_CLASSIFICATION_CSS: dict[str, str] = {
    "best": "#66bb6a",
    "defensible": "#a5d6a7",
    "speculative": "#ffb74d",
    "costly miss": "#ef5350",
    "unrated": "#90a4ae",
}

# ---------------------------------------------------------------------------
# Link helpers
# ---------------------------------------------------------------------------


def _card_css(color: str) -> str:
    """Return a CSS hex color for the given MTG color string."""
    if not color:
        return _COLORLESS_CSS
    chars = [ch for ch in color if ch in "WUBRG"]
    if not chars:
        return _COLORLESS_CSS
    if len(chars) == 1:
        return _COLOR_CSS.get(chars[0], _COLORLESS_CSS)
    return _MULTI_CSS


def _card_link(name: str, color: str) -> str:
    """Return an HTML anchor for a card name, colored by MTG color identity."""
    url = f"https://scryfall.com/search?q={quote_plus(name)}"
    css = _card_css(color)
    return (
        f'<a href="{url}" target="_blank" rel="noopener noreferrer" '
        f'style="color:{css};text-decoration:none;font-weight:bold">'
        f"{escape(name)}</a>"
    )


def _pick_link(draft_id: str, pack: int, pick_num: int) -> str:
    """Return an HTML anchor for a pick reference (e.g. P2P01) linking to 17lands."""
    url = f"https://www.17lands.com/draft/{draft_id}/{pack}/{pick_num}"
    label = f"P{pack}P{pick_num:02d}"
    return (
        f'<a href="{url}" target="_blank" rel="noopener noreferrer" '
        f'class="pick-link">{label}</a>'
    )


def _linkify_picks(text: str, draft_id: str) -> str:
    """
    Replace all P{pack}P{pick} patterns in a string with 17lands anchor links.
    Handles patterns like 'P1P06' or 'P3P11'.
    """

    def _replace(m: re.Match) -> str:
        pack = int(m.group(1))
        pick_num = int(m.group(2))
        return _pick_link(draft_id, pack, pick_num)

    return re.sub(r"P(\d)P(\d{2})", _replace, text)


def _fmt_rating_html(val: Optional[float]) -> str:
    return f"{val:.1f}%" if val is not None else "N/A"


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

_CSS = """\
  * { box-sizing: border-box; }
  body {
    background: #1a1a2e;
    color: #e0e0e0;
    font-family: 'Courier New', Courier, monospace;
    font-size: 16px;
    line-height: 1.6;
    margin: 0;
    padding: 24px 32px;
  }
  h1 { color: #ffd600; margin-bottom: 4px; font-size: 1.5em; letter-spacing: 1px; }
  h2 {
    color: #90caf9;
    border-bottom: 1px solid #2a2a4a;
    padding-bottom: 4px;
    margin-top: 28px;
    margin-bottom: 10px;
    font-size: 1.05em;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }
  .meta { color: #90a4ae; margin-bottom: 20px; }
  .meta span { color: #e0e0e0; }
  dl { display: grid; grid-template-columns: max-content 1fr; gap: 2px 16px; margin: 0 0 8px; }
  dt { color: #90a4ae; white-space: nowrap; }
  dd { margin: 0; }
  table { border-collapse: collapse; width: 100%; margin-bottom: 8px; }
  th { color: #90a4ae; text-align: left; padding: 4px 12px 4px 0; border-bottom: 1px solid #2a2a4a; font-weight: normal; }
  td { padding: 3px 12px 3px 0; vertical-align: top; }
  tr:hover td { background: #1f2040; }
  .pick-link {
    color: #b39ddb;
    text-decoration: none;
    font-weight: bold;
  }
  .pick-link:hover { text-decoration: underline; }
  .gap-negative { color: #ef5350; }
  .gap-zero     { color: #66bb6a; }
  .pack-row { margin-bottom: 4px; }
  .tag-best      { color: #66bb6a; }
  .tag-defensible { color: #a5d6a7; }
  .tag-speculative { color: #ffb74d; }
  .tag-costly    { color: #ef5350; }
  .tag-unrated   { color: #90a4ae; }
  .wr { color: #80cbc4; }
  section { margin-bottom: 8px; }
  .signal-color { color: #90a4ae; width: 40px; }
"""

# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------


def _build_header(draft: dict, rating_key: str = DRAFT_RATING_KEY) -> str:
    did = escape(draft["draft_id"])
    exp = escape(draft["expansion"])
    fmt = escape(draft["format"])
    rec = escape(f"{draft['wins']}-{draft['losses']}")
    metric = escape(rating_key)
    return f"""\
<h1>Draft Analysis</h1>
<p class="meta">
  Draft ID: <span>{did}</span> &nbsp;|&nbsp;
  Set: <span>{exp}</span> &nbsp;|&nbsp;
  Format: <span>{fmt}</span> &nbsp;|&nbsp;
  Record: <span>{rec}</span> &nbsp;|&nbsp;
  Metric: <span>{metric}</span>
</p>
"""


def _build_overall_stats(evaluations: list[dict], rating_key: str) -> str:
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

    best_pct = f" ({100 * n_best / n_rated:.1f}%)" if n_rated else ""
    top3_pct = f" ({100 * n_top3 / n_rated:.1f}%)" if n_rated else ""
    avg_rank_str = f"{avg_rank_val:.1f}" if avg_rank_val is not None else "N/A"
    avg_gap_str = (
        f'<span class="gap-negative">-{avg_gap_val:.2f} pp</span>'
        if avg_gap_val is not None
        else "N/A"
    )

    return f"""\
<section>
<h2>Overall Stats</h2>
<dl>
  <dt>Rated picks</dt>    <dd>{n_rated} / {total}</dd>
  <dt>Best card taken</dt><dd>{n_best} / {n_rated}{escape(best_pct)}</dd>
  <dt>Top-3 pick</dt>     <dd>{n_top3} / {n_rated}{escape(top3_pct)}</dd>
  <dt>Avg pick rank</dt>  <dd>{escape(avg_rank_str)}</dd>
  <dt>Avg {escape(rating_key)} gap</dt><dd>{avg_gap_str}</dd>
</dl>
</section>
"""


def _build_pick_classification(evaluations: list[dict]) -> str:
    counts = Counter(e["classification"] for e in evaluations)
    rows = [
        ("best", f"= 0.0 pp", counts["best"]),
        (
            "defensible",
            f"&le; {PICK_DEFENSIBLE_THRESHOLD:.1f} pp",
            counts["defensible"],
        ),
        ("speculative", f"&le; {PICK_COSTLY_THRESHOLD:.1f} pp", counts["speculative"]),
        ("costly miss", f"&gt; {PICK_COSTLY_THRESHOLD:.1f} pp", counts["costly miss"]),
        ("unrated", "", counts["unrated"]),
    ]
    tag_cls = {
        "best": "tag-best",
        "defensible": "tag-defensible",
        "speculative": "tag-speculative",
        "costly miss": "tag-costly",
        "unrated": "tag-unrated",
    }
    trs = ""
    for cls, threshold, count in rows:
        tc = tag_cls.get(cls, "")
        threshold_cell = f"<td>{threshold}</td>" if threshold else "<td></td>"
        trs += (
            f"<tr>"
            f'<td class="{tc}">{escape(cls)}</td>'
            f"{threshold_cell}"
            f"<td>{count}</td>"
            f"</tr>\n"
        )
    return f"""\
<section>
<h2>Pick Classification</h2>
<table>
  <thead><tr><th>Class</th><th>Threshold</th><th>Count</th></tr></thead>
  <tbody>{trs}</tbody>
</table>
</section>
"""


def _build_biggest_misses(evaluations: list[dict], draft_id: str) -> str:
    misses = find_biggest_misses(evaluations)
    if not misses:
        return "<section><h2>Biggest Misses</h2><p>(none)</p></section>\n"

    trs = ""
    for n, e in enumerate(misses, start=1):
        color = (e["chosen_meta"].get("color") or "") if e["chosen_meta"] else ""
        best_color = (e["best_meta"].get("color") or "") if e["best_meta"] else ""
        gap_str = f"-{e['gap']:.1f}pp"
        pick_ref = _pick_link(draft_id, e["pack"], e["pick_num"])
        chosen_link = _card_link(e["chosen_name"] or "?", color)
        best_link = _card_link(e["best_name"] or "?", best_color)
        trs += (
            f"<tr>"
            f"<td>{n}.</td>"
            f"<td>{pick_ref}</td>"
            f"<td>{chosen_link}</td>"
            f'<td class="gap-negative">{escape(gap_str)}</td>'
            f"<td>over</td>"
            f"<td>{best_link}</td>"
            f"</tr>\n"
        )
    return f"""\
<section>
<h2>Biggest Misses</h2>
<table>
  <thead><tr><th>#</th><th>Pick</th><th>Taken</th><th>Gap</th><th></th><th>Should Have Taken</th></tr></thead>
  <tbody>{trs}</tbody>
</table>
</section>
"""


def _build_pack_summaries(pack_summaries: list[dict]) -> str:
    trs = ""
    for i, ps in enumerate(pack_summaries, start=1):
        avg_str = f"{ps['avg_gap']:.1f}pp" if ps["avg_gap"] is not None else "N/A"
        trs += (
            f"<tr>"
            f"<td>Pack {i}</td>"
            f'<td>avg gap <span class="wr">{escape(avg_str)}</span></td>'
            f'<td><span class="tag-best">{ps["best"]} best</span></td>'
            f'<td><span class="tag-defensible">{ps["defensible"]} defensible</span></td>'
            f'<td><span class="tag-speculative">{ps["speculative"]} speculative</span></td>'
            f'<td><span class="tag-costly">{ps["costly_miss"]} costly</span></td>'
            f"</tr>\n"
        )
    return f"""\
<section>
<h2>Pack Summaries</h2>
<table><tbody>{trs}</tbody></table>
</section>
"""


def _build_draft_arc(
    evaluations: list[dict], lane_signals: list[dict], draft_id: str
) -> str:
    timeline = build_pool_timeline(evaluations)
    arc = summarize_draft_arc(evaluations, lane_signals, timeline)

    pivot_html = _linkify_picks(escape(arc["pivot_window"]), draft_id)
    summary_html = _linkify_picks(escape(arc["summary"]), draft_id)

    return f"""\
<section>
<h2>Draft Arc</h2>
<dl>
  <dt>Early lane</dt>      <dd>{escape(arc["early_lane"])}</dd>
  <dt>Pivot window</dt>    <dd>{pivot_html}</dd>
  <dt>Final lane read</dt> <dd>{escape(arc["final_lane"])}</dd>
  <dt>Summary</dt>         <dd>{summary_html}</dd>
</dl>
</section>
"""


def _build_pool_timeline(evaluations: list[dict]) -> str:
    timeline = build_pool_timeline(evaluations)
    if not timeline:
        return "<section><h2>Pool / Lane Timeline</h2><p>(none)</p></section>\n"

    trs = ""
    for snap in timeline:
        trs += (
            f"<tr>"
            f"<td>{escape(snap['label'])}</td>"
            f"<td>{escape(snap['pool_counts'])}</td>"
            f"<td>likely lane <strong>{escape(snap['lane'])}</strong></td>"
            f"</tr>\n"
        )
    return f"""\
<section>
<h2>Pool / Lane Timeline</h2>
<table><tbody>{trs}</tbody></table>
</section>
"""


def _build_signal_summary(lane_signals: list[dict]) -> str:
    signal_summary = summarize_lane_signals_by_color(lane_signals)
    if not signal_summary:
        return "<section><h2>Signal Summary by Color</h2><p>(none)</p></section>\n"

    # Build name → color lookup from raw signals for accurate per-card coloring
    card_color_lookup: dict[str, str] = {s["name"]: s["color"] for s in lane_signals}

    trs = ""
    for summary in signal_summary:
        color = summary["color"]
        css = _card_css(color)
        key_cards_parts = []
        for name, count in summary["top_cards"]:
            card_color = card_color_lookup.get(name, color)
            link = _card_link(name, card_color)
            suffix = f" ×{count}" if count > 1 else ""
            key_cards_parts.append(f"{link}{escape(suffix)}")
        key_cards_html = ", ".join(key_cards_parts)
        trs += (
            f"<tr>"
            f'<td style="color:{css};font-weight:bold">{escape(color)}</td>'
            f"<td>{summary['count']} late signals</td>"
            f'<td class="wr">best {escape(_fmt_rating_html(summary["best_rating"]))}</td>'
            f"<td>{key_cards_html}</td>"
            f"</tr>\n"
        )

    takeaway = escape(f"Strongest late signals pointed to {signal_summary[0]['color']}")
    return f"""\
<section>
<h2>Signal Summary by Color</h2>
<table>
  <thead><tr><th>Color</th><th>Signals</th><th>Best WR</th><th>Key Cards</th></tr></thead>
  <tbody>{trs}</tbody>
</table>
<p style="color:#90a4ae;margin-top:6px">{takeaway}</p>
</section>
"""


def _build_lane_signals(lane_signals: list[dict], draft_id: str) -> str:
    if not lane_signals:
        return (
            f"<section><h2>Lane Signals "
            f"<small style='color:#90a4ae'>(pick {LANE_SIGNAL_PICK_CUTOFF}+, not taken — top 5 per pack)</small>"
            f"</h2><p>(none)</p></section>\n"
        )

    pack_sections = ""
    for pack_num in (1, 2, 3):
        pack_signals = [s for s in lane_signals if s["pack"] == pack_num]
        top5 = sorted(pack_signals, key=lambda x: x["rating"], reverse=True)[:5]
        if not top5:
            pack_sections += f'<h3 style="color:#90caf9;margin:14px 0 6px">Pack {pack_num}</h3><p style="color:#90a4ae">(none)</p>\n'
            continue
        trs = ""
        for s in top5:
            color = s["color"] if s["color"] else "C"
            css = _card_css(color)
            pick_ref = _pick_link(draft_id, s["pack"], s["pick_num"])
            card_a = _card_link(s["name"], s["color"])
            trs += (
                f"<tr>"
                f"<td>{pick_ref}</td>"
                f"<td>{card_a}</td>"
                f'<td style="color:{css};font-weight:bold">{escape(color)}</td>'
                f'<td class="wr">{escape(_fmt_rating_html(s["rating"]))}</td>'
                f"</tr>\n"
            )
        pack_sections += f"""\
<h3 style="color:#90caf9;margin:14px 0 6px">Pack {pack_num}</h3>
<table>
  <thead><tr><th>Pick</th><th>Card</th><th>Color</th><th>WR</th></tr></thead>
  <tbody>{trs}</tbody>
</table>
"""
    return f"""\
<section>
<h2>Lane Signals <small style="color:#90a4ae">(pick {LANE_SIGNAL_PICK_CUTOFF}+, not taken &mdash; top 5 per pack)</small></h2>
{pack_sections}</section>
"""


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def format_analysis_html(
    draft: dict,
    evaluations: list[dict],
    pack_summaries: list[dict],
    lane_signals: list[dict],
    rating_key: str = DRAFT_RATING_KEY,
) -> str:
    """
    Produce a self-contained HTML draft analysis report.

    Returns a complete HTML document string ready to write to a .html file.
    """
    draft_id = draft["draft_id"]

    body = (
        _build_header(draft, rating_key)
        + _build_overall_stats(evaluations, rating_key)
        + _build_pick_classification(evaluations)
        + _build_biggest_misses(evaluations, draft_id)
        + _build_pack_summaries(pack_summaries)
        + _build_draft_arc(evaluations, lane_signals, draft_id)
        + _build_pool_timeline(evaluations)
        + _build_signal_summary(lane_signals)
        + _build_lane_signals(lane_signals, draft_id)
    )

    title = escape(f"Draft Analysis — {draft_id}")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
{_CSS}
  </style>
</head>
<body>
{body}
</body>
</html>
"""
