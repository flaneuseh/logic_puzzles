import pandas as pd
import ultraimport
from copy import deepcopy

ultraimport("__dir__/../LogicPuzzles.py", package="main")
from main.LogicPuzzles import apply_hint, get_available_moves, get_move_diff
from main.HintToEnglish import hint_to_english
from main.insight_tree import insights_to_string
from puzzle_defs import (
    PUZZLE_DEFS,
    PASTA_SHAPES,
    PASTA_SAUCES,
    SUNLIGHT_HOURS,
    SUNLIGHT_PLANTS,
    WATER_PLANTS,
    WATER_OZ,
    PROTEIN_FOODS,
    PROTEIN_GRAMS,
    HUB_FOOD,
    HUB_ORDER,
    HUB_QUANTITY,
)

# Analyze user data to hypothesize which insights participants used.


def recover_moves(puzzle, hints, u_moves):
    r_moves = []
    for u_move in u_moves:
        result = deepcopy(puzzle)
        apply_hint(result, u_move)
        u_move_diff = get_move_diff(puzzle, result)
        _, s_moves = get_available_moves(puzzle, hints)
        recovered = False
        for s_move in s_moves:
            s_move_diff = s_move["move_diff"]
            if u_move_diff.print_grid() == s_move_diff.print_grid():
                r_moves.append(s_move)
                recovered = True
        if not recovered:
            r_moves.append({
                "type": "unknown",
                "move_diff": u_move_diff,
                "result": deepcopy(result),
                "insights": [],
            })
        puzzle = deepcopy(result)
    return r_moves


def clean_user_data(raw_df):
    puzzle_name_mapping = {
        "spoke_pasta": "Pasta in Sauce",
        "spoke_sunlight": "Amount of Sunlight",
        "spoke_water": "Water Amount",
        "spoke_protein": "Amount of Protein",
        "hub_soup": "Cooking Pot",
    }

    clean_data = {
        "spoke_pasta": [],
        "spoke_sunlight": [],
        "spoke_water": [],
        "spoke_protein": [],
        "hub_soup": [],
    }

    for [clean_key, raw_key] in puzzle_name_mapping.items():
        raw_puzzle_df = raw_df[raw_df["ParentChain"].str.contains(raw_key)].copy()
        raw_moves = raw_puzzle_df["PuzzleUniqueID"].tolist()
        clean_data[clean_key] = clean_puzzle_moves(clean_key, raw_moves)

    return clean_data


def clean_puzzle_moves(clean_key, raw_moves):
    match clean_key:
        case "spoke_pasta":
            return _clean_puzzle_moves__spoke_pasta(raw_moves)
        case "spoke_sunlight":
            return _clean_puzzle_moves__spoke_sunlight(raw_moves)
        case "spoke_water":
            return _clean_puzzle_moves__spoke_water(raw_moves)
        case "spoke_protein":
            return _clean_puzzle_moves__spoke_protein(raw_moves)
        case "hub_soup":
            return _clean_puzzle_moves__hub_soup(raw_moves)
        case _:
            return []


def _clean_puzzle_moves__spoke_pasta(raw_moves):
    puzzle = PUZZLE_DEFS["spoke_pasta"]["puzzle"]
    hints = PUZZLE_DEFS["spoke_pasta"]["hints"]
    clean_moves = []

    for raw_move in raw_moves:
        entities = raw_move.split("Pasta Bowl - ")
        if len(entities) == 1:
            entities = raw_move.split("Pata Bowl - ")
        clean_moves.append(
            {"is": [PASTA_SHAPES, entities[0], PASTA_SAUCES, entities[1]]}
        )

    return {
        "puzzle": puzzle,
        "hints": hints,
        "moves": clean_moves,
    }


def _clean_puzzle_moves__spoke_sunlight(raw_moves):
    puzzle = PUZZLE_DEFS["spoke_sunlight"]["puzzle"]
    hints = PUZZLE_DEFS["spoke_sunlight"]["hints"]
    clean_moves = []

    for raw_move in raw_moves:
        parts = raw_move.split(" - ")
        if len(parts) < 2:
            continue
        hr_parts = parts[0].split("Snap Area ")
        hr = hr_parts[-1]
        plant_parts = parts[1].split(" ")
        plant = plant_parts[1]
        terms = [SUNLIGHT_HOURS, hr, SUNLIGHT_PLANTS, plant]
        if len(plant_parts) == 3:
            clean_moves.append({"not": [{"is": terms}]})
        else:
            clean_moves.append({"is": terms})

    return {
        "puzzle": puzzle,
        "hints": hints,
        "moves": clean_moves,
    }


def _clean_puzzle_moves__spoke_water(raw_moves):
    puzzle = PUZZLE_DEFS["spoke_water"]["puzzle"]
    hints = PUZZLE_DEFS["spoke_water"]["hints"]
    clean_moves = []

    for raw_move in raw_moves:
        parts = raw_move.split(" Valve Combo - ")
        plant = parts[0]
        match plant:
            case "GreenOnion":
                plant = "Green Onions"
            case "Potato":
                plant = "Potatoes"
            case "Carrot":
                plant = "Carrots"
        if plant == "GreenOnion":
            plant = "Green Onions"
        oz_parts = parts[1].split("Oz")
        oz_str = oz_parts[0]
        oz = ""
        match oz_str:
            case "Twenty":
                oz = "20oz"
            case "Forty":
                oz = "40oz"
            case "Sixty":
                oz = "60oz"
            case "Eighty":
                oz = "80oz"
            case _:
                continue
        clean_moves.append({"is": [WATER_PLANTS, plant, WATER_OZ, oz]})

    return {
        "puzzle": puzzle,
        "hints": hints,
        "moves": clean_moves,
    }


def _clean_puzzle_moves__spoke_protein(raw_moves):
    puzzle = PUZZLE_DEFS["spoke_protein"]["puzzle"]
    hints = PUZZLE_DEFS["spoke_protein"]["hints"]
    clean_moves = []

    for raw_move in raw_moves:
        parts = raw_move.split(" - ")
        entity_parts = parts[0].split(" Token Socket ")
        food = entity_parts[0]
        if food == "Penuts":
            food = "Peanuts"
        grams_idx = int(entity_parts[1].strip("()")) - 1
        grams = PROTEIN_GRAMS.entities[grams_idx]
        terms = [PROTEIN_FOODS, food, PROTEIN_GRAMS, grams]
        if parts[1] == "Filled":
            clean_moves.append({"is": terms})
        else:
            clean_moves.append({"not": [{"is": terms}]})

    return {
        "puzzle": puzzle,
        "hints": hints,
        "moves": clean_moves,
    }


def _clean_puzzle_moves__hub_soup(raw_moves):
    puzzle = PUZZLE_DEFS["hub_soup_alt"]["puzzle"]
    hints = PUZZLE_DEFS["hub_soup_alt"]["hints"]
    clean_moves = []

    for raw_move in raw_moves:
        parts = raw_move.split(" - ")
        entity_parts = parts[0].split(" ")
        ingredient = entity_parts[0]
        match ingredient:
            case "Carrot":
                ingredient = "Carrots"
            case "Tomato":
                ingredient = "Tomatoes"
        cat2 = None
        match entity_parts[1]:
            case "Amount":
                cat2 = HUB_QUANTITY
            case "Order":
                cat2 = HUB_ORDER
            case _:
                continue
        cat2_idx = int(entity_parts[3].strip("()")) - 1
        ent2 = cat2.entities[cat2_idx]
        terms = [HUB_FOOD, ingredient, cat2, ent2]

        match parts[1]:
            case "Filled GreenPin":
                clean_moves.append({"is": terms})
            case "Removed GreenPin":
                clean_moves.append({"not": [{"is": terms}]})
            case "Filled RedPin":
                clean_moves.append({"not": [{"is": terms}]})
            case _:
                continue

    return {
        "puzzle": puzzle,
        "hints": hints,
        "moves": clean_moves,
    }


def print_moves(file, puzzle, hints, moves):
    file.write("Puzzle:\n")
    file.write(puzzle.print_grid())
    file.write("Hints:\n")
    for hint in hints:
        file.write(hint_to_english(hint) + "\n")
    file.write("\n")

    for idx, move in enumerate(moves):
        file.write(f"user move {idx}:\n")
        board_str = move["move_diff"].print_grid().splitlines()
        for line in board_str:
            file.write(f"{line}\n")
        file.write(f"predicted move type: ")
        if "indexed_hint" in move:
            hint = move["indexed_hint"]["hint"]
            file.write(f'hint - "{hint_to_english(hint)}"\n')
        else:
            file.write(f"{move['type']}\n")
        file.write(f"predicted insights: ")
        insights = move["insights"]
        if len(insights) == 0:
            file.write("unknown\n")
        file.write(f"{insights_to_string(insights)}\n\n")


def load_user_data(file):
    df = pd.read_csv(file)

    df = df[df["ElementType"] == "Interaction"].copy()
    df = df[df["Outcome"] != "WrongMove"].copy()
    df = df.drop(
        columns=[
            "TimeStampUTC",
            "TimeFromLastMove",
            "ElementType",
            "IsCompleted",
            "Outcome",
        ]
    )

    return df


if __name__ == "__main__":
    file = "user_log.csv"
    raw_df = load_user_data(file)
    clean_data = clean_user_data(raw_df)
    for key, info in clean_data.items():
        recovered_moves = recover_moves(info["puzzle"], info["hints"], info["moves"])
        file = open("recovered_tree_{}.txt".format(key), "w")
        print_moves(file, info["puzzle"], info["hints"], recovered_moves)
