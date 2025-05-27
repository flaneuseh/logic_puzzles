import jsonpickle
from Evolution import HintSet, get_needed, get_needed2, minimal_subsets 

map_elite_file = "school3/puzzleIndex.json"

json = open( map_elite_file, "r").read()

index = jsonpickle.decode(json)

insightsNeededIndex ={}
#hintSet = mapElit.grid[444][4][1]

for key in index:
    hintSet = index[key]["hintset"]

    needed1 = get_needed(hintSet.puzzle,hintSet.non_duplicates()) 

    print("needed 1") 
    print(needed1)

    print("needed 2")
    needed2 = get_needed2(hintSet.puzzle,hintSet.non_duplicates()) 
    print(needed2)


    

    print("minimal subsets")
    needed3 = minimal_subsets(hintSet.puzzle,hintSet.non_duplicates()) 
    print(needed3)
    print(len(needed3))
    print("\n\n")

    insightsNeededIndex[key] = {"easiestInsights": needed1, "requiredInsights":needed2, "minimalSubsets": needed3}

new_json = jsonpickle.encode(insightsNeededIndex)

file = open("InsightsKey.json", "w")
file.write(new_json)