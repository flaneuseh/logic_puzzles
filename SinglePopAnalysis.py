import pickle 
import matplotlib.pyplot as plt 
from colorPalette import COLOR1, COLOR2, COLOR3, COLOR4, COLOR5, LINE1, LINE2, LINE3, LINE4, LINE5 
from DataVisualization import set_font_sizes  
full_folder = "ViolationsExperiement/full"
no_vio_folder = "ViolationsExperiement/noVio"
half_vio_folder = "ViolationsExperiement/halfVio"
forth_vio_folder = "ViolationsExperiement/forthVio"

def get_num_feasible(folder, trial_length):
    num_feasible = []
    for i in range(trial_length): 
        file = open(folder + "/pop" + str(i) + ".p", "rb") 
        pop, history  = pickle.load(file) 
        num_feasible.append(history.num_feasible)
    return num_feasible


def get_num_violation(folder, trial_length, generation_length):
    violations = []
    for i in range(generation_length):
        violations.append([])
    
    for i in range(trial_length): 
        file = open(folder + "/pop" + str(i) + ".p", "rb") 
        pop, history  = pickle.load(file) 
        all_pops = history.all_populations 
        for j in range(len(all_pops)):
            indivual = all_pops[j][0][1]
            v = indivual.completed_puzzle.num_violations()
            violations[j].append(v)
    
    return violations




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


def plot_avg(average, mininum, maximum, color, linestyle,  label):

    x = list(range(len(average)))
    plt.plot(x, average, color = color, linestyle = linestyle, label = label)
    plt.legend()
    #plt.fill_between(x, mininum, maximum, color=color, alpha=0.1)


if __name__ == "__main__":
    set_font_sizes(14,16,18)
    feasible = get_num_feasible(full_folder, 27) 
    a, m_0, m_1 = avg_min_max(feasible)
    plot_avg(a, m_0, m_1, COLOR1, LINE1, "1/3")

    feasible = get_num_feasible(half_vio_folder, 27) 
    a, m_0, m_1 = avg_min_max(feasible)
    plot_avg(a, m_0, m_1, COLOR2, LINE2,  "1/6")

    feasible = get_num_feasible(forth_vio_folder, 27) 
    a, m_0, m_1 = avg_min_max(feasible)
    plot_avg(a, m_0, m_1, COLOR3, LINE3, "1/12")

    feasible = get_num_feasible(no_vio_folder, 27) 
    a, m_0, m_1 = avg_min_max(feasible)
    plot_avg(a, m_0, m_1, COLOR4, LINE4, "0")
   
  
    plt.title("Feasible Indivuals Found by Violation Weight")
    plt.ylabel("Number of feasible Indivuals")
    plt.xlabel("Generation")
    plt.show()

    #print(get_num_violation(violation_folder, 30, 100))




