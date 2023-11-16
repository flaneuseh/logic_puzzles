import matplotlib.pyplot as plt 
import pickle 
from HintToEnglish import hint_to_english

def plot_history(history, folder):
    plt.plot(history.num_feasible)
    plt.xlabel("Generation")
    plt.ylabel("Number of Feasible Indivuals")
    plt.title("Feasible solutions over Evolution")
    plt.savefig(folder + '/feasible.png')
    plt.clf()
    plt.plot(history.feasible_fitness, label = "Feasible")
    plt.plot(history.infeasible_fitness, label = "Infeasible")
    plt.xlabel("Generation")
    plt.ylabel("Fitness")
    plt.title("Fitness over generations")
    plt.legend()
    plt.savefig(folder + '/fitness.png')


def create_agg_plot(trials, color, label):
    x = list(range(0, len(trials[0])))
    
    trial_avg  = [] 
    trial_max = [] 
    trial_min = [] 

    for gen in x:
        fitness = [trials[i][gen] for i in range(len(trials))]
        trial_avg.append(sum(fitness) / len(fitness))
        trial_max.append(max(fitness))
        trial_min.append(min(fitness))
        
    plt.plot(x, trial_avg, color = color, label = label)
    plt.legend()
    plt.fill_between(x, trial_min, trial_max, color=color, alpha=0.1)
    return trial_avg


def plot_histories(histories, folder):
    feasible = [history.feasible_fitness for history in histories]
    infeasible = [history.infeasible_fitness for history in histories]
    num_feasible = [history.num_feasible for history in histories]

    fes_average = create_agg_plot(feasible, "red", "Feasible Fitness")
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

def first_feasible(histories): 
    num_feasible = [history.num_feasible for history in histories]
    first_feasible = [[ n for n,i in enumerate(li) if i>0.7 ][0] for li in num_feasible]

    return sum(first_feasible) / len(first_feasible), min(first_feasible), max(first_feasible)


def process_folder(experiement_folder, num_trials):
    histories = [] 
    feasible_pops = [] 
    infeasible_pops =[]
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

    data_file.close()

    hint_file = open(experiement_folder + "/hints.txt", "w")
    sol_file = open(experiement_folder + "/solutions.txt", "w")
    num = 1 
    for fitness, hint_set in feasible_pops: 
        hints = hint_set.hints 
        hint_file.write("Hints for puzzle:{}\n".format(num))
        hint_num = 1 
        for hint in hints:
            hint_file.write("\t{}. {}\n".format(hint_num, hint_to_english(hint)))
            hint_num += 1 
        hint_file.write("\n\n")

        sol_file.write("Solution for puzzle:{}\n".format(num))
        sol_file.write(hint_set.completed_puzzle.print_grid())
        sol_file.write("\n\n")

        num+=1 
    
    hint_file.close()
    sol_file.close()
    

if __name__ == "__main__":
    process_folder("Experiements4", 30)