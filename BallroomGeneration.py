from LogicPuzzles import Puzzle, Category, ALL_INSIGHTS, BEFORE_NUM_SPOTS, BEFORE_NUM_SPOTS_THREE
from MapEliteGeneration import map_elite_generate
from MapElitesVisualization import write_hint_files

if __name__ == "__main__":
    subject = Category("time", ["1", "2", "3", "4"], True)
    teacher = Category("suspect", ["Lady Eleanor Appleton", "Lord George Elliot", "Miss Clementine Baker", "Mr. John Parker"], False)
    time = Category("dance", ["Waltz", "Foxtrot", "Tango", "Quickstep"], False)

    puzzle = Puzzle([subject, teacher, time]) 

    folder = "BallroomInsights"
    starting =0 
    num_trials = 1
    gen_len = 101 
    pop_size = 100
    mut_rate = 0.8 
    x_rate = 0.6
    add_rate = 0.5 
    elits = 10

    print(ALL_INSIGHTS)
    map_elite_generate(puzzle, folder, starting, num_trials, gen_len, pop_size, mut_rate, x_rate, add_rate, elits, required_insights_oneof={BEFORE_NUM_SPOTS}, forbidden_insights={BEFORE_NUM_SPOTS_THREE})
    write_hint_files(folder, num_trials)
