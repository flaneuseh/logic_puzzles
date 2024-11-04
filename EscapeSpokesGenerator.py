from MapElites import evolve 
from LogicPuzzles import Puzzle, Category 
import jsonpickle
import random
from HintToEnglish import hint_to_english 


folder = "EscapeSpokes"
starting =0 
num_trials = 1
gen_len = 1000 
pop_size = 100
mut_rate = 0.8 
x_rate = 0.6
add_rate = 0.5 
elits = 10


def hintset_to_string(hint_set):
    s = ""
    for hint in hint_set.hints:
        s += "\t" + hint_to_english(hint) + "\n"
    return s

def make_hint_file(hint_sets, file_path):
    file = open(file_path, "w") 
    file.write("solution:\n")
    file.write(hint_sets[0][1].completed_puzzle.print_grid()) 
    for row in range(len(hint_sets)):
        child = hint_sets[row]
        if(not child is None):
            file.write("Hints for with loop size: {}\n".format(row + 1 ))
            file.write(hintset_to_string(child[1]))
            file.write("\n\n")

def write_puzzles (name, solution, elit_grid, infeasible, history): 
    elite_json = jsonpickle.encode(elit_grid)
    elite_file = open(folder + "/map_grid_{}.p".format(name), "w")
    elite_file.write(elite_json)
    elite_file.close()

    history_json = jsonpickle.encode(history)
    history_file = open(folder + "/history_{}.p".format(name), "w")
    history_file.write(history_json)
    history_file.close()

    unfes_json = jsonpickle.encode(infeasible)
    unfes_file = open(folder + "/unfeasibles_{}.p".format(name), "w")
    unfes_file.write(unfes_json)
    unfes_file.close()

    solutions_to_write = elit_grid.grid[elit_grid.solutions[solution]] 
    make_hint_file(solutions_to_write, folder + "/hints_{}.p".format(name))

# Spoke puzzle 1 

days = Category("day", ["30", "60", "90", "120"], True)
vegetables = Category("plant", [ "Potato", "Green Onion",  "Eggplant", "Broccoli"], False)
puzzle1 = Puzzle([days, vegetables])

solution = """------
|XXXO|
|OXXX|
|XOXX|
|XXOX|\n"""

elit_grid, infeasible, history = evolve(puzzle1, gen_len, pop_size, x_rate, mut_rate, add_rate, elits) 


print(elit_grid.grid[elit_grid.solutions[solution]])
write_puzzles("HarvestDays", solution, elit_grid, infeasible, history)

# Spoke puzzle 2 

sun_hours = Category("hour", ["2 hours", "4 hours", "6 hours", "8 hours"], True)
vegetables = Category("plant", ['Pumpkins', 'Kale', 'Blueberries', 'Cauliflower'], False)
puzzle2 = Puzzle([sun_hours, vegetables])

solution = """------
|XXXO|
|XOXX|
|OXXX|
|XXOX|\n"""

elit_grid, infeasible, history = evolve(puzzle2, gen_len, pop_size, x_rate, mut_rate, add_rate, elits) 


print(elit_grid.grid[elit_grid.solutions[solution]])
write_puzzles("AmountOfSun", solution, elit_grid, infeasible, history)

# Spoke puzzle 3 

# Peanuts (26/100 g), Salmon (22/100 g),  Egg (13/100 g), Tofu (8/100 g)  

protein = Category("percent", ["10", "15", "20", "25"], True)
food_source = Category("plant", ['Salmon', 'Egg', 'Tofu', 'Peanuts'], False)
puzzle3 = Puzzle([protein, food_source])

solution = """------
|XXOX|
|XOXX|
|OXXX|
|XXXO|\n"""

elit_grid, infeasible, history = evolve(puzzle3, gen_len, pop_size, x_rate, mut_rate, add_rate, elits) 


print(elit_grid.grid[elit_grid.solutions[solution]])
write_puzzles("AmountOfProtein", solution, elit_grid, infeasible, history)

# Spoke puzzle 4 

# Peanuts (26/100 g), Salmon (22/100 g),  Egg (13/100 g), Tofu (8/100 g)  

pasta = Category("shape", ["Elbow", "Bowtie", "Linguine", "Shell" ], False)
sauce = Category("sauce", ["Tomato", "Alfredo", "Pesto", "Carbonara" ], False)
puzzle4 = Puzzle([pasta, sauce])

solution = """------
|OXXX|
|XXXO|
|XOXX|
|XXOX|\n"""

elit_grid, infeasible, history = evolve(puzzle4, gen_len, pop_size, x_rate, mut_rate, add_rate, elits) 


print(elit_grid.grid[elit_grid.solutions[solution]])
write_puzzles("Pasta", solution, elit_grid, infeasible, history)

