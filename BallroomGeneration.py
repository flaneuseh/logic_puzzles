from LogicPuzzles import Puzzle, Category 
from MapEliteGeneration import map_elite_generate

if __name__ == "__main__":
    subject = Category("time", ["1", "2", "3", "4"], True)
    teacher = Category("suspect", ["Lady Eleanor Appleton", "Lord George Elliot", "Miss Clementine Baker", "Mr. John Parker"], False)
    time = Category("dance", ["Waltz", "Foxtrot", "Tango", "Quickstep"], False)

    puzzle = Puzzle([subject, teacher, time]) 

    folder = "Ballroom"
    starting =0 
    num_trials = 1
    gen_len = 1000 
    pop_size = 300
    mut_rate = 0.8 
    x_rate = 0.6
    add_rate = 0.5 
    elits = 10

    map_elite_generate(puzzle, folder, starting, num_trials, gen_len, pop_size, mut_rate, x_rate, add_rate, elits)
