from LogicPuzzles import * 
from Evolution import random_hint_set, select, decide  

class History:
    def __init__(self):
        self.all_populations = []
        self.max_fit  = [] 
        self.avg_fit = []
        self.num_feasible = []
        self.feasible = []
    
    def update(self, population):
        self.all_populations.append(population) 
        fitnesses = [i[0] for i in population] 
        self.max_fit.append(max(fitnesses))
        self.avg_fit.append(sum(fitnesses)  / len(fitnesses)) 
        feasible = []
        for i in population:
            if i[1].is_valid():
                feasible.append(i)
        self.num_feasible.append(len(feasible))
        self.feasible.append(feasible)

def evolve(puzzle, generations, pop_size, x_rate, mut_rate, add_rate, elits, weights = [0.33, 0.33, 0.33]):
    population = [] 
    history = History()

    # Create initial population 
    for i in range(pop_size):
        hints = random_hint_set(puzzle)
        fitness = hints.weighted_feasiblility(weights[0], weights[1], weights[2])
        population.append((fitness, hints))
        
    for gen in range(generations):
     
        new_population = []

        
        population.sort(reverse= True, key = lambda a: a[0])


        history.update(population)

        if gen % 50 == 0: 
            print("-"* 40) 
            print("GENERATION " + str(gen))
            print("-"* 80)
    
            print(population[0])
            print(population[0][1].completed_puzzle.print_grid())
            print(population[0][1].completed_puzzle.num_violations())
          
        # elitism 
   
        new_population= population[:elits]
        

        #create new population 
        while len(new_population) < pop_size:
            
         
            indiv1 = select(population)[1]
            indiv2 = select(population)[1]
       
            
            
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
            fitness = child1.weighted_feasiblility(weights[0], weights[1], weights[2])
            new_population.append((fitness, child1))

            if len(population) < pop_size:
                fitness = child2.weighted_feasiblility(weights[0], weights[1], weights[2])
                new_population.append((fitness, child2))
                
        population = new_population 
    return population, history 

if __name__ == "__main__":
    num_trials = 10 
    gen_len = 100 
    pop_size = 50 
    mut_rate = 0.8 
    x_rate = 0.3 
    add_rate = 0.5 
    elits = 2 

    suspects = Category("suspect", ["Ms. carlet", "Mrs. White", "Col. Mustard", "Prof. Plum"], False)
    weapons = Category("weapon", ["Knife", "Rope", "Candle Stick", "Wrench"], False)
    rooms = Category("room", ["Ball room", "Living Room", "Kitchen", "Study"], False)
    time = Category("hour", ["1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM"], True)

    puzzle = Puzzle([suspects, weapons, rooms, time]) 


    population, history = evolve(puzzle, gen_len, pop_size, x_rate, mut_rate, add_rate, elits)

    print(history.num_feasible)