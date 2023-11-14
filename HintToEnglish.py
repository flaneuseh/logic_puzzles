from LogicPuzzles import generate_hint, Puzzle , Category
import random 
random.seed(42)
suspects = Category("suspect", ["Ms. Scarlet", "Ms. White", "Col Mustard", "Prof Plum"], False)
weapons = Category("weapon", ["Knife", "Rope", "Candle Stick", "Wrench"], False)
rooms = Category("room", ["Ball room", "Living Room", "Kitchen", "Study"], False)
time = Category("hour", ["1:00 pm", "2:00 pm", "3:00 pm", "4:00 pm"], True)

puzzle = Puzzle([suspects, weapons, rooms, time])

def is_to_english(attributes):
    cat1 = attributes[0]
    ent1 = attributes[1]
    cat2 = attributes[2]
    ent2 = attributes[3]

    s = "The {} {} is the {} {}".format(cat1.title, ent1, cat2.title, ent2)
    return s 

def not_to_english(attributes):
    attributes = attributes[0]["is"]
    cat1 = attributes[0]
    ent1 = attributes[1]
    cat2 = attributes[2]
    ent2 = attributes[3]

    s = "The {} {} is not the {} in the category {}".format( cat1.title, ent1, cat2.title, ent2)
    return s  

def before_to_english(attributes):
    cat1 = attributes[0]
    ent1 = attributes[1]
    cat2 = attributes[2]
    ent2 = attributes[3]

    num_cat = attributes[4]

    timed = len(attributes) == 6 
    if timed:
        amount  = attributes[5] 
    if not timed: 
        s = "The {} {} is at least 1 {} before the {} {}".format(cat1.title, ent1, num_cat.title, cat2.title, ent2)
    else:
        s = "The {} {} is {} {}s before the {} {}".format(cat1.title, ent1, amount,  num_cat.title, cat2.title,  ent2)
    return s  

def simple_or_to_english(attributes):
    cat1 = attributes[0]
    ent1 = attributes[1]
    cat2 = attributes[2]
    ent2 = attributes[3]

    is_cat = attributes[4]
    is_ent = attributes[5] 

    s = "Either the {} {} or the {} {} is the {} {}".format( cat1.title, ent1, cat2.title, ent2, is_cat, is_ent, )
    return s 

def compound_or_to_english(attributes):
    hint1 = attributes[0]
    hint2 = attributes[1]

    s = "Either {} or {}".format(hint_to_english(hint1), hint_to_english(hint2))
    return s 

def hint_to_english(hint):
    kind = next(iter(hint))

    if kind == "is":
        return is_to_english(hint[kind])
    elif kind == "not":
        return not_to_english(hint[kind])
    elif kind == "before":
        return before_to_english(hint[kind])
    elif kind == "simple_or":
        return simple_or_to_english(hint[kind])
    elif kind == "compound_or":
        return compound_or_to_english(hint[kind])
    else:
        return "NOT IMPLEMENTED YET"
if __name__ == "__main__":
    is_hint = generate_hint(puzzle)
    print(is_hint)
    print(hint_to_english(is_hint))
    print("")

    compond_or_hint = generate_hint(puzzle)
    print(hint_to_english(compond_or_hint))
    print("")

    before_hint = generate_hint(puzzle)
    print(before_hint)
    print(hint_to_english(before_hint))
    print("")

    hint = generate_hint(puzzle)
    hint = generate_hint(puzzle)

    not_hint = generate_hint(puzzle)
    print(not_hint)
    print(hint_to_english(not_hint))
    print("")

    hint = generate_hint(puzzle)
    hint = generate_hint(puzzle)
    hint = generate_hint(puzzle)
    hint = generate_hint(puzzle)
    hint = generate_hint(puzzle)
    hint = generate_hint(puzzle)
    hint = generate_hint(puzzle)
    hint = generate_hint(puzzle)

    simple_or_hint = generate_hint(puzzle)
    print(simple_or_hint)
    print(hint_to_english(simple_or_hint))
    print("")



