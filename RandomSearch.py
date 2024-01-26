from Evolution import * 
import matplotlib.pyplot as plt 
seeds = list(range(100))


suspects = Category("suspect", ["Ms. carlet", "Mrs. White", "Col. Mustard", "Prof. Plum"], False)
weapons = Category("weapon", ["Knife", "Rope", "Candle Stick", "Wrench"], False)
rooms = Category("room", ["Ball room", "Living Room", "Kitchen", "Study"], False)
time = Category("hour", ["1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM"], True)

puzzle = Puzzle([suspects, weapons, rooms, time]) 


"""cycle_results = []

for seed in seeds: 
    cycles = 0 
    random.seed(seed)
    indivual = random_hint_set(puzzle)

    while not indivual.is_valid():
        indivual = indivual.mutate(0.5)
        cycles += 1 
    cycle_results.append(cycles)
    print(cycles)"""

cycle_results = [198, 60, 285, 58, 370, 157, 120, 91, 27, 291, 117, 95, 465, 83, 306, 269, 62, 185, 88, 101, 317, 99, 145, 55, 179, 58, 311, 6, 308, 121, 185, 149, 304, 79, 11, 265, 239, 512, 102, 392, 173, 129, 56, 171, 368, 90, 98, 648, 481, 173, 119, 159, 169, 161, 209, 70, 78, 525, 96, 234, 16, 423, 75, 398, 361, 90, 252, 231, 126, 28, 513, 55, 181, 106, 309, 184, 116, 86, 40, 457, 755, 236, 389, 527, 54, 332, 183, 185, 219, 58, 207, 80, 348, 280, 334, 49, 17, 170, 404, 14]


print(sum(cycle_results) / len(cycle_results))
plt.hist(cycle_results, bins = 20)
plt.title("Random Search for Feasible Indivuals")
plt.xlabel("Number of mutations")
plt.ylabel("Frequency")
plt.show()