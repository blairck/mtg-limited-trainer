# MTG Limited Trainer - Refactored Codebase

This application helps train Magic: The Gathering limited format skills by presenting simulated card packs and evaluating card pick decisions against optimal win rate data.

## Project Structure

The codebase has been refactored into a modular structure for better organization and maintainability:

```
mtg-limited-trainer/
├── main.py                 # Main application entry point
├── settings.py             # Legacy settings file (deprecated)
├── pyproject.toml          # Poetry configuration and dependencies
├── src/                    # Core application modules
│   ├── __init__.py
│   ├── config.py           # Configuration constants and settings
│   ├── data.py             # Data loading and validation utilities
│   ├── cards.py            # Card operations and pack generation
│   ├── game_logic.py       # Game scoring and evaluation logic
│   ├── display.py          # UI formatting and user interaction
│   └── quiz.py             # Quiz generation and orchestration
├── resources/              # Card data files
│   └── sets/
│       ├── fin/           # Foundations data
│       └── tdm/           # The Duskmourn House of Horror data
└── utilities/             # Additional utility scripts
    └── knapsack/
```

## Development Setup

This project uses Poetry for dependency management:

1. The devcontainer will automatically install Poetry and all dependencies
2. To add new dependencies: `poetry add package-name`
3. To install dependencies manually: `poetry install`
4. To activate the virtual environment: `poetry shell`

### Dependencies

- Python 3.12+
- Poetry for package management
- termcolor - Terminal text colorization

## Module Descriptions

### `modules/config.py`
Contains all configuration constants and settings:
- Magic set selection
- Data staleness thresholds
- Pack composition settings
- CSV column mappings

### `modules/data.py`
Handles data loading and validation:
- CSV file discovery and date validation
- Card data loading and filtering
- Exclude list management
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
- Pick summary display

## Key Improvements

1. **Separation of Concerns**: Each module has a specific responsibility
2. **Type Hints**: Added type annotations for better code documentation
3. **Constants**: Centralized configuration in `config.py`
4. **Error Handling**: Improved error handling throughout modules
5. **Documentation**: Added docstrings and comments
6. **Maintainability**: Smaller, focused functions that are easier to test and modify

## Usage

Run the application as before:

```bash
python main.py
```

The application will:
1. Load the most recent card data for the configured set
2. Present 3 packs of cards for evaluation
3. Score your picks against optimal win rate data
4. Provide feedback on your card evaluation skills

## Configuration

Modify `modules/config.py` to change:
- Which Magic set to use (`MAGIC_SET`)
- Data staleness threshold (`STALE_DATA_CUTOFF_DAYS`)
- Advancement requirements (`ADVANCE_THRESHOLD`)
- Pack composition (`COMMONS_PER_PACK`, `UNCOMMONS_PER_PACK`)
