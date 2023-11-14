import matplotlib.pyplot as plt 

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
    