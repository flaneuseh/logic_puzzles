import jsonpickle
import random

from MapElites import evolve 

def map_elite_generate(puzzle, folder, starting, num_trials, gen_len, pop_size, mut_rate, x_rate, add_rate, elits):
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
