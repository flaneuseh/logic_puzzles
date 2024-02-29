import json 
import jsonpickle
from HintToEnglish import hint_to_english


def category_to_json(cat):
    di = {}
    di["name"] = cat.title 
    di["entities"] = cat.entities 
    return di 


def hintset_to_json(hintset, file_path):
    di = {}

    di["solution"] = hintset.completed_puzzle.print_grid_small()
    di["categories"] = [category_to_json(cat) for cat in hintset.completed_puzzle.categories]
    di["hints"] = [hint_to_english(hint) for hint in hintset.hints]

    file = open(file_path, "w")
    json.dump(di,file)
    file.close()



if __name__ == "__main__":
    file = "MapElites10k/map_grid_trial_0.p"
    write_to = "hint_json.json"
    json_str = open( file, "r").read()
    grid = jsonpickle.decode(json_str) 
    hintset = grid.select()[1]

    hintset_to_json(hintset, write_to)

