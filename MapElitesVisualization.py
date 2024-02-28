import jsonpickle 
import matplotlib.pyplot as plt 
import matplotlib as mpl 
import seaborn as sns
import numpy as np
from HintToEnglish import hint_to_english 
def heat_map(grid, reverse, title = "", xlabel = "", ylabel = "", colorbar_label="", vmin = 0):
    
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

    plt.show()


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



def duplicate_grid(map_grid):
    dup_grid = []
    for row in range(map_grid.height):
        new_row = []
        for col in range(map_grid.width):
            child = map_grid.grid[row][col]
            if(child is None):
                new_row.append(-1)
            else:
                new_row.append(child[1].num_duplicates())
        dup_grid.append(new_row)
    return dup_grid




def get_agg_hint_grids(folder, trial_size):
    grids = []
    for trial in range(trial_size):
        json = open( folder + "/map_grid_trial_{}.p".format(trial), "r").read()
        grid = jsonpickle.decode(json) 
        grids.append(grid.get_fitness_grid())
    
    return get_agg_grid(grids)

def get_agg_duplicate_grids(folder, trial_size):
    grids = []
    for trial in range(trial_size):
        json = open( folder + "/map_grid_trial_{}.p".format(trial), "r").read()
        grid = jsonpickle.decode(json) 
        grids.append(duplicate_grid(grid))
    
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
    for hint in hint_set.hints:
        s += "\t" + hint_to_english(hint) + "\n"
    return s


def make_hint_file(map_grid, file_path):
    file = open(file_path, "w") 
    for row in range(map_grid.height):
        for col in range(map_grid.width):
            child = map_grid.grid[row][col]
            if(not child is None):
                file.write("Hints for grid cell [{}][{}]\n".format(row, col))
                file.write(hintset_to_string(child[1]))
                file.write("\n\n")

    file.close()

def make_solution_file(map_grid, file_path):
    file = open(file_path, "w") 
    for row in range(map_grid.height):
        for col in range(map_grid.width):
            child = map_grid.grid[row][col]
            if(not child is None):
                file.write("Solution for grid cell [{}][{}]\n".format(row, col))
                file.write(child[1].completed_puzzle.print_grid())
                file.write("\n\n")

    file.close()



def write_hint_files(folder, trial_size):
    for trial in range(trial_size):
        json = open( folder + "/map_grid_trial_{}.p".format(trial), "r").read()
        grid = jsonpickle.decode(json) 
        make_hint_file(grid, folder + "/hints_{}.txt".format(trial))
        make_solution_file(grid, folder + "/solutions_{}.txt".format(trial))


if __name__ == "__main__":
    folder = "MapElites10k"
    trials = 15
    agg_grid = get_agg_hint_grids(folder, trials)
    heat_map(agg_grid, True, title = "Average Hint Size by Cell", ylabel="Gini Coefficent", xlabel="Solver loops", colorbar_label="Average Hint Size", vmin = 4)

    agg_total_grid = get_agg_children_grids(folder, trials)
    heat_map(agg_total_grid, False, title = "Average Children Produced by Cell", ylabel="Gini Coefficent", xlabel="Solver loops", colorbar_label="Average Children Produced")

    agg_grid = get_agg_duplicate_grids(folder, trials)
    heat_map(agg_grid, True, title = "Average Duplicates by Cell", ylabel="Gini Coefficent", xlabel="Solver loops", colorbar_label="Average Duplicates")

    write_hint_files(folder, trials)