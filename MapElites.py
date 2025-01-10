# %%
import random 
# Imports Baby 
#import import_ipynb 
from copy import deepcopy
from LogicPuzzles import Puzzle, generate_hint, str_hint, Category, apply_hint, find_openings, find_transitives  
from HintToEnglish import hint_to_english  
# from DataVisualization import plot_history
import math 
import numpy.random as npr
import pickle 
from itertools import combinations 
from Evolution import HintSet, random_hint_set


# %%
def decide(rate):
  return random.random() < rate


# %% [markdown]
# ## Representation 
#
# ### Mutation 
#
# The following kinds of mutation are implemented: 
# 1. Add new hint 
# 2. Remove a hint 
#
# ### Cross-over 
# Randomly add hints to each of children 
#
# ### Heuristic 
#
# #### Feasibility 
# The fesability heuristic is the percentage of empty (unsolved). A valid puzzle is completely filled, but if the hints are incomplete or inlogical the resulting puzzle will have many empty pieces. This assumes that the hints will stop being applied when an invalid hint is attempted. 
#
# #### Optimization 
# We are hoping to optimize for challenge. Certain hint types are more challenging then others, so the algorithm will find the average of the difficulty of each hint (according to a dicitonary). In the future more complex algorithms could be considered (what types of deductions need to be made, etc.). This way harder hints (ex: or) will be selected over easier hints (ex: is)

class EliteGrid:

    def __init__(self, width):
        self.width = width 
        self.grid = []
        self.total_children = []
        self.solutions = {}
        self.pop_size = 0 
        self.height = 0 

    
    def add_row(self):
        row = []
        total_row = []
        for j in range(self.width):
            row.append(None)
            total_row.append(0)
        self.grid.append(row)
        self.total_children.append(total_row)
        self.height += 1 
        return self.height - 1 
    
    def select(self):
        if(self.pop_size == 0):
            return None 
        else:
            row = random.randint(0, self.height- 1)
            col = random.randint(0, self.width -1 )

            while(self.grid[row][col] == None):
                row = random.randint(0, self.height - 1)
                col = random.randint(0, self.width - 1)
            return self.grid[row][col]
    
    def _choose_index(self, value):
        increments = 1 / self.height 
        return math.floor(value / increments)
    
    def get_row(self, hint_set):
        solution = hint_set.completed_puzzle.print_grid_small() 
        if solution in self.solutions:
            return self.solutions[solution]
        else:
            row =  self.add_row()
            self.solutions[solution] = row 
            return row
    
    def add_child(self, hint_set):

        row = self.get_row(hint_set)
        col = min((hint_set.solver_loops() - 1), self.width - 1)

        self.total_children[row][col] += 1 

    

        if self.grid[row][col] == None or hint_set.hint_size() <= self.grid[row][col][0]:
            if self.grid[row][col] == None: 
                self.pop_size += 1 
            self.grid[row][col] = (hint_set.hint_size(), hint_set)

    
    def get_fitness_grid(self):
        fit_grid = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                if self.grid[i][j] == None:
                    row.append(-1)
                else:
                    row.append(self.grid[i][j][0])
            fit_grid.append(row)
        return fit_grid

    def print_fit_grid(self):
        fit_grid = self.get_fitness_grid()
        for row in fit_grid:
            row = [str(val).rjust(2) for val in row]
            print(row)

    
    def get_largest_rows(self):
        largest_rows = [] 
        least_empty =self.width 
        fit_grid = self.get_fitness_grid()
        for i in range(self.height):
            row = fit_grid[i]
            empty = row.count(-1)

            if empty < least_empty:
                largest_rows = [row]
                least_empty = empty 
            elif empty == least_empty:
                largest_rows.append(row) 
        return largest_rows
            
    
    def print_progress(self):
        print("Stats:")
        print("\t Height:{}".format(self.height))
        print("\t Total pop:{}".format(self.pop_size))

        for row in self.get_largest_rows():
            row = [str(val).rjust(2) for val in row]
            print(row)

class History:
    def __init__(self): 
        self.elit_grids = []
        self.infes_fits = []
        self.num_fes = [] 
        self.total_grid = []
        self.cycles = 0 
    
    def update(self, elit_grid, infeasible):
        self.cycles+= 1 
        self.infes_fits.append(infeasible[0][0])
        self.num_fes.append(elit_grid.pop_size)

        if(self.cycles % 50 == 0):
            self.elit_grids.append(elit_grid.get_fitness_grid())
            self.total_grid.append(deepcopy(elit_grid.total_children))



# %%

def select(population):
    m = sum([c[0] for c in population])
    if(m == 0):
      selection_probs = [1/len(population) for c in population]
    else:
      selection_probs = [c[0]/m for c in population]
    return population[npr.choice(len(population), p=selection_probs)]




# %%
def _add_child(hints, feasible_grid, infeasible):
    """
    if hint set is valid, add to feasible pop with optmiziation fitness, 
    otherwise add to infeasible pop with feasibility fitness 
    """
    if hints.is_valid():
        #fitness = hints.optimize_func()
        feasible_grid.add_child(hints)
    else:
        fitness = hints.feasibility()
        infeasible.append((fitness, hints)) 

def evolve(puzzle, generations, pop_size, x_rate, mut_rate, add_rate, elits, required_insights_oneof=set(), forbidden_insights=set()):
    feasible_grid = EliteGrid(10) 
    infeasible = []
    history = History()

    # Create initial population 
    for i in range(pop_size):
        hints = random_hint_set(puzzle, required_insights_oneof, forbidden_insights)
        _add_child(hints, feasible_grid, infeasible)
        
    for gen in range(generations):
     
        new_infeasible = []

        
        infeasible.sort(reverse= True, key = lambda a: a[0]) 

        
        history.update(feasible_grid, infeasible)

        if gen % 50 == 0: 
            print("-"* 40) 
            print("GENERATION " + str(gen))
            print("-"* 80)
            if len(infeasible) > 0:
                print("Infeasible")
                print(infeasible[0])
                print(infeasible[0][1].completed_puzzle.print_grid())
                print(infeasible[0][1].completed_puzzle.num_violations())
   
            print("feasible:")
    
            feasible_grid.print_progress()
            print("-"* 80)

        # elitism 
        if len(infeasible) > 0:
            new_infeasible = infeasible[:elits]

        #create new population 
        for j in range(math.floor(pop_size / 2)):
            
            # Selection 
            # Not clear to me how to choose which pop to select from, 
            # right now am deciding randomly based on size of two pops 

            if decide(feasible_grid.pop_size / (feasible_grid.pop_size + len(infeasible))):
                # selecting from feasible
                indiv1 = feasible_grid.select()[1]
                indiv2 = feasible_grid.select()[1]
            else:
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
            _add_child(child1, feasible_grid, new_infeasible)

          
            _add_child(child2, feasible_grid, new_infeasible)
                
        infeasible = new_infeasible 
    for row in range(feasible_grid.height):
        for col in range(feasible_grid.width):
            child_cell = feasible_grid.grid[row][col]
            if(not child_cell is None):
                child = child_cell[1]
                assert len(child.insights & required_insights_oneof) > 0 or len(required_insights_oneof) == 0, "insights: {} does not include any of: {}. Child required: {}".format(child.insights, required_insights_oneof, child.required_insights_oneof)
                assert len(child.insights & forbidden_insights) == 0, "insights: {} includes forbidden: {}. Child forbidden: {}".format(child.insights, child.insights & forbidden_insights, child.forbidden_insights)
                assert not child.require_insight or  len(child.dumb_insights & required_insights_oneof) == 0, "dumb insights: {} includes required: {}. Child required: {}".format(child.dumb_insights, child.insights & required_insights_oneof, child.required_insights_oneof)
    return feasible_grid, infeasible, history 


# %%
if __name__ == "__main__":
    suspects = Category("suspect", ["Scarlet", "White", "Mustard", "Plum"], False)
    weapons = Category("weapon", ["Knife", "Rope", "Candle Stick", "Wrench"], False)
    rooms = Category("room", ["Ball room", "Living Room", "Kitchen", "Study"], False)
    time = Category("hour", ["1:00", "2:00", "3:00", "4:00"], True)

    puzzle = Puzzle([suspects, weapons, rooms, time]) 

    pop = evolve(puzzle, 100,50, 0.2, 1, 0.5, 2) 
    pop[0].print_fit_grid()
    print(pop[2].total_grid[-1])

    
    
# %%
