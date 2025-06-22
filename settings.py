# The Magic: The Gathering set code to use for card ratings and data
# This determines which set's card rating files will be loaded from the resources/sets/ directory
magic_set = "fin"

# Number of days after which card rating data is considered stale
# Card rating files older than this many days will be considered outdated
stale_data_cutoff_days = 5

# Threshold value for advancing to the next pack
# If the user's score is below this threshold, they will not advance to the next pack
advance_threshold = 5