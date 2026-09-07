# Top Cards Feature

The `top-cards` feature identifies the most valuable cards in a Magic set based on a cumulative value threshold using prices from Scryfall.

## Usage

```bash
poetry run python main.py top-cards [options]
```

## Options

- `--set SET`: Magic set code (e.g., `sos`, `dft`). Defaults to the `MAGIC_SET` configured in `config.py`.
- `--rarities RARITY [RARITY ...]`: One or more rarity levels to include (e.g., `common`, `uncommon`, `rare`, `mythic`). Defaults to all rarities.
- `--threshold PERCENT`: Cumulative value threshold as a percentage (0-100). Defaults to 50%.

## Examples

### Find top cards in Streets of New Capenna at 50% threshold
```bash
poetry run python main.py top-cards --set sos --threshold 50
```

### Find common and uncommon cards in the latest set at 75% value threshold
```bash
poetry run python main.py top-cards --rarities common uncommon --threshold 75
```

### Find all rare and mythic cards needed to reach 90% of total set value
```bash
poetry run python main.py top-cards --rarities rare mythic --threshold 90
```

## Algorithm

1. **Fetch cards**: Retrieves all cards from the specified Magic set using the Scryfall API
2. **Filter by rarity**: Filters cards to include only those with the specified rarity levels
3. **Sort by price**: Sorts cards by USD price in descending order (highest value first)
4. **Calculate threshold**: Determines the target cumulative value (threshold % of total set value)
5. **Select cards**: Selects the minimum number of cards needed to meet or exceed the threshold
6. **Sort by color**: Returns results organized by color in MTG order (W, U, B, R, G, Colorless)

## Output

The tool displays:
- Cards grouped by color
- Card name, price, and rarity for each selected card
- Total cumulative value of selected cards
- Summary statistics (number of cards selected, rarity filters applied)

## Example Output

```
======================================================================
Top Cards (Cumulative Value: $15.50)
======================================================================

White:
  Cleansing Nova                           $5.00 (Rare)
  Swordswoman                              $2.50 (Uncommon)

Blue:
  Counterspell                             $4.00 (Uncommon)
  Island                                   $2.00 (Common)

Black:
  Fatal Push                               $2.00 (Common)

======================================================================

Selected 5 card(s) to reach 50.0% threshold
Total value: $15.50
Rarities included: common, uncommon, rare
```

## Implementation Details

- **API**: Uses Scryfall's public API (`https://api.scryfall.com`)
- **Pricing**: Prefers USD prices, falls back to other currency options if unavailable
- **Color sorting**: Uses MTG standard color order with colorless/lands appearing last
- **Error handling**: Validates parameters and provides helpful error messages for API failures or missing data

## Testing

The feature includes comprehensive unit tests:

```bash
poetry run pytest tests/test_top_cards.py -v
```

Tests cover:
- Price extraction and fallback logic
- Color identification and sorting
- Rarity filtering (including case-insensitive matching)
- Threshold calculation and card selection
- API pagination handling
- Parameter validation
