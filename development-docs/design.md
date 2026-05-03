# Magic card rating quiz

This feature will generate multiple-choice quizes for players. Each question will test the player's knowledge of the rating of the card. One answer will be correct, and others will be wrong. After an initial quiz of randomly selected cards, the program will re-ask wrong questions until all are answered.

## Basic flow

1. Show user multiple-choice questions, one at a time. The number of questions is configurable, and defaults to 14 cards. Players get immediate feedback on whether their answer is correct or not, but do not see the correct answer.
2. Show the player which questions they got wrong, and a score percentage correct. Do not show the player what the correct answer is.
3. Shuffle the order of the wrong questions. The answer that the user previously guessed incorrectly is removed for each card. Use those questions to repeat step 1.
4. When no questions are incorrect, display some stats to the player and exit.

## Question details

Each question will show the card name, rarity, and an image of the card. The question will ask the player to guess the rating of the card. The multiple-choice options will be generated based on calculating quantiles of the ratings of the card in the set. Then the quantiles are mapped to descriptions like "good", "bad", "great", etc. 

The number of options will depend on the difficulty level, which is configurable. The default difficulty is "medium", which has 4 options. The options will be color-coded based on the difficulty level, with "easy" being red/yellow/green, "medium" being red/yellow/green/blue, and "hard" being red/yellow/green/blue/magenta.

### Example question

Here is an example of a question with a true rating of 51.8, which makes it "okay". A link to the card image will be provided in the actual quiz, but is omitted here for simplicity.

- 1. Aerith Rescue Mission (C) - link
- a) bad
- b) okay
- c) good
- d) great

## Configuration

There should be options to configure:
- Rarities of cards to include. Default to C (common) and U (uncommon).
- The rating to quiz on. Default to CARD_OHWR (from config file)