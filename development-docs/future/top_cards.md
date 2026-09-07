# Description

Create a command-line tool that identifies the most valuable cards in a Magic set based on a cumulative value threshold.

**Status**: ✅ **IMPLEMENTED** - See [top_cards_documentation.md](../top_cards_documentation.md) for full details.

## Input Parameters
- **Set code**: Magic set identifier (e.g., `dft` for Aetherdrift)
- **Rarity filter**: One or more rarity levels to include (e.g., `common`, `uncommon`, `rare`, `mythic`)
- **Threshold**: A percentage (0–100%) representing the cumulative value target

## Algorithm
1. Fetch card prices from Scryfall API for the specified set
2. Filter cards by the provided rarity levels
3. Sort cards by price (highest to lowest)
4. Return the minimum set of cards needed to meet or exceed the cumulative value threshold

## Example

Given these cards (in a set with total value of 1.0):
1. Card Two: 0.4
2. Card Three: 0.3
3. Card Four: 0.2
4. Card One: 0.1

With a **50% threshold**, the tool returns **Card Two** and **Card Three** because their combined value (0.7) meets the 50% threshold while requiring the fewest cards.

## Output

Results sorted by color, displaying the card name and price for each matching card.

## Quick Start

```bash
poetry run python main.py top-cards --set sos --rarities rare mythic --threshold 50
```

See [top_cards_documentation.md](../top_cards_documentation.md) for more examples and options.