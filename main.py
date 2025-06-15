import csv
from termcolor import colored, cprint
from random import randint, shuffle

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

with open("resouces/sets/tdm/card-ratings-2025-05-25.csv", encoding='utf-8-sig') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')

    first = True
    i = 0
    for row in csvreader:
        if first:
            cardFields = row
            first = False
        else:
            newCard = {}
            for j in range(0, 5):
                newCard[cardFields[j]] = row[j]
            # print(newCard)
            # i += 1
            # if i > 10:
            #     break
            cards.append(newCard)

commonCards = [i for i in cards if i[cardRarity] == "C"]
uncommonCards = [i for i in cards if i[cardRarity] == "U"]
rareCards = [i for i in cards if i[cardRarity] == "R"]
mythicCards = [i for i in cards if i[cardRarity] == "M"]

def drawPack(common, uncommon, rare, mythic):
    result = []
    containsMythic = False
    if randint(1, 8) == 8:
        containsMythic = True
    
    shuffle(common)
    shuffle(uncommon)
    shuffle(rare)
    shuffle(mythic)

    for count, card in enumerate(common):
        if count < 11:
            result.append(card)

    for count, card in enumerate(uncommon):
        if count < 3:
            result.append(card)
    
    if containsMythic:
        result.append(mythicCards[0])
    else:
        result.append(rareCards[0])
    
    return result


for i in range(1):
    packCards = drawPack(commonCards, uncommonCards, rareCards, mythicCards)
    packCards.reverse()
    packCards = list(i for i in packCards if i[cardGIHWR] is not "")
    for card in packCards:
        card[cardGIHWR] = float(card[cardGIHWR].replace("%", ""))
    cardLookupByPackSort = {}
    for index, card in enumerate(packCards):
        lineText = "{0}. {1} ({2})".format(index+1, card[cardName], card[cardRarity])
        card["PackIndex"] = index+1
        cardLookupByPackSort[index+1] = card
        cprint(lineText, getColorCode(card[cardColor]))

    print("- - - - - - - ")
    userInput= input("Please enter your selection as comma seperated numbers: ")
    parsedInput = list(int(i) for i in userInput.split(","))
    print(parsedInput)
    print("Top picks: ")

    cardLookupByScoreSort = {}
    packCards.sort(key=lambda x: x[cardGIHWR], reverse=True)
    for index, card in enumerate(packCards):
        cardLookupByScoreSort[index+1] = card
        if index+1 < 4:
            lineText = "{0}. {1} ({2})".format(index+1, card[cardName], card[cardRarity])
            cprint(lineText, getColorCode(card[cardColor]))
