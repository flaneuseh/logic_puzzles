import pymongo
import jsonpickle
import json 
from ItterativeMapElits import evolve as itterative_evolve 
from ItterativeMapElits import EliteGrid 
from LogicPuzzles import Category, Puzzle 
from bson.objectid import ObjectId

myclient = pymongo.MongoClient("mongodb://localhost:27017/")

mydb = myclient["puzzleDatabase"]

userDB = mydb["users"]

sampleDatabase = mydb["samples"]


admins_public_keys = ["Admin 1"]

evolveSessions = mydb["evolveSessions"]

def add_user(user_id, privateKey, publicKey, mode):
    user = get_user(user_id)
    if user["publicKey"] in admins_public_keys:
        if get_user(privateKey) is None: 
            user_template = {"privateKey": privateKey, "publicKey": publicKey, "mode": mode, "nextPuzzleIdx":0, "likedPuzzles":[], "grammar": {}, "evolveSessions": {"nextIdx": 0}, "categories":[]}
            i = userDB.insert_one(user_template)
        
            return i 
        else: 
            return None 
    else:
        return -1 


def get_user(user_id):
    user = userDB.find_one({"privateKey": user_id})

    if not user is None:
        if not "nextPuzzleIdx" in user:
            userDB.find_one_and_update({"privateKey": user_id},  {"$set": {"nextPuzzleIdx":0}})
        if not "mode" in user:
            userDB.find_one_and_update({"privateKey": user_id}, {"$set": {"mode": "mixed"}})

    return user 

def like_puzzle(user_id, puzzle):
    user = get_user(user_id)
    next_idx = user["nextPuzzleIdx"]

    puzzle["key"] = next_idx

    result = userDB.find_one_and_update({"privateKey": user_id}, 
            {"$push": {"likedPuzzles": puzzle}, "$inc": {"nextPuzzleIdx":1}})
    
    if not result is None:
        return next_idx 
    else:
        return None 

def update_puzzle(user_id, key, new_puzzle):


    result = userDB.find_one_and_update({"privateKey": user_id,"likedPuzzles":{"$elemMatch": {"key": key}}}, 
            {"$set": {"likedPuzzles.$": new_puzzle}})
    
    
    return not result is None 

def remove_puzzle(user_id, key):

    result = userDB.find_one_and_update({"privateKey": user_id}, 
            {"$pull": {"likedPuzzles": {"key": key}}})
    
    return not result is None 

def get_liked_puzzles(user_id):
    user = get_user(user_id)

    if not user is None: 
        return user["likedPuzzles"]
    else:
        return None 

def get_user_grammar(user_id):
    
    user= get_user(user_id) 
   
    database = sampleDatabase.find_one({})
    

    if user!=None:
        custom_grammar = user["grammar"]
        print(custom_grammar)
    else: 
        custom_grammar = {}
        
        
    database["grammar"].update(custom_grammar)
    return database["grammar"]

def add_grammar_rule(user_id, request_data):

    update= {} 

    user = get_user(user_id)
    
    rule_type = request_data["type"]
    key_str = "grammar."

    if rule_type == "is":
        cat1 = request_data["cat1"] 
        cat2 = request_data["cat2"]
        key_str += cat1 + "." + cat2 + ".is"
        update[key_str] = request_data["template"]
      
    elif rule_type == "not":
        cat1 = request_data["cat1"] 
        cat2 = request_data["cat2"]
        key_str += cat1 + "." + cat2 + ".not"
        update[key_str] = request_data["template"]
    elif rule_type == "before":
        cat1 = request_data["cat1"] 
        cat2 = request_data["cat2"]
        num_cat = request_data["num_cat"]
        template1 = request_data["untimed"]
        template2 = request_data["timed"]
        step = request_data["step"]

        value = {"step": step, "untimed": template1, "timed": template2}



        key_str += cat1 + "." + cat2 + "." + num_cat + ".before"
        update[key_str] = value
    elif rule_type == "or":
        cat1 = request_data["cat1"] 
        cat2 = request_data["cat2"]
        is_cat = request_data["is_cat"]

        value = request_data["template"]


        key_str += cat1 + "." + cat2 + "." + is_cat + ".or"
        update[key_str] = value

    if user["publicKey"] in admins_public_keys:
        result = sampleDatabase.find_one_and_update({}, {"$push": update})
    else: 

        result = userDB.find_one_and_update({"privateKey": user_id}, {"$push": update})

    return result 

def add_brainstorm(user_id, request_data):

    update= {} 
    
    rule_type = request_data["type"]
    key_str = "brainstorm."

    if rule_type == "is":
        cat1 = request_data["cat1"] 
        cat2 = request_data["cat2"]
        key_str += cat1 + "." + cat2 + ".is"
        update[key_str] = request_data["template"]
      
    elif rule_type == "not":
        cat1 = request_data["cat1"] 
        cat2 = request_data["cat2"]
        key_str += cat1 + "." + cat2 + ".not"
        update[key_str] = request_data["template"]
    elif rule_type == "before":
        cat1 = request_data["cat1"] 
        cat2 = request_data["cat2"]
        num_cat = request_data["num_cat"]
        template = request_data["template"]
        timed = request_data["timed"]

        if timed: 
            key_str += cat1 + "." + cat2 + "." + num_cat + ".before.timed"
        else: 
            key_str += cat1 + "." + cat2 + "." + num_cat + ".before.untimed"

        update[key_str] = template
    elif rule_type == "or":
        cat1 = request_data["cat1"] 
        cat2 = request_data["cat2"]
        is_cat = request_data["is_cat"]

        value = request_data["template"]


        key_str += cat1 + "." + cat2 + "." + is_cat + ".or"
        update[key_str] = value
    
    
    user = get_user(user_id)

    if user["publicKey"] in admins_public_keys:
        result = sampleDatabase.find_one_and_update({}, {"$push": update})
    else: 

        result = userDB.find_one_and_update({"privateKey": user_id}, {"$push": update})

    return result 

def get_user_brainstorms(user_id):
    
    user= get_user(user_id) 
   
    database = sampleDatabase.find_one({})
    

    if user!=None:
        custom_grammar = user["brainstorm"]
    else: 
        custom_grammar = {}
        
    if "brainstorm" in database:

        database["brainstorm"].update(custom_grammar)
        return database["brainstorm"]
    else:
        return custom_grammar  


def add_category(user_id, request_data): 
    category = {"name": request_data["category"]["name"], "entities": request_data["category"]["entities"], "is_numeric": request_data["category"]["is_numeric"]}

    user = get_user(user_id)
    if user["publicKey"] in admins_public_keys:
        result = sampleDatabase.find_one_and_update({}, 
             {"$push": {"categories": category}})
    else: 
        result = userDB.find_one_and_update({"privateKey": user_id}, 
             {"$push": {"categories": category}})
    
    return result 
    
def get_categories(user_id):
    user = get_user(user_id)

    database = sampleDatabase.find_one({})["categories"]

    if not user is None: 
        return user["categories"] + database 
    else:
        return database

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


def get_new_evolve_id(user, request):


    grid = EliteGrid(10)
    puzzle = get_puzzle(request)
    gen_data = get_gen_data(request_data=request)

    data = {"user": user, "puzzle": request["puzzle"], "gen_data": gen_data, "grid": jsonpickle.encode(grid)}

    results = evolveSessions.insert_one(data)

    data["grid"] = grid
    data["puzzle"] = puzzle 
    return data, str(results.inserted_id)

def get_grid_with_id(user, request_data): 
    id = str(request_data["id"]) 


    data = evolveSessions.find_one({ "_id" : ObjectId(id), "user":user})



    if not data is None: 
        print(data.keys())
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

        data["grid"] = jsonpickle.decode(data["grid"])
        data["puzzle"] = get_puzzle(data)
        if update:
            userDB.find_one_and_update({ "_id" : ObjectId(id), "user":user}, {"$set": {"evolveSessions." + str(id) +".gen_data":gen_data}})
        return data 
     

    else: 
        return None 




def update_grid(user, id, grid): 
    grid_str = jsonpickle.encode(grid)

    results = evolveSessions.find_one_and_update({ "_id" : ObjectId(id), "user":user}, {"$set" : {"evolveSessions." + str(id) + ".grid": grid_str}})


