import json 
import jsonpickle
from HintToEnglish import hint_to_english, serialized_hint_grammar


def category_to_json(cat):
    di = {}
    di["name"] = cat.title 
    di["entities"] = cat.entities 
    di["is_numeric"] = cat.is_numeric
    return di 



def hintset_to_json(hintset, id):
    di = {}

    di["solution"] = hintset.completed_puzzle.print_grid_small()
    di["categories"] = [category_to_json(cat) for cat in hintset.completed_puzzle.categories]
    di["hints"] = [hint_to_english(hint) for hint in hintset.hints]
    di["id"] = id 

    return di

def hintset_to_di(hintset, row, col, database={}, data={}):
    di = {}
    di["solution"] = hintset.completed_puzzle.print_grid_small()
    di["categories"] = [
        category_to_json(cat) for cat in hintset.completed_puzzle.categories
    ]
    di["hints"] = [
        hint_to_english(hint, grammar_dict=database) for hint in hintset.hints
    ]
    di["hint_grammar"] = [serialized_hint_grammar(hint) for hint in hintset.hints]
    di["diff"] = col + 1
    di["sol"] = row
    if "name" in data:
        di["name"] = data["name"]
    if "scenario" in data:
        di["scenario"] = data["scenario"]
    return di

    


if __name__ == "__main__":
    file = "EscapeHelperPuzzles/Pasta/map_grid_trial_0.p"
    write_to = "EscapeHelperPuzzles/Pasta/puzzle.json"
    json_str = open( file, "r").read()
    grid = jsonpickle.decode(json_str) 
    child = grid.grid[0][1][1]
    di = hintset_to_di(child, 0, 1) 
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

