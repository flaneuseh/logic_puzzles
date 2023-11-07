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
from LogicPuzzles import Puzzle, generate_hint, Category 
import random 
import math 
import numpy.random as npr


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
    "is": 0.1,
    "not": 0.1,
    "before": 0.5,
    "simple_or": 0.5,
    "compound_or": 1
  }


# %%
def apply_hints(puzzle, hints):
    """
    not fully implemented 
    just for testing 
    """
    copy = Puzzle(puzzle.categories)
    entities = copy._all_ents()
    for hint in hints:
        ent1 = random.choice(entities)
 
        ent2 = random.choice(entities)
        copy.answer(ent1[0], ent2[0], ent1[1], ent2[1], "X")
    return copy 


# %%
class HintSet:
    def __init__(self, hints, puzzle) -> None:
        self.hints = hints 
        self.puzzle = puzzle # assumed to be blank 
        self.completed_puzzle = apply_hints(self.puzzle, self.hints)

    def mutate(self, add_rate):
        hint_copy = self.hints[:]
        if(decide(add_rate)):
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
        return len(self.hints) > 0 and self.completed_puzzle.is_valid()
    
    def feasibility(self):
        return 1 - self.completed_puzzle.percent_complete()
    
    def optimize_func(self):
        if len(self.hints) == 0:
            return 0 
        score = 0 
        for hint in self.hints:
            rule = list(hint.keys())[0]
            if rule == "simple_hint":
                rule = list(hint.keys())[0]
            score += HINT_VALUES[rule] 
        
        return score / len(self.hints)


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
    if hints.is_valid:
        fitness = hints.optimize_func()
        feasible.append((fitness, hints))
    else:
        fitness = hints.feasibility()
        infeasible.append((fitness, hints)) 

def evolve(puzzle, generations, pop_size, x_rate, mut_rate, add_rate, elits):
    feasible = []
    infeasible = []

    # Create initial population 
    for i in range(pop_size):
        hints = random_hint_set(puzzle)
        _add_child(hints, feasible, infeasible)
        

    for gen in range(generations):
        new_feasible = []
        new_infeasible = []

        # elitism 
        feasible.sort(reverse= True, key = lambda a: a[0])
        infeasible.sort(reverse= True, key = lambda a: a[0]) 

        if len(feasible) > elits:
            new_feasible = feasible[:elits]
        if len(infeasible) > elits:
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
    return feasible, infeasible


# %%
suspects = Category("suspects", ["Scarlet", "White", "Mustard", "Plum"], False)
weapons = Category("weapons", ["Knife", "Rope", "Candle Stick", "Wrench"], False)
rooms = Category("rooms", ["Ball room", "Living Room", "Kitchen", "Study"], False)
time = Category("Time", ["1:00", "2:00", "3:00", "4:00"], True)

puzzle = Puzzle([suspects, weapons, rooms, time]) 

pop = evolve(puzzle, 1000,10, 0.2, 0.7, 0.5, 1) 

# %%
feasible = pop[0]
infeasible = pop[1]

print(feasible[0][1].hints)

print(infeasible[0][1].hints)
