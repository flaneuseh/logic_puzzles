full_folder = "ViolationsExperiement/full"
no_vio_folder = "ViolationsExperiement/noVio"
half_vio_folder = "ViolationsExperiement/halfVio"
forth_vio_folder = "ViolationsExperiement/forthVio"
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

    # violations 1/3 
    pop = evolve(puzzle, gen_len,pop_size, x_rate, mut_rate, add_rate, elits) 

    file = open(full_folder + "/pop" + str(trial) + ".p", "wb")
    pickle.dump(pop, file)

    # no violations 
    pop = evolve(puzzle, gen_len,pop_size, x_rate, mut_rate, add_rate, elits, weights=[0.5, 0.5, 0]) 

    file = open(no_vio_folder + "/pop" + str(trial) + ".p", "wb")
    pickle.dump(pop, file)

    # violations 1/6 of fitness 
    pop = evolve(puzzle, gen_len,pop_size, x_rate, mut_rate, add_rate, elits, weights=[0.4166, 0.4166, 0.1666]) 

    file = open(half_vio_folder + "/pop" + str(trial) + ".p", "wb")
    pickle.dump(pop, file)

    # violations 1/12
    pop = evolve(puzzle, gen_len,pop_size, x_rate, mut_rate, add_rate, elits, weights=[0.4583, 0.4583, 0.0833]) 

    file = open(forth_vio_folder + "/pop" + str(trial) + ".p", "wb")
    pickle.dump(pop, file)







