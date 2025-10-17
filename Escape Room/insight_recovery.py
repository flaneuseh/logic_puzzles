import pandas as pd
import ultraimport
from copy import deepcopy
import os
import json
import re
from pathlib import Path

ultraimport("__dir__/../LogicPuzzles.py", package="main")
from main.LogicPuzzles import (
    get_available_moves,
    get_move_diff,
    find_openings,
    apply_hints,
    Category,
    Puzzle,
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


# Determine whether move is correct, incorrect, or neutral.
def get_move_value(move_diff, hints):
    value = ""
    solution, _, _, _ = apply_hints(move_diff, hints)
    for cat1 in move_diff.left_right:
        for cat2 in move_diff.top_bottom:
            diff_grid = move_diff.get_grid(cat1, cat2)
            soln_grid = solution.get_grid(cat1, cat2)
            if diff_grid is None or soln_grid is None:
                continue
            for ent2_idx in range(0, len(diff_grid)):
                for ent1_idx in range(0, len(diff_grid[ent2_idx])):
                    diff_cell = diff_grid[ent2_idx][ent1_idx]
                    soln_cell = soln_grid[ent2_idx][ent1_idx]
                    if diff_cell in ["_", "X", "O"]:
                        # Part of the current move.
                        if diff_cell == "_" and value not in ["Correct", "Incorrect"]:
                            value = "Neutral"
                        elif diff_cell != soln_cell:
                            value = "Incorrect"
                        elif value != "Incorrect":
                            value = "Correct"

    return value


# Analyze user data to hypothesize which insights participants used.
def recover_moves(puzzle, hints, u_moves):
    r_moves = []
    for raw_move, rec_moves in u_moves:
        result = deepcopy(puzzle)
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
        possible_moves = []
        temp = deepcopy(result)
        for move in rec_moves:
            result.answer(*move)
            u_move_diff, changed = get_move_diff(temp, result, True)
            temp = deepcopy(result)
            if changed:
                if len(rec_moves) == 1 or move[-1] == "O":
                    for s_move in dedupe_moves:
                        s_move_diff = s_move["move_diff"]
                        if u_move_diff.print_grid() == s_move_diff.print_grid():
                            poss_move = {
                                "type": s_move["type"],
                                "insights": s_move["insights"],
                                "repair": s_move["repair"],
                            }
                            if "indexed_hint" in s_move:
                                poss_move["indexed_hint"] = s_move["indexed_hint"]
                            possible_moves.append(poss_move)
                            recovered = True
        if not recovered:
            possible_moves.append({
                "type": "unknown",
                "insights": [],
                "repair": False,
            })

        u_move_diff, _ = get_move_diff(puzzle, result)
        r_move = {
            "move_diff": u_move_diff,
            "possible_moves": possible_moves,
            "value": get_move_value(u_move_diff, hints),
        }
        r_moves.append((raw_move, r_move))
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


def clean_online_moves(puzzle, raw_moves):
    puzzle = deepcopy(puzzle)
    clean_moves = []
    raw_moves = list(filter(lambda rm: rm["type"] == "cellChange", raw_moves))
    raw_moves = sorted(raw_moves, key=lambda m: m["time"])
    for _, raw_move in enumerate(raw_moves):
        moves = []
        puzzle_str = raw_move["puzzleState"]
        topdown_rows = re.split("-+", puzzle_str)
        topdown_rows = list(filter(lambda tdr: len(tdr) > 0, topdown_rows))
        for tdr, topdown_row in enumerate(topdown_rows):
            cat1 = puzzle.top_bottom[tdr]
            rows = topdown_row.split("\n")
            rows = list(filter(lambda r: len(r) > 0, rows))
            for r, row in enumerate(rows):
                ent1 = cat1.entities[r]
                leftright_rows = row.split("|")
                leftright_rows = list(filter(lambda cr: len(cr) > 0, leftright_rows))
                for lrr, leftright_row in enumerate(leftright_rows):
                    cat2 = puzzle.left_right[lrr]
                    symbols = list(leftright_row)
                    for s, new_symbol in enumerate(symbols):
                        if new_symbol == "?":
                            new_symbol = "N"
                        elif new_symbol == "!":
                            new_symbol = "Y"
                        ent2 = cat2.entities[s]
                        old_symbol = puzzle.get_symbol(cat1, cat2, ent1, ent2)
                        if old_symbol != new_symbol:
                            moves.append([cat1, cat2, ent1, ent2, new_symbol])
        for move in moves:
            puzzle.answer(*move)

        clean_moves.append((puzzle_str, moves))
    return clean_moves


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
        if len(entities) == 1:
            entities = raw_move.split("Pata Bowl  - ")
        if len(entities) == 1:
            entities = raw_move.split("Pasta Bowl  - ")

        moves = []
        if entities[1] == "Reset":
            for sauce in PASTA_SAUCES.entities:
                moves.append([PASTA_SHAPES, PASTA_SAUCES, entities[0], sauce, "*"])
        else:
            for sauce in PASTA_SAUCES.entities:
                move = [PASTA_SHAPES, PASTA_SAUCES, entities[0], sauce]
                if sauce == entities[1]:
                    move.append("O")
                else:
                    # Each pasta can only have one sauce at a time.
                    move.append("X")
                moves.append(move)
        clean_moves.append((raw_move, moves))

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
            print(f"Unable to process move: {raw_move}")
            continue
        hr_parts = parts[0].split(" ")
        hr = hr_parts[1].strip("s")
        plant_parts = parts[1].split(" ")
        plant = ""
        if len(plant_parts) < 2:
            plant = plant_parts[0]
        else:
            plant = plant_parts[1]
        if plant not in SUNLIGHT_PLANTS.entities:
            print(f"Unable to process move: {raw_move}")
            continue
        moves = []
        if len(plant_parts) == 3:
            for h in SUNLIGHT_HOURS.entities:
                moves.append([SUNLIGHT_HOURS, SUNLIGHT_PLANTS, h, plant, "*"])
        else:
            for h in SUNLIGHT_HOURS.entities:
                move = [SUNLIGHT_HOURS, SUNLIGHT_PLANTS, h, plant]
                if h == hr:
                    move.append("O")
                else:
                    move.append("X")
                moves.append(move)

        clean_moves.append((raw_move, moves))

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
        moves = []
        for o in ["20oz", "40oz", "60oz", "80oz"]:
            move = [WATER_PLANTS, WATER_OZ, plant, o]
            if o == oz:
                move.append("O")
            else:
                move.append("X")
            moves.append(move)
        clean_moves.append((raw_move, moves))

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
        move = [PROTEIN_FOODS, PROTEIN_GRAMS, food, grams]
        if parts[1] == "Filled":
            move.append("O")
        else:
            move.append("*")

        clean_moves.append((raw_move, [move]))

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
        ent1 = ""
        ent2 = ""
        cat1 = None
        cat2 = None
        cat2_idx = 0
        if entity_parts[0] == "Amount":
            cat1 = HUB_QUANTITY
            cat1_idx = int(entity_parts[1]) - 1
            ent1 = cat1.entities[cat1_idx]
            cat2_idx = 3
        elif entity_parts[0] in set(HUB_FOOD.entities) | {"Carrot", "Tomato"}:
            cat1 = HUB_FOOD
            ent1 = entity_parts[0]
            match ent1:
                case "Carrot":
                    ent1 = "Carrots"
                case "Tomato":
                    ent1 = "Tomatoes"
            cat2_idx = 1

        ent2_ent_idx = cat2_idx + 2
        match entity_parts[cat2_idx]:
            case "Amount":
                cat2 = HUB_QUANTITY
            case "Order":
                cat2 = HUB_ORDER
            case "OrderSpot":
                cat2 = HUB_ORDER
                ent2_ent_idx -= 1
            case _:
                print(f"Unable to process move: {raw_move}")
                continue

        ent2_idx = int(entity_parts[ent2_ent_idx].strip("()")) - 1
        ent2 = cat2.entities[ent2_idx]

        move = [cat1, cat2, ent1, ent2]
        match parts[1]:
            case "Filled GreenPin":
                move.append("O")
            case "Removed GreenPin":
                move.append("*")
            case "Filled RedPin":
                move.append("X")
            case "Removed RedPin":
                move.append("*")
            case _:
                continue

        clean_moves.append((raw_move, [move]))

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

    for idx, (raw_move, move) in enumerate(moves):
        if move == None:
            file.write(f"User Move {idx+1} (Wrong, Ignored): {raw_move}\n")
        else:
            file.write(f"User Move {idx+1} ({move['value']}): {raw_move}\n")
            board_str = move["move_diff"].print_grid().splitlines()
            for line in board_str:
                file.write(f"{line}\n")

            file.write("Possible Reasonings: \n")
            for i, poss_move in enumerate(move["possible_moves"]):
                typestr = poss_move["type"]
                if poss_move["repair"]:
                    typestr += " (repair)"
                    print("!!repair move used!!")
                if "indexed_hint" in poss_move:
                    typestr += (
                        f" - \"{hint_to_english(poss_move['indexed_hint']['hint'])}\""
                    )
                file.write(f"{i+1}: {typestr} - {poss_move['insights']}\n")

        file.write(f"\n\n")


def load_user_data(file):
    df = pd.read_csv(file)

    df = df[df["ElementType"] == "Interaction"].copy()
    # df = df[df["Outcome"] != "WrongMove"].copy()
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


def load_online_data(dir):
    action_json = None
    with open(f"{dir}/action_data.json") as f:
        action_json = json.load(f)
    gameplay_df = pd.read_csv(f"{dir}/gameplay_data.csv")
    puzzle_names = [
        "helper1_2",
        "helper1_3",
        "helper2_2",
        "helper2_3",
        "one_loop_puzzle1",
        "one_loop_puzzle2",
        "one_loop_puzzle3",
        "spoke1_1",
        "spoke1_2",
        "spoke1_3",
        "spoke2_1",
        "spoke2_2",
        "spoke2_3",
    ]

    puzzles = {}
    for name in puzzle_names:
        puzzle_json = None
        with open(f"{dir}/{name}.json") as f:
            puzzle_json = json.load(f)
        categories = []
        for cat_json in puzzle_json["categories"]:
            categories.append(
                Category(cat_json["name"], cat_json["entities"], cat_json["is_numeric"])
            )
        raw_hints = puzzle_json["hint_grammar"]
        hints = []
        for raw_hint in raw_hints:
            hint = {}
            rule = list(raw_hint.keys())[0]
            terms = raw_hint[rule]
            if rule == "is":
                cat1 = None
                cat2 = None
                cat1_name = terms[0]
                ent1 = terms[1]
                cat2_name = terms[2]
                ent2 = terms[3]
                for cat in categories:
                    if cat.title == cat1_name:
                        cat1 = cat
                    if cat.title == cat2_name:
                        cat2 = cat
                hint = {"is": [cat1, ent1, cat2, ent2]}
            elif rule == "not":
                terms = terms[0]["is"]
                cat1 = None
                cat2 = None
                cat1_name = terms[0]
                ent1 = terms[1]
                cat2_name = terms[2]
                ent2 = terms[3]
                for cat in categories:
                    if cat.title == cat1_name:
                        cat1 = cat
                    if cat.title == cat2_name:
                        cat2 = cat
                hint = {"not": [{"is": [cat1, ent1, cat2, ent2]}]}
            elif rule == "before":
                bef_cat = None
                bef_cat_name = terms[0]
                aft_cat = None
                aft_cat_name = terms[2]
                num_cat = None
                bef_ent = terms[1]  
                aft_ent = terms[3]
                num_cat_name = terms[4]
                for cat in categories:
                    if cat.title == bef_cat_name:
                        bef_cat = cat
                    if cat.title == aft_cat_name:
                        aft_cat = cat
                    if cat.title == num_cat_name:
                        num_cat = cat
                num = 1
                if len(terms) == 6:
                    num = terms[5]
                hint = {"before": [bef_cat, bef_ent, aft_cat, aft_ent, num_cat, num]}
            elif rule == "simple_or":
                pos_cat1 = None
                pos_cat1_name = terms[0]
                pos_ent1 = terms[1]  
                pos_cat2 = None
                pos_cat2_name = terms[2]
                pos_ent2 = terms[3]
                ans_cat = None
                ans_cat_name = terms[4]
                ans_ent = terms[5]
                for cat in categories:
                    if cat.title == pos_cat1_name:
                        pos_cat1 = cat
                    if cat.title == pos_cat2_name:
                        pos_cat2 = cat
                    if cat.title == ans_cat_name:
                        ans_cat = cat
                hint = {"simple_or": [pos_cat1, pos_ent1, pos_cat2, pos_ent2, ans_cat, ans_ent]}
            elif rule == "compound_or":
                optionA_terms = terms[0]["is"]
                catA1 = None
                catA1_name = optionA_terms[0]
                entA1 = optionA_terms[1]
                catA2 = None
                catA2_name = optionA_terms[2]
                entA2 = optionA_terms[3]

                optionB_terms = terms[1]["is"]
                catB1 = None
                catB1_name = optionB_terms[0]
                entB1 = optionB_terms[1]
                catB2 = None
                catB2_name = optionB_terms[2]
                entB2 = optionB_terms[3]

                for cat in categories:
                    if cat.title == catA1_name:
                        catA1 = cat
                    if cat.title == catA2_name:
                        catA2 = cat
                    if cat.title == catB1_name:
                        catB1 = cat
                    if cat.title == catB2_name:
                        catB2 = cat
                
                optionA = [catA1, entA1, catA2, entA2]
                optionB = [catB1, entB1, catB2, entB2]
                hint = {"compound_or": [{"is": optionA}, {"is": optionB}]}
            hints.append(hint)

        puzzles[puzzle_json["id"]] = {
            "puzzle": Puzzle(categories),
            "hints": hints,
        }

    clean_data = {}
    gameplay_df = (
        gameplay_df.reset_index()
    )  # make sure indexes pair with number of rows
    for _, row in gameplay_df.iterrows():
        session_id = row["_id"]
        if session_id not in action_json:
            continue
        raw_moves = action_json[session_id]
        puzzle_id = row["pid"]
        if puzzle_id not in puzzles:
            continue
        puzzle = puzzles[puzzle_id]["puzzle"]
        hints = puzzles[puzzle_id]["hints"]
        clean_data[session_id] = {
            "puzzle_id": puzzle_id,
            "puzzle": puzzle,
            "hints": hints,
            "moves": clean_online_moves(puzzle, raw_moves),
        }
    return clean_data


if __name__ == "__main__":
    # vr_dir = "user_data/vr_study"
    # vr_users = [f.name for f in os.scandir("user_data/vr_study") if f.is_dir()]
    # for user in vr_users:
    #     print(user)
    #     userfile = f"{vr_dir}/{user}/{user}_PuzzleLogs.csv"
    #     raw_df = load_user_data(userfile)
    #     clean_data = clean_user_data(raw_df)
    #     for key, info in clean_data.items():
    #         print(key)
    #         recovered_moves = recover_moves(
    #             info["puzzle"], info["hints"], info["moves"]
    #         )
    #         move_file = open(f"{vr_dir}/{user}/recovered_tree_{key}.txt", "w")
    #         print_moves(move_file, info["puzzle"], info["hints"], recovered_moves)

    online_dir = "user_data/online_puzzle_study"
    clean_data = load_online_data(online_dir)
    for session_id, session in clean_data.items():
        print(session_id)
        recovered_moves = recover_moves(
            session["puzzle"], session["hints"], session["moves"]
        )
        output_path = f"{online_dir}/recovered_trees/{session['puzzle_id']}/recovered_{session_id}.txt"
        output_file = Path(output_path)
        output_file.parent.mkdir(exist_ok=True, parents=True)
        move_file = open(output_path, "w")
        print_moves(move_file, session["puzzle"], session["hints"], recovered_moves)
