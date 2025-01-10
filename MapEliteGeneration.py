import jsonpickle
import random

from MapElites import evolve 

def map_elite_generate(puzzle, folder, starting, num_trials, gen_len, pop_size, mut_rate, x_rate, add_rate, elits, required_insights_oneof={}, forbidden_insights={}):
    for trial in range(starting, num_trials):
        random.seed(trial)
        print("Starting Trial:{}".format(trial))
        elit_grid, infeasible, history = evolve(puzzle, gen_len, pop_size, x_rate, mut_rate, add_rate, elits, required_insights_oneof, forbidden_insights)

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

        for row in range(elit_grid.height):
            for col in range(elit_grid.width):
                child_cell = elit_grid.grid[row][col]
                if(not child_cell is None):
                    child = child_cell[1]
                    assert len(child.insights & required_insights_oneof) > 0 or len(required_insights_oneof) == 0, "insights: {} does not include any of: {}".format(child.insights, required_insights_oneof)
                    assert len(child.insights & forbidden_insights) == 0, "insights: {} includes forbidden: {}".format(child.insights, child.insights & forbidden_insights)
                    assert len(child.dumb_insights & required_insights_oneof) == 0, "dumb insights: {} includes required: {}".format(child.dumb_insights, child.insights & required_insights_oneof)
