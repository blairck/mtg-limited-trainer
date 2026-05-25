"""
Configuration settings for the MTG Limited Trainer.
"""

# The Magic 3-letter set code to use for card ratings and data
# This determines which set's card rating files will be loaded from the resources/sets/ directory
MAGIC_SET = "sos"

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
CARDS_IN_QUIZ = 14
QUIZ_RARITIES = ["C", "U"]  # Default rarities to include in quiz
QUIZ_RATING_KEY = CARD_OHWR  # Default rating to quiz. CARD_OHWR/CARD_GIHWR/etc

# Draft analysis
DRAFT_DATA_DIR = "resources/drafts"
DRAFT_RATING_KEY = CARD_GIHWR
# OH WR gap (pp) at or below which a miss is "defensible"
PICK_DEFENSIBLE_THRESHOLD = 1.0
# OH WR gap (pp) above which a miss is "costly"
PICK_COSTLY_THRESHOLD = 3.0
LANE_SIGNAL_PICK_CUTOFF = 6  # picks numbered >= this are treated as "late"
# minimum rating (%) for a late card to count as a lane signal
LANE_SIGNAL_WR_THRESHOLD = 55.0
