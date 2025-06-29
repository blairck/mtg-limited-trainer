# Magic card rating quiz

This feature will generate multiple-choice quizes for players. Each question will test the player's knowledge of the rating of the card. One answer will be correct, and others will be wrong. After an initial quiz of randomly selected cards, the program will re-ask wrong questions until all are answered.

## Basic flow

1. Show user multiple-choice questions, one at a time. The number of questions is the same as the pack size, 15 cards. Don't show the player which questions are right or wrong until the end.
2. Show the player which questions they got wrong, and a score percentage correct. Do not show the player what the correct answer is.
3. Shuffle the order of the wrong questions. Use those questions to repeat step 1.
4. When no questions are incorrect, display some stats to the player and exit.

## Question details

A question should ask the rating of a card. The rating should be rounded to the nearest 0.5 for the purpose creating the multiple choices. For example, 53.2 would be rounded to 53.0. Each question has 5 choices, called A, B, C, D, and E.

A spread of ratings should be created for the 5 multiple choices. Randomly including some choices that are close to the correct value and some that are further away. Keep in mind that no answer should be below the lowest value in the cards list (from ./resources/set/MAGIC_SET/*.csv), and no answer should be higher than the highest value.

The multiple choice answers should be shuffled, and an answer is right if it's less than 0.5 away from the true answer.

### Example question

Here is an example of the 1st question with a true rating of 51.8. The correct answer is "d".

- 1. Aerith Rescue Mission (C) - link
- a) 54.0
- b) 51.5
- c) 56.0
- d) 52.0
- e) 50.5

## Configuration

There should be options to configure:
- Rarities of cards to include. Default to C (common) and U (uncommon).
- The rating to quiz on. Default to CARD_OHWR (from config file)