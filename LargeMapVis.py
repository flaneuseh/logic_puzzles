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


def get_loop_grid(grids):
    sum_grid = [0] * len(grids[0][0])
    print(len(grids))
    leng_grid = [0] * len(grids[0][0])


    for col in range(len(sum_grid)):
        for grid in grids: 
            for row in range(len(grid)):
                if(grid[row][col] != -1):
                    sum_grid[col] += grid[row][col]
                    leng_grid[col] += 1 


    for col in range(len(grids[0][0])):
            if(leng_grid[col] == 0):
                sum_grid[col] = -1 
            else: 
                sum_grid[col] = sum_grid[col] / leng_grid[col]
    
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


def solutions_with_n(grid, n =3): 
    fitness_grid = grid.get_fitness_grid()
    children_grid = grid.total_children 

    fitness = []
    children = []

    for i in range(len(fitness_grid)):
        row = fitness_grid[i]
        num_empty = row.count(-1)
        num_filled = len(row) - num_empty 

        if(num_filled >= n):
            fitness.append(row)
            children.append(children_grid[i])
    return fitness, children

def num_puzzles(grid): 
    fitness_grid = grid.get_fitness_grid()

    numbers = []

    for i in range(len(fitness_grid)):
        row = fitness_grid[i]
        num_empty = row.count(-1)
        num_filled = len(row) - num_empty 
        numbers.append(num_filled)

        
    return numbers


def get_grids(folder, trial_size):
    grids = []
    for trial in range(trial_size):
        json = open( folder + "/map_grid_trial_{}.p".format(trial), "r").read()
        grid = jsonpickle.decode(json) 
        grids.append(grid)
    return grids 
def get_loop_hint_size(folder, trial_size):
    grids = []
    for trial in range(trial_size):
        json = open( folder + "/map_grid_trial_{}.p".format(trial), "r").read()
        grid = jsonpickle.decode(json) 
        grids.append(grid.get_fitness_grid())
    
    return get_loop_grid(grids)

def get_loop_duplicate_grids(folder, trial_size):
    grids = []
    for trial in range(trial_size):
        json = open( folder + "/map_grid_trial_{}.p".format(trial), "r").read()
        grid = jsonpickle.decode(json) 
        grids.append(duplicate_grid(grid))
    
    return get_loop_grid(grids)

def get_loop_children_grids(folder, trial_size):
    grids = []
    for trial in range(trial_size):
        json = open( folder + "/history_trial_{}.p".format(trial), "r").read()
        grid = jsonpickle.decode(json) 
        grids.append(grid.total_grid[-1])
    
    return get_loop_grid(grids)


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
    folder = "school3"
    trials = 10

    grids = get_grids(folder, trials)

    fitness, children = solutions_with_n(grids[1], n=5)
    heat_map(fitness, True, title = "Average Hint Size for Solutions 5 or more puzzles", ylabel="Solution", xlabel="Solver loops", colorbar_label="Hint Size", vmin=3)
    heat_map(children, True, title = "Average Children  for Solutions 5 or more puzzles", ylabel="Solution", xlabel="Solver loops", colorbar_label="Children Produced", vmin=1)
    puzzle_lengths = num_puzzles(grids[1])
    puzzle_lengths = np.array(puzzle_lengths)
    labels, counts = np.unique(puzzle_lengths, return_counts=True)
    plt.ylabel("Number of Solutions")
    plt.xlabel("Unqiue Solver loops per solution")
    plt.title("Histogram of puzzles found by solution")
    plt.bar(labels, counts, align='center')
    plt.gca().set_xticks(labels)
    plt.show()

    """"agg_grid = get_loop_hint_size(folder, trials)
    
    #plt.figure(figsize=(12, 8))
    ax = plt.bar(list(range(1,11)),agg_grid)
    plt.title("Average Hint size by solver loops")
    plt.ylabel("Average Hint size")
    plt.xlabel("Solver Loop")
    plt.xticks([1,2,3,4,5,6,7,8,9,10])
    plt.ylim(0, 7)
    plt.show()
    

    agg_total_grid = get_loop_children_grids(folder, trials)
    plt.title("Average number of children by solver loop")
    plt.ylabel("Average Number of children")
    plt.xlabel("Solver Loop")
    ax = plt.bar(list(range(1,11)),agg_total_grid)
    plt.xticks([1,2,3,4,5,6,7,8,9,10])
    plt.show()
    
    agg_grid = get_loop_duplicate_grids(folder, trials)
    heat_map(agg_grid, True, title = "Average Duplicates by Solver Loops", ylabel="Average", xlabel="Solver loops", colorbar_label="Average Duplicates")
    """
    #write_hint_files(folder, trials)