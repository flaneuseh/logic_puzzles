import jsonpickle 
import matplotlib.pyplot as plt 
import matplotlib as mpl 
import seaborn as sns
import numpy as np
from HintToEnglish import hint_to_english 
from DataVisualization import create_agg_plot
from colorPalette import COLOR1, COLOR3, COLOR4,  COLOR5, COLORS 

def average_grid(map_grid):
    s = 0 
    l = 0 
    for row in range(len(map_grid)):
        for col in range(len(map_grid[0])):
            child = map_grid[row][col]            
            if( child != -1):

                l += 1
                s += child 
    return s / l  

def count_grid(map_grid):
    s = 0 
    l = 0 
    for row in range(len(map_grid)):
        for col in range(len(map_grid[0])):
            child = map_grid[row][col]            
            if( child != -1):
                l += 1 
    return l  

def difficult_lengths(map_grid):
    lengths = [0] * 10 
    for row in range(len(map_grid)):
        l = 0 
        for col in range(len(map_grid[0])):
            child = map_grid[row][col]            
            if( child != -1):
                l += 1 
        lengths[l] += 1 
    return lengths  

def history_average(histories):
    hint_averages = []
    for history in histories:
        grids = history.elit_grids 
        averages = [average_grid(grid) for grid in grids]
        hint_averages.append(averages)
    return hint_averages 

def history_counts(histories):
    hint_averages = []
    for history in histories:
        grids = history.elit_grids 
        averages = [count_grid(grid) for grid in grids]
        hint_averages.append(averages)
    return hint_averages 

def history_num_solutions(histories):
    hint_averages = []
    for history in histories:
        grids = history.elit_grids 
        averages = [len(grid) for grid in grids]
        hint_averages.append(averages)
    return hint_averages 



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


def solution_dict(grid, n =3, di = {}): 
    fitness_grid = grid.get_fitness_grid()

    for i in range(len(fitness_grid)):
        row = fitness_grid[i]
        
        
        num_empty = row.count(-1)
        num_filled = len(row) - num_empty 

        if(num_filled >= n):
            j = 0 
            while (grid.grid[i][j] is None):
                j += 1 
            hint_set = grid.grid[i][j][1] 
            solution = hint_set.completed_puzzle.print_grid_small() 
            if(solution in di):
                di[solution] += 1 
            else:
                di[solution] = 1 
    return di


def top_solutions(grids, n=5):
    di = {}
    for grid in grids:
        di = solution_dict(grid, n, di)
    
    return di 


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

def get_histories(folder, trial_size):
    grids = []
    for trial in range(trial_size):
        json = open( folder + "/history_trial_{}.p".format(trial), "r").read()
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

def get_average_diff_length(folder, trial_size):
    grids = []
    len_sums = [0] * 10
    for trial in range(trial_size):
        json = open( folder + "/map_grid_trial_{}.p".format(trial), "r").read()
        grid = jsonpickle.decode(json) 
        grid = grid.get_fitness_grid() 
        lengths = difficult_lengths(grid)
     

        for i in range(len(lengths)):
            len_sums[i] += lengths[i]

    avg_lengths = [l / trial_size for l in len_sums]    
    return avg_lengths


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
    folder = "Chili"
    trials = 1

    """avg_lengths = get_average_diff_length(folder, trials)
    plt.title("Average number levels of difficulty per solution")
    plt.ylabel("Average Number of Solutions")
    plt.xlabel("Levels of Difficulty")
    ax = plt.bar(list(range(1,11)),avg_lengths, color = COLOR4)
    plt.xticks([1,2,3,4,5,6,7,8,9,10])
    plt.show()"""
    
    
    """histories = get_histories(folder, trials)
    


    averages = history_average(histories)
    #print(averages)
    plt.title("Average Hint Size in Map-Elite Grid by Generation")
    plt.ylabel("Hint Size")
    plt.xlabel("Generation")
    create_agg_plot(averages, color=COLOR4, label ="average hint size", legend=False,  multiplier=50)
    plt.show()

    counts = history_counts(histories)
    #print(averages)
    plt.title("Number of children in Map-Elite Grid by Generation")
    plt.ylabel("Number of children")
    plt.xlabel("Generation")
    create_agg_plot(counts, color=COLOR4, label="number of feasible", legend=False, multiplier=50)
    plt.show()

    solutions = history_num_solutions(histories)
    #print(averages)
    plt.title("Number of Unique Solutions in Map-Elite Grid by Generation")
    plt.ylabel("Number of Solutions")
    plt.xlabel("Generation")
    plt.axhline(y = 576, color = COLOR1, linestyle = "dashed", label = "Number of solutions possible") 
    create_agg_plot(solutions, color=COLOR4, label="Number of solutions in top grid", legend=True, multiplier=50)
    plt.show()

    infeasible = [history.infes_fits[:10] for history in histories]
   
    plt.title("Infeasible Fitness by Generation")
    plt.ylabel("Fitness")
    plt.xlabel("Generation")
    create_agg_plot(infeasible, color=COLOR4, label="infesible fitness", legend=False)
    plt.show()"""


    """grids = get_grids(folder, trials)
    print(average_grid(grids[0].get_fitness_grid()))

    top_sols = top_solutions(grids, n=5)

    for sol, amount in top_sols.items():
        if(amount >= 4):
            print(amount)
            print(sol)
            print("\n\n")


    fitness, children = solutions_with_n(grids[0], n=5)
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
    plt.show()""" 

    """agg_grid = get_loop_hint_size(folder, trials)
    
    #plt.figure(figsize=(12, 8))
    ax = plt.bar(list(range(1,11)),agg_grid,  color = COLOR4)
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
    ax = plt.bar(list(range(1,11)),agg_total_grid, color = COLOR4)
    plt.xticks([1,2,3,4,5,6,7,8,9,10])
    plt.show()
    
    agg_grid = get_loop_duplicate_grids(folder, trials)
    heat_map(agg_grid, True, title = "Average Duplicates by Solver Loops", ylabel="Average", xlabel="Solver loops", colorbar_label="Average Duplicates")"""
    
    write_hint_files(folder, trials)