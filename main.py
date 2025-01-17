from flask import Flask, render_template, request, url_for, jsonify
from flask_cors import CORS, cross_origin
from MapElites import evolve as map_evolve  
from HintSetToJson import category_to_json 
from HintToEnglish import hint_to_english
from LogicPuzzles import Category, Puzzle 
from ItterativeMapElits import evolve as itterative_evolve 
from ItterativeMapElits import EliteGrid 
import json 
import jsonpickle
import random 

app = Flask(__name__)

ACCOUNT_DATABASE_FILE_STRING = "UserData.json"

def get_user_database():
    file = open(ACCOUNT_DATABASE_FILE_STRING, "r")
    json_str = file.read()
    file.close()
    database = jsonpickle.loads(json_str)
    return database 

def update_user_database(new_database):
        file = open(ACCOUNT_DATABASE_FILE_STRING, "w")
        file.write(jsonpickle.encode(new_database))
        file.close()




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

def get_new_puzzles(grid):
    new = grid.get_top_layer()

    formated_list = [hintset_to_di(child["puzzle"], child["row"], child["col"]) for child in new ]

    return formated_list 

def get_puzzle(request_data):
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
    return puzzle 

def get_gen_data(request_data):
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

    return [gen_len, pop_size, x_rate, mut_rate, add_rate, elits]


def get_new_id(curr_ids):
    id = random.randint(0, 1000 + len(curr_ids))

    while id in curr_ids:
        id = random.randint(0,  1000 + len(curr_ids))
    return id 
    

def get_new_evolve_id(database, user, request):
    user_data = database[user]

    grid = EliteGrid(10)
    puzzle = get_puzzle(request)
    gen_data = get_gen_data(request_data=request)

    data = {"puzzle": puzzle, "gen_data": gen_data, "grid": grid}

    if not "evolve_sessions" in user_data:
        user_data["evolve_sessions"] = {} 
    
    id = get_new_id(user_data["evolve_sessions"])

    user_data["evolve_sessions"][id] = data 

    update_user_database(database)
    
    return data, id 

def get_grid_with_id(database, user, request_data): 
    id = str(request_data["id"]) 
    user_data = database[user] 

    if  "evolve_sessions" in user_data and id in user_data["evolve_sessions"]: 
        data =  user_data["evolve_sessions"][id]
        gen_data = data["gen_data"] 
        update = False 

        if "gens" in request_data:
            gen_data[0] = request_data["gens"] 
            update = True 

        
        if "pop_size" in request_data:
            gen_data[1] = request_data["pop_size"] 
            update = True 
   
        
        if "x_rate" in request_data:
            gen_data[2] = request_data["x_rate"] 
            update = True
       
        if "mut_rate" in request_data:
            gen_data[3] = request_data["mut_rate"] 
            update = True
     
        
        if "add_rate" in request_data:
            gen_data[4] = request_data["add_rate"] 
            update = True
    

        if "elites" in request_data:
            gen_data[5] = request_data["elites"] 
            update = True

        if update:
            update_user_database(database)
        return data 
     

    else: 
        return None 


@app.route('/add_account', methods=['POST'])
@cross_origin()
def add_account():

    database = get_user_database()
    request_data = request.get_json() 

    username = request_data["username"]

    if username in database:
        response = jsonify("existing user")
        return response 
    else: 
        database[username] = {} 
        update_user_database(database)
        response = jsonify("success")
        return response 
    
@app.route('/like_puzzle', methods=['POST'])
@cross_origin()
def like_puzzle():
    database  = get_user_database()
    request_data = request.get_json() 

    username = request_data["username"]

    if username in database:
        if "liked_puzzles" in database[username]:
            database[username]["liked_puzzles"].append(request_data["puzzle"])
        else:
            database[username]["liked_puzzles"] = [request_data["puzzle"]]
        
        update_user_database(database)
        response = jsonify("success")
        return response 

    else: 
        response = jsonify("user not found")
        return response , 406 

@app.route('/get_liked_puzzles', methods=['GET'])
@cross_origin()
def get_liked_puzzles():
    database  = get_user_database()
    username = request.args.get('username')


    if username in database:
        if "liked_puzzles" in database[username]:
            print(database[username]["liked_puzzles"][0]) 
            return jsonify(database[username]["liked_puzzles"])
        else: 
            return jsonify([])  

    else: 
        response = jsonify("user not found")
        return response , 406 




    

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


    puzzle = get_puzzle(request_data) 
    gen_len, pop_size, x_rate, mut_rate, add_rate, elits = get_gen_data(request_data)
    
    #return jsonify("get fucked")
    elit_grid, infeasible, history = map_evolve(puzzle, gen_len, pop_size, x_rate, mut_rate, add_rate, elits) 

    #print(elit_grid)

    #print(elite_grid_to_json(elit_grid))

    return elite_grid_to_json(elit_grid)
    #return "hello world"

@app.route('/iterate_map_evolve', methods=['POST'])
@cross_origin()
def iter_map_evolve_api(*args):
    print("args", args)

    request_data = request.get_json() 

    user_data = get_user_database()

    if not "user" in request_data or not request_data["user"] in user_data: 
        response = jsonify("user not found")
        return response , 406  


    if "id" in request_data:
        id = request_data["id"]
        data = get_grid_with_id(user_data, request_data["user"], request_data)
        if data is None: 
            print(request_data["id"])
            print(user_data[request_data["user"]]["evolve_sessions"].keys())
            response = jsonify("evolve session not found")
            return response , 407
    else: 
        data, id = get_new_evolve_id(user_data, request_data["user"], request_data)

    gen_len, pop_size, x_rate, mut_rate, add_rate, elits = data["gen_data"]
    puzzle = data["puzzle"]
    grid = data["grid"]
    #grid = EliteGrid(10)
    elit_grid, infeasible, history = itterative_evolve(puzzle, gen_len, pop_size, x_rate, mut_rate, add_rate, elits, feasible_grid=grid) 

    new_puzzles = get_new_puzzles(elit_grid)

    return_di = {"puzzles": new_puzzles, "id": id}

    return jsonify(return_di)


if __name__ == '__main__':
   app.run(port=3000) 