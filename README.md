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
