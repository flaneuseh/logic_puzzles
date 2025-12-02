import pandas as pd
import ultraimport
from copy import deepcopy
import os
import json
import re
from pathlib import Path
import csv
from random import randint

ultraimport("__dir__/../LogicPuzzles.py", package="main")
from main.LogicPuzzles import (
    get_available_moves,
    get_move_diff,
    find_openings,
    apply_hints,
    Category,
    Puzzle,
    Insight,
    apply_move,
    repair,
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

def replace_sy(puzzle, loc, sy):
    (cat1, cat2, ent1_idx, ent2_idx) = loc
    puzzle.answer(
        cat1, cat2, cat1.entities[ent1_idx], cat2.entities[ent2_idx], sy
    )
    return puzzle

def get_diff_sy(diff):
    for cat1 in diff.left_right:
        for cat2 in diff.top_bottom:
            grid = diff.get_grid(cat1, cat2)
            if grid is None:
                continue
            for ent2_idx in range(0, len(grid)):
                for ent1_idx in range(
                    0, len(grid[ent2_idx])
                ):
                    sy = grid[ent2_idx][ent1_idx]
                    if sy in ["X", "O", "Y", "N", "_"]:
                        return (cat1, cat2, ent1_idx, ent2_idx), sy
    return None, None

# def update_state_df(
#     node_df,
#     edge_df,
#     grid_to_label,
#     label_to_grid,
#     puzzle_id,
#     puzzle,
#     hints,
#     moves,
#     user_id,
#     prompt_mode,
#     level_mode,
# ):
#     source_state = puzzle
#     source_grid_id = f"{puzzle_id}:{source_state.print_grid()}"
#     if source_grid_id not in grid_to_label:
#         label = randint(10000, 99999)
#         while label in label_to_grid:
#             label = randint(10000, 99999)
#         label_to_grid[label] = source_grid_id
#         grid_to_label[source_grid_id] = label
#         node_row = [label, label, puzzle_id, source_grid_id, "start"]
#         node_df.loc[len(node_df)] = node_row
#     source_label = grid_to_label[source_grid_id]

#     if len(moves) == 0:
#         return
#     user_success = "failure"
#     _, final_move = moves[-1]
#     final_state = final_move["puzzle_state"]
#     solution, _, _, _ = apply_hints(puzzle, hints)
#     correct = not repair(final_state, solution)
#     if correct:
#         if is_solved(final_state):
#             user_success = "success"
#         else:
#             user_success = "partial"
#     for _, move in moves:
#         target_grid_id = f'{puzzle_id}:{move["board_state"]}'
#         target_state = move["puzzle_state"]
#         value = ""
#         if target_grid_id not in grid_to_label:
#             label = randint(10000, 99999)
#             while label in label_to_grid:
#                 label = randint(10000, 99999)
#             label_to_grid[label] = target_grid_id
#             grid_to_label[target_grid_id] = label
#             correct = not repair(target_state, solution)
#             if correct:
#                 if (is_solved(target_state)):
#                     value = "solved"
#                 else:
#                     value = "correct"
#             else:
#                 if (not target_state.is_valid()):
#                     value = "impossible"
#                 value = "incorrect"
#             node_row = [label, label, puzzle_id, target_grid_id, value]
#             node_df.loc[len(node_df)] = node_row
#         target_label = grid_to_label[target_grid_id]

#         solver_value = "insight"
#         if move["possible_moves"][0]["type"] == "unknown":
#             solver_value = "unknown"
#         else:
#             if move["possible_moves"][0]["violation"]:
#                 solver_value = "violation"
#             elif move["possible_moves"][0]["repair"]:
#                 solver_value = "repair"
#         edge_row = [
#             source_label,
#             target_label,
#             user_id,
#             user_success,
#             solver_value,
#             move["value"],
#             prompt_mode,
#             level_mode,
#         ]
#         edge_df.loc[len(edge_df)] = edge_row  # adding a row
#         source_label = target_label

def add_node(puzzle_id, grid_id, value, grid_to_label, node_df):
    if grid_id in grid_to_label:
        print("!!caught node duplicate")
        return grid_to_label[grid_id]
    node_id = randint(10000, 99999)
    while node_id in grid_to_label.values():
        node_id = randint(10000, 99999)
    if node_id in grid_to_label.values():
        print("!! confused :(")
    grid_to_label[grid_id] = node_id
    node_row = [node_id, puzzle_id, grid_id, value]
    if ((node_df["Id"] == node_id)).any():
        print("!!duplicate not caught....")
    node_df.loc[len(node_df)] = node_row
    return node_id
    
def get_max_insight(move):
    max_insight = Insight.NO_INSIGHT
    for insight in move["insights"]:
        if insight.value > max_insight.value:
            max_insight = insight
    return max_insight

def get_grid_id(puzzle_id, state):
    # Treat the unopened and opened state as equivalent
    opened_state = deepcopy(state)
    find_openings(opened_state)
    grid_str = opened_state.print_grid()
    grid_id = f"{puzzle_id}:{grid_str}"
    return grid_id

# Analyze user data to hypothesize which insights participants used.
def recover_moves(puzzle, hints, user_id, prompt_mode, level_mode, u_moves, u_success, grid_to_label, node_df, edge_df):
    
    # Empty state node.
    source_state = puzzle
    source_grid_id = f"{puzzle_id}:{source_state.print_grid()}"
    if source_grid_id not in grid_to_label:
        add_node(puzzle_id, source_grid_id, "start", grid_to_label, node_df)
    source_label = grid_to_label[source_grid_id]
    solution, _, _, _ = apply_hints(puzzle, hints)

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
                    and o_move["insights"] == s_move["insights"]
                    and o_move["move_diff"].print_grid()
                    == s_move["move_diff"].print_grid()
                ):
                    if "indexed_hint" in o_move and "indexed_hint" in s_move:
                        o_move_hint = hint_to_english(o_move["indexed_hint"]["hint"])
                        s_move_hint = hint_to_english(s_move["indexed_hint"]["hint"])
                        if o_move_hint != s_move_hint:
                            # Not same hint
                            continue
                    duplicate = True
                    break
            if not duplicate:
                o_move["type"] = f"(after filling in openings) {o_move['type']}"
                dedupe_o_moves.append(o_move)
        dedupe_moves.extend(dedupe_o_moves)

        # Moves that reach the same grid state are collapsed to only the move with the lowest ranked insight
        collapsed_moves = {}
        for s_move in dedupe_moves:
            state = s_move["result"]
            grid_id = get_grid_id(puzzle_id, state)
            max_insight = get_max_insight(s_move)
            
            if grid_id not in collapsed_moves or max_insight.value < collapsed_moves[grid_id]["max_insight"].value:
                # Keep the move with the lowest ranked insight
                type = s_move["type"]
                opened_state = deepcopy(state)
                find_openings(opened_state)
                correct = not repair(opened_state, solution)
                grid_value = "correct"
                if not correct:
                    grid_value = "incorrect"
                collapsed_moves[grid_id] = {
                    "type": type,
                    "max_insight": max_insight,
                    "move_diff": s_move["move_diff"],
                    "state": opened_state,
                    "grid_value": grid_value
                }
                if "indexed_hint" in s_move:
                    hint = hint_to_english(s_move["indexed_hint"]["hint"])
                    collapsed_moves[grid_id]["hint"] = hint
                if s_move["repair"]:
                    collapsed_moves[grid_id]["solver_value"] = "repair"
                else:
                    collapsed_moves[grid_id]["solver_value"] = "insight"


        for c_move in collapsed_moves.copy().values():
            # Find alternative states by setting the changed symbol to the other options.
            # This is either overconfidence (e.g. marking O when the solver would mark Y), 
            # uncertainty (e.g. marking Y when the solver would mark O), or
            # contradiction (e.g. marking X when the solver would mark O).
            # Contradictions are lowest ranked, as our primary goal is to determine the thought
            # process of the user, and they represent an unknown thought process. We keep them 
            # as different states arising from the same contradiction at the same time can be considered as equivalent.
            move_diff = c_move["move_diff"]
            move_state = c_move["state"]
            diff_loc, diff_sy = get_diff_sy(move_diff)
            alt_moves = {}
            if diff_sy == "O":
                alt_moves["X"] = "contradiction"
                alt_moves["Y"] = "uncertain"
                alt_moves["N"] = "contradiction"
            elif diff_sy == "X":
                alt_moves["O"] = "contradiction"
                alt_moves["Y"] = "contradiction"
                alt_moves["N"] = "uncertain"
            elif diff_sy == "Y":
                alt_moves["O"] = "overconfident"
                # Since this is an uncertain move, don't mark a contradiction.
            # The solver never marks "N"

            for alt_sy, solver_value in alt_moves.items():
                alt_diff = replace_sy(move_diff, diff_loc, alt_sy)
                alt_state = replace_sy(move_state, diff_loc, alt_sy)
                alt_move = deepcopy(c_move)
                alt_move["solver_value"] = solver_value
                alt_move["move_diff"] = alt_diff
                alt_move["state"] = alt_state
                alt_move["og_sy"] = diff_sy
                correct = not repair(alt_state, solution)
                grid_value = "correct"
                if not correct:
                    grid_value = "incorrect"
                alt_move["grid_value"] = grid_value

                grid_id = get_grid_id(puzzle_id, alt_state)
                if grid_id not in collapsed_moves:
                    collapsed_moves[grid_id] = alt_move
                else:
                    # Collapse equivalent grid ids, taking into account the confidence of the respective moves 
                    # as well as their insight rankings.
                    ex_move = collapsed_moves[grid_id]
                    ex_solver_value = ex_move["solver_value"]
                    alt_solver_value = alt_move["solver_value"]
                    ex_max_insight = ex_move["max_insight"]
                    alt_max_insight = alt_move["max_insight"]
                    if "og_sy" in ex_move:
                        # The comparison move is also an alternative.
                        if diff_sy == ex_move["og_sy"]:
                            # Take the lower ranked insight for the same alternative to the same original
                            if alt_max_insight.value < ex_max_insight.value:
                                collapsed_moves[grid_id] = alt_move
                            continue
                        if alt_solver_value != ex_solver_value:
                            if alt_solver_value in ["overconfident", "uncertain"]:
                                # ex_solver_value must be "contradiction", as they have the same symbol (uncertain marks may not be overconfident; X and O cannot be uncertain)
                                collapsed_moves[grid_id] = alt_move
                                continue
                        else:
                            # If they have the same confidence, take the lower ranked insight of the two.
                            if alt_max_insight.value < ex_max_insight.value:
                                collapsed_moves[grid_id] = alt_move
                            
                    else:
                        if alt_sy in ["O", "X"]:
                            # The move matches an insight already discovered by the solver, give credit to that insight.
                            continue

                        if alt_solver_value == "uncertain":
                            # When the solver and the move are both uncertain, use the lowest ranked insight.
                            if alt_max_insight.value < ex_max_insight.value:
                                collapsed_moves[grid_id] = alt_move
                                continue
                        # Otherwise, the solver is uncertain and the move is a contradiction, follow the rules of contradictions and keep the uncertain move.

        # Find collapsed moves that are equivalent (same type, insight, hint, and solver_value)
        equivalent_moves = {}
        for grid_id, c_move in collapsed_moves.items():
            type = c_move["type"]
            max_insight = c_move["max_insight"]
            hint = ""
            if "hint" in c_move:
                hint = c_move["hint"]
            solver_value = c_move["solver_value"]
            equiv_id = f"{type}:{max_insight}:{hint}:{solver_value}"
            if equiv_id not in equivalent_moves:
                equivalent_moves[equiv_id] = []
            equivalent_moves[equiv_id].append(grid_id)

        # Find or create the node representing this state.
        for equiv_id, grid_ids in equivalent_moves.items():
            label = ""
            for grid_id in grid_ids:
                # Check whether the grid can be added to existing equivalent nodes.
                if grid_id in grid_to_label:
                    if label != "" and label != grid_to_label[grid_id]:
                        print("!!there are multiple labels that could apply to one grid!!")
                    label = grid_to_label[grid_id]
                    
            if label == "":
                grid_value = collapsed_moves[grid_ids[0]]["grid_value"]
                label = add_node(puzzle_id, grid_ids[0], grid_value, grid_to_label, node_df)
            for grid_id in grid_ids:
                grid_to_label[grid_id] = label

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
                        for cat1 in puzzle.left_right:
                            for cat2 in puzzle.top_bottom:
                                u_move_grid = u_move_diff.get_grid(cat1, cat2)
                                s_move_grid = s_move_diff.get_grid(cat1, cat2)
                                if u_move_grid is None or s_move_grid is None:
                                    continue
                                for ent2_idx in range(0, len(u_move_grid)):
                                    for ent1_idx in range(
                                        0, len(u_move_grid[ent2_idx])
                                    ):
                                        u_move_sy = u_move_grid[ent2_idx][ent1_idx]
                                        s_move_sy = s_move_grid[ent2_idx][ent1_idx]
                                        if u_move_sy != "*" and s_move_sy != "*":
                                            # The moves affect the same grid location
                                            if (
                                                (
                                                    u_move_sy in ["O", "Y"]
                                                    and s_move_sy in ["O", "Y"]
                                                )
                                                or (
                                                    u_move_sy in ["X", "N"]
                                                    and s_move_sy in ["X", "N"]
                                                )
                                                or (
                                                    u_move_sy == "_"
                                                    and s_move_sy == "_"
                                                )
                                            ):
                                                poss_move = {
                                                    "type": s_move["type"],
                                                    "insights": s_move["insights"],
                                                    "repair": s_move["repair"],
                                                    "violation": False,
                                                    "move_diff": s_move["move_diff"],
                                                    "incomplete": False,
                                                }
                                                if u_move_sy in [
                                                    "Y",
                                                    "N",
                                                ] or s_move_sy in ["Y", "N"]:
                                                    poss_move["incomplete"] = "incomplete"
                                                    if u_move_sy not in ["Y", "N"]:
                                                        poss_move["incomplete"] = "overconfident"
                                                    elif s_move_sy not in ["Y", "N"]:
                                                        poss_move["incomplete"] = "uncertain"
                                                if "indexed_hint" in s_move:
                                                    poss_move["indexed_hint"] = s_move[
                                                        "indexed_hint"
                                                    ]
                                                possible_moves.append(poss_move)
                                                recovered = True
                                            elif u_move_sy != "_" and s_move_sy in [
                                                "X",
                                                "O",
                                            ]:
                                                # The user made a move that contradicts the solver.
                                                poss_move = {
                                                    "type": s_move["type"],
                                                    "insights": s_move["insights"],
                                                    "repair": s_move["repair"],
                                                    "violation": True,
                                                    "move_diff": s_move["move_diff"],
                                                    "incomplete": False,
                                                }
                                                if "indexed_hint" in s_move:
                                                    poss_move["indexed_hint"] = s_move[
                                                        "indexed_hint"
                                                    ]
                                                possible_moves.append(poss_move)
                                                recovered = True
        if not recovered:
            possible_moves.append({
                "type": "unknown",
                "insights": {Insight.NO_INSIGHT},
                "repair": False,
                "violation": False,
                "incomplete": False,
            })

        u_move_diff, _ = get_move_diff(puzzle, result)
        board_state = result.print_grid()
        r_move = {
            "puzzle_state": deepcopy(result),
            "board_state": board_state,
            "move_diff": u_move_diff,
            "possible_moves": possible_moves,
            "value": get_move_value(u_move_diff, hints),
        }

        opened_state = deepcopy(result)
        find_openings(opened_state)
        grid_str = opened_state.print_grid()
        grid_id = f"{puzzle_id}:{grid_str}"

        solver_value = "unknown"
        if grid_id not in grid_to_label:
            correct = not repair(opened_state, solution)
            grid_value = "correct"
            if not correct:
                grid_value = "incorrect"
            add_node(puzzle_id, grid_id, grid_value, grid_to_label, node_df)
        target_label = grid_to_label[grid_id]
        if grid_id in collapsed_moves:
            solver_value = collapsed_moves[grid_id]["solver_value"]
            
        edge_row = [
            source_label,
            target_label,
            user_id,
            u_success,
            solver_value,
            r_move["value"],
            prompt_mode,
            level_mode,
        ]
        if (edge_df == edge_row).all(1).any():
            # Only add an edge once per user (while user retracing their steps could be interesting if looking at single user, we are interested in comparing users.)
            continue
        edge_df.loc[len(edge_df)] = edge_row  # adding a row
        source_label = target_label

        r_moves.append((raw_move, r_move))
        puzzle = deepcopy(result)


    return r_moves

# Analyze user data to hypothesize which insights participants used.
# def recover_moves(puzzle, hints, u_moves):
#     r_moves = []
#     for raw_move, rec_moves in u_moves:
#         result = deepcopy(puzzle)
#         opened_puzzle = deepcopy(puzzle)
#         find_openings(opened_puzzle)
#         _, s_moves = get_available_moves(puzzle, hints, True)
#         _, opened_moves = get_available_moves(opened_puzzle, hints, True)
#         dedupe_moves = s_moves
#         dedupe_o_moves = []
#         for o_move in opened_moves:
#             duplicate = False
#             for s_move in s_moves:
#                 if (
#                     o_move["type"] == s_move["type"]
#                     and o_move["insights"] == s_move["insights"]
#                     and o_move["move_diff"].print_grid()
#                     == s_move["move_diff"].print_grid()
#                 ):
#                     if "indexed_hint" in o_move and "indexed_hint" in s_move:
#                         o_move_hint = hint_to_english(o_move["indexed_hint"]["hint"])
#                         s_move_hint = hint_to_english(s_move["indexed_hint"]["hint"])
#                         if o_move_hint != s_move_hint:
#                             # Not same hint
#                             continue
#                     duplicate = True
#                     break
#             if not duplicate:
#                 o_move["type"] = f"(after filling in openings) {o_move['type']}"
#                 dedupe_o_moves.append(o_move)
#         dedupe_moves.extend(dedupe_o_moves)

#         recovered = False
#         possible_moves = []
#         temp = deepcopy(result)

#         for move in rec_moves:
#             result.answer(*move)
#             u_move_diff, changed = get_move_diff(temp, result, True)
#             temp = deepcopy(result)
#             if changed:
#                 if len(rec_moves) == 1 or move[-1] == "O":
#                     for s_move in dedupe_moves:
#                         s_move_diff = s_move["move_diff"]
#                         for cat1 in puzzle.left_right:
#                             for cat2 in puzzle.top_bottom:
#                                 u_move_grid = u_move_diff.get_grid(cat1, cat2)
#                                 s_move_grid = s_move_diff.get_grid(cat1, cat2)
#                                 if u_move_grid is None or s_move_grid is None:
#                                     continue
#                                 for ent2_idx in range(0, len(u_move_grid)):
#                                     for ent1_idx in range(
#                                         0, len(u_move_grid[ent2_idx])
#                                     ):
#                                         u_move_sy = u_move_grid[ent2_idx][ent1_idx]
#                                         s_move_sy = s_move_grid[ent2_idx][ent1_idx]
#                                         if u_move_sy != "*" and s_move_sy != "*":
#                                             # The moves affect the same grid location
#                                             if (
#                                                 (
#                                                     u_move_sy in ["O", "Y"]
#                                                     and s_move_sy in ["O", "Y"]
#                                                 )
#                                                 or (
#                                                     u_move_sy in ["X", "N"]
#                                                     and s_move_sy in ["X", "N"]
#                                                 )
#                                                 or (
#                                                     u_move_sy == "_"
#                                                     and s_move_sy == "_"
#                                                 )
#                                             ):
#                                                 poss_move = {
#                                                     "type": s_move["type"],
#                                                     "insights": s_move["insights"],
#                                                     "repair": s_move["repair"],
#                                                     "violation": False,
#                                                     "move_diff": s_move["move_diff"],
#                                                     "incomplete": False,
#                                                 }
#                                                 if u_move_sy in [
#                                                     "Y",
#                                                     "N",
#                                                 ] or s_move_sy in ["Y", "N"]:
#                                                     poss_move["incomplete"] = True
#                                                 if "indexed_hint" in s_move:
#                                                     poss_move["indexed_hint"] = s_move[
#                                                         "indexed_hint"
#                                                     ]
#                                                 possible_moves.append(poss_move)
#                                                 recovered = True
#                                             elif u_move_sy != "_" and s_move_sy in [
#                                                 "X",
#                                                 "O",
#                                             ]:
#                                                 # The user made a move that contradicts the solver.
#                                                 poss_move = {
#                                                     "type": s_move["type"],
#                                                     "insights": s_move["insights"],
#                                                     "repair": s_move["repair"],
#                                                     "violation": True,
#                                                     "move_diff": s_move["move_diff"],
#                                                     "incomplete": False,
#                                                 }
#                                                 if "indexed_hint" in s_move:
#                                                     poss_move["indexed_hint"] = s_move[
#                                                         "indexed_hint"
#                                                     ]
#                                                 possible_moves.append(poss_move)
#                                                 recovered = True
#         if not recovered:
#             possible_moves.append({
#                 "type": "unknown",
#                 "insights": [],
#                 "repair": False,
#                 "violation": False,
#                 "incomplete": False,
#             })

#         u_move_diff, _ = get_move_diff(puzzle, result)
#         board_state = result.print_grid()
#         r_move = {
#             "puzzle_state": deepcopy(result),
#             "board_state": board_state,
#             "move_diff": u_move_diff,
#             "possible_moves": possible_moves,
#             "value": get_move_value(u_move_diff, hints),
#         }
#         r_moves.append((raw_move, r_move))
#         puzzle = deepcopy(result)

#     return r_moves


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


def clean_online_moves(puzzle, hints, raw_moves):
    user_puzzle = deepcopy(puzzle)
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
            user_puzzle.answer(*move)

        
        clean_moves.append((puzzle_str, moves))
    solution, _, _, _ = apply_hints(puzzle, hints)
    correct = not repair(user_puzzle, solution)
    user_success = "failure"
    if correct:
        if is_solved(user_puzzle):
            user_success = "success"
        else:
            user_success = "partial"
    return clean_moves, user_success


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

def is_solved(puzzle):
    for cat1 in puzzle.left_right:
        for cat2 in puzzle.top_bottom:
            grid = puzzle.get_grid(cat1, cat2)
            if grid is None:
                continue

            for ent2_idx in range(0, len(grid)):
                row_O = False
                for ent1_idx in range(0, len(grid[ent2_idx])):
                    if (
                        grid[ent2_idx][ent1_idx] == "O"
                    ):
                        row_O = True
                if not row_O:
                    return False
    return True


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
                if poss_move["incomplete"]:
                    typestr += " (incomplete)"
                if poss_move["violation"]:
                    typestr += " (violation)"
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
        "helper1_1",
        "helper1_2",
        "helper1_3",
        "helper2_1",
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
                hint = {
                    "simple_or": [
                        pos_cat1,
                        pos_ent1,
                        pos_cat2,
                        pos_ent2,
                        ans_cat,
                        ans_ent,
                    ]
                }
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
        user_id = row["userId"]
        session_id = row["_id"]
        if session_id not in action_json:
            continue
        raw_moves = action_json[session_id]
        puzzle_id = row["pid"]
        if puzzle_id not in puzzles:
            print(f"couldn't find puzzle {puzzle_id} :(")
            continue
        puzzle = puzzles[puzzle_id]["puzzle"]
        hints = puzzles[puzzle_id]["hints"]
        if user_id not in clean_data:
            clean_data[user_id] = {
                "promptMode": row["promptMode"],
                "levelMode": row["levelMode"],
                "puzzles": {},
            }
        cleaned_moves, user_success = clean_online_moves(puzzle, hints, raw_moves)
        clean_data[user_id]["puzzles"][puzzle_id] = {
            "puzzle": puzzle,
            "hints": hints,
            "moves": cleaned_moves,
            "success": user_success,
        }
    return clean_data


if __name__ == "__main__":
    node_df = pd.DataFrame(
        columns=[
            "Id",
            "puzzleId",
            "currGrid",
            "value",
        ]
    )
    edge_df = pd.DataFrame(
        columns=[
            "Source",
            "Target",
            "userId",
            "userSuccess",
            "solverValue",
            "value",
            "promptMode",
            "levelMode",
        ]
    )
    grid_to_label = {}
    label_to_grid = {}
    vr_dir = "user_data/vr_study"
    vr_users = [f.name for f in os.scandir("user_data/vr_study") if f.is_dir()]
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
    #         update_state_df(
    #             node_df,
    #             edge_df,
    #             grid_to_label,
    #             label_to_grid,
    #             key,
    #             info["puzzle"],
    #             info["hints"],
    #             recovered_moves,
    #             user,
    #             "vr",
    #             "vr",
    #         )

    online_dir = "user_data/online_puzzle_study"
    clean_data = load_online_data(online_dir)
    for user_id, user_data in clean_data.items():
        print(user_id)
        for puzzle_id, session in user_data["puzzles"].items():
            print(puzzle_id)
            recovered_moves = recover_moves(
                session["puzzle"], session["hints"], user_id, user_data["promptMode"], user_data["levelMode"], session["moves"], session["success"], grid_to_label, node_df, edge_df
            )
            output_path = (
                f"{online_dir}/recovered_trees/{user_id}/recovered_tree_{puzzle_id}.txt"
            )
            output_file = Path(output_path)
            output_file.parent.mkdir(exist_ok=True, parents=True)
            move_file = open(output_path, "w")
            print_moves(move_file, session["puzzle"], session["hints"], recovered_moves)
    node_df.to_csv("user_data/nodegraph.csv", index=False)
    edge_df.to_csv("user_data/edgegraph.csv", index=False)
