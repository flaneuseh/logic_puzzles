from LogicPuzzles import Puzzle, Category, generate_hint, apply_hint
from Evolution import apply_hints 

suspects = Category("suspects", ["Scarlet", "White", "Mustard", "Plum"], False)
weapons = Category("weapons", ["Knife", "Rope", "Candle Stick", "Wrench"], False)
rooms = Category("rooms", ["Ball room", "Living Room", "Kitchen", "Study"], False)
time = Category("Time", ["1:00", "2:00", "3:00", "4:00"], True)

puzzle = Puzzle([suspects, weapons, rooms, time]) 

print(puzzle.percent_complete())

hints =  [generate_hint(puzzle) for i in range(20)]
print(hints)
new_puzzle = apply_hints(puzzle, hints)
print(new_puzzle.print_grid())