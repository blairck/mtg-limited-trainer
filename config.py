"""
Configuration settings for the MTG Limited Trainer.
"""

# The Magic: The Gathering set code to use for card ratings and data
# This determines which set's card rating files will be loaded from the resources/sets/ directory
MAGIC_SET = "fin"

# Number of days after which card rating data is considered stale
# Card rating files older than this many days will be considered outdated
STALE_DATA_CUTOFF_DAYS = 5

# Threshold value for advancing to the next pack
# If the user's score is below this threshold, they will not advance to the next pack
ADVANCE_THRESHOLD = 4

# CSV column names
CARD_NAME = "Name"
CARD_COLOR = "Color"
CARD_RARITY = "Rarity"
CARD_NGIH = "# GIH"
CARD_GIHWR = "GIH WR"
CARD_OHWR = "OH WR"

# Pack configuration
COMMONS_PER_PACK = 10
UNCOMMONS_PER_PACK = 5
PICKS_PER_PACK = 5
TOTAL_PACKS = 3

# Quiz configuration
QUIZ_RARITIES = ["C", "U"]  # Default rarities to include in quiz
QUIZ_RATING_KEY = CARD_OHWR  # Default rating field to quiz on
QUIZ_NUM_CHOICES = 6  # Number of multiple-choice options in quizzes
