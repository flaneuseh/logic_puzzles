import ultraimport

ultraimport("__dir__/../LogicPuzzles.py", package="main")
from main.LogicPuzzles import Category, Puzzle

PUZZLE_DEFS = {}

# Sunlight puzzle
SUNLIGHT_HOURS = Category("hours", ["2hr", "4hr", "6hr", "8hr"], True)
SUNLIGHT_PLANTS = Category(
    "plants", ["Tomato", "Spinach", "Cauliflower", "Pumpkin"], False
)
sunlight_puzzle = Puzzle([SUNLIGHT_HOURS, SUNLIGHT_PLANTS])

sunlight_hints = [
    {"is": [SUNLIGHT_PLANTS, "Tomato", SUNLIGHT_HOURS, "2hr"]},
    {
        "compound_or": [
            {"is": [SUNLIGHT_PLANTS, "Spinach", SUNLIGHT_HOURS, "4hr"]},
            {"is": [SUNLIGHT_PLANTS, "Tomato", SUNLIGHT_HOURS, "6hr"]},
        ]
    },
    {
        "before": [
            SUNLIGHT_PLANTS,
            "Tomato",
            SUNLIGHT_PLANTS,
            "Cauliflower",
            SUNLIGHT_HOURS,
            2,
        ]
    },
]
PUZZLE_DEFS["spoke_sunlight"] = {"puzzle": sunlight_puzzle, "hints": sunlight_hints}

sunlight_hints_alt = [
    {
        "simple_or": [
            SUNLIGHT_PLANTS,
            "Pumpkins",
            SUNLIGHT_PLANTS,
            "Cauliflower",
            SUNLIGHT_HOURS,
            "2h",
        ]
    },
    {
        "before": [
            SUNLIGHT_PLANTS,
            "Pumpkins",
            SUNLIGHT_PLANTS,
            "Spinach",
            SUNLIGHT_HOURS,
            1,
        ]
    },
    {
        "before": [
            SUNLIGHT_PLANTS,
            "Tomato",
            SUNLIGHT_PLANTS,
            "Spinach",
            SUNLIGHT_HOURS,
            2,
        ]
    },
]

PUZZLE_DEFS["spoke_sunlight_alt"] = {
    "puzzle": sunlight_puzzle,
    "hints": sunlight_hints_alt,
}

# Harvesting Order Puzzle
HARVEST_DAYS = Category("days", ["30", "60", "90", "120"], True)
HARVEST_PLANTS = Category(
    "plant", ["Potatoes", "Green Onions", "Eggplant", "Broccoli"], False
)
harvest_puzzle = Puzzle([HARVEST_DAYS, HARVEST_PLANTS])

harvest_hints = [
    {"is": [HARVEST_PLANTS, "Eggplant", HARVEST_DAYS, "60"]},
    {
        "before": [
            HARVEST_PLANTS,
            "Green Onions",
            HARVEST_PLANTS,
            "Eggplant",
            HARVEST_DAYS,
        ]
    },
    {
        "simple_or": [
            HARVEST_PLANTS,
            "Green Onions",
            HARVEST_PLANTS,
            "Potatoes",
            HARVEST_DAYS,
            "120",
        ]
    },
]
PUZZLE_DEFS["spoke_harvest"] = {"puzzle": harvest_puzzle, "hints": harvest_hints}

WATER_PLANTS = Category("plants", ["Green Onions", "Carrots", "Kale", "Potatoes"], False)
WATER_OZ = Category("amounts", ["20oz", "40oz", "60oz", "80oz"], True)
water_puzzle = Puzzle([WATER_PLANTS, WATER_OZ])

water_hints = [
    {"is": [WATER_PLANTS, "Carrots", WATER_OZ, "40oz"]},
    {
        "before": [
            WATER_PLANTS,
            "Green Onions",
            WATER_PLANTS,
            "Carrots",
            WATER_OZ,
        ]
    },
    {
        "simple_or": [
            WATER_PLANTS,
            "Green Onions",
            WATER_PLANTS,
            "Potatoes",
            WATER_OZ,
            "80oz",
        ]
    },
]
PUZZLE_DEFS["spoke_water"] = {"puzzle": water_puzzle, "hints": water_hints}

# Protein
PROTEIN_GRAMS = Category("grams", ["10g", "15g", "20g", "25g"], True)
PROTEIN_FOODS = Category("food", ["Fish", "Eggs", "Tofu", "Peanuts"], False)
protein_puzzle = Puzzle([PROTEIN_GRAMS, PROTEIN_FOODS])

protein_hints = [
    {"is": [PROTEIN_FOODS, "Eggs", PROTEIN_GRAMS, "15g"]},
    {"before": [PROTEIN_FOODS, "Fish", PROTEIN_FOODS, "Peanuts", PROTEIN_GRAMS, 1]},
]
PUZZLE_DEFS["spoke_protein"] = {"puzzle": protein_puzzle, "hints": protein_hints}

# Pasta
PASTA_SHAPES = Category("shapes", ["Elbow", "Bowtie", "Linguine", "Penne"], False)
PASTA_SAUCES = Category("sauces", ["Tomato", "Alfredo", "Pesto", "Carbonara"], False)
pasta_puzzle = Puzzle([PASTA_SHAPES, PASTA_SAUCES])

pasta_hints = [
    {
        "simple_or": [
            PASTA_SHAPES,
            "Elbow",
            PASTA_SHAPES,
            "Penne",
            PASTA_SAUCES,
            "Tomato",
        ]
    },
    {"is": [PASTA_SAUCES, "Alfredo", PASTA_SHAPES, "Penne"]},
    {
        "compound_or": [
            {"is": [PASTA_SAUCES, "Carbonara", PASTA_SHAPES, "Linguine"]},
            {"is": [PASTA_SHAPES, "Bowtie", PASTA_SAUCES, "Alfredo"]},
        ]
    },
]
PUZZLE_DEFS["spoke_pasta"] = {"puzzle": pasta_puzzle, "hints": pasta_hints}

# Hub
HUB_ORDER = Category("order", ["1st", "2nd", "3rd", "4th"], True)
HUB_QUANTITY = Category("cup", ["1 cup", "2 cups", "3 cups", "4 cups"], True)
HUB_FOOD = Category("ingredient", ["Beans", "Pasta", "Tomatoes", "Carrots"], False)
hub_puzzle = Puzzle([HUB_ORDER, HUB_QUANTITY, HUB_FOOD])

hub_hints = [
    {"before": [HUB_FOOD, "Pasta", HUB_FOOD, "Beans", HUB_ORDER, 2]},
    {"before": [HUB_FOOD, "Tomatoes", HUB_FOOD, "Beans", HUB_QUANTITY, 2]},
    {"is": [HUB_FOOD, "Tomatoes", HUB_ORDER, "4th"]},
    {"before": [HUB_FOOD, "Beans", HUB_FOOD, "Carrots", HUB_QUANTITY, 1]},
]

PUZZLE_DEFS["hub_soup"] = {"puzzle": hub_puzzle, "hints": hub_hints}

hub_hints_alt = [
    {"before": [HUB_FOOD, "Beans", HUB_FOOD, "Carrots", HUB_QUANTITY, 1]},
    {"simple_or": [HUB_QUANTITY, "2 cups", HUB_FOOD, "Beans", HUB_ORDER, "4th"]},
    {"before": [HUB_FOOD, "Beans", HUB_FOOD, "Carrots", HUB_ORDER, 2]},
    {"before": [HUB_FOOD, "Pasta", HUB_FOOD, "Carrots", HUB_QUANTITY, 2]},
]

PUZZLE_DEFS["hub_soup_alt"] = {"puzzle": hub_puzzle, "hints": hub_hints_alt}
