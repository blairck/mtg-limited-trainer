# Copilot Instructions for mtg-limited-trainer

This document helps GitHub Copilot (and other AI coding agents) get up to speed quickly on this codebase.

## 1. High-Level Architecture

- **Entry point:** `main.py` kicks off the quiz session.
- **Core modules (in `src/`):**
  - `config.py` – global constants (e.g. `MAGIC_SET`, `CARDS_IN_QUIZ`).
  - `data.py` – discover and load the latest CSVs from `resources/sets/<SET>/`; applies staleness filters.
  - `cards.py` – pack generation, rarity filtering, and exclusion handling.
  - `game_logic.py` – scoring picks against 17lands win-rate data.
  - `display.py` – terminal UI formatting via `termcolor` and click-style prompts.
  - `quiz.py` – orchestration layer tying data, cards, game_logic, and display into a playable session.

## 2. Developer Workflows

- **Devcontainer:** VS Code will auto-prompt creation from `.devcontainer/devcontainer.json` on first open.
- **Dependencies:** managed by Poetry. Run:
  ```bash
  poetry install      # install dependencies
  poetry shell        # activate venv
  ```
- **Run application:**
  ```bash
  poetry run python main.py
  ```
- **Run tests:** tests assume `src/` on `sys.path` via `tests/conftest.py`.
  ```bash
  poetry run pytest
  ```

## 3. Project-Specific Conventions

- **Resource layout:** CSV data lives in `resources/sets/<SET>/card-ratings-YYYY-MM-DD.csv`.
- **Exclusions:** optional `exclude.csv` in same folder. Parsed in `cards.py`.
- **Configuration:** two layers:
  - project-root `config.py` for CLI users
  - module `src/config.py` for internal constants
- **Staleness filter:** controlled by `STALE_DATA_CUTOFF_DAYS` in `src/config.py`.

## 4. Integration & Data Flow

1. **Discover CSVs** in `src/data.py` → return filtered Pandas frame.
2. **Generate packs** in `src/cards.py` with rarity and exclude rules.
3. **Run quiz** in `src/quiz.py`, delegates to `game_logic.py` and `display.py`.
4. **Score and output** in terminal with colors and prompts.

## 5. Testing Patterns

- Each `tests/test_*.py` exercises one module.
- `tests/conftest.py` injects project root into `sys.path`.
- Use fixtures in `test_data.py` to simulate CSV inputs.

## 6. Tips for AI Agents

- Refer to `tasks.md` for planned enhancements (e.g., import CLI support).
- Avoid generic changes to CSV parsing; align with existing `pandas` usage in `data.py`.
- Preserve quiz flow in `quiz.py` when modifying logic – display and scoring are decoupled.

---
*Please review and suggest edits if any area needs more detail or examples.*
