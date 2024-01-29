import pickle 
import matplotlib.pyplot as plt 
all_components_folder = "FitnessExperiements/full"
nothing_folder = "FitnessExperiements/nothing"
complete_folder = "FitnessExperiements/complete"
valid_folder = "FitnessExperiements/valid"
violation_folder = "FitnessExperiements/violation" 


def get_num_feasible(folder, trial_length):
    num_feasible = []
    for i in range(trial_length): 
        file = open(folder + "/pop" + str(i) + ".p", "rb") 
        pop, history  = pickle.load(file) 
        num_feasible.append(history.num_feasible)
    return num_feasible

def avg_min_max(list_of_lists):

    avg = []
    minimum = []
    maximum = []

    for i in range(len(list_of_lists[0])):
        generation = [list_of_lists[j][i] for j in range(len(list_of_lists))]
        avg.append(sum(generation) / len(generation))
        minimum.append(min(generation))
        maximum.append(max(generation))
    
    return avg, minimum, maximum 


def plot_avg(average, mininum, maximum, color, label):

    x = list(range(len(average)))
    plt.plot(x, average, color = color, label = label)
    plt.legend()
    #plt.fill_between(x, mininum, maximum, color=color, alpha=0.1)


if __name__ == "__main__":
    feasible = get_num_feasible(all_components_folder, 30) 
    a, m_0, m_1 = avg_min_max(feasible)
    plot_avg(a, m_0, m_1, "green", "Full Fitness")

    feasible = get_num_feasible(complete_folder, 30) 
    a, m_0, m_1 = avg_min_max(feasible)
    plot_avg(a, m_0, m_1, "orange", "No Completetion")

    feasible = get_num_feasible(valid_folder, 30) 
    a, m_0, m_1 = avg_min_max(feasible)
    plot_avg(a, m_0, m_1, "blue", "No Valid")

    feasible = get_num_feasible(violation_folder, 30) 
    a, m_0, m_1 = avg_min_max(feasible)
    plot_avg(a, m_0, m_1, "purple", "No Violations")

    feasible = get_num_feasible(nothing_folder, 30) 
    a, m_0, m_1 = avg_min_max(feasible)
    plot_avg(a, m_0, m_1, "red", "Random Search")
    plt.title("Feasible Indivuals Found by Fitness Function")
    plt.ylabel("Number of feasible Indivuals")
    plt.xlabel("Generation")
    plt.show()




