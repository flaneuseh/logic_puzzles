# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.15.2
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Evolution 
#
# An evolutionary Algorithm to evolve logic puzzles

# %%
# !pip install import_ipynb

# %%
# Imports Baby 
import import_ipynb 
from LogicPuzzles import Puzzle, generate_hint, Category, apply_hint, find_openings, find_transitives  
from HintToEnglish import hint_to_english  
from DataVisualization import plot_history
import random 
import math 
import numpy.random as npr
import pickle 


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

# %%
HINT_VALUES = {
    "is": 0.2,
    "not": 0.4,
    "before": 0.7,
    "simple_or": 0.7,
    "compound_or": 0.1
  }


# %%
def apply_hints(puzzle, hints):
    """
    not fully implemented 
    just for testing 
    """
    copy = Puzzle(puzzle.categories)
    queue = hints[:]
    backlog = []
    applied = True 
    is_valid = True
    while is_valid  and applied and len(queue) > 0:
        applied = False 
        for hint in queue: 
            a, is_valid, complete = apply_hint(copy, hint)
            applied = applied or a
            if not complete: 
                backlog.append(hint)
            if not is_valid:
                break 

            # Apply additional logic 
            if a: 
                a_3, is_valid, complete = find_transitives(copy)
                a_2, is_valid, complete = find_openings(copy)
                applied = applied or a_2 or a_3# test if anything was changed 
        
        queue = backlog 
        backlog = [] 
    return copy 


# %%
class HintSet:
    def __init__(self, hints, puzzle) -> None:
        self.hints = hints 
        self.puzzle = puzzle # assumed to be blank 
        self.completed_puzzle = apply_hints(self.puzzle, self.hints)

    def mutate(self, add_rate):
        hint_copy = self.hints[:]
        if((decide(add_rate)) and len(hint_copy) <= 20) or  len(hint_copy) <= 0:
            new_hint = generate_hint(self.puzzle)
            hint_copy.append(new_hint)
        else:
            index = random.randint(0, len(hint_copy) - 1)
            del hint_copy[index] 
            
        
        return HintSet(hint_copy, self.puzzle)
    
    def cross_over(self, other):
        hints = self.hints[:] + other.hints[:]
        random.shuffle(hints)
        threshold = math.floor(len(hints) / 2)

        return HintSet(hints[0:threshold], self.puzzle), HintSet(hints[threshold: len(hints)], self.puzzle)
    
    def is_valid(self):
        return len(self.hints) > 0 and self.completed_puzzle.is_complete()

    def _violations_fun(self, violations):
        if violations > 10:
            return 0 
        elif violations <= 0:
            return 1 
        else:
            return 1 - (violations / 10 ) 
    
    def weighted_feasiblility(self, complete_w, valid_w, violation_w):
        complete, valid = self.completed_puzzle.percent_complete()
        violations = self.completed_puzzle.num_violations()
 
        return (complete_w * complete) + (valid_w* valid) + (violation_w * self._violations_fun(violations))

    
    def feasibility(self):
        complete, valid = self.completed_puzzle.percent_complete()
        violations = self.completed_puzzle.num_violations()
 
        return (0.33 * complete) + (0.33 * valid) + (0.33 * self._violations_fun(violations))
     
    def optimize_func(self):
        if len(self.hints) == 0:
            return 0 
        score = 0 
        for hint in self.hints:
            rule = list(hint.keys())[0]
            if rule == "simple_hint":
                rule = list(hint.keys())[0]
            score += HINT_VALUES[rule] 
        
        return (0.5 * score / len(self.hints)) + (0.5 * (1 - (len(self.hints) / 20)))

class History:
    def __init__(self):
        self.num_feasible = []
        self.feasible_fitness = []
        self.infeasible_fitness = []

    def update_history(self, feasible, infeasible):
        self.num_feasible.append(len(feasible))

        if len(feasible) == 0:
            self.feasible_fitness.append(0)
        else: 
            self.feasible_fitness.append(feasible[0][0])
        
        if len(infeasible) == 0:
            self.infeasible_fitness.append(0)
        else: 
            self.infeasible_fitness.append(infeasible[0][0])






# %%
def random_hint_set(puzzle):
    num = random.randint(1,5) 
    hints = [generate_hint(puzzle) for i in range(num)]
    return HintSet(hints, puzzle)


# %% [markdown]
# ## Evolution 

# %%

def select(population):
    m = sum([c[0] for c in population])
    if(m == 0):
      selection_probs = [1/len(population) for c in population]
    else:
      selection_probs = [c[0]/m for c in population]
    return population[npr.choice(len(population), p=selection_probs)]


# %%
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

def evolve(puzzle, generations, pop_size, x_rate, mut_rate, add_rate, elits):
    feasible = []
    infeasible = []
    history = History()

    # Create initial population 
    for i in range(pop_size):
        hints = random_hint_set(puzzle)
        _add_child(hints, feasible, infeasible)
        
    for gen in range(generations):
     
        new_feasible = []
        new_infeasible = []

        
        feasible.sort(reverse= True, key = lambda a: a[0])
        infeasible.sort(reverse= True, key = lambda a: a[0]) 

        history.update_history(feasible, infeasible)

        if gen % 50 == 0: 
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
        if len(feasible) > 0:
            new_feasible = feasible[:elits]
        if len(infeasible) > 0:
            new_infeasible = infeasible[:elits]

        #create new population 
        while len(new_feasible) + len(new_infeasible) < pop_size:
            
            # Selection 
            # Not clear to me how to choose which pop to select from, 
            # right now am deciding randomly based on size of two pops 

            if decide(len(feasible) / (len(feasible) + len(infeasible))):
                # selecting from feasible
                indiv1 = select(feasible)[1]
                indiv2 = select(feasible)[1]
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
            _add_child(child1, new_feasible, new_infeasible)

            if len(new_feasible) + len(new_infeasible) < pop_size:
                _add_child(child2, new_feasible, new_infeasible)
                
        feasible = new_feasible
        infeasible = new_infeasible 
    return feasible, infeasible, history 


# %%
if __name__ == "__main__":
    suspects = Category("suspect", ["Scarlet", "White", "Mustard", "Plum"], False)
    weapons = Category("weapon", ["Knife", "Rope", "Candle Stick", "Wrench"], False)
    rooms = Category("room", ["Ball room", "Living Room", "Kitchen", "Study"], False)
    time = Category("hour", ["1:00", "2:00", "3:00", "4:00"], True)

    puzzle = Puzzle([suspects, weapons, rooms, time]) 

    pop = evolve(puzzle, 100,50, 0.2, 1, 0.5, 2) 

# %%
if __name__ == "__main__":
    file = open("Experiement1/pop1.p", "wb")
    pickle.dump(pop, file)
    feasible = pop[0]
    infeasible = pop[1]
    history = pop[2]

    print(feasible)
    print(feasible[0][1].completed_puzzle.print_grid())
    print(len(feasible[0][1].hints))
    print([hint_to_english(hint) for hint in feasible[0][1].hints])
    print("\n\n")
    print(infeasible)
    plot_history(history, "Experiement1")
