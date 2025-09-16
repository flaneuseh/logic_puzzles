import pickle
from HintToEnglish import hint_to_english
from Evolution import apply_hints 


folder= "DifficultyOnly" 
num_trials = 30 


for i in range(num_trials): 
    feasible, infeasible, history = pickle.load( open(folder + "/pop" + str(i) + ".p", "rb" ))
    feasible = feasible[0][1]
    copy, valid, loops = apply_hints(feasible.puzzle, feasible.hints)
    if(not valid):
        print("Indivual {} wasn't valid".format(i))
        print([hint_to_english(hint) for hint in feasible.hints])
        print("-"* 100)