import pickle
import matplotlib.pyplot as plt 


experiment_folder = "InfeasibleExperiement1" 

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
    
    return histories, feasible_pops, infeasible_pops 

def average_parts(history):
    parts_by_pop = history.feasible_parts

    complete_agg = []
    valid_agg = []
    vio_agg = []
    for pop in parts_by_pop:
        complete_li = [l[0] for l in pop]
        complete_agg.append((sum(complete_li) / len(complete_li), complete_li[0]))
        valid_li = [l[1] for l in pop]
        valid_agg.append((sum(valid_li) / len(valid_li),valid_li[0]))
        vio_li = [l[2] for l in pop]
        vio_agg.append((sum(vio_li) / len(vio_li),vio_li[0]))
    
    return complete_agg, valid_agg, vio_agg 

def avg_parts_trials(histories):
    complete_avg = [0] * len(histories[0].feasible_parts)
    complete_max = [0] * len(histories[0].feasible_parts)
    valid_avg = [0] * len(histories[0].feasible_parts)
    valid_max = [0] * len(histories[0].feasible_parts)

    vio_avg = [0] * len(histories[0].feasible_parts)
    vio_max =[0] * len(histories[0].feasible_parts)

    for history in histories: 
        trial_complete, trial_valid, trial_agg = average_parts(history) 
        for i in range(len(trial_complete)):
            complete_avg[i] = complete_avg[i] + trial_complete[i][0]
            complete_max[i] += trial_complete[i][1]

            valid_avg[i] += trial_valid[i][0]
            valid_max[i] += trial_valid[i][1]

            vio_avg[i] += trial_agg[i][0]
            vio_max[i] += trial_agg[i][1]
    
    complete_avg = [s / len(histories) for s in complete_avg]
    valid_avg = [s / len(histories) for s in valid_avg]
    vio_avg = [s / len(histories) for s in vio_avg]

    complete_max = [s / len(histories) for s in complete_max]
    valid_max = [s / len(histories) for s in valid_max]
    vio_max = [s / len(histories) for s in vio_max]
    return [complete_avg,valid_avg, vio_avg], [complete_max, valid_max, vio_max]


def plot_data(data, title):
    plt.plot(data[0], label = "complete")
    plt.plot(data[1], label = "valid")
    plt.plot(data[2], label = "violation")
    plt.title(title)
    plt.ylabel("Infeasible Fitness Component")
    plt.xlabel("Generation")
    plt.legend()
    plt.show()





histories, feasible_pops, infeasible_pops = process_folder(experiment_folder, 6)

averages, maxes =  avg_parts_trials(histories) 

plot_data(averages, "Fitness component average over population")
plot_data(maxes, "Fitness component elites over population")