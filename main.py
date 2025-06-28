import csv
import os
import glob
import sys
from datetime import datetime, timedelta
from termcolor import cprint
from random import shuffle

from settings import magic_set, stale_data_cutoff_days, advance_threshold

cards = []

# Open the CSV file
setName = "tdm"
# https://www.17lands.com/card_data?expansion=TDM&format=PremierDraft&start=2025-04-08&view=table&columns=everInHand&sort=name%2Casc
# Example:
# "Name",           "Color",    "Rarity",   "# GIH",    "GIH WR"
# "Abzan Devotee",  "B",        "C",        "56817",    "52.7%"

cardName = "Name"
cardColor = "Color"
cardRarity = "Rarity"
cardNGIH = "# GIH"
cardGIHWR = "GIH WR"
cardOHWR = "OH WR"


def make_clickable_link(url, text="link"):
    return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"


def find_most_recent_csv(set_name):
    """Find the most recent card-ratings CSV file for the given set."""
    pattern = f"resources/sets/{set_name}/card-ratings-*.csv"
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"No CSV files found for set '{set_name}' in pattern: {pattern}")
    # Sort by filename (which includes the date) in descending order
    files.sort(reverse=True)
    most_recent_file = files[0]
    
    # Extract date from filename and check if it's more than 1 week old
    filename = os.path.basename(most_recent_file)
    try:
        # Extract date from filename like 'card-ratings-2025-06-18.csv'
        date_str = filename.replace('card-ratings-', '').replace('.csv', '')
        file_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        current_date = datetime.now().date()
        
        if (current_date - file_date) > timedelta(days=stale_data_cutoff_days):
            print(
                f"Error: The most recent data file is from {file_date.strftime('%Y-%m-%d')}, "
                f"which is more than {stale_data_cutoff_days} days old."
                f"\nGo to {make_clickable_link(
                    f'https://www.17lands.com/card_data?expansion={set_name}&format=PremierDraft&start=2025-06-10&view=table&columns=opening',
                    "17lands.com")} "
                f"to retrieve the latest data file for {set_name}."
            )
            print(f"Please update the data files in resources/sets/{set_name}/")
            sys.exit(1)
    except ValueError:
        print(f"Error: Could not parse date from filename: {filename}")
        sys.exit(1)

    # print(f"Using most recent CSV file: {most_recent_file}")
    return most_recent_file

def getColorCode(cardColor):
    if cardColor == "G":
        return "green"
    elif cardColor == "W":
        return "white"
    elif cardColor == "U":
        return "blue"
    elif cardColor == "B":
        return "black"
    elif cardColor == "R":
        return "red"
    elif len(cardColor) > 1:
        return "yellow"
    return (150, 75, 0)

csv_file_path = find_most_recent_csv(magic_set)
with open(csv_file_path, encoding='utf-8-sig') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')

    first = True
    i = 0
    for row in csvreader:
        if first:
            cardFields = row
            first = False
        else:
            newCard = {}
            for j in range(0, len(cardFields)):
                newCard[cardFields[j]] = row[j]
            cards.append(newCard)

cards = [card for card in cards if card[cardOHWR] != ""]
commonCards = [i for i in cards if i[cardRarity] == "C"]
uncommonCards = [i for i in cards if i[cardRarity] == "U"]
#rareCards = [i for i in cards if i[cardRarity] == "R"]
#mythicCards = [i for i in cards if i[cardRarity] == "M"]

def drawPack(common, uncommon, exclude=None):
    result = []
    seen = set()
    shuffle(common)
    shuffle(uncommon)

    # Add up to 10 unique commons
    for card in common:
        card_id = card.get('Name')
        if card_id not in seen and (exclude is None or card_id not in exclude):
            result.append(card)
            seen.add(card_id)
        if len(result) == 10:
            break

    # Add up to 5 unique uncommons (not already in result)
    for card in uncommon:
        card_id = card.get('Name')
        if card_id not in seen and (exclude is None or card_id not in exclude):
            result.append(card)
            seen.add(card_id)
        if len(result) == 15:
            break
    return result


def get_card_url(card_name):
    # Scryfall search URL, spaces replaced with '+'
    return f"https://scryfall.com/search?q={card_name.replace(' ', '+')}"


def format_card_line(card, show_percent=False):
    """
    Returns a string like 'Brainstorm (U) - link' with the card name, rarity, and clickable link.
    """
    name = card[cardName]
    rarity = card[cardRarity]
    url = get_card_url(name)
    link = make_clickable_link(url, "link")
    if show_percent:
        percent = card[cardOHWR]
        return f"{name} ({rarity}) - {link} - {percent}"
    return f"{name} ({rarity}) - {link}"


def print_intro():
    print("Welcome to the MTG Card Selection Game!")
    print("You will be presented with 3 packs of cards.")
    print("For each pack, you will select 5 cards based on their Win Rate Order (OH WR).")
    print("Your goal is to match the top 5 cards by Win Rate Order as closely as possible.")
    print("Let's begin!\n")

def get_cards_to_remove(i):
    return 0 if i == 0 else i * 5

def convert_ohwr_to_float(packCards):
    for card in packCards:
        try:
            card[cardOHWR] = float(card[cardOHWR].replace("%", ""))
        except AttributeError:
            pass

def remove_top_n_by_winrate(packCards, cards_to_remove):
    if cards_to_remove > 0:
        packCards = sorted(packCards, key=lambda x: x[cardOHWR], reverse=True)[cards_to_remove:]
    return packCards

def print_pack(packCards):
    cardLookupByPackSort = {}
    for index, card in enumerate(packCards):
        lineText = f"{index+1}. {format_card_line(card)}"
        card["PackIndex"] = index+1
        cardLookupByPackSort[index+1] = card
        cprint(lineText, getColorCode(card[cardColor]))
    return cardLookupByPackSort

def get_user_input(packCards):
    while True:
        try:
            userInput = input(f"Please enter your selection as comma separated numbers (1-{len(packCards)}): ")
            parsedInput = list(int(i) for i in userInput.split(","))
            if len(parsedInput) == 5 and all(1 <= i <= len(packCards) for i in parsedInput):
                return parsedInput
            else:
                print(f"Invalid input. Please enter exactly 5 numbers between 1 and {len(packCards)}.")
        except ValueError:
            print("Invalid input. Please enter valid integers.")

def get_winrate_order(packCards):
    return sorted(packCards, key=lambda x: x[cardOHWR], reverse=True)

def evaluate_picks(parsedInput, cardLookupByPackSort, winRateOrder):
    user_score = 0
    pick_results = []
    for j, pick in enumerate(parsedInput):
        user_card = cardLookupByPackSort.get(pick)
        winrate_card = winRateOrder[j] if j < len(winRateOrder) else None
        if user_card and winrate_card and user_card[cardName] == winrate_card[cardName]:
            user_score += 1
            pick_results.append((j+1, user_card[cardName], True))
        else:
            user_name = user_card[cardName] if user_card else None
            winrate_name = winrate_card[cardName] if winrate_card else None
            pick_results.append((j+1, user_name, False, winrate_name))
    return user_score, pick_results

def print_pick_summary(pick_results, packCards):
    print("Pick summary:")
    for result in pick_results:
        pick_num = result[0]
        
        if result[2] == True:
            card = next((c for c in packCards if c[cardName] == result[1]), None)
            card_text = format_card_line(card, True)
            cprint(f"Pick {pick_num}: {card_text} - Correct", getColorCode(card[cardColor]))
        elif result[1] is not None:
            user_card = next((c for c in packCards if c[cardName] == result[1]), None)
            best_card = next((c for c in packCards if c[cardName] == result[3]), None)
            
            # Print user pick
            if user_card:
                user_str = format_card_line(user_card, True)
                cprint(f"Pick {pick_num}: {user_str}", getColorCode(user_card[cardColor]))
            else:
                print(f"Pick {pick_num}: {result[1]}")
            
            # Print best pick
            if best_card:
                best_str = format_card_line(best_card, True)
                cprint(f"\t - Wrong, best pick is: {best_str}", getColorCode(best_card[cardColor]))
            else:
                print(f"\t - Wrong, best pick is: {result[3]}")
        else:
            print(f"Pick {pick_num}: Invalid selection")


def load_exclude_list(set_name):
    """Load the exclude list from exclude.csv if it exists."""
    exclude_file_path = f"resources/sets/{set_name}/exclude.csv"
    exclude_list = set()
    
    if os.path.exists(exclude_file_path):
        try:
            with open(exclude_file_path, encoding='utf-8-sig') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
                first = True
                for row in csvreader:
                    if first:
                        first = False  # Skip header row
                    else:
                        if row and len(row) > 0:  # Check if row is not empty
                            exclude_list.add(row[0])  # Add card name to exclude set
        except Exception as e:
            print(f"Warning: Could not load exclude file {exclude_file_path}: {e}")
    
    return exclude_list


def main():
    print_intro()
    overall_score = 0
    pack = 0
    excludeCards=load_exclude_list(magic_set)
    while True:
        cards_to_remove = get_cards_to_remove(pack)
        packCards = drawPack(commonCards, uncommonCards, excludeCards)
        convert_ohwr_to_float(packCards)
        packCards = remove_top_n_by_winrate(packCards, cards_to_remove)
        shuffle(packCards)
        cardLookupByPackSort = print_pack(packCards)
        print("- - - - - - - ")
        parsedInput = get_user_input(packCards)
        winRateOrder = get_winrate_order(packCards)
        user_score, pick_results = evaluate_picks(parsedInput, cardLookupByPackSort, winRateOrder)
        print(f"\nYour pick accuracy score: {user_score}/5")
        print_pick_summary(pick_results, packCards)
        overall_score += user_score
        pack += 1
        if user_score < advance_threshold:
            print(f"You did not match {advance_threshold} of the cards. Game over.")
            break
        if pack > 2:
            break
    print(f"\nOverall score: {overall_score} points out of {3*5} possible points.")

if __name__ == "__main__":
    main()
