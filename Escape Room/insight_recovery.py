import pandas as pd
import ultraimport
from copy import deepcopy

ultraimport("__dir__/../LogicPuzzles.py", package="main")
from main.LogicPuzzles import (
    get_available_moves,
    get_move_diff,
    find_openings,
    Insight,
)
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
        result.answer(*u_move)
        u_move_diff = get_move_diff(puzzle, result, True)
        opened_puzzle = deepcopy(puzzle)
        find_openings(opened_puzzle)
        _, s_moves = get_available_moves(puzzle, hints, True)
        _, opened_moves = get_available_moves(opened_puzzle, hints, True)
        dedupe_moves = s_moves
        dedupe_o_moves = []
        for o_move in opened_moves:
            duplicate = False
            for s_move in s_moves:
                if (
                    o_move["type"] == s_move["type"]
                    and set(o_move["insights"]) == set(s_move["insights"])
                    and o_move["move_diff"].print_grid()
                    == s_move["move_diff"].print_grid()
                ):
                    duplicate = True
                    if "indexed_hint" in o_move and "indexed_hint" in s_move:
                        if o_move["indexed_hint"] != s_move["indexed_hint"]:
                            # Not same hint
                            duplicate = False
            if not duplicate:
                o_move["type"] = f"(after filling in openings) {o_move['type']}"
                dedupe_o_moves.append(o_move)
        dedupe_moves.extend(dedupe_o_moves)
        recovered = False
        r_move = {"move_diff": get_move_diff(puzzle, result), "possible_moves": []}
        for s_move in dedupe_moves:
            s_move_diff = s_move["move_diff"]
            if u_move_diff.print_grid() == s_move_diff.print_grid():
                poss_move = {
                    "type": s_move["type"],
                    "insights": s_move["insights"],
                }
                if "indexed_hint" in s_move:
                    poss_move["indexed_hint"] = s_move["indexed_hint"]
                r_move["possible_moves"].append(poss_move)
                recovered = True
        if not recovered:
            r_move["possible_moves"].append({
                "type": "unknown",
                "insights": [],
            })
        r_moves.append(r_move)
        puzzle = deepcopy(result)
    return r_moves


def apply_move(puzzle, move):
    diff = move["move_diff"]
    for cat1 in puzzle.left_right:
        for cat2 in puzzle.top_bottom:
            move_grid = diff.get_grid(cat1, cat2)
            if move_grid is None:
                continue
            for ent2_idx in range(0, len(move_grid)):
                for ent1_idx in range(0, len(move_grid[ent2_idx])):
                    if move_grid[ent2_idx][ent1_idx] != "*":
                        puzzle.answer(
                            cat1,
                            cat2,
                            cat1.entities[ent1_idx],
                            cat2.entities[ent2_idx],
                            move_grid[ent2_idx][ent1_idx],
                            False,
                        )


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
        clean_moves.append([PASTA_SHAPES, PASTA_SAUCES, entities[0], entities[1], "O"])

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
        terms = [SUNLIGHT_HOURS, SUNLIGHT_PLANTS, hr, plant]
        if len(plant_parts) == 3:
            terms.append("X")
            clean_moves.append(terms)
        else:
            terms.append("O")
            clean_moves.append(terms)

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
        clean_moves.append([WATER_PLANTS, WATER_OZ, plant, oz, "O"])

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
        terms = [PROTEIN_FOODS, PROTEIN_GRAMS, food, grams]
        if parts[1] == "Filled":
            terms.append("O")
            clean_moves.append(terms)
        else:
            terms.append("X")
            clean_moves.append(terms)

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
        terms = [HUB_FOOD, cat2, ingredient, ent2]

        match parts[1]:
            case "Filled GreenPin":
                terms.append("O")
                clean_moves.append(terms)
            case "Removed GreenPin":
                terms.append("X")
                clean_moves.append(terms)
            case "Filled RedPin":
                terms.append("X")
                clean_moves.append(terms)
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
        file.write(f"User Move {idx+1}:\n")
        board_str = move["move_diff"].print_grid().splitlines()
        for line in board_str:
            file.write(f"{line}\n")

        file.write("Possible Reasonings: \n")
        for i, poss_move in enumerate(move["possible_moves"]):
            typestr = poss_move["type"]
            if "indexed_hint" in poss_move:
                typestr += (
                    f" - \"{hint_to_english(poss_move['indexed_hint']['hint'])}\""
                )
            file.write(f"{i+1}: {typestr} - {poss_move['insights']}\n")

        file.write(f"\n\n")


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
    file = "user_data/vr_study/user_log.csv"
    raw_df = load_user_data(file)
    clean_data = clean_user_data(raw_df)
    for key, info in clean_data.items():
        recovered_moves = recover_moves(info["puzzle"], info["hints"], info["moves"])
        file = open("recovered_tree_{}.txt".format(key), "w")
        print_moves(file, info["puzzle"], info["hints"], recovered_moves)
