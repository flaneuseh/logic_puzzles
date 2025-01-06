from flask import Flask, render_template, request, url_for, jsonify
from flask_cors import CORS, cross_origin
from MapElites import evolve as map_evolve  
from HintSetToJson import category_to_json 
from HintToEnglish import hint_to_english
from LogicPuzzles import Category, Puzzle 
import json 
app = Flask(__name__)

def hintset_to_di(hintset, row, col):
    di = {}
    di["solution"] = hintset.completed_puzzle.print_grid_small()
    di["categories"] = [category_to_json(cat) for cat in hintset.completed_puzzle.categories]
    di["hints"] = [hint_to_english(hint) for hint in hintset.hints]
    di["diff"] = col + 1 
    di["sol"] = row 
    return di 

def elite_grid_to_json(grid):
    grid_di = []
    i = 0 
    for row in range(grid.height):
        for col in range(grid.width):
            child = grid.grid[row][col]
            if(not child is None):
                grid_di.append(hintset_to_di(child[1], row, col)) 
                i +=1 
    return grid_di
    

@app.route('/sample_categories', methods=['GET'])
@cross_origin()
def get_sample_categories():
    with open("database.json", 'r') as file:
        database = json.load(file)
    return jsonify(database["categories"])


@app.route('/map_evolve', methods=['POST'])
@cross_origin()
def map_evolve_api(*args):
    print("args", args)

    request_data = request.get_json() 

    print("data", request_data)



    if "puzzle" in request_data:
        categories = []
        puzzle_data = request_data["puzzle"]

        if "categories" in puzzle_data:
            for element in puzzle_data["categories"]:
                name = element["name"]
                entities = element["entities"]
                is_numeric = element["is_numeric"]
                category = Category(name, entities, is_numeric)
                categories.append(category)
        print("categories", categories[0].entities)
        puzzle = Puzzle(categories) 
    else: 
        subject = Category("order", ["1st", "2nd", "3rd", "4th"], True)
        teacher = Category("ingredients", ["Black Beans", "Tomatoes", "Jalapenos", "Chili Powder"], False)
        time = Category("store", ["Herb & Harvest", "O'Reilly's Farm", "Bayside Market", "Greenfield Co-op"], False)

        puzzle = Puzzle([subject, teacher, time]) 
    
    if "gens" in request_data:
        gen_len = request_data["gens"]
    else:
        gen_len = 300 
    
    if "pop_size" in request_data:
        pop_size = request_data["pop_size"]
    else:
        pop_size = 100 
    
    if "x_rate" in request_data:
        x_rate = request_data["x_rate"]
    else:
        x_rate = 0.6 
    
    if "mut_rate" in request_data:
        mut_rate = request_data["mut_rate"]
    else: 
        mut_rate = 0.8 
    
    if "add_rate" in request_data:
        add_rate = request_data["add_rate"]
    else:
        add_rate = 0.5 

    if "elites" in request_data:
        elits = request_data["elites"]
    else:
        elits = 10 

    print("puzzle", puzzle)
    #return jsonify("get fucked")
    elit_grid, infeasible, history = map_evolve(puzzle, gen_len, pop_size, x_rate, mut_rate, add_rate, elits) 

    #print(elit_grid)

    #print(elite_grid_to_json(elit_grid))

    return elite_grid_to_json(elit_grid)
    #return "hello world"

if __name__ == '__main__':
   app.run(port=3000) 