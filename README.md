# MTG Limited Trainer

MTG Limited Trainer is a command-line project for practicing limited card evaluation and reviewing completed drafts against 17Lands card-rating data.

## Setup

This repository is designed to be set up in a devcontainer, and run locally with Poetry.

1. Open the repository in VS Code and create the devcontainer from `.devcontainer/devcontainer.json` if prompted.
2. Add 17Lands card-rating CSVs under `resources/sets/<set>/` using the naming pattern `card-ratings-YYYY-MM-DD.csv`.
3. Optionally add `exclude.csv` in the same set folder to omit specific cards from quiz mode.
4. Set the default expansion in `config.py` by changing `MAGIC_SET`.

Example resource layout:

```text
resources/
  sets/
    sos/
      card-ratings-2026-05-24.csv
      exclude.csv
```

## Usage

`main.py` exposes subcommands. Run one of these:

```bash
poetry run python main.py quiz
poetry run python main.py analyze <draft_id>
```

### Quiz mode

`quiz` loads the most recent CSV for `MAGIC_SET`, filters cards by rarity, excludes any names listed in `exclude.csv`, then asks you to evaluate each card into rating bands.

Common options:

```bash
poetry run python main.py quiz --difficulty easy
poetry run python main.py quiz --difficulty hard --num-questions 20
poetry run python main.py quiz --rarities C U R --rating-key "GIH WR"
```

Supported quiz arguments:

- `--rarities`: defaults to `QUIZ_RARITIES` from `config.py`
- `--rating-key`: defaults to `QUIZ_RATING_KEY`
- `--num-questions`: defaults to `CARDS_IN_QUIZ`
- `--difficulty`: `easy`, `medium`, or `hard`

### Draft analysis mode

`analyze` fetches one or more draft logs from 17Lands, saves the raw JSON locally, then generates an HTML report for each draft.

```bash
poetry run python main.py analyze b030c150a65c4491b98ab3b041f3f8df
poetry run python main.py analyze <draft_id_1> <draft_id_2> --rating-key "GIH WR"
```

Outputs:

- Raw draft logs: `output/drafts/raw/<draft_id>.json`
- HTML reports: `output/drafts/html/<draft_id>_analysis.html`

If `S3_BUCKET_NAME` is set in the environment, the generated HTML report is also uploaded to that bucket.

For fetch-only workflows, you can also run the helper module directly:

```bash
poetry run python -m src.fetch_draft <draft_id>
```

## Configuration

Most runtime settings live in `config.py`:

- `MAGIC_SET`: default set code used by quiz mode
- `STALE_DATA_CUTOFF_DAYS`: how old card-rating CSVs can be before they are treated as stale
- `CARDS_IN_QUIZ`: default number of quiz questions
- `QUIZ_RARITIES`: default rarities included in quiz mode
- `QUIZ_RATING_KEY`: default metric for quiz mode
- `DRAFT_RATING_KEY`: default metric for draft analysis
- `DRAFT_RAW_OUTPUT_DIR`: where fetched draft JSON files are written
- `DRAFT_HTML_OUTPUT_DIR`: where generated HTML reports are written
- `PICK_DEFENSIBLE_THRESHOLD`, `PICK_COSTLY_THRESHOLD`: draft pick classification thresholds
- `LANE_SIGNAL_PICK_CUTOFF`, `LANE_SIGNAL_WR_THRESHOLD`: lane-signal detection settings

## Draft Report Contents

Each HTML report is generated deterministically from the saved pick log plus the most recent card-ratings CSV for the draft's set.

Sections currently included:

- Overall Stats
- Pick Classification
- Biggest Misses
- Pack Summaries
- Draft Arc
- Pool / Lane Timeline
- Signal Summary by Color
- Lane Signals

The report links picks back to 17Lands and card names out to Scryfall.

## Development

Run the full test suite with:

```bash
poetry run pytest
```

Useful dependency and formatting commands:

```bash
poetry add <package>
poetry shell
./github-scripts/format_code.sh
```

## Project Structure

```text
mtg-limited-trainer/
├── main.py
├── config.py
├── src/
│   ├── cards.py
│   ├── data.py
│   ├── display.py
│   ├── draft_analysis.py
│   ├── fetch_draft.py
│   ├── game_logic.py
│   ├── html_report.py
│   └── quiz.py
├── tests/
└── resources/
```

Module overview:

- `main.py`: CLI entrypoint for quiz and draft analysis flows
- `src/data.py`: card-rating CSV discovery, loading, and staleness handling
- `src/cards.py`: rarity filtering and exclusion-aware card selection helpers
- `src/display.py`: terminal formatting helpers for quiz mode
- `src/draft_analysis.py`: deterministic pick evaluation and lane-signal analysis
- `src/fetch_draft.py`: 17Lands API fetcher for draft logs
- `src/html_report.py`: HTML report generation for analyzed drafts
- `src/quiz.py`: reusable quiz-question generation helpers
