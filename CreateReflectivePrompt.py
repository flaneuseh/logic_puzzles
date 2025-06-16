import inflect
p = inflect.engine()
from copy import deepcopy
import random 

from Evolution import get_available_moves, get_move_information
from HintToEnglish import hint_to_english
from LogicPuzzles import Category, Puzzle, Insight

def create_prompt(text, params, ents, hints):

    for i, param in enumerate(params):
        
        value = ""

        if param[0] == "ents":
            value = ents[param[1]][param[2]]
        else:
            
            hint_num = hints[param[1]]
            hint_num += 1 
            value = str(p.ordinal(hint_num))
        
        text = text.replace("{" + str(i) +"}", value)
    return text 

PROMPT_DICT = {

# Repair (Cat1, ent1) x (cat2, ent2) is incorrect 

"repair": [
    ("What assumptions have you made about the '{0}' and '{1}'? How could you question those?",[("ents", 0, 1), ("ents", 0,0)]),
    ("What was the process that made you decide the answer for '{0}' and '{1}'?", [("ents", 0,0), ("ents", 0,0)])
    ],

# cross out (cat1, ent1) x (cat2, ent2) is True, others can be cross out 
"cross_out": [
    ("Think about the '{0}' and '{1}'. Can this information be useful anywhere else in the puzzle?", [("ents", 0,1), ("ents", 1 ,1)]),
    ("How does what you know about '{0}' inform how you are thinking about the category '{1}'?", [("ents", 0,1), ("ents", 1,0)])
],
## Opening (cat1, ent1) x (cat2, ent2) is the only one that can be true 
"opening": [
    ("What do you know about '{0}' and '{1}'? Are there any other conclusions you can make?", [("ents", 0,0), ("ents",1,0)]),
    ("What possibilities remain for '{0}'?", [("ents", 0, 1)])
],

# abc_true (catA, entA) x (catb, entB) X (catc, entC) a=b and b=c so a=c
"abc_true":[
    ("What do you know about '{0}', '{1}', and '{2}'?",[("ents", 0,1), ("ents", 1,1), ("ents", 2,1)]),
    ("How could what you know about '{0}', inform how you think about '{1}'?", [("ents",1,1), ("ents",2,1)])
],

# abc_false (catA, entA) x (catb, entB) X (catc, entC) a=b and b!=c so a!=c
"abc_false":[
    ("What do you know about '{0}', '{1}', and '{2}'?",[("ents", 0,1), ("ents", 1,1), ("ents", 2,1)]),
    ("How could what you know about '{0}', inform how you think about '{1}'?", [("ents",1,1), ("ents",2,1)])
], 

# trans_sets (catA, entA) x (catb, entB) X (catc) c in a has no commalities in c in b, therefore a != b
"trans_sets":[
    ("What are the possibilities available for '{0}'? How do these differ from the possibilities of '{1}'", [("ents", 0,1), ("ents", 1,1)]), 
    ("What do you know about '{0}'? How could this effect '{1}' or '{2}'?", [("ents", 2,0),("ents", 0,0), ("ents", 1,0)])
],
# is (Cat1, ent1) x (cat2, ent2) is true  
"is":[
    ("What does the {0} hint tell you about the puzzle?", [("hint", 0)]), 
    ("What information do you have that can tell you about '{0}'?", [("ents",0,1)])
],
"not":[
    ("What does the {0} hint tell you about the puzzle?", [("hint", 0)]), 
    ("What information do you have that can tell you about '{0}'?", [("ents",0,1)])
],

# before_diff_cat (befcat, befent) X (aftcat, aftent) bef_ent is different from after_ent from clue 
"before_diff_cat": [
    ("How does '{0}' relate to '{1}'?", [("ents", 0,1), ("ents", 1,1)]),
    ("How does the {0} hint inform what you know about {1}?", [("hints", 0), ("ents", 0,1)])
],
# apply_before (cat1, ent1) x (cat2, ent2)x (cat3, ent3) ent1=ent3 based on the restrictions on ent2 on cat3 
"apply_before":[
    ("What does the {0} hint tell you about the puzzle?", [("hint", 0)]), 
    ("What information do you have that can tell you about '{0}'?", [("ents",2,1)])
],
# before no info (cat1, ent1) X (cat2, ent2) ent1 != ent2 (ents can't be in k first/last places)
"before_noinfo":[
    ("How does the {0} hint inform what is possible for entities in the category {1}?", (("hints", 0), ("ents", 0,0))),
    ("What information do you have that could be applicable to '{0}'?", [("ents", 1,1)])
],
# spots shift (cat1, ent1)X(comCat, comEnt)X(cat2, ent2) ent1!=ent2 based on possibilities of compEnt
"spots_shift":[
    ("How does what you know about '{0}' inform what is possible for '{1}'?", [("ents", 1,1), ("ents", 0,1)]),
    ("What does the {0} hint tell you about '{1}, given the current state of the puzzle?", (("hints",0), ("ents", 0,0)))
],
# spots cross (ent1, ent2, ent3) ent!=ent3 based on the before and what's available in ent2 
"spots_cross":[
    ("How does what you have eliminated from '{0}' inform the possibilities for '{1}", [("ents", 1,1), ("ents", 0, 1)]),
    ("What does the {0} hint tell you about '{1}, given the current state of the puzzle?", (("hints",0), ("ents", 0,0)))
],
# or false (pos_cat1, pos_ent1), (pos_cat2, pos_ent2), (ans_cat, ans_ent) ent1!=ans_ent bc other is answered 
"or_false":[
     ("What does the {0} hint tell about the puzzle, given the current state of the puzzle?", (("hints",0))),
     ("What possibilities remain for {0}, given the information you currently have?", (("ents", 0,0)))
], 
# or true  (pos_cat1, pos_ent1), (pos_cat2, pos_ent2), (ans_cat, ans_ent) ent1==ans_ent bc other is answered 
"or_true":[
     ("What does the {0} hint tell about the puzzle, given the current state of the puzzle?", (("hints",0))),
     ("What possibilities remain for '{0}', given the information you currently have?", (("ents", 0,0)))
], 
# or diff  (pos_cat1, pos_ent1), (pos_cat2, pos_ent2), (ans_cat, ans_ent) ent1!=ent2 bc of or clue 
"or_diff":[
    ("What does the {0} hint tell about '{1}'?", [("hints", 0), ("ents", 0,1)]), 
    ("What information do you have about {0} and {1}?", [("ents", 0,1), ("ents", 1,1)])
], 
# or same (pos_cat1, ent1)(ans_cat, ans_ent) ent1!=ans_ent bc only pos1 or pos2 must be ans_ent 
"or_same":[
    ("What does the {0} hint tell about the possibilities for '{}'?", [("hints", 0), ("ents", 1,1)]), 
    ("What possibilities could be eliminated for {1}", [("ents", 1,1)])
]
}

def get_prompt(puzzle, hints):
    moves = get_move_information(puzzle, hints)

    move = random.choice(moves)

    prompts = PROMPT_DICT[move["type"]]
    prompt = random.choice(prompts)
    ents = move["ents"]
    hint = move["hint"] if "hint" in move else []

    return create_prompt(prompt[0], prompt[1], ents, hint)


if __name__ == "__main__":
    order = Category("order", ["1st", "2nd", "3rd", "4th"], True)
    quantity = Category("cup", ["1 cup", "2 cups", "3 cups", "4 cups"], True)
    food = Category("ingredient", ["Beans", "Pasta", "Tomato", "Carrots"], False)
    puzzle = Puzzle([order, quantity, food])

    hints = [
        {"before": [food, "Pasta", food, "Beans", order, 2]},
        {"before": [food, "Tomato", food, "Beans", quantity, 2]},
        {"is": [food, "Tomato", order, "4th"]},
        {"before": [food, "Beans", food, "Carrots", quantity, 1]},
    ]

    for i in range(10):
        print(get_prompt(puzzle, hints)) 