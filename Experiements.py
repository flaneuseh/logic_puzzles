folder = "ExperimentsKaylah7"
num_trials = 30 
gen_len = 1000 
pop_size = 50 
mut_rate = 0.8 
x_rate = 0.3 
add_rate = 0.5 
elits = 2 

from Evolution import evolve 
from LogicPuzzles import Puzzle, Category 
from HintToEnglish import hint_to_english 
import pickle 

for trial in range(num_trials):
    print("Running trial: {}".format(trial))
    suspects = Category("suspect", ["Ms. carlet", "Mrs. White", "Col. Mustard", "Prof. Plum"], False)
    weapons = Category("weapon", ["Knife", "Rope", "Candle Stick", "Wrench"], False)
    rooms = Category("room", ["Ball room", "Living Room", "Kitchen", "Study"], False)
    time = Category("hour", ["1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM"], True)

    puzzle = Puzzle([suspects, weapons, rooms, time]) 

    pop = evolve(puzzle, gen_len,pop_size, x_rate, mut_rate, add_rate, elits) 

    file = open(folder + "/pop" + str(trial) + ".p", "wb")
    pickle.dump(pop, file)
    feasible = pop[0]
    infeasible = pop[1]
    history = pop[2]

    if len(feasible) > 0:
        print([hint_to_english(hint) for hint in feasible[0][1].hints])


