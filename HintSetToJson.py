import json 
import jsonpickle
from HintToEnglish import hint_to_english


def category_to_json(cat):
    di = {}
    di["name"] = cat.title 
    di["entities"] = cat.entities 
    return di 


def hintset_to_json(hintset, file_path, id):
    di = {}

    di["solution"] = hintset.completed_puzzle.print_grid_small()
    di["categories"] = [category_to_json(cat) for cat in hintset.completed_puzzle.categories]
    di["hints"] = [hint_to_english(hint) for hint in hintset.hints]
    di["id"] = id 

    file = open(file_path, "w")
    json.dump(di,file)
    file.close()



if __name__ == "__main__":
    file = "School2/map_grid_trial_7.p"
    write_to = "example.json"
    json_str = open( file, "r").read()
    grid = jsonpickle.decode(json_str) 
    child = grid.grid[0][0]
    i = 0 
    puzzle_index = {}
    for row in range(grid.height):
        for col in range(grid.width):
            child = grid.grid[row][col]
            if(not child is None):
                newFilePath = "School2/puzzle_" + str(i) +".json"
                hintset_to_json(child[1], newFilePath, i)
                puzzle_index[i] = {"gini": row, "loops": col, "hintset": child[1]}
                i += 1 
    
    puzzle_json = jsonpickle.encode(puzzle_index)
    open("School2/puzzleIndex.json", "w").write(puzzle_json)

