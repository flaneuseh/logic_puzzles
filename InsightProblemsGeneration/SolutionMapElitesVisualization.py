import jsonpickle 
import matplotlib.pyplot as plt 
import matplotlib as mpl 
import seaborn as sns
import numpy as np
import json
import ultraimport
ultraimport("__dir__/../LogicPuzzles.py", package="main")
from main.HintToEnglish import hint_to_english 
from main.HintSetToJson import hintset_to_json
from main.LogicPuzzles import Insight

def heat_map(grid, reverse, title = "", xlabel = "", ylabel = "", colorbar_label="", vmin = 0, savefile = ""):
    
    # create the value mask
    #mask = np.logical_and(grid >= 20, grid < 21)

    # create the colormap with extremes
    if(reverse):

        cmap = mpl.colormaps["plasma_r"].with_extremes(under='black')
    else:
        cmap = mpl.colormaps["plasma"]

    # plot
    g = sns.heatmap(grid, vmin=vmin, cmap=cmap, cbar_kws={'label': colorbar_label})
    # reset the xticklabels to show the correct column labels
    #_ = g.set_xticks(ticks=g.get_xticks(), labels=range(5, 20))

    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    plt.title(title)

    if savefile == "":
        plt.show()
    else:
        plt.savefig(savefile)
    plt.clf()


def get_agg_grid(grids):
    sum_grid = []
    leng_grid = []

    for row in range(len(grids[0])):
        row_li = []
        row_li2 = []
        for col in range(len(grids[0][0])):
            row_li.append(0)
            row_li2.append(0)
        sum_grid.append(row_li)
        leng_grid.append(row_li2)


    for row in range(len(grids[0])):
        for col in range(len(grids[0][0])):
            for grid in grids:
                if(grid[row][col] != -1):
                    sum_grid[row][col] += grid[row][col]
                    leng_grid[row][col] += 1 

    for row in range(len(grids[0])):
        for col in range(len(grids[0][0])):
            if(leng_grid[row][col] == 0):
                sum_grid[row][col] = -1 
            else: 
                sum_grid[row][col] = sum_grid[row][col] / leng_grid[row][col]
    
    return sum_grid


def get_agg_hint_grids(folder, trial_size):
    grids = []
    for trial in range(trial_size):
        json = open( folder + "/map_grid_trial_{}.p".format(trial), "r").read()
        grid = jsonpickle.decode(json) 
        grids.append(grid.get_fitness_grid())
    
    return get_agg_grid(grids)

def get_agg_children_grids(folder, trial_size):
    grids = []
    for trial in range(trial_size):
        json = open( folder + "/history_trial_{}.p".format(trial), "r").read()
        grid = jsonpickle.decode(json) 
        grids.append(grid.total_grid[-1])
    
    return get_agg_grid(grids)


def hintset_to_string(hint_set):
    s = ""
    for hint in hint_set.clues():
        s += "\t" + hint_to_english(hint) + "\n"
    return s

def make_hint_file(map_grid, file_path):
    file = open(file_path, "w") 
    for insight_set, row in map_grid.insight_sets.items():
        for col in range(map_grid.width):
            cell = map_grid.grid[row][col]
            if cell is None:
                continue
            for i, (_, child) in enumerate(cell):
                file.write(f"Hints for insight set {insight_set}, {col} loops, {i}th child (grid cell [{row}][{col}][{i}])\n")
                file.write(hintset_to_string(child))
                file.write("\n\n")

    file.close()

def make_solution_file(map_grid, file_path):
    file = open(file_path, "w") 
    for insight_set, row in map_grid.insight_sets.items():
        for col in range(map_grid.width):
            cell = map_grid.grid[row][col]
            if cell is None:
                continue
            for i, child in enumerate(cell):
                file.write(f"Solution for insight set {insight_set}, {col} loops, {i}th child (grid cell [{row}][{col}][{i}])\n")
                file.write(child[1].applied_puzzle.print_grid())
                file.write("\n\n")

    file.close()

def make_insight_file(map_grid, file_path):
    insights_seen = {}
    for insight in Insight.ALL_INSIGHTS:
        insights_seen[insight.name] = 0
    for insight_set in map_grid.insight_sets.keys():
        insights = insight_set.split(",")
        for insight in insights:
            if insight not in insights_seen:
                insights_seen[insight] = 0
            insights_seen[insight] += 1
    with open(file_path, "w") as file:
        json.dump(insights_seen, file)

def make_json_file(map_grid, file_path):
    grid_di = []

    file = open(file_path, "w")
    insight_sets = map_grid.insight_sets
    for insight_set, row in insight_sets.items():
        for col in range(map_grid.width):
            cell = map_grid.grid[row][col]
            if cell is None:
                continue
            for i, child in enumerate(cell):
                hintset = child[1]
                id = f"({insight_set}){row}:{col}:{i}"
                hint_di = hintset_to_json(hintset, id)
                grid_di.append(hint_di)
    
    json.dump(grid_di,file)
    file.close()

def make_summary_json_file(map_grid, file_path):
    summary = {}

    insight_sets = map_grid.insight_sets
    for insight_set, row in insight_sets.items():
        summary[insight_set] = []
        for col in range(map_grid.width):
            cell = map_grid.grid[row][col]
            if cell is None:
                summary[insight_set].append(0)
            else:
                summary[insight_set].append(len(cell))

    with open(file_path, "w") as file:
        json.dump(summary,file)


def write_hint_files(folder, trial_size):
    for trial in range(trial_size):
        json = open( folder + "/map_grid_trial_{}.p".format(trial), "r").read()
        grid = jsonpickle.decode(json) 
        make_hint_file(grid, folder + "/hints_{}.txt".format(trial))
        make_solution_file(grid, folder + "/solutions_{}.txt".format(trial))
        make_json_file(grid, folder + "/json_{}.json".format(trial))

def write_summary_json_files(folder, trial_size):
    for trial in range(trial_size):
        json = open( folder + "/map_grid_trial_{}.p".format(trial), "r").read()
        grid = jsonpickle.decode(json) 
        make_summary_json_file(grid, folder + f"/summary_json_{trial}.json")
        make_insight_file(grid, f"{folder}/unmissable_insights_{trial}.json")

if __name__ == "__main__":
    folders = ["NewEscape/SoupSimple"]
    trials = 1
    """agg_grid = get_agg_hint_grids(folder, trials)
    heat_map(agg_grid, True, title = "Average Hint Size by Cell", ylabel="Gini Coefficent", xlabel="Solver loops", colorbar_label="Average Hint Size", vmin = 3)

    agg_total_grid = get_agg_children_grids(folder, trials)
    heat_map(agg_total_grid, False, title = "Average Children Produced by Cell", ylabel="Gini Coefficent", xlabel="Solver loops", colorbar_label="Average Children Produced")

    agg_grid = get_agg_duplicate_grids(folder, trials)
    heat_map(agg_grid, True, title = "Average Duplicates by Cell", ylabel="Gini Coefficent", xlabel="Solver loops", colorbar_label="Average Duplicates")"""

    for folder in folders:
        write_hint_files(folder, trials)