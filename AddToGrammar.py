from LogicPuzzles import generate_hint , Category, Puzzle
import json 
from HintToEnglish import hint_to_english

def get_categories():
    file = open("database.json", "r")
    text = file.read()
    file.close()

    database = json.loads(text)

    return database["categories"]

def get_grammar():
    file = open("database.json", "r")
    text = file.read()
    file.close()

    database = json.loads(text)

    return database["grammar_dict"]

def update_grammar_dict(di):
    file = open("database.json", "r")
    text = file.read()
    file.close()

    database = json.loads(text)

    database["grammar_dict"] = di 

    file = open("database.json", "w")
    text = json.dumps(database)
    file.write(text)
    file.close()

def get_empty_is(di, cats): 
    empty = [] 
    for cat1 in cats: 
        cat1 = cat1["name"]
        for cat2 in cats: 
            cat2=cat2["name"]
            if cat1 != cat2: 
                if not (cat1 in di and cat2 in di[cat1] and "is" in di[cat1][cat2]):
                    empty.append((cat1, cat2))
    return empty 

def get_empty_not(di, cats): 
    empty = [] 
    for cat1 in cats: 
        cat1 = cat1["name"]
        for cat2 in cats: 
            cat2=cat2["name"]
            if cat1 != cat2: 
                if not (cat1 in di and cat2 in di[cat1] and "not" in di[cat1][cat2]):
                    empty.append((cat1, cat2))
    return empty 

def get_empty_before(di, cats): 
    empty = [] 
    for cat1 in cats: 
        cat1 = cat1["name"]
        for cat2 in cats: 
            cat2=cat2["name"]
            for cat3 in cats: 
                if cat3["is_numeric"]: 
                    cat3 = cat3["name"]
                    if cat1 != cat3 and cat2 != cat3: 
                        if not (cat1 in di and cat2 in di[cat1] and cat3 in di[cat1][cat2] and  "before" in di[cat1][cat2][cat3]):
                            empty.append((cat1, cat2, cat3))
    return empty 

def get_empty_or(di, cats): 
    empty = [] 
    for cat1 in cats: 
        cat1 = cat1["name"]
        for cat2 in cats: 
            cat2=cat2["name"]
            for cat3 in cats: 
                cat3 = cat3["name"]
                if cat1 != cat3 and cat2 != cat3: 
                    if not (cat1 in di and cat2 in di[cat1] and cat3 in di[cat1][cat2] and  "or" in di[cat1][cat2][cat3]):
                        empty.append((cat1, cat2, cat3))
    return empty 

def make_new_grammar():
    di= get_grammar()
    cats = get_categories()

    empty_is = get_empty_is(di, cats)
    empty_not = get_empty_not(di, cats)
    empty_before = get_empty_before(di, cats)
    empty_or = get_empty_or(di, cats)

    options = []

    if len(empty_is) > 0: 
        options.append("is")

    if len(empty_not) > 0: 
        options.append("not")
    
    if len(empty_before) > 0: 
        options.append("before")
    if len(empty_or) > 0: 
        options.append("or")

    print("Select hint type:")
    for opt, i in enumerate(options):
        print("\t" + str(opt) + " [{}]".format(i))
    selection = int(input("Enter option number:"))
    t = options[selection]

    if t == "is":
        print("Select available categories:")
        for i, tu in enumerate(empty_is):
            print("\t" + str(tu) + " [{}]".format(i))
        selection = int(input("Enter option number:"))   
        categories = empty_is[selection]
        print("Selected: {} with categories: {}".format(t, categories))
        template = input("Enter template: ")
        if categories[0] not in di:
            di[categories[0]] = {}
        if categories[1] not in di[categories[0]]:
            di[categories[0]][categories[1]] = {}
        di[categories[0]][categories[1]]["is"] = template 
    elif t == "not":
        print("Select available categories:")
        for i, tu in enumerate(empty_not):
            print("\t" + str(tu) + " [{}]".format(i))
        selection = int(input("Enter option number:"))   
        categories = empty_not[selection]
        print("Selected: {} with categories: {}".format(t, categories))
        template = input("Enter template: ")
        if categories[0] not in di:
            di[categories[0]] = {}
        if categories[1] not in di[categories[0]]:
            di[categories[0]][categories[1]] = {}
        di[categories[0]][categories[1]]["not"] = template 
    elif t == "before":
        print("Select available categories:")
        for i, tu in enumerate(empty_before):
            print("\t" + str(tu) + " [{}]".format(i))
        selection = int(input("Enter option number:"))   
        categories = empty_before[selection]
        print("Selected: {} with categories: {}".format(t, categories))
       
        step = input("Enter step:")
        template1 = input("Enter untimed template: ")
        templated2 = input("Enter timed template:")

        value = {"step": step, "untimed": template1, "timed": templated2}


        if categories[0] not in di:
            di[categories[0]] = {}
        if categories[1] not in di[categories[0]]:
            di[categories[0]][categories[1]] = {}
        if categories[2] not in di[categories[0]][categories[1]]: 
            di[categories[0]][categories[1]][categories[2]] = {}

        di[categories[0]][categories[1]][categories[2]]["before"] = value
    elif t == "or":
        print("Select available categories:")
        for i , tu in enumerate(empty_or):
            print("\t" + str(tu) + " [{}]".format(i))
        selection = int(input("Enter option number:"))   
        categories = empty_or[selection]
        print("Selected: {} with categories: {}".format(t, categories))
        template = input("Enter template: ")

      

        if categories[0] not in di:
            di[categories[0]] = {}
        if categories[1] not in di[categories[0]]:
            di[categories[0]][categories[1]] = {}
        if categories[2] not in di[categories[0]][categories[1]]: 
            di[categories[0]][categories[1]][categories[2]] = {}

        di[categories[0]][categories[1]][categories[2]]["or"] = template 
    
    update_grammar_dict(di)

if __name__ == "__main__":
    make_new_grammar()

    con = input("Make another (y/n)").lower().startswith("y")

    while con: 
        make_new_grammar()
        con = input("Make another (y/n)").lower().startswith("y")
    """suspects = Category("suspect", ["Ms. Scarlet", "Ms. White", "Col Mustard", "Prof Plum"], False)
    weapons = Category("weapon", ["Knife", "Rope", "Candle Stick", "Wrench"], False)
    rooms = Category("room", ["Ball room", "Living Room", "Kitchen", "Study"], False)
    time = Category("hour", ["1:00 pm", "2:00 pm", "3:00 pm", "4:00 pm"], True)

    puzzle = Puzzle([suspects, weapons, time])

    grammar = get_grammar()
    for i in range(10):
        print(hint_to_english(generate_hint(puzzle), grammar_dict=grammar))"""
        




