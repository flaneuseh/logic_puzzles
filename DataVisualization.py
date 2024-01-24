import matplotlib.pyplot as plt 
import numpy as np
import pickle 
from HintToEnglish import hint_to_english
from Evolution import Category, Puzzle, apply_hints
from LogicPuzzles import str_hint

# def plot_history(history, folder):
#     plt.plot(history.num_feasible)
#     plt.xlabel("Generation")
#     plt.ylabel("Number of Feasible Indivuals")
#     plt.title("Feasible solutions over Evolution")
#     plt.savefig(folder + '/feasible.png')
#     plt.clf()
#     plt.plot(history.feasible_fitness, label = "Feasible")
#     plt.plot(history.infeasible_fitness, label = "Infeasible")
#     plt.xlabel("Generation")
#     plt.ylabel("Fitness")
#     plt.title("Fitness over generations")
#     plt.legend()
#     plt.savefig(folder + '/fitness.png')


def create_agg_plot(trials, color, label, normalize=False):
    x = list(range(0, len(trials[0])))
    
    trial_avg  = [] 
    trial_max = [] 
    trial_min = [] 

    for gen in x:
        fitness = [trials[i][gen] for i in range(len(trials))]
        if normalize and max(fitness) > 1:
            fitness = list(map(lambda f: f/10, fitness))
        trial_avg.append(sum(fitness) / len(fitness))
        trial_max.append(max(fitness))
        trial_min.append(min(fitness))
        
    plt.plot(x, trial_avg, color = color, label = label)
    plt.legend()
    plt.fill_between(x, trial_min, trial_max, color=color, alpha=0.1)
    return trial_avg


def plot_histories(histories, folder):
    plt.clf()
    feasible = [history.feasible_fitness for history in histories]
    infeasible = [history.infeasible_fitness for history in histories]
    num_feasible = [history.num_feasible for history in histories]

    fes_average = create_agg_plot(feasible, "red", "Feasible Fitness", True)
    infes_average = create_agg_plot(infeasible, "blue", "Infeasible Fitness")
    plt.xlabel("Generation")
    plt.ylabel("Fitness")
    plt.title("Fitness over generations")
    plt.legend()
    plt.savefig(folder + '/fitness.png')

    plt.clf()
    create_agg_plot(num_feasible, "red", "number of feasible")
    plt.xlabel("Generation")
    plt.ylabel("Number of Feasible Indivuals")
    plt.title("Feasible solutions over Evolution")
    plt.savefig(folder + '/feasible.png')

    return fes_average, infes_average

def plot_hint_type_averages(averages, folder):
    def var_to_english(hint_type):
        return hint_type.replace("_", " ")
    plt.clf()
    plt.title("Average Hints per Puzzle")
    plt.pie(averages.values(), labels=list(map(var_to_english, averages.keys())), autopct='%1.1f%%')
    plt.savefig(folder + '/hint_types_pie.png')

def plot_type_vs_loops(loops, hint_pcts, folder):
    def var_to_english(hint_type):
        return hint_type.replace("_", " ")
    colors = ['b', 'g', 'r', 'c', 'm']
    plt.clf()
    plt.title("Loops by Hint Type")
    plt.xlabel("Percent Hint Type in Puzzle")
    plt.ylabel("Number of Solver Loops")
    i = 0
    for hint_type, pcts in hint_pcts.items():
        x = pcts
        y = loops
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        plt.plot(x, p(x), color=colors[i], label=var_to_english(hint_type))
        plt.legend()
        i += 1

    # plt.yticks(range(min(loops), max(loops)))
    plt.savefig(folder + '/hint_types_vs_loops.png')

def plot_types_over_solve_time(hint_type_loops, folder):
    def var_to_english(hint_type):
        return hint_type.replace("_", " ")
    plt.clf()

    _, ax = plt.subplots()

    max_loops = len(hint_type_loops["is"])
    labels = []
    for l in range(max_loops):
        labels.append(str(l+1))

    bottom = np.zeros(max_loops)
    for hint_type, loops in hint_type_loops.items():
        ax.bar(labels, loops, bottom=bottom, label=var_to_english(hint_type))
        bottom += loops

    ax.set_title("Hint types used by each solve loop")
    ax.legend()
    plt.ylabel("Hints Remaining in Solve Queue")
    plt.xlabel("Solve Loop")

    plt.savefig(folder + '/types_over_solve_time.png')


def first_feasible(histories): 
    num_feasible = [history.num_feasible for history in histories]
    first_feasible = [[ n for n,i in enumerate(li) if i>0.7 ][0] for li in num_feasible]

    return sum(first_feasible) / len(first_feasible), min(first_feasible), max(first_feasible)


def process_folder(experiement_folder, num_trials):
    histories = [] 
    feasible_pops = [] 
    infeasible_pops =[]

    total_counts = {
        'is': 0,
        'not': 0,
        'before': 0,
        'simple_or': 0,
        'compound_or': 0
    }
    per_puzzle_counts = {
        'is': [],
        'not': [],
        'before': [],
        'simple_or': [],
        'compound_or': []
    }
    per_puzzle_pcts = {
        'is': [],
        'not': [],
        'before': [],
        'simple_or': [],
        'compound_or': []
    }
    hint_sizes = []  
    
    per_puzzle_loops = []
    per_puzzle_duplicates = []
    total_duplicates = 0

    hint_type_loops = {
        'is': [],
        'not': [],
        'before': [],
        'simple_or': [],
        'compound_or': []
    }

    for i in range(num_trials): 
        feasible, infeasible, history = pickle.load( open(experiement_folder + "/pop" + str(i) + ".p", "rb" ) )
        histories.append(history)
        if len(feasible) > 0: 
            feasible_pops.append(feasible[0])
        if len(infeasible) > 0: 
            infeasible_pops.append(infeasible[0])
    
    fes_average, infes_average = plot_histories(histories, experiement_folder)
    avg_first, min_first, max_first = first_feasible(histories) 

    data_file = open(experiement_folder + "/data.txt", "w")
    data_file.write("Average first feasible solution found in the {} generation \n".format(avg_first + 1))
    data_file.write("Min first feasible solution found in the {} generation \n".format(min_first + 1))
    data_file.write("Max first feasible solution found in the {} generation \n".format(max_first + 1))



    data_file.write("\n\nAverage Feasible Fitness in Generation 500:{}\n".format(fes_average[-1]))
    data_file.write("Average Infeasible Fitness in Generation 500:{}\n".format(infes_average[-1]))

    data_file.write("\n\nAverage Feasible Fitness for all gens:{}\n".format(fes_average))
    data_file.write("Average Infeasible Fitness for all gens:{}\n".format(infes_average))

    

    hint_file = open(experiement_folder + "/hints.txt", "w")
    sol_file = open(experiement_folder + "/solutions.txt", "w")
    num = 1 
    for fitness, hint_set in feasible_pops: 
        hints = hint_set.hints 

        hint_set_trace = {}
        try:
            hint_set_trace = hint_set.trace
        except AttributeError:
            suspects = Category("suspect", ["Ms. carlet", "Mrs. White", "Col. Mustard", "Prof. Plum"], False)
            weapons = Category("weapon", ["Knife", "Rope", "Candle Stick", "Wrench"], False)
            rooms = Category("room", ["Ball room", "Living Room", "Kitchen", "Study"], False)
            time = Category("hour", ["1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM"], True)

            puzzle = Puzzle([suspects, weapons, rooms, time]) 
            _, hint_set_trace = apply_hints(puzzle, hints)

        loops = max(len(hint_trace) for hint_trace in hint_set_trace.values())
        per_puzzle_loops.append(loops)
        
        duplicate_counts = {}
        types_counts = {
            'is': 0,
            'not': 0,
            'before': 0,
            'simple_or': 0,
            'compound_or': 0
        }
        hint_file.write("Hints for puzzle:{}\n".format(num))
        hint_num = 1 
        for hint in hints:
            english = hint_to_english(hint)
            hint_file.write("\t{}. {}\n".format(hint_num, english))
            hint_num += 1 

            if english in duplicate_counts:
                duplicate_counts[english] += 1
            else:
                duplicate_counts[english] = 0

                #type anal 
                kind = next(iter(hint)) 
                types_counts[kind] += 1           
                total_counts[kind] += 1 

                trace_key = str_hint(hint)
                trace = hint_set_trace[trace_key]
                while len(hint_type_loops[kind]) < loops:
                    hint_type_loops[kind].append(0)
                for l in trace:
                    hint_type_loops[kind][l-1] += 1

        hint_file.write("\n\n")

        for key in types_counts: 
            count = types_counts[key]
            pct = count/len(hints)
            per_puzzle_counts[key].append(count)
            per_puzzle_pcts[key].append(pct)


        num_duplicates = sum(duplicate_counts.values())
        hint_sizes.append(len(hints) - num_duplicates) 
        total_duplicates += num_duplicates
        per_puzzle_duplicates.append(num_duplicates)

        sol_file.write("Solution for puzzle:{}\n".format(num))
        sol_file.write(hint_set.completed_puzzle.print_grid())
        sol_file.write("\n\n")

        num+=1 

    data_file.write("\n\nAverage clue length:{}".format(sum(hint_sizes) / len(hint_sizes)))
    data_file.write("\nMin clue size:{}".format(min(hint_sizes)))
    data_file.write("\nMax Clue Size:{}".format(max(hint_sizes)))

    data_file.write("\n\nAverage num loops:{}".format(sum(per_puzzle_loops) / len(per_puzzle_loops)))
    data_file.write("\nMin num loops:{}".format(min(per_puzzle_loops)))
    data_file.write("\nMax num loops:{}".format(max(per_puzzle_loops)))

    data_file.write("\n\nTotal Clue Amounts")
    for key in total_counts:
        data_file.write("\n\t{}:{}".format(key, total_counts[key]))
    
    data_file.write("\n\nAverages")
    hint_type_averages = {}
    for key in total_counts:
        key_avg = total_counts[key]/len(feasible_pops)
        hint_type_averages[key] = key_avg
        data_file.write("\n\t{}:{}".format(key, key_avg))
    plot_hint_type_averages(hint_type_averages, experiement_folder)
    plot_type_vs_loops(per_puzzle_loops, per_puzzle_pcts, experiement_folder)

    for kind in hint_type_loops.keys():
        while len(hint_type_loops[kind]) < max(per_puzzle_loops):
            hint_type_loops[kind].append(0)
    plot_types_over_solve_time(hint_type_loops, experiement_folder)
    
    # data_file.write("\n\nClues per Puzzle when Hint Type is included")
    # for key in per_puzzle_counts:
    #     avg = sum(per_puzzle_counts[key]) / len(per_puzzle_counts[key])
    #     data_file.write("\n\t{}:{}".format(key, avg))
    
    data_file.write("\n\nTotal duplicates:{}".format(total_duplicates))
    data_file.write("\nAverage duplicates:{}".format(sum(per_puzzle_duplicates) / len(per_puzzle_duplicates)))
    data_file.write("\nMin duplicates:{}".format(min(per_puzzle_duplicates)))
    data_file.write("\nMax duplicates:{}".format(max(per_puzzle_duplicates)))
    
    data_file.close()
    
    hint_file.close()
    sol_file.close()
    

if __name__ == "__main__":
    process_folder("ExperimentsKaylah8", 30)
