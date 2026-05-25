# MTG Limited Trainer

This application helps train Magic: The Gathering limited format skills by presenting cards and measuring card evaluation against 17lands data.

## First Time Setup

- Create a new devcontainer based on `.devcontainer/devcontainer.json`. VS Code should automatically prompt this when opening the repository for the first time. 
  - See here for more details: https://code.visualstudio.com/docs/devcontainers/create-dev-container 
- Create `resources/` and `resources/sets/` directories
- Create a Magic set folder with the 3-letter set code based on preference `resources/sets/<SET>/`
- Download your own card rating data from 17lands:
  - Go to [17lands](https://www.17lands.com/) -> Analytics -> Card Data -> Table -> (select desired set)
  - Save the CSV files under `resources/sets/<set>/card-ratings-YYYY-MM-DD.csv`
  - Optionally, add an `exclude.csv` in the same folder to list cards to exclude
- Update the expansion code in `config.py` to a desired Magic set (such as `fin`, `eoe`, etc).
- See next section for usage details

## Usage

Run the application in the terminal as follows:

```bash
poetry run python main.py
```

The application will:
1. Load the most recent card data for the configured set
2. Start a new quiz with the configured difficulty
3. Score your evaluations against the card data
4. Provide quiz results

### Configuration

Modify `modules/config.py` to change:
- Which Magic set to use (`MAGIC_SET`)
- Data staleness threshold (`STALE_DATA_CUTOFF_DAYS`)
- Cards in quiz (`CARDS_IN_QUIZ`)

## Project Structure

The codebase has a modular structure for organization and maintainability:

```
mtg-limited-trainer/
├── main.py                 # Main application entry point
├── config.py               # Configuration file
├── pyproject.toml          # Poetry configuration and dependencies
├── src/                    # Core application modules
│   ├── config.py           # Configuration constants and settings
│   ├── data.py             # Data loading and validation utilities
│   ├── cards.py            # Card operations and pack generation
│   ├── game_logic.py       # Game scoring and evaluation logic
│   ├── display.py          # UI formatting and user interaction
│   └── quiz.py             # Quiz generation and orchestration
├── tests/                  # Tests for application modules
```

## Development Setup

This project uses Poetry for dependency management:

1. The devcontainer will automatically install Poetry and all dependencies
2. To add new dependencies: `poetry add package-name`
3. To install dependencies manually: `poetry install`
4. To activate the virtual environment: `poetry shell`

### Running Tests

- To run the tests: `poetry run pytest`

### Dependencies

- Python 3.12+
- Poetry for package management
- termcolor - Terminal text colorization

## Draft Analysis

After fetching a draft with `poetry run python main.py fetch <draft_id>`, a plain-text report is written to `resources/drafts/<draft_id>_analysis.txt`. You can also run analysis on an already-saved log:

```bash
poetry run python main.py analyze --draft-log resources/drafts/<draft_id>.json
```

Every section in the report is derived deterministically from your pick log and the 17Lands card-ratings CSV for the relevant set. No external calls are made at analysis time.

### Report sections

**OVERALL STATS**

High-level accuracy metrics across the whole draft:

- *Rated picks* — how many of your 42 picks had a 17Lands win-rate entry. Basics and very new cards may be unrated.
- *Best card taken* — picks where the card you chose had the highest win rate of any available rated card.
- *Top-3 pick* — picks where your choice ranked in the top 3 by win rate.
- *Avg pick rank* — mean rank of your chosen card among rated options in each pack (lower is better; 1.0 is perfect).
- *Avg gap* — mean difference in win rate between the best available card and your choice, in percentage points. Shown as a negative number; closer to 0 is better.

**PICK CLASSIFICATION**

Each pick is bucketed by how far it fell from the best-rated option:

| Label | Gap from best |
|---|---|
| best | 0.0 pp — you took the highest-rated card |
| defensible | ≤ 1.0 pp — close call, reasonable choice |
| speculative | ≤ 3.0 pp — below optimal but not a large swing |
| costly miss | > 3.0 pp — significant win-rate left on the table |
| unrated | your pick had no 17Lands data |

Thresholds are configured in `config.py` (`PICK_DEFENSIBLE_THRESHOLD`, `PICK_COSTLY_THRESHOLD`).

**BIGGEST MISSES**

The five picks with the largest win-rate gap. Format is:

```
P{pack}P{pick}  <card you took>  (<color>, <gap in pp>)  over  <best available card>
```

The gap is shown as a negative number (e.g. `-8.6pp`) representing how many percentage points of win rate you gave up relative to the best option in the pack.

**PACK SUMMARIES**

Per-pack rollup of the pick-classification counts and the average gap for that pack. Useful for spotting which pack had the most costly decisions.

**DRAFT ARC**

A rule-based narrative of how your lane developed:

- *Early lane* — the two most-picked colors in your first five picks.
- *Pivot window* — the earliest pack/pick where a strong late signal appeared for a color you weren't in, suggesting a potential pivot point. Requires at least three late signals in that color to fire.
- *Final lane read* — the two most-picked colors across your entire pool.
- *Summary* — a one-line sentence assembled from the above facts.

**POOL / LANE TIMELINE**

Snapshots of your picked color counts at four checkpoints: end of pack 1, mid pack 2 (pick 7), end of pack 2, and end of pack 3. "Likely lane" is simply the two most-represented colors at that point.

**SIGNAL SUMMARY BY COLOR**

Groups all late-pack lane signals (see below) by color and shows counts, the best win rate seen, and the most-repeated card names. The *Takeaway* line names the color with the most late signals — this is the color the table was most likely passing to you.

**LANE SIGNALS**

Individual strong cards (≥ 55.0% OH WR by default, configurable via `LANE_SIGNAL_WR_THRESHOLD` in `config.py`) that appeared in a pack at pick 6 or later and were not taken. A card showing up repeatedly at this position suggests its color is open at the table. The cutoff pick is configurable via `LANE_SIGNAL_PICK_CUTOFF`.

**FULL PICK LOG**

One line per pick showing your chosen card, its win rate, the best-rated alternative, and the gap. The gap column is negative for any pick that wasn't the best option and `0.0pp` for picks where you took the best card.

---

## Module Descriptions

### `modules/config.py`
Contains all configuration constants and settings:
- Magic set selection
- Data staleness thresholds
- Quiz composition settings
- CSV column mappings

### `modules/data.py`
Handles data loading and validation:
- CSV file discovery and date validation
- Card data loading and filtering
- Data format conversion utilities

### `modules/cards.py`
Card operations and pack generation:
- Card filtering by rarity
- Pack drawing with exclusion support
- Win rate sorting and filtering
- Card manipulation utilities

### `modules/game_logic.py`
Core game logic and scoring:
- Pick evaluation against optimal choices
- Score calculation and thresholds
- Game progression logic
- Result analysis

### `modules/display.py`
User interface and formatting:
- Terminal output formatting with colors
- Clickable link generation
- User input handling
