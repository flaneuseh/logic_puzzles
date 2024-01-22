from Evolution import * 
def _add_child(hints, feasible, infeasible):
    """
    if hint set is valid, add to feasible pop with optmiziation fitness, 
    otherwise add to infeasible pop with feasibility fitness 
    """
    if hints.is_valid():
        fitness = hints.optimize_func()
        feasible.append((fitness, hints))
    else:
        fitness = hints.feasibility()
        infeasible.append((fitness, hints))  
def first_n_feasible(puzzle,fes_size, pop_size, x_rate, mut_rate, add_rate, elits):
    feasible = []
    infeasible = []
    history = History()
    gen = 0 

    # Create initial population 
    for i in range(pop_size):
        hints = random_hint_set(puzzle)
        _add_child(hints, feasible, infeasible)
        
    while len(feasible) < fes_size:
     
        new_infeasible = []

        
        feasible.sort(reverse= True, key = lambda a: a[0])
        infeasible.sort(reverse= True, key = lambda a: a[0]) 

        history.update_history(feasible, infeasible)

        if gen % 30 == 0: 
            print("-"* 40) 
            print("GENERATION " + str(gen))
            print("-"* 80)
            if len(infeasible) > 0:
                print("Infeasible")
                print(infeasible[0])
                print(infeasible[0][1].completed_puzzle.print_grid())
                print(infeasible[0][1].completed_puzzle.num_violations())
            if len(feasible) > 0 :
                print("feasible:")
                print(feasible[0])
                print(feasible[0][1].completed_puzzle.print_grid())
            print("-"* 80)

        # elitism 
        if len(infeasible) > 0:
            new_infeasible = infeasible[:elits]

        #create new population 
        while len(new_infeasible) < pop_size:
            
            # we are only selecting infeasible in this 
            indiv1 = select(infeasible)[1]
            indiv2 = select(infeasible)[1]
            
            
            # cross over 
            if decide(x_rate):
                indiv1, indiv2 = indiv1.cross_over(indiv2)

            # mutation 
            if decide(mut_rate):
                child1 = indiv1.mutate(add_rate)
                child2 = indiv2.mutate(add_rate)
            else:
                child1 = indiv1
                child2 = indiv2

            # add children 
            _add_child(child1, feasible, new_infeasible)

            if len(new_infeasible) < pop_size:
                _add_child(child2, feasible, new_infeasible)
                
        infeasible = new_infeasible 
        gen +=1 
    return feasible, infeasible, history 


def mutate_n_times(population, num_mutations, add_rate):
    populations = []
    for mut in range(num_mutations):
        feasible = []
        infeasible = []

        for parent in population:
            child = parent[1].mutate(add_rate) 
            _add_child(child, feasible, infeasible)
        population = feasible + infeasible 
        populations.append((feasible, infeasible))
    return populations 

def analyze_mutations(mutated_pop):
    fes_ratio = len(mutated_pop[0]) / (len(mutated_pop[0]) + len(mutated_pop[1]))
    infes_fits = [child[0] for child in mutated_pop[1]]
    return fes_ratio, infes_fits

def analyze_all_muts(populations):
    ratios = [] 
    fitnesses = [] 
    for pop in populations:
        fit_ratio, fitness = analyze_mutations(pop)
        ratios.append(fit_ratio)
        fitnesses.append(fitness)
    return ratios, fitnesses 


if __name__ == "__main__":
    num_trials = 30
    fes_size = 100
    pop_size = 50 
    mut_rate = 0.8 
    x_rate = 0.3 
    add_rate = 0.5 
    elits = 2 
    suspects = Category("suspect", ["Ms. carlet", "Mrs. White", "Col. Mustard", "Prof. Plum"], False)
    weapons = Category("weapon", ["Knife", "Rope", "Candle Stick", "Wrench"], False)
    rooms = Category("room", ["Ball room", "Living Room", "Kitchen", "Study"], False)
    time = Category("hour", ["1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM"], True)

    ratios = [] 
    fitnesses = [] 

    puzzle = Puzzle([suspects, weapons, rooms, time]) 
    for i in range(num_trials):
        print("Starting Trial {}".format(i))
        feasible, infesible, history = first_n_feasible(puzzle, fes_size, pop_size, x_rate, mut_rate, add_rate, elits)
        print(len(feasible))
        print(feasible[0])

        populations = mutate_n_times(feasible, 5,  add_rate)

        ratio, fit = analyze_all_muts(populations)
        print(ratio)

        ratios.append(ratio)
        fitnesses.append(fit)
    file = open("MutationData" + "/ratios" + ".p", "wb")
    file1 = open("MutationData" + "/fits" + ".p", "wb")
    pickle.dump(ratios, file)
    pickle.dump(fitnesses, file1)

