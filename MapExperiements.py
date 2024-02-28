from MapElites import evolve 
from LogicPuzzles import Puzzle, Category 
import jsonpickle
import random
suspects = Category("suspect", ["Ms. Scarlet", "Mrs. White", "Col. Mustard", "Prof. Plum"], False)
weapons = Category("weapon", ["Knife", "Rope", "Candlestick", "Wrench"], False)
rooms = Category("room", ["Ballroom", "Living Room", "Kitchen", "Study"], False)
time = Category("hour", ["1:00", "2:00", "3:00", "4:00"], True)

puzzle = Puzzle([suspects, weapons, rooms, time]) 

folder = "MapElites10k"
starting = 10
num_trials = 15
gen_len = 10000 
pop_size = 100
mut_rate = 0.8 
x_rate = 0.3 
add_rate = 0.5 
elits = 5

for trial in range(starting, num_trials):
    random.seed(trial)
    print("Starting Trial:{}".format(trial))
    elit_grid, infeasible, history = evolve(puzzle, gen_len, pop_size, x_rate, mut_rate, add_rate, elits)

    elite_json = jsonpickle.encode(elit_grid)
    elite_file = open(folder + "/map_grid_trial_{}.p".format(trial), "w")
    elite_file.write(elite_json)
    elite_file.close()

    history_json = jsonpickle.encode(history)
    history_file = open(folder + "/history_trial_{}.p".format(trial), "w")
    history_file.write(history_json)
    history_file.close()

    unfes_json = jsonpickle.encode(infeasible)
    unfes_file = open(folder + "/unfeasibles_trial_{}.p".format(trial), "w")
    unfes_file.write(unfes_json)
    unfes_file.close()


