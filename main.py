from flask import Flask, render_template, request, url_for, jsonify
from flask_cors import CORS, cross_origin
from MapElites import evolve as map_evolve  
from HintSetToJson import category_to_json 
from HintToEnglish import hint_to_english,serialized_hint_grammar
from LogicPuzzles import Category, Puzzle 
from ItterativeMapElits import evolve as itterative_evolve 
from ItterativeMapElits import EliteGrid 
import json 
import jsonpickle
import random 
import Database
from AddToGrammar import get_empty_before, get_empty_is, get_empty_not, get_empty_or

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




def hintset_to_di(hintset, row, col, database={}, data={}):
    di = {}
    di["solution"] = hintset.completed_puzzle.print_grid_small()
    di["categories"] = [category_to_json(cat) for cat in hintset.completed_puzzle.categories]
    di["hints"] = [hint_to_english(hint, grammar_dict=database) for hint in hintset.hints]
    di["hint_grammar"] = [serialized_hint_grammar(hint) for hint in hintset.hints]
    di["diff"] = col + 1
    di["sol"] = row 
    if "name" in data:
        di["name"] = data["name"]
    if "scenario" in data:
        di["scenario"] = data["scenario"]
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

def get_new_puzzles(grid,database={}, data={}):
    new = grid.get_top_layer()

    formated_list = [hintset_to_di(child["puzzle"], child["row"], child["col"],  database, data) for child in new ]

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
                inc = element["inc"] if "inc" in element else 1 
                category = Category(name, entities, is_numeric, increment=inc)
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



def get_formatted_unused_grammar(di, cats):

    empty_is = get_empty_is(di, cats)
    empty_not = get_empty_not(di, cats)
    empty_before = get_empty_before(di, cats)
    empty_or = get_empty_or(di, cats)

    return_di = {}
    if len(empty_is) > 0:
        empty_formatted = [{"cat1": e[0], "cat2": e[1]} for e in empty_is]
        return_di["is"] = {"logic": "The entity {ent1} in the category {cat1} is connect to the entity {ent2} in the category {cat2}", "vars": ["{cat1}", "{cat2}", "{ent1}", "{ent2}"],
                           "default_temp": "The {cat1} {ent1} is the {cat2} {ent2}", "empty": empty_formatted }
    if len(empty_not) > 0:
        empty_formatted = [{"cat1": e[0], "cat2": e[1]} for e in empty_not]
        return_di["not"] = {"logic": "The entity {ent1} in the category {cat1} is not connect to the entity {ent2} in the category {cat2}", "vars": ["{cat1}", "{cat2}", "{ent1}", "{ent2}"],
                           "default_temp": "The {cat1} {ent1} is not the {cat2} {ent2}", "empty": empty_formatted }
    if len(empty_before) > 0:
        empty_formatted = [{"cat1": e[0], "cat2": e[1], "num_cat": e[2]} for e in empty_before]
        return_di["before"] = {"logic": "The entity {ent1} in the category {cat1} is before/smaller then the {ent2} in the category {cat2}. The amount of which {ent1} is smaller may be specified or unspecified", "vars": ["{cat1}", "{cat2}", "{ent1}", "{ent2}", "{num_ent}", "{amount}", "{step}"],
                           "default_temp": "Unspecified version: The {cat1} {ent1} is at least {step} {num_cat} before the {cat2} {ent2}. Specified version: The {cat1} {ent1} is {amount} {num_cat}s before the {cat2} {ent2}", "empty": empty_formatted }
    if len(empty_or) > 0:
        empty_formatted = [{"cat1": e[0], "cat2": e[1], "is_cat": e[2]} for e in empty_or]
        return_di["or"] = {"logic": "Either the entity {ent1} in the category {cat1} or the entity {ent2} in the category {cat2} is connected to the entity {is_ent} in the category {is_cat}, but not both",  
                           "vars": ["{cat1}", "{cat2}", "{ent1}", "{ent2}", "{is_ent}", "{is_cat}"],
                           "default_temp": "Either the {cat1} {ent1} or the {cat2} {ent2} is the {is_cat} {is_ent}", "empty": empty_formatted }
    return return_di 



@app.route('/get_unused_grammar', methods=['POST'])
@cross_origin()
def get_unused_grammars():
    request_data = request.get_json() 
    user= request_data["username"]
    cats = request_data["cats"]

    grammar = Database.get_user_grammar(user)

    return_di = get_formatted_unused_grammar(grammar, cats)

    return_di = jsonify(return_di)
    return return_di 

@app.route('/add_category', methods=['POST'])
@cross_origin()
def add_category():

    request_data = request.get_json() 

    result = Database.add_category(request_data["user"], request_data)

    if result is None:
        response = jsonify("user not found")
        return response , 406
    else:
        response = jsonify("success")
        return response
    
@app.route('/add_scenario', methods=['POST'])
@cross_origin()
def add_scen():

    request_data = request.get_json() 

    result = Database.add_scenario(request_data["user"], request_data)

    if result is None:
        response = jsonify("user not found")
        return response , 406
    else:
        response = jsonify("success")
        return response
    
@app.route('/get_scenarios', methods=['GET'])
@cross_origin()
def get_scenarios():
    

    if "user" in request.args:
       username = request.args.get('user')
    else:
       username = "null"

    if "getSample" in request.args:
        get_sample = request.args.get("getSample")
    else:
        get_sample = False 

    user_data = Database.get_scenario(username, get_sample)
    
    return jsonify(user_data)

    
@app.route('/get_template', methods=['POST'])
@cross_origin()
def get_template():
    
    request_data = request.get_json()
    user_dict = Database.get_user_grammar(request_data["user"])
    rule_type = request_data["type"]

    if rule_type == "is":
        cat1 = request_data["cat1"] 
        cat2 = request_data["cat2"]
        if not cat1 in user_dict or not cat2 in user_dict[cat1] or not "is" in user_dict[cat1][cat2]:
            return "The {cat1} {ent1} is the {cat2} {ent2}"
        else: 
            return user_dict[cat1][cat2]["is"]
    elif rule_type == "not":
        cat1 = request_data["cat1"] 
        cat2 = request_data["cat2"]
        if not cat1 in user_dict or not cat2 in user_dict[cat1] or not "not" in user_dict[cat1][cat2]:
            return "The {cat1} {ent1} is not the {cat2} {ent2}"
        else: 
            return user_dict[cat1][cat2]["not"]
    elif rule_type == "before":
        cat1 = request_data["cat1"] 
        cat2 = request_data["cat2"]
        num_cat = request_data["num_cat"]
    

        value = {"step": 1, "untimed": "The {cat1} {ent1} is at least {step} {num_cat} before the {cat2} {ent2}.", "timed": " The {cat1} {ent1} is {amount} {num_cat}s before the {cat2} {ent2}"}

        if not cat1 in user_dict or not cat2 in user_dict[cat1] or not num_cat in user_dict[cat1][cat2] or not "before" in user_dict[cat1][cat2][num_cat]:
            return jsonify(value) 
        else: 
            return jsonify(user_dict[cat1][cat2][num_cat]["before"]) 
            

 
    elif rule_type == "or":
        cat1 = request_data["cat1"] 
        cat2 = request_data["cat2"]
        is_cat = request_data["is_cat"]

        if not cat1 in user_dict or not cat2  in user_dict[cat1] or not  is_cat in user_dict[cat1][cat2] or not "or" in user_dict[cat1][cat2][is_cat]:
           value = "Either the {cat1} {ent1} or the {cat2} {ent2} is the {is_cat} {is_ent}"
        else: 
            value = user_dict[cat1][cat2][is_cat]["or"]
        return value 



@app.route('/add_grammar_rule', methods=['POST'])
@cross_origin()
def add_grammar_rule():
    
    request_data = request.get_json() 

    results = Database.add_grammar_rule(request_data["user"], request_data)

    if results is None:
        response = jsonify("user not found")
        return response , 406
    else:
       
        response = jsonify("success")
        return response 


@app.route('/get_brainstorm', methods=['POST'])
@cross_origin()
def get_brainstorm():
    
    request_data = request.get_json()
    user_dict = Database.get_user_brainstorms(request_data["user"])
    rule_type = request_data["type"]

    if rule_type == "is":
        cat1 = request_data["cat1"] 
        cat2 = request_data["cat2"]
        if not cat1 in user_dict or not cat2 in user_dict[cat1] or not "is" in user_dict[cat1][cat2]:
            return []
        else: 
            return user_dict[cat1][cat2]["is"]
    elif rule_type == "not":
        cat1 = request_data["cat1"] 
        cat2 = request_data["cat2"]
        if not cat1 in user_dict or not cat2 in user_dict[cat1] or not "not" in user_dict[cat1][cat2]:
            return []
        else: 
            return user_dict[cat1][cat2]["not"]
    elif rule_type == "before":
        cat1 = request_data["cat1"] 
        cat2 = request_data["cat2"]
        num_cat = request_data["num_cat"]
    

        value = {"untimed":[], "timed": []}

        if not cat1 in user_dict or not cat2 in user_dict[cat1] or not num_cat in user_dict[cat1][cat2] or not "before" in user_dict[cat1][cat2][num_cat]:
            return jsonify(value) 
        else: 
            return jsonify(user_dict[cat1][cat2][num_cat]["before"]) 
            

 
    elif rule_type == "or":
        cat1 = request_data["cat1"] 
        cat2 = request_data["cat2"]
        is_cat = request_data["is_cat"]

        if not cat1 in user_dict or not cat2  in user_dict[cat1] or not  is_cat in user_dict[cat1][cat2] or not "or" in user_dict[cat1][cat2][is_cat]:
          
           value = []
        else: 
            value = user_dict[cat1][cat2][is_cat]["or"]
        return value 



@app.route('/add_brainstorm', methods=['POST'])
@cross_origin()
def add_brainstorm():
    
    request_data = request.get_json() 

    results = Database.add_brainstorm(request_data["user"], request_data)

    if results is None:
        response = jsonify("user not found")
        return response , 406
    else:
       
        response = jsonify("success")
        return response 



@app.route('/add_account', methods=['POST'])
@cross_origin()
def add_account():

    request_data = request.get_json() 

    adminId = request_data["user"]
    privateKey = request_data["privateKey"]
    publicKey = request_data["publicKey"]
    mode = request_data["mode"]

    result = Database.add_user(adminId, privateKey, publicKey, mode)


    if not result is None and result != -1: 
        response = jsonify("success")
        return response 
    elif result is None: 
        response = jsonify("existing user")
        return response 
    else: 
        response = jsonify("requires admin access")
        return response , 401  


@app.route('/get_public_key', methods=['POST'])
@cross_origin()
def get_public_key():

    request_data = request.get_json() 

    id = request_data["user"]

    result = Database.get_user(id)

    mode = result["mode"] if  "mode" in result else "mixed"


    if not result is None: 
        response = jsonify({"publicKey": result["publicKey"], "mode": mode})
        return response 
    elif result is None: 
        response = jsonify("user doesn't exist")
        return response, 401
 
        
    
@app.route('/like_puzzle', methods=['POST'])
@cross_origin()
def like_puzzle():

    request_data = request.get_json() 

    username = request_data["username"]

    result = Database.like_puzzle(username, (request_data["puzzle"])) 

    if not result is None: 
        return {"key": result}  

    else: 
        response = jsonify("user not found")
        return response , 406 
    
@app.route('/remove_puzzle', methods=['POST'])
@cross_origin()
def remove_puzzle():

    request_data = request.get_json() 

    username = request_data["username"]

    result = Database.remove_puzzle(username, request_data["key"]) 

    if result: 
        return "success"

    else: 
        response = jsonify("user not found")
        return response , 406 
    
@app.route('/update_puzzle', methods=['POST'])
@cross_origin()
def update_puzzle():

    request_data = request.get_json() 

    username = request_data["username"]

    result = Database.update_puzzle( username,  request_data["key"],  request_data["puzzle"]) 

    if result: 
        return "success"

    else: 
        response = jsonify("user not found")
        return response , 406 

@app.route('/get_liked_puzzles', methods=['GET'])
@cross_origin()
def get_liked_puzzles():
    username = request.args.get('username')

    result = Database.get_liked_puzzles(username)

    if  not result is None: 
            return jsonify(result)

    else: 
        response = jsonify("user not found")
        return response , 406 


    

@app.route('/sample_categories', methods=['GET'])
@cross_origin()
def get_sample_categories():
    

    if "user" in request.args:
       username = request.args.get('user')
    else:
       username = "null"

    user_data = Database.get_categories(username)
    
    return jsonify(user_data)






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


    request_data = request.get_json() 

    if not "user" in request_data or Database.get_user(request_data["user"]) is None: 
        response = jsonify("user not found")
        return response , 406  

    user_grammar = Database.get_user_grammar(request_data["user"])

    if "id" in request_data:
        id = request_data["id"]
        data = Database.get_grid_with_id(request_data["user"], request_data)
        if data is None: 
            response = jsonify("evolve session not found")
            return response , 407
    else: 

        data, id = Database.get_new_evolve_id( request_data["user"], request_data)

    gen_len, pop_size, x_rate, mut_rate, add_rate, elits = data["gen_data"]
    puzzle = data["puzzle"]
    grid = data["grid"]
    #grid = EliteGrid(10)
    elit_grid, infeasible, history = itterative_evolve(puzzle, gen_len, pop_size, x_rate, mut_rate, add_rate, elits, feasible_grid=grid) 

    new_puzzles = get_new_puzzles(elit_grid, user_grammar, data)

    return_di = {"puzzles": new_puzzles, "id": id}

    Database.update_grid(request_data["user"], id, elit_grid) 

    return jsonify(return_di)


if __name__ == '__main__':
   app.run(port=3000) 