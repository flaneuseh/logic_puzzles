import ultraimport
import random
from pathlib import Path
from copy import deepcopy

ultraimport("__dir__/../LogicPuzzles.py", package="main")
from main.LogicPuzzles import Puzzle, Category
from SolutionMapEliteGeneration import map_elite_generate
from SolutionMapElitesVisualization import write_hint_files, heat_map, get_agg_children_grids, get_agg_hint_grids, write_summary_json_files
from ExhaustiveGeneration import ExtGenerator
import random

def get_puzzle_for_dimensions(categories, cat_cnt, ent_cnt, num_cnt):
    alp_cats = []
    num_cats = []
    for cat in categories:
        if cat.is_numeric:
            num_cats.append(cat)
        else:
            alp_cats.append(cat)

    cats = num_cats[:num_cnt]
    alp_cnt = cat_cnt - num_cnt
    cats.extend(alp_cats[:alp_cnt])
    trunc_cats = []
    for cat in cats:
        trunc_cats.append(Category(cat.title, cat.entities[:ent_cnt], cat.is_numeric))
    print(trunc_cats)
    return Puzzle(trunc_cats)

if __name__ == "__main__":
    time = Category("time", ["1", "2", "3", "4", "5", "6"], True)
    suspect = Category("suspect", ["Scarlet", "Plum", "White", "Mustard", "Peacock", "Green"])
    weapon = Category("weapon", ["candlestick", "rope", "lead pipe", "revolver", "poison", "polearm"])
    room = Category("room", ["Greenhouse", "Library", "Salon", "Dining Room", "Kitchen", "Bedroom"])

    base = "GeneratedSolutionMapElites"
    categories = [time, suspect, weapon, room]

    combos = [(2, 3, 0), (2, 3, 1), (2, 4, 1), (3, 3, 0), (3, 3, 1), (3, 4, 1)]
    for (cat_cnt, ent_cnt, num_cnt) in combos:
        combo_name = f"{cat_cnt}x{ent_cnt}x{num_cnt}"
        print(f"Generate puzzles for combo: {combo_name}")
        puzzle = get_puzzle_for_dimensions(categories, cat_cnt, ent_cnt, num_cnt)
        folder = f"{base}/{combo_name}"  

        # solutions = ExtGenerator.generate_all_solutions(puzzle)
        # solution = random.choice(solutions).print_grid()

        # starting = 0
        num_trials = 1
        # gen_len = 100
        # pop_size = 1000
        # cell_capacity = 10
        # mut_rate = 0.8
        # x_rate = 0.6
        # add_rate = 0.5
        # elits = 100

        # grid = map_elite_generate(
        #     puzzle,
        #     solution,
        #     folder,
        #     starting,
        #     num_trials,
        #     gen_len,
        #     pop_size,
        #     mut_rate,
        #     x_rate,
        #     add_rate,
        #     elits,
        # )

        write_hint_files(folder, num_trials)
        agg_grid = get_agg_hint_grids(folder, num_trials)
        heat_map(agg_grid, True, title = "Average Hint Size by Cell", ylabel="Gini Coefficent", xlabel="Solver loops", colorbar_label="Average Hint Size", vmin = 3, savefile=f"{folder}/hintsize_heatmap.png")

        agg_total_grid = get_agg_children_grids(folder, num_trials)
        heat_map(agg_total_grid, False, title = "Average Children Produced by Cell", ylabel="Gini Coefficent", xlabel="Solver loops", colorbar_label="Average Children Produced", savefile=f"{folder}/children_heatmap.png")

        write_summary_json_files(folder, num_trials)
        print(f"finished generating and saving puzzles for combo {combo_name}")
