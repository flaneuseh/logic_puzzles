import pymongo
import jsonpickle
import json
from ItterativeMapElits import evolve as itterative_evolve
from ItterativeMapElits import EliteGrid
from LogicPuzzles import Category, Puzzle
from bson.objectid import ObjectId
from copy import deepcopy

myclient = pymongo.MongoClient("mongodb://localhost:27017/")

mydb = myclient["puzzleDatabase"]

userDB = mydb["users"]

sampleDatabase = mydb["samples"]

scenarioDatabase = mydb["scenarios"]

admins_public_keys = ["Admin 1", "Admin 2"]

evolveSessions = mydb["evolveSessions"]

sessions = mydb["sessions"]

posted_puzzles_hybrid = mydb["community_hybrid"]

posted_puzzles_serious = mydb["community_serious"]

survey_db = mydb["surveys"]


def get_user_data(user):
    user = get_user(user)

    del user["_id"]
    del user["community_puzzles"]

    return user 


def add_survey(user, data):
 
    user = get_user(user)
    if user != None:
        data["username"] = user["publicKey"]
        survey_db.insert_one(data)
    return 1


def get_number_surveys(user):
    user = get_user(user)
    if user != None:
        surveys = list(survey_db.find({"username": user["publicKey"]}))

        return len(surveys)
    else:
        return -1


def add_user(user_id, privateKey, publicKey, mode):
    user = get_user(user_id)
    if user["publicKey"] in admins_public_keys:
        if get_user(privateKey) is None:
            user_template = {
                "mode": mode,
                "privateKey": privateKey,
                "publicKey": publicKey,
                "nextPuzzleIdx": 0,
                "likedPuzzles": [],
                "grammar": {},
                "evolveSessions": {"nextIdx": 0},
                "categories": [],
            }
            i = userDB.insert_one(user_template)

            return i
        else:
            return None
    else:
        return -1


def get_posted_puzzles(user_id):
    user = get_user(user_id) 
    if user != None and user["mode"] != "admin":
        posted_puzzles = posted_puzzles_hybrid if user["mode"] == "mixed" else posted_puzzles_serious
        puzzles = list(posted_puzzles.find({}))
   
        for p in puzzles:
            p["_id"] = str(p["_id"])
        return puzzles
    elif user != None and user["mode"] == "admin":
        mixed_puzzles = list(posted_puzzles_hybrid.find({}))
   
        for p in mixed_puzzles:
            p["_id"] = str(p["_id"])
        
        serious_puzzles = list(posted_puzzles_serious.find({}))
   
        for p in serious_puzzles:
            p["_id"] = str(p["_id"])

        return {"mixed": mixed_puzzles, "serious": serious_puzzles}
        
        
    else:
        return None


def view_puzzle(user_id, puzzle_id, mode = None):
    user = get_user(user_id)
    if get_user(user_id) != None:
        posted_puzzles = posted_puzzles_hybrid if (user["mode"] == "mixed" or mode == "mixed") else posted_puzzles_serious
        result = posted_puzzles.find_one_and_update({"_id": ObjectId(puzzle_id)}, {"$inc": {"views": 1}})
        return result 
    
def post_puzzle(user_id, post_title, post_body, time,  puzzle):
    user = get_user(user_id)

    if user != None:
        posted_puzzles = posted_puzzles_hybrid if user["mode"] == "mixed" else posted_puzzles_serious
        data = {
            "username": user["publicKey"],
            "time": time,
            "title": post_title,
            "body": post_body,
            "puzzle": puzzle,
            "comments": [],
            "views": 0,
            "likes": 0,
        }

        puzzle = posted_puzzles.insert_one(data)


        if user["mode"] == "admin":
            posted_puzzles_hybrid.insert_one(data)
        return puzzle
    else:
        return None

def delete_puzzle(admin_id, mode, puzzle_id):
    admin = get_user(admin_id)

    if (admin["mode"] == "admin"):
        posted_puzzles = posted_puzzles_hybrid if mode == "mixed" else posted_puzzles_serious
        result = posted_puzzles.find_one_and_delete({"_id": ObjectId(puzzle_id)})
        return result 
    else:
        return None 

def post_comment(user_id, puzzle_id, comment, time, mode = None):

    user = get_user(user_id)

    if user != None:
        posted_puzzles = posted_puzzles_hybrid if (user["mode"] == "mixed" or mode == "mixed") else posted_puzzles_serious
        data = {"username": user["publicKey"], "time": time, "comment": comment}

        result = posted_puzzles.find_one_and_update(
            {"_id": ObjectId(puzzle_id)}, {"$push": {"comments": data}}
        )
        return result
    else:
        return -1
def delete_comment(admin_id, mode, puzzle_id, time):
    admin = get_user(admin_id)

    if (admin != None and admin["mode"] == "admin"):
        posted_puzzles = posted_puzzles_hybrid if mode == "mixed" else posted_puzzles_serious
        result = posted_puzzles.find_one_and_update({"_id": ObjectId(puzzle_id)}, {"$pull": {"comments": {"time": time}}})
        return result
    else: 
        return None 

def like_posted_puzzles(user_id, puzzle_id):

    result = userDB.find_one_and_update(
        {"privateKey": user_id}, {"$push": {"community_puzzles": puzzle_id}}
    )
    user = get_user(user_id)
    posted_puzzles = posted_puzzles_hybrid if user["mode"] == "mixed" else posted_puzzles_serious
    result = posted_puzzles.find_one_and_update(
        {"_id": ObjectId(puzzle_id)}, {"$inc": {"likes": 1}}
    )

    return not result is None


def unlike_posted_puzzles(user_id, puzzle_id):

    result = userDB.find_one_and_update(
        {"privateKey": user_id}, {"$pull": {"community_puzzles": puzzle_id}}
    )
    user = get_user(user_id)
    posted_puzzles = posted_puzzles_hybrid if user["mode"] == "mixed" else posted_puzzles_serious
    result = posted_puzzles.find_one_and_update(
        {"_id": ObjectId(puzzle_id)}, {"$inc": {"likes": -1}}
    )

    return not result is None


def get_liked_posted_puzzles(user_id):
    user = get_user(user_id) 

    if user is None:
        return None

    elif "community_puzzles" in user:
        puzzles = []

        ids = [ObjectId(i) for i in user["community_puzzles"]]
        posted_puzzles = posted_puzzles_hybrid if user["mode"] == "mixed" else posted_puzzles_serious
        puzzles = list(posted_puzzles.find({"_id": {"$in": ids}}))
        for p in puzzles:
            p["_id"] = str(p["_id"])
        return puzzles
    else:
        return []


def get_user(user_id):
    user = userDB.find_one({"privateKey": user_id})
    if not user is None and user["publicKey"] in admins_public_keys:
        if "mode" not in user:
            user["mode"] = "admin"
            userDB.find_one_and_update({"privateKey": user_id}, {"$set": {"mode": "admin"}})

    if not user is None and not "nextPuzzleIdx" in user:
        userDB.find_one_and_update(
            {"privateKey": user_id}, {"$set": {"nextPuzzleIdx": 0}}
        )

    return user


def new_session(privateKey, start_time):
    user = get_user(privateKey)
    if not get_user(privateKey) is None:
        session_template = {
            "user": user["publicKey"],
            "startTime": start_time,
            "totalCasual": 0,
            "totalSerious": 0,
            "totalNeutral": 0,
            "clicks": [],
            "totalTime": 0,
        }
        i = sessions.insert_one(session_template)

        return str(i.inserted_id)
    else:
        return None


def add_click(sessionId, data):
    click_data = {"name": data["name"], "time": data["time"], "type": data["type"]}
    if "data" in data:
        click_data["data"] = data["data"]

    inc = "totalNeutral"
    if data["type"] == "casual":
        inc = "totalCasual"
    elif data["type"] == "serious":
        inc = "totalSerious"
    session = sessions.find_one_and_update(
        {"_id": ObjectId(sessionId)},
        {
            "$push": {"clicks": click_data},
            "$inc": {inc: 1},
            "$set": {"totalTime": data["time"]},
        },
    )


def like_puzzle(user_id, puzzle):

    user = get_user(user_id)
    next_idx = user["nextPuzzleIdx"]

    puzzle["key"] = next_idx

    result = userDB.find_one_and_update(
        {"privateKey": user_id},
        {"$push": {"likedPuzzles": puzzle}, "$inc": {"nextPuzzleIdx": 1}},
    )

    if not result is None:
        return next_idx
    else:
        return None


def update_puzzle(user_id, key, new_puzzle):

    result = userDB.find_one_and_update(
        {"privateKey": user_id, "likedPuzzles": {"$elemMatch": {"key": key}}},
        {"$set": {"likedPuzzles.$": new_puzzle}},
    )

    return not result is None


def remove_puzzle(user_id, key):

    result = userDB.find_one_and_update(
        {"privateKey": user_id}, {"$pull": {"likedPuzzles": {"key": key}}}
    )

    return not result is None


def get_liked_puzzles(user_id):
    user = get_user(user_id)

    if not user is None:
        return user["likedPuzzles"]
    else:
        return None

def merge_dicts(di1, di2):
    new_di = {}

    for key in di1:
        if key in di2:
            if( isinstance(di1[key], list) or isinstance(di1[key], str) or isinstance(di1[key], int)) :
                new_di[key] = di1[key] 
            elif (isinstance(di1[key], dict) and isinstance(di2[key], dict)): 
                new_di[key] = merge_dicts(di1[key], di2[key])
            else:
                print("Something is wrong here")
                print(di1)
                print(di1[key])
        else:
            new_di[key] = di1[key]
    
    for key in di2:
        if not key in di1:
            new_di[key] = di2[key]

    return new_di
        


def get_user_grammar(user_id):

    user = get_user(user_id)

    database = sampleDatabase.find_one({})

    if user != None:
        custom_grammar = user["grammar"]
    else:
        custom_grammar = {}

    #database["grammar"].update(custom_grammar)
    grammar = merge_dicts(custom_grammar, database["grammar"])
    return grammar


def add_grammar_rule(user_id, request_data):
    update = {}

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
        result = sampleDatabase.find_one_and_update({}, {"$set": update})
    else:
        result = userDB.find_one_and_update({"privateKey": user_id}, {"$set": update})

    return result


def add_brainstorm(user_id, request_data):

    update = {}

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

    user = get_user(user_id)

    database = sampleDatabase.find_one({})

    if user != None and "brainstorm" in user:
        custom_grammar = user["brainstorm"]
    else:
        custom_grammar = {}

    if "brainstorm" in database:

        database["brainstorm"].update(custom_grammar)
        return database["brainstorm"]
    else:
        return custom_grammar


def update_scenario(user_id, request_data):
    scenario = request_data["scenario"]
    name = request_data["name"]
    categories = request_data["categories"]

    user = get_user(user_id)
    user_scenarios = user["scenarios"]

    values = {
        "scenario": scenario,
        "name": name,
        "categories": categories,
    }

    for idx, scen in enumerate(user_scenarios):
        if scen["name"] == name:
            user_scenarios[idx] = values

    if user["publicKey"] in admins_public_keys:
        result = scenarioDatabase.find_one_and_replace({"name": name}, values)
    else:
        result = userDB.find_one_and_update(
            {"privateKey": user_id}, {"$set": {"scenarios": user_scenarios}}
        )

    return result

def delete_scenario(user_id, request_data):
    name = request_data["name"]

    user = get_user(user_id)
    user_scenarios = user["scenarios"]

    for idx, scen in enumerate(user_scenarios):
        if scen["name"] == name:
            del user_scenarios[idx]

    if user["publicKey"] in admins_public_keys:
        result = scenarioDatabase.delete_many({"name": name})
    else:
        result = userDB.find_one_and_update(
            {"privateKey": user_id}, {"$set": {"scenarios": user_scenarios}}
        )

    return result


def add_scenario(user_id, request_data):
    scenario = request_data["scenario"]
    name = request_data["name"]
    categories = request_data["categories"]

    user = get_user(user_id)

    updated_scenarios = []
    if user["mode"] == "admin":
        updated_scenarios = list(scenarioDatabase.find({}, {"_id": 0}))
    elif "scenarios" in user:
        updated_scenarios = user["scenarios"]
    
    # Merge any duplicatly named cats
    cats_no_dupes = []
    cat_names = []
    for cat in categories:
        if cat["name"] in cat_names:
            for og_cat in cats_no_dupes:
                if og_cat["name"] == cat["name"]:
                    if cat["is_numeric"]:
                        # Replace entities in the same position.
                        for i, entity in enumerate(og_cat["entities"]):
                            if cat["entities"][i] != "entity":
                                og_cat["entities"][i] = entity
                    else:
                        og_cat["entities"] = list(set(og_cat["entities"] + cat["entities"]) - {"entity"})
        else:
            cat_names.append(cat["name"])
            cats_no_dupes.append(cat)
    categories = cats_no_dupes

    # Update existing scenarios
    scen_found = False
    for uscen in updated_scenarios:
        # Replace existing scenario narrative
        if uscen["name"] == name:
            scen_found = True
            uscen["scenario"] = scenario
        # Merge duplicate categories
        for ucat in uscen["categories"]:
            cat_found = False
            for cat in categories:
                if ucat["name"] == cat["name"]:
                    cat_found = True
                    if cat["is_numeric"]:
                        # Replace entities in the same position, keep enties in higher positions if they are not dupes.
                        for i, entity in enumerate(ucat["entities"]):
                            if i >= len(cat["entities"]) and entity not in cat["entities"]:
                                cat["entities"].append(entity)
                    else:
                        cat["entities"] = list(set(cat["entities"] + ucat["entities"]) - {"entity"})
            # Merge duplicate scenario categories
            if not cat_found and uscen["name"] == name:
                categories.append(ucat)
    if not scen_found:
        updated_scenarios.append({
            "name": name,
            "scenario": scenario,
            "categories": categories
        })

    # Update categories in existing scenarios
    for uscen in updated_scenarios:
        if uscen["name"] == name:
            uscen["categories"] = categories
        else:
            needs_update = False
            for cat in categories:
                for ucat in uscen["categories"]:
                    if ucat["name"] == cat["name"]:
                        if not ucat["is_numeric"] and set(ucat["entities"]) != set(cat["entities"]):
                            ucat["entities"] = cat["entities"]
                            needs_update = True
                        elif ucat["is_numeric"] and ucat["entities"] == cat["entities"]:
                            ucat["entities"] = cat["entities"]
                            needs_update = True
            if needs_update and user["mode"] == "admin":
                result = scenarioDatabase.update_many({"name": uscen["name"]}, {
            "$set": {"categories": uscen["categories"]}}, upsert = True)

    if user["mode"] == "admin":
        result = scenarioDatabase.update_many({"name": name}, {
            "$set": {"scenario": scenario, "categories": categories}}, upsert = True)
    else:
        result = userDB.find_one_and_update(
            {"privateKey": user_id}, {"$set": {"scenarios": updated_scenarios}}
        )

    return result


def get_scenario(user_id, get_samples=True):
    scenarios = []
    if get_samples:
        samples = list(scenarioDatabase.find({}, {"_id": 0}))
        [s.update({"origin": "sample"}) for s in samples]
        scenarios += samples
        
    user = get_user(user_id)
    if not user is None and "scenarios" in user:
        user_scens = user["scenarios"]
        [s.update({"origin": "user"}) for s in user_scens]
        scenarios += user_scens

    return scenarios


def add_category(user_id, request_data):
    category = {
        "name": request_data["category"]["name"],
        "entities": request_data["category"]["entities"],
        "is_numeric": request_data["category"]["is_numeric"],
    }

    user = get_user(user_id)
    if user["publicKey"] in admins_public_keys:
        result = sampleDatabase.find_one_and_update(
            {}, {"$push": {"categories": category}}
        )
    else:
        result = userDB.find_one_and_update(
            {"privateKey": user_id}, {"$push": {"categories": category}}
        )

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
        teacher = Category(
            "ingredients",
            ["Black Beans", "Tomatoes", "Jalapenos", "Chili Powder"],
            False,
        )
        time = Category(
            "store",
            ["Herb & Harvest", "O'Reilly's Farm", "Bayside Market", "Greenfield Co-op"],
            False,
        )

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
    scenario = request["scenario"] if "scenario" in request else ""
    name = request["name"] if "name" in request else "untitled"

    data = {
        "user": user,
        "puzzle": request["puzzle"],
        "gen_data": gen_data,
        "grid": jsonpickle.encode(grid),
        "scenario": scenario,
        "name": name,
    }

    results = evolveSessions.insert_one(data)

    data["grid"] = grid
    data["puzzle"] = puzzle
    return data, str(results.inserted_id)


def get_grid_with_id(user, request_data):
    id = str(request_data["id"])

    data = evolveSessions.find_one({"_id": ObjectId(id), "user": user})

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
            userDB.find_one_and_update(
                {"_id": ObjectId(id), "user": user},
                {"$set": {"evolveSessions." + str(id) + ".gen_data": gen_data}},
            )
        return data

    else:
        return None


def update_grid(user, id, grid):
    grid_str = jsonpickle.encode(grid)

    results = evolveSessions.find_one_and_update(
        {"_id": ObjectId(id), "user": user},
        {"$set": {"evolveSessions." + str(id) + ".grid": grid_str}},
    )
