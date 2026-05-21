import jsonpickle
import random
import ultraimport

ultraimport("__dir__/../LogicPuzzles.py", package="main")
from SolutionMapElites import evolve
from main.LogicPuzzles import Solver

# Todo: create a pool for a solution, and evolve with only hints for that solution
# Entities can be shuffled to create comparable puzzles for different solutions,
# if there is not one desired solution;
# or, a pool may exist for each solution, provided there are few enough.
# But, I feel the hint types and insights matter more than solution variation,
# as solutions may be varied trivially, by performing a 1:1 swap of entities in hints.
# Right?

def map_elite_generate(
    puzzle,
    solution,
    folder,
    starting,
    num_trials,
    gen_len,
    pop_size,
    mut_rate,
    x_rate,
    add_rate,
    elits,
    required_insights=set(),
    forbidden_insights=set(),
):
    for trial in range(starting, num_trials):
        random.seed(trial)
        elit_grid, infeasible, history = evolve(
            puzzle,
            solution,
            gen_len,
            pop_size,
            x_rate,
            mut_rate,
            add_rate,
            elits,
            required_insights,
            forbidden_insights,
            folder,
            trial=0,
        )

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
                children = elit_grid.grid[row][col]
                if not children is None:
                    for (_, child) in children:
                        solver = Solver()
                        assert solver.can_solve_without_forbidden(child.blank_puzzle, child.clues()), "can't solve with all insights available"
                        if len(required_insights) > 0:
                            solver = Solver(required_insights | forbidden_insights)
                            assert not solver.can_solve_without_forbidden(
                                child.blank_puzzle, child.clues()
                            ), "can solve without required insights: {}".format(required_insights)
                        if len(forbidden_insights) > 0:
                            solver = Solver(forbidden_insights)
                            assert solver.can_solve_without_forbidden(
                                child.blank_puzzle, child.clues()
                            ), "can't solve without forbidden insights {}".format(forbidden_insights)
        
        return elit_grid
                    
