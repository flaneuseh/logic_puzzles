from MapElites import evolve 
from LogicPuzzles import Puzzle, Category 
import jsonpickle
import random
subject = Category("subject", ["Math", "Science", "English", "History"], False)
teacher = Category("teacher", ["Ms. Smith", "Mr. Johnson", "Ms. McDonald", "Mr. Baker"], False)
time = Category("hour", ["1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM"], True)

puzzle = Puzzle([subject, teacher, time]) 

folder = "school3"
starting = 4
num_trials = 10
gen_len = 3000 
pop_size = 300
mut_rate = 0.8 
x_rate = 0.6
add_rate = 0.5 
elits = 10

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


