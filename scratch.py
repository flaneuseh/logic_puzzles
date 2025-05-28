from insight_tree import save_move_tree, choose_move_lazy, choose_move_ordered
from LogicPuzzles import Category, Puzzle
from Evolution import get_needed


# The shapes Linguine is the sauces Pesto
# Either the sauces Tomato or the sauces Pesto is the shapes Bowtie
# The sauces Carbonara was not the shapes Shell
# Either the shapes Bowtie or the shapes Elbow is the sauces Tomato
# Either the shapes Shell is the sauces Alfredo or the sauces Alfredo is the shapes Linguine
# Either the shapes Elbow or the shapes Bowtie is the sauces Carbonara
# The sauces Alfredo was not the shapes Linguine

shapes = Category("shapes", ["Elbow", "Bowtie", "Linguine", "Shell"], False)
sauces = Category("sauces", ["Tomato", "Alfredo", "Pesto", "Carbonara"], False)
puzzle = Puzzle([shapes, sauces])

hints = [
    {"is": [shapes, "Linguine", sauces, "Pesto"]},
    {"simple_or": [sauces, "Tomato", sauces, "Pesto", shapes, "Bowtie"]},
    {"not": [{"is": [sauces, "Carbonara", shapes, "Shell"]}]},
    {"simple_or": [shapes, "Bowtie", shapes, "Elbow", sauces, "Tomato"]},
    {"compound_or": [
        {"is": [shapes, "Shell", sauces, "Alfredo"]},
        {"is": [sauces, "Alfredo", shapes, "Linguine"]},
    ]},
    {"simple_or": [shapes, "Elbow", shapes, "Bowtie", sauces, "Carbonara"]},
    {"not": [{"is": [sauces, "Alfredo", shapes, "Linguine"]}]},
]

get_needed(puzzle, hints, True)
save_move_tree(puzzle, hints, choose_move_ordered, "ordered")
save_move_tree(puzzle, hints, choose_move_lazy, "lazy")
