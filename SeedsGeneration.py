from LogicPuzzles import Puzzle, Category, Insight
from MapEliteGeneration import map_elite_generate
from MapElitesVisualization import write_hint_files

if __name__ == "__main__":
    seed = Category("seed", ["Pumpkin", "Kale", "Blueberry", "Cauliflower"], False)
    sunlight = Category("sunlight", ["2h", "4h", "6h", "8h"], True)
    water = Category("water", ["1/4c", "1/2c", "3/4c", "1c"], True)

    puzzle = Puzzle([seed, sunlight, water]) 

    folder = "SeedInsights"
    starting =0 
    num_trials = 1
    gen_len = 1000 
    pop_size = 300
    mut_rate = 0.8 
    x_rate = 0.6
    add_rate = 0.5 
    elits = 10

    map_elite_generate(puzzle, folder, starting, num_trials, gen_len, pop_size, mut_rate, x_rate, add_rate, elits, required_insights_oneof={Insight.BEFORE_N_SPOTS_NOINFO}, forbidden_insights={Insight.BEFORE_N_SPOTS_SHIFT, Insight.BEFORE_N_SPOTS_CROSSCHECK, Insight.TRANS_SETS, Insight.TRANS_ABC_FALSE, Insight.SIMPLE_OR_DIFF_CAT})
    write_hint_files(folder, num_trials)

    # recipe = BEFORE_N_SPOTS_SHIFT or BEFORE_N_SPOTS_CROSSCHECK, SIMPLE_OR_DIFF_CAT