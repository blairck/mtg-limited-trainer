"""
Configuration settings for the MTG Limited Trainer.
"""

# The Magic 3-letter set code to use for card ratings and data
# This determines which set's card rating files will be loaded from the resources/sets/ directory
MAGIC_SET = "eoe"

# Number of days after which card rating data is considered stale
# Card rating files older than this many days will be considered outdated
STALE_DATA_CUTOFF_DAYS = 5

# CSV column names
CARD_NAME = "Name"
CARD_COLOR = "Color"
CARD_RARITY = "Rarity"
CARD_NGIH = "# GIH"
CARD_GIHWR = "GIH WR"
CARD_OHWR = "OH WR"
CARD_PERCENT_GP = "% GP"

# Quiz configuration
CARDS_IN_QUIZ = 12
QUIZ_RARITIES = ["C", "U"]  # Default rarities to include in quiz
QUIZ_RATING_KEY = CARD_OHWR  # Default rating field to quiz on
