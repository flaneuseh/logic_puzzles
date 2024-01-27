full_folder = "FitnessExperiements/full"
no_valid_folder = "FitnessExperiements/valid"
no_violation_folder = "FitnessExperiements/violation"
no_complete_folder = "FitnessExperiements/complete"
nothing_folder = "FitnessExperiements/nothing"
num_trials = 30
gen_len = 100
pop_size = 50
mut_rate = 0.8 
x_rate = 0.3 
add_rate = 0.5 
elits = 2 

from SinglePopulationEvolution import evolve 
from LogicPuzzles import Puzzle, Category 
from HintToEnglish import hint_to_english 
import pickle 

suspects = Category("suspect", ["Ms. carlet", "Mrs. White", "Col. Mustard", "Prof. Plum"], False)
weapons = Category("weapon", ["Knife", "Rope", "Candle Stick", "Wrench"], False)
rooms = Category("room", ["Ball room", "Living Room", "Kitchen", "Study"], False)
time = Category("hour", ["1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM"], True)

puzzle = Puzzle([suspects, weapons, rooms, time]) 

for trial in range(num_trials):
    print("RUNNING TRIAL: {}".format(trial))

    # all weighted 
    pop = evolve(puzzle, gen_len,pop_size, x_rate, mut_rate, add_rate, elits) 

    file = open(full_folder + "/pop" + str(trial) + ".p", "wb")
    pickle.dump(pop, file)

    # no violations 
    pop = evolve(puzzle, gen_len,pop_size, x_rate, mut_rate, add_rate, elits, weights=[0.5, 0.5, 0]) 

    file = open(no_violation_folder + "/pop" + str(trial) + ".p", "wb")
    pickle.dump(pop, file)

    # no valid
    pop = evolve(puzzle, gen_len,pop_size, x_rate, mut_rate, add_rate, elits, weights=[0.5, 0, 0.5]) 

    file = open(no_valid_folder + "/pop" + str(trial) + ".p", "wb")
    pickle.dump(pop, file)

    # no complete 
    pop = evolve(puzzle, gen_len,pop_size, x_rate, mut_rate, add_rate, elits, weights=[0, 0.5, 0.5]) 

    file = open(no_complete_folder + "/pop" + str(trial) + ".p", "wb")
    pickle.dump(pop, file)

    # no fitness 
    pop = evolve(puzzle, gen_len,pop_size, x_rate, mut_rate, add_rate, elits, weights=[0, 0, 0]) 

    file = open(nothing_folder + "/pop" + str(trial) + ".p", "wb")
    pickle.dump(pop, file)







