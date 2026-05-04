import json 
import jsonpickle
from HintToEnglish import hint_to_english


def category_to_json(cat):
    di = {}
    di["name"] = cat.title 
    di["entities"] = cat.entities 
    di["is_numeric"] = cat.is_numeric
    return di 



def hintset_to_json(hintset, id):
    di = {}

    applied_puzzle = None
    if hasattr(hintset, "applied_puzzle"):
        applied_puzzle = hintset.applied_puzzle
    else:
        applied_puzzle = hintset.completed_puzzle
    di["solution"] = applied_puzzle.print_grid_small()
    di["categories"] = [category_to_json(cat) for cat in applied_puzzle.categories]
    clues = []
    if hasattr(hintset, "hints"):
        clues = hintset.hints
    else:
        clues = hintset.clues()
    di["hints"] = [hint_to_english(hint) for hint in clues]
    di["id"] = id 

    return di

    


if __name__ == "__main__":
    file = "Ballroom/map_grid_trial_0.p"
    write_to = "Ballroom/ballroomInfo.json"
    json_str = open( file, "r").read()
    grid = jsonpickle.decode(json_str) 
    child = grid.grid[387][2][1]
    di = hintset_to_json(child, 0) 
    file = open(write_to, "w")
    json.dump(di,file)
    file.close()

    fitness_grid = grid.get_fitness_grid()
    """puzzle_index = {}
    i = 0 
    columns = (0, 1, 3, 5)
    for row in range(grid.height):
            children = []
            for col in columns:
                child = grid.grid[row][col]
                if(not child is None):
                    children.append((col, grid.grid[row][col])) 
            
            if(len(children) == len(columns)):
                for col, child in children: 
                    newFilePath = "school3/puzzle_" + str(row) + "_"  + str(col) +".json"
                    hintset_to_json(child[1], newFilePath, i)
                    puzzle_index[i] = {"solution": row, "loops": col, "hintset": child[1]} 
                    i += 1 

    
    puzzle_json = jsonpickle.encode(puzzle_index)
    open("School2/puzzleIndex.json", "w").write(puzzle_json)"""

