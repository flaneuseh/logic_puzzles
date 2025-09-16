from LogicPuzzles import Category, Puzzle
from Evolution import HintSet, hint_to_english
from insight_tree import save_move_tree, choose_move_lazy, choose_move_ordered

if __name__ == "__main__":
    # Sunlight puzzle
    hours = Category("hours", ["2h", "4h", "6h", "8h"], True)
    plants = Category(
        "plants", ["Pumpkins", "Kale", "Blueberries", "Cauliflower"], False
    )
    puzzle = Puzzle([hours, plants])

    hints = [
        {"is": [plants, "Blueberries", hours, "2h"]},
        {
            "compound_or": [
                {"is": [plants, "Kale", hours, "4h"]},
                {"is": [plants, "Blueberries", hours, "6h"]},
            ]
        },
        {"before": [plants, "Blueberries", plants, "Cauliflower", hours, 2]},
    ]

    print("Sunlight (original)")
    hintset = HintSet(hints, puzzle)

    for hint in hints:
        print(hint_to_english(hint))
    print(hintset.completed_puzzle.print_grid())
    print("loops: ", hintset.loops)
    print("required insights: ", hintset.insights)
    save_move_tree(puzzle, hints, choose_move_lazy, "lazy_sunlight")
    print("------------------")

    hints = [
        {"simple_or": [plants, "Pumpkins", plants, "Cauliflower", hours, "2h"]},
        {"before": [plants, "Pumpkins", plants, "Kale", hours, 1]},
        {"before": [plants, "Blueberries", plants, "Kale", hours, 2]},
    ]

    print("Sunlight (alternative)")
    hintset = HintSet(hints, puzzle)

    for hint in hints:
        print(hint_to_english(hint))
    print(hintset.completed_puzzle.print_grid())
    print("loops: ", hintset.loops)
    print("required insights: ", hintset.insights)
    save_move_tree(puzzle, hints, choose_move_lazy, "lazy_sunalt")
    print("------------------")

    # Harvesting Order Puzzle
    days = Category("days", ["30", "60", "90", "120"], True)
    plants = Category(
        "plant", ["Potatoes", "Green Onions", "Eggplant", "Broccoli"], False
    )
    puzzle = Puzzle([days, plants])

    hints = [
        {"is": [plants, "Eggplant", days, "60"]},
        {"before": [plants, "Green Onions", plants, "Eggplant", days]},
        {"simple_or": [plants, "Green Onions", plants, "Potatoes", days, "120"]},
    ]

    print("Harvest")
    hintset = HintSet(hints, puzzle)

    for hint in hints:
        print(hint_to_english(hint))
    print(hintset.completed_puzzle.print_grid())
    print("loops: ", hintset.loops)
    print("required insights: ", hintset.insights)
    save_move_tree(puzzle, hints, choose_move_lazy, "lazy_harvest")
    print("------------------")

    # Protein
    grams = Category("grams", ["10", "15", "20", "25"], True)
    foods = Category("food", ["Salmon", "Eggs", "Tofu", "Peanuts"], False)
    puzzle = Puzzle([grams, foods])

    hints = [
        {"is": [foods, "Eggs", grams, "15"]},
        {"before": [foods, "Salmon", foods, "Peanuts", grams, 1]},
    ]

    print("Protein")
    hintset = HintSet(hints, puzzle)

    for hint in hints:
        print(hint_to_english(hint))
    print(hintset.completed_puzzle.print_grid())
    print("loops: ", hintset.loops)
    print("required insights: ", hintset.insights)
    save_move_tree(puzzle, hints, choose_move_lazy, "lazy_protein")
    print("------------------")

    # Pasta
    shapes = Category("shapes", ["Elbow", "Bowtie", "Linguine", "Shell"], False)
    sauces = Category("sauces", ["Tomato", "Alfredo", "Pesto", "Carbonara"], False)
    puzzle = Puzzle([shapes, sauces])

    hints = [
        {"simple_or": [shapes, "Elbow", shapes, "Shell", sauces, "Tomato"]},
        {"is": [sauces, "Alfredo", shapes, "Shell"]},
        {
            "compound_or": [
                {"is": [sauces, "Carbonara", shapes, "Linguine"]},
                {"is": [shapes, "Bowtie", sauces, "Alfredo"]},
            ]
        },
    ]

    print("Pasta")
    hintset = HintSet(hints, puzzle)

    for hint in hints:
        print(hint_to_english(hint))
    print(hintset.completed_puzzle.print_grid())
    print("loops: ", hintset.loops)
    print("required insights: ", hintset.insights)
    save_move_tree(puzzle, hints, choose_move_lazy, "lazy_pasta")
    print("------------------")

    # Hub
    order = Category("order", ["1st", "2nd", "3rd", "4th"], True)
    quantity = Category("cup", ["1 cup", "2 cups", "3 cups", "4 cups"], True)
    food = Category("ingredient", ["Beans", "Pasta", "Tomato", "Carrots"], False)
    puzzle = Puzzle([order, quantity, food])

    hints = [
        {"before": [food, "Pasta", food, "Beans", order, 2]},
        {"before": [food, "Tomato", food, "Beans", quantity, 2]},
        {"is": [food, "Tomato", order, "4th"]},
        {"before": [food, "Beans", food, "Carrots", quantity, 1]},
    ]

    print("Hub")
    hintset = HintSet(hints, puzzle)

    for hint in hints:
        print(hint_to_english(hint))
    print(hintset.completed_puzzle.print_grid())
    print("loops: ", hintset.loops)
    print("required insights: ", hintset.insights)
    save_move_tree(puzzle, hints, choose_move_lazy, "lazy_hub")
    print("------------------")

    print("Hub (alt)")
    #     Hints for grid cell [148][2]
    # 	The ingredient Beans is 1 cups before the ingredient Carrots
    # 	Either the cup 2 cups or the ingredient Beans is the order 4th
    # 	The ingredient Beans is 2 orders before the ingredient Carrots
    # 	The ingredient Pasta is 2 cups before the ingredient Carrots
    # Insights: {<Insight.TRANS_ABC_TRUE: 14>, <Insight.SIMPLE_OR_DIFF_CAT: 10>, <Insight.BEFORE_N_SPOTS_CROSSCHECK: 17>, <Insight.APPLY_OR: 5>, <Insight.OPENING: 2>, <Insight.BEFORE_N_SPOTS_NOINFO: 13>}
    hints = [
        {"before": [food, "Beans", food, "Carrots", quantity, 1]},
        {"simple_or": [quantity, "2 cups", food, "Beans", order, "4th"]},
        {"before": [food, "Beans", food, "Carrots", order, 2]},
        {"before": [food, "Pasta", food, "Carrots", quantity, 2]},
    ]

    hintset = HintSet(hints, puzzle)

    for hint in hints:
        print(hint_to_english(hint))
    print(hintset.completed_puzzle.print_grid())
    print("loops: ", hintset.loops)
    print("required insights: ", hintset.insights)
    save_move_tree(puzzle, hints, choose_move_lazy, "lazy_hubalt")
    save_move_tree(puzzle, hints, choose_move_ordered, "ordered_hubalt")
    print("------------------")
