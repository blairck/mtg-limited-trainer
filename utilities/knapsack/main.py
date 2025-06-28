from functools import reduce
import itertools

# {'item description': (item score, item cost)}
valuesToPrice = {
    "Floodfarm Verge (W/U)": (14, 850),
    "Gloomlake Verge (U/B)": (15, 1000),
    "Blazemire Verge (B/R)": (14, 1100),
    "Thornspire Verge (R/G)": (15, 650),
    "Hushwood Verge (G/W)": (13, 800),
    "Bleachbone Verge (B/W)": (11, 800),
    "Sunbillow Verge (W/R)": (13, 700),
    "Wastewood Verge (G/B)": (13, 700),
    "Willowrush Verge (U/G)": (16, 450),
}

allItems = list(valuesToPrice.keys())
maxSeenScore = 0
costValue = 4100
result = ""

for i in range(1, 11):
    # print("Attempting {0} combinations".format(i))
    combinations = list(itertools.combinations(allItems, i))
    found = False

    for item in combinations:
        # print("The item is: {0}".format(item))
        combinationCost = reduce(
            lambda x, y: x + y, (valuesToPrice[i][1] for i in item)
        )
        combinationScore = reduce(
            lambda x, y: x + y, (valuesToPrice[i][0] for i in item)
        )
        # print("The cost is: {0}".format(result))
        costs = []
        for value in item:
            costs.append(valuesToPrice[value][1])
        if combinationScore > maxSeenScore and combinationCost <= costValue:
            maxSeenScore = combinationScore
            itemDescriptions = ""
            for value in item:
                description = value
                itemDescriptions = "{0}, {1}".format(itemDescriptions, description)
            result = "{0} costs {1}, {2} and has a score of {3}".format(
                itemDescriptions, combinationCost, costs, combinationScore
            )
            found = True

    # if not found:
    #     print("No answer found!")

print(result)
