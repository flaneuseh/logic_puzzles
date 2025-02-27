from LogicPuzzles import (
    Category,
    Puzzle
)
from Evolution import apply_hints

if __name__ == "__main__":
    # Sunlight puzzle
    hours = Category("hours", ["2h", "4h", "6h", "8h"], True)
    plants = Category("plants", ["Pumpkins", "Kale", "Blueberries", "Cauliflower"], False)
    puzzle = Puzzle([hours, plants])
   
    hints = [
        {
            "is": [plants, "Blueberries", hours, "2h"]
        },
        {
            "compound_or": [{"is": [plants, "Kale", hours, "4h"]}, {"is": [plants, "Blueberries", hours, "6h"]}]
        },
        {
            "before": [plants, "Blueberries", plants, "Cauliflower", hours, 2]
        }
    ]

    completed_puzzle, valid, loops, insights = apply_hints(
            puzzle,
            hints,
    )

    print(completed_puzzle)
    print("loops: ", loops)
    print(insights)

    # Harvesting Order Puzzle
    days = Category("days", ["30", "60", "90", "120"], True)
    plants = Category("plant", ["Potatoes", "Green Onions", "Eggplant", "Broccoli"], False)
    puzzle = Puzzle([days, plants])
   
    hints = [
        {
            "is": [plants, "Eggplant", days, "60"]
        },
        {
            "before": [plants, "Green Onions", plants, "Eggplant", days]
        },        
        {
            "compound_or": [{"is": [plants, "Green Onions", days, "120"]}, {"is": [plants, "Potatoes", days, "120"]}]
        },
    ]

    completed_puzzle, valid, loops, insights = apply_hints(
            puzzle,
            hints,
    )

    print(completed_puzzle)
    print("loops: ", loops)
    print(insights)

    # Protein
    grams = Category("grams", ["10", "15", "20", "25"], True)
    foods = Category("food", ["Salmon", "Eggs", "Tofu", "Peanuts"], False)
    puzzle = Puzzle([grams, foods])
   
    hints = [
        {
            "is": [foods, "Eggs", grams, "15"]
        },
        {
            "before": [foods, "Salmon", foods, "Peanuts", grams, 1]
        },        
    ]

    completed_puzzle, valid, loops, insights = apply_hints(
            puzzle,
            hints,
    )

    print(completed_puzzle)
    print("loops: ", loops)
    print(insights)

    # Pasta
    shapes = Category("shapes", ["Elbow", "Bowtie", "Linguine", "Shell"], False)
    sauces = Category("sauces", ["Tomato", "Alfredo", "Pesto", "Carbonara"], False)
    puzzle = Puzzle([shapes, sauces])
   
    hints = [
        {
            "simple_or": [shapes, "Elbow", shapes, "Shell", sauces, "Tomato"]
        },
        {
            "is": [sauces, "Alfredo", shapes, "Shell"]
        },      
        {
            "compound_or": [{"is": [sauces, "Carbonara", shapes, "Linguine"]}, {"is": [shapes, "Bowtie", sauces, "Alfredo"]}]
        },  
    ]

    completed_puzzle, valid, loops, insights = apply_hints(
            puzzle,
            hints,
    )

    print(completed_puzzle)
    print("loops: ", loops)
    print(insights)

    # Hub
    order = Category("order", ["1st", "2nd", "3rd", "4th"], True)
    quantity = Category("cup", ["1 cup", "2 cups", "3 cups", "4 cups"], True)
    food = Category("ingredient", ["Beans", "Pasta", "Tomato", "Carrots"], False)
    puzzle = Puzzle([order, quantity, food]) 
   
    hints = [
        {
            "before": [food, "Pasta", food, "Beans", order, 2]
        },  
        {
            "before": [food, "Tomato", food, "Beans", quantity, 2]
        },    
        {
            "is": [food, "Tomato", order, "4th"]
        }, 
        {
            "before": [food, "Beans", food, "Carrots", quantity, 1]
        },
    ]

    completed_puzzle, valid, loops, insights = apply_hints(
            puzzle,
            hints,
            print_soln=True
    )

    print("Solution: ")
    print(completed_puzzle.print_grid())
    print("loops: ", loops)
    print(insights)