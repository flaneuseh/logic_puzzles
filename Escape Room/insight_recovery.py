import pandas as pd
import ultraimport
from copy import deepcopy
import os
import json
import re
from pathlib import Path
import csv
from random import randint
from statistics import fmean as mean

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
def get_move_value(move_diff, solution):
    value = ""
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
                    if diff_cell in ["_", "X", "O", "Y", "N"]:
                        # Part of the current move.
                        if diff_cell in ["_", "Y", "N"] and value not in [
                            "correct",
                            "incorrect",
                        ]:
                            value = "neutral"
                        elif diff_cell != soln_cell:
                            value = "incorrect"
                        elif value != "incorrect":
                            value = "correct"

    return value


def replace_sy(puzzle, loc, sy):
    if loc == None:
        return puzzle
    (cat1, cat2, ent1_idx, ent2_idx) = loc
    puzzle.answer(cat1, cat2, cat1.entities[ent1_idx], cat2.entities[ent2_idx], sy)
    return puzzle


def get_diff_sy(diff):
    for cat1 in diff.left_right:
        for cat2 in diff.top_bottom:
            grid = diff.get_grid(cat1, cat2)
            if grid is None:
                continue
            for ent2_idx in range(0, len(grid)):
                for ent1_idx in range(0, len(grid[ent2_idx])):
                    sy = grid[ent2_idx][ent1_idx]
                    if sy in ["X", "O", "Y", "N", "_"]:
                        return (cat1, cat2, ent1_idx, ent2_idx), sy
    return None, None


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
    # opened_puzzle = deepcopy(state)
    # find_openings(opened_puzzle)
    # grid_str = opened_puzzle.print_grid()
    grid_str = state.print_grid()
    grid_id = f"{puzzle_id}:{grid_str}"
    return grid_id


def get_composite_moves(puzzle_id, curr_state, solution, moves):
    # Moves that reach the same grid state are collapsed to only the move with the lowest ranked max insight
    # We check the max insight because the insights returned by the solver are all necessary to the move,
    # not a list of possible ways to reach the move.
    collapsed_moves = {}
    for s_move in moves:
        move_state = deepcopy(curr_state)
        move_diff = s_move["move_diff"]
        diff_loc, diff_sy = get_diff_sy(move_diff)
        if diff_loc == None:
            continue
        replace_sy(move_state, diff_loc, diff_sy)
        grid_id = get_grid_id(puzzle_id, move_state)
        max_insight = get_max_insight(s_move)

        if (
            grid_id not in collapsed_moves
            or max_insight.value < collapsed_moves[grid_id]["max_insight"].value
        ):
            # Keep the move with the lowest ranked max insight, as before
            type = s_move["type"]
            grid_value = "correct"
            if repair(move_state, solution, False):
                grid_value = "incorrect"
            diff_loc, diff_sy = get_diff_sy(s_move["move_diff"])
            collapsed_moves[grid_id] = {
                "type": type,
                "max_insight": max_insight,
                "move_diff": s_move["move_diff"],
                "state": move_state,
                "grid_value": grid_value,
                "simple_diff": (diff_loc, diff_sy),
            }
            if "indexed_hint" in s_move:
                hint = s_move["indexed_hint"]["idx"]
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
        diff_loc, diff_sy = c_move["simple_diff"]
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
            simple_diff = (diff_loc, alt_sy)
            alt_move["simple_diff"] = simple_diff
            alt_move["state"] = alt_state
            alt_move["og_sy"] = diff_sy
            correct = not repair(alt_state, solution, False)
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
    composite_moves = {}
    grid_id_to_comp_id = {}
    for grid_id, c_move in collapsed_moves.items():
        type = c_move["type"]
        max_insight = c_move["max_insight"]
        hint = ""
        if "hint" in c_move:
            hint = c_move["hint"]
        solver_value = c_move["solver_value"]
        comp_id = f"{type}:{max_insight}:{hint}:{solver_value}"

        if comp_id not in composite_moves:
            composite_moves[comp_id] = {
                "type": type,
                "insight": max_insight,
                "hint": hint,
                "solver_value": solver_value,
                "moves": {},
            }
        composite_moves[comp_id]["moves"][grid_id] = {
            "move_diff": c_move["move_diff"],
            "state": c_move["state"],
            "grid_value": c_move["grid_value"],
            "simple_diff": c_move["simple_diff"],
        }
        grid_id_to_comp_id[grid_id] = comp_id

    return composite_moves, grid_id_to_comp_id


def get_solver_moves(puzzle, hints):
    # Get all conceivable moves for the puzzle state. Include moves from the "opened" version of the puzzle,
    # as the user could be holding this information in their head, and we want to catch as many possible insights as we can.
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
                and o_move["move_diff"].print_grid() == s_move["move_diff"].print_grid()
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
            # o_move["type"] = f"(after filling in openings) {o_move['type']}"
            dedupe_o_moves.append(o_move)
    dedupe_moves.extend(dedupe_o_moves)
    return dedupe_moves


def get_possible_moves(puzzle, u_moves, available_moves):
    possible_moves = []
    recovered = False
    temp = deepcopy(puzzle)

    u_move_diff = None
    for move in u_moves:
        puzzle.answer(*move)
        u_move_diff, changed = get_move_diff(temp, puzzle, True)
        temp = deepcopy(puzzle)
        if changed:
            if len(u_moves) == 1:
                for s_move in available_moves:
                    s_move_diff = s_move["move_diff"]
                    for cat1 in puzzle.left_right:
                        for cat2 in puzzle.top_bottom:
                            u_move_grid = u_move_diff.get_grid(cat1, cat2)
                            s_move_grid = s_move_diff.get_grid(cat1, cat2)
                            if u_move_grid is None or s_move_grid is None:
                                continue
                            for ent2_idx in range(0, len(u_move_grid)):
                                for ent1_idx in range(0, len(u_move_grid[ent2_idx])):
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
                                            or (u_move_sy == "_" and s_move_sy == "_")
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
                                                    poss_move["incomplete"] = (
                                                        "overconfident"
                                                    )
                                                elif s_move_sy not in ["Y", "N"]:
                                                    poss_move["incomplete"] = (
                                                        "uncertain"
                                                    )
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

    return possible_moves


def get_node_id(
    user_history, curr_grid_value, puzzle_id, node_df, state_to_node_id, curr_move_id
):
    # Sort all the hint insights the user has made so that users reaching insights in different orders are considered to reach the same state.

    move_ids = {curr_move_id}
    for move_id, _ in user_history.values():
        if (
            "unknown" not in move_id
            and "OPENING" not in curr_move_id
            and "CROSS_OUT" not in curr_move_id
        ):
            # Only save the current unknown
            move_ids.add(move_id)
    move_ids = sorted(list(move_ids))
    state = f"{puzzle_id}:{curr_grid_value}:{move_ids}"

    if state not in state_to_node_id:
        node_id = randint(10000, 99999)
        while node_id in state_to_node_id.values():
            node_id = randint(10000, 99999)
        if ((node_df["Id"] == node_id)).any():
            print("!! something is broken, there is a duplicate node id")

        node_row = [node_id, puzzle_id, state, curr_grid_value, move_ids]
        node_df.loc[len(node_df)] = node_row
        state_to_node_id[state] = node_id

    return state_to_node_id[state]


def get_diff_loc_str(diff_loc):
    (cat1, cat2, ent1_idx, ent2_idx) = diff_loc
    return f"{cat1.title}:{cat2.title}:{ent1_idx}:{ent2_idx}"


# Analyze user data to hypothesize which insights participants used.
def recover_moves(
    puzzle_id,
    puzzle,
    hints,
    user_id,
    prompt_mode,
    level_mode,
    u_moves,
    u_success,
    state_to_node_id,
    node_df,
    edge_df,
    action_json,
    session_id,
    session_outcome_json,
):
    # The history of which insights and composite moves are associated with which moves for this user.
    user_history = {}

    # Empty state node.
    source_id = get_node_id(
        user_history, "start", puzzle_id, node_df, state_to_node_id, "start"
    )
    success_id = get_node_id(
        user_history, "success", puzzle_id, node_df, state_to_node_id, "success"
    )
    failure_id = get_node_id(
        user_history, "failure", puzzle_id, node_df, state_to_node_id, "failure"
    )
    partial_id = get_node_id(
        user_history, "partial", puzzle_id, node_df, state_to_node_id, "partial"
    )

    solution, _, _, _ = apply_hints(puzzle, hints)

    r_moves = []
    mi = 0
    for time, raw_str, rec_moves in u_moves:
        result = deepcopy(puzzle)  # copy that will have current move applied

        available_moves = get_solver_moves(puzzle, hints)  # All solver-aware moves
        composite_moves, grid_id_to_comp_id = get_composite_moves(
            puzzle_id, puzzle, solution, available_moves
        )  # Available solver moves collapsed into individual insights

        possible_moves = get_possible_moves(result, rec_moves, available_moves)

        u_move_diff, changed = get_move_diff(puzzle, result, True)

        if not changed:
            continue

        if len(rec_moves) > 1:
            # This is a "clear" move; reset progress
            target_id = source_id
            user_history = {}
            edge_row = [
                source_id,
                target_id,
                user_id,
                mi,
                u_success,
                "unknown-neutral",
                "neutral",
                prompt_mode,
                level_mode,
            ]
            mi = mi + 1
            if (edge_df == edge_row).all(1).any():
                # Only add an edge once per user (while user retracing their steps could be interesting if looking at single user, we are interested in comparing users.)
                continue
            edge_df.loc[len(edge_df)] = edge_row  # adding a row
            source_id = target_id

            puzzle = deepcopy(result)
            continue

        diff_loc, diff_sy = get_diff_sy(u_move_diff)
        board_state = result.print_grid()
        r_move = {
            "puzzle_state": deepcopy(result),
            "board_state": board_state,
            "move_diff": u_move_diff,
            "simple_diff": (diff_loc, diff_sy),
            "possible_moves": possible_moves,
            "value": get_move_value(u_move_diff, solution),
        }

        if get_move_value(u_move_diff, solution) == "":
            print("WE SHOULD HAVE A MOVE VALUE BUT WE DON'T!!!!!")

        r_moves.append((time, raw_str, r_move))

        grid_id = get_grid_id(puzzle_id, result)

        solver_value = "unknown"
        if diff_sy in ["Y", "N", "_"]:
            solver_value = "unknown-neutral"
        elif repair(u_move_diff, solution, False):
            solver_value = "unknown-incorrect"
        else:
            solver_value = "unknown-correct"

        diff_loc_str = get_diff_loc_str(diff_loc)
        move_id = f"{solver_value}:{diff_loc_str}:{diff_sy}"
        if grid_id in grid_id_to_comp_id:
            comp_id = grid_id_to_comp_id[grid_id]
            composite = composite_moves[comp_id]
            # In the future, consider the case of the same hint having the same insight applied multiple times
            # A "composite grid" in that case is defined to be the total of all moves that can be applied with
            # the current insight and hint, *including moves that may have already been applied in an earlier state*
            # composite_grid = get_composite_grid(composite)
            type = composite["type"]
            insight_str = f"{composite['insight']}"
            hint = composite["hint"]
            if composite["solver_value"] != "contradiction": 
                solver_value = composite["solver_value"]
                if solver_value in ["uncertain", "overconfident"]:
                    solver_value = "insight"
            
            # Add the insight to the action JSON.
            move_idx = 0
            for i, move_data in enumerate(action_json[session_id]):
                if move_data["time"] == time:
                    move_idx = i
                    break
            action_json[session_id][move_idx]["insight"] = insight_str
            move_id = f"{type}:{hint}:{insight_str}"

        curr_grid_value = "correct"
        if repair(result, solution, False):
            curr_grid_value = "incorrect"

        if diff_loc in user_history:
            _, h_sy = user_history[diff_loc]
            if h_sy != diff_sy:
                user_history[diff_loc] = (move_id, diff_sy)
        else:
            user_history[diff_loc] = (move_id, diff_sy)
        target_id = get_node_id(
            user_history, curr_grid_value, puzzle_id, node_df, state_to_node_id, move_id
        )

        edge_row = [
            source_id,
            target_id,
            user_id,
            mi,
            u_success,
            solver_value,
            r_move["value"],
            prompt_mode,
            level_mode,
        ]
        mi = mi + 1
        if (edge_df == edge_row).all(1).any():
            # Only add an edge once per user (while user retracing their steps could be interesting if looking at single user, we are interested in comparing users.)
            continue
        edge_df.loc[len(edge_df)] = edge_row  # adding a row
        source_id = target_id

        puzzle = deepcopy(result)

    target_id = ""
    if u_success == "success":
        target_id = success_id
    elif u_success == "failure":
        target_id = failure_id
    elif u_success == "partial":
        target_id = partial_id
    edge_row = [
        source_id,
        target_id,
        user_id,
        mi,
        u_success,
        "",
        "",
        prompt_mode,
        level_mode,
    ]

    # Get available insights at the end.
    available_insights = set()
    if u_success != "success":
        # If the user was successful, ignore any optional insights.
        available_moves = get_solver_moves(puzzle, hints)
        for s_move in available_moves:
            available_insights.add(f"{get_max_insight(s_move)}")

    session_outcome_json[session_id] = {
        "outcome": u_success,
        "available_insights": list(available_insights),
    }

    if (edge_df == edge_row).all(1).any():
        # Only add an edge once per user (while user retracing their steps could be interesting if looking at single user, we are interested in comparing users.)
        return r_moves
    edge_df.loc[len(edge_df)] = edge_row
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


def clean_online_moves(puzzle, hints, raw_moves):
    user_puzzle = deepcopy(puzzle)
    clean_moves = []
    raw_moves = list(filter(lambda rm: rm["type"] == "cellChange" or (rm["type"] == "button" and rm["button"] == "clear"), raw_moves))
    raw_moves = sorted(raw_moves, key=lambda m: m["time"])
    for _, raw_move in enumerate(raw_moves):
        time = raw_move["time"]
        moves = []
        puzzle_str = puzzle
        if raw_move["type"] == "cellChange":
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
                        old_symbol = user_puzzle.get_symbol(cat1, cat2, ent1, ent2)
                        if old_symbol != new_symbol:
                            moves.append([cat1, cat2, ent1, ent2, new_symbol])
        for move in moves:
            user_puzzle.answer(*move)

        clean_moves.append((time, puzzle_str, moves))
    solution, _, _, _ = apply_hints(puzzle, hints)
    correct = not repair(user_puzzle, solution, False)
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
                    if grid[ent2_idx][ent1_idx] == "O":
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

    for idx, (time, raw_state, move) in enumerate(moves):
        if move == None:
            file.write(f"{time}: User Move {idx+1} (Wrong, Ignored): {raw_state}\n")
        else:
            file.write(f"User Move {idx+1} ({move['value']}): {raw_state}\n")
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
        puzzle_id = row["pid"]
        if session_id not in action_json:
            print(f"{user_id}:{session_id} for {puzzle_id} not in action json")
            continue
        raw_moves = action_json[session_id]
        
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
            "session_id": session_id,
        }
    return clean_data, action_json


def gen_data_views(dir, edge_df, node_df):
    # user_success_vals = set(edge_df["UserSuccess"].unique())
    # user_success_vals.add(None)
    # prompt_mode_vals = set(edge_df["PromptMode"].unique())
    # prompt_mode_vals.add(None)
    # level_mode_vals = set(edge_df["LevelMode"].unique())
    # level_mode_vals.add(None)

    # for u in user_success_vals:
    #     for p in prompt_mode_vals:
    #         for l in level_mode_vals:
    edge_view = edge_df.copy()
    view_name = "ALL"
    # if u != None:
    #     view_name += f"_endstate={u}"
    #     edge_view = edge_view[edge_view["UserSuccess"] == u]
    # else:
    #     view_name += "_endstate=all"
    # if p != None:
    #     view_name += f"_prompts={p}"
    #     edge_view = edge_view[edge_view["PromptMode"] == p]
    # else:
    #     view_name += "_prompts=all"
    # if l != None:
    #     view_name += f"_levels={l}"
    #     edge_view = edge_view[edge_view["LevelMode"] == l]
    # else:
    #     view_name += "_levels=all"
    node_view_name = f"nodegraph{view_name}"
    edge_nodes = list(edge_view["Source"])
    edge_nodes.extend(list(edge_view["Target"]))
    node_view = node_df[node_df["Id"].isin(edge_nodes)]
    edge_view_name = f"edgegraph{view_name}"
    edge_view.to_csv(f"{dir}/{edge_view_name}.csv", index=False)
    node_view.to_csv(f"{dir}/{node_view_name}.csv", index=False)

    # if u == None and p == None and l == None:
    combined_view = pd.merge(
        edge_view, node_view, left_on="Target", right_on="Id"
    )
    # % successful, % concede, % success but failed at least once, % concede while partially correct
    

    puzzle_ids = list(combined_view["PuzzleId"].unique())

    stats_by_pid = {}
    for pid in puzzle_ids:
        pg_view = combined_view.copy()
        pg_view = pg_view[pg_view["PuzzleId"] == pid]
        real_moves = pg_view[
            pg_view["MoveValue"].isin(
                ["correct", "incorrect", "neutral"]
            )
        ]
        
        pg_all = pg_view["UserId"].unique()
        pg_view = pg_view[pg_view["UserId"].isin(real_moves["UserId"])]
        pg_real = pg_view["UserId"].unique()
        for user in pg_all:
            if user not in pg_real:
                print(f"{user} not in {pid}")

        p_users = pg_view["UserId"].unique()
        print(f"Num users for {pid}: {len(p_users)}")

        user_view = pg_view.copy()
        user_view = user_view.drop_duplicates(["UserId", "UserSuccess"])
        success_counts = user_view.value_counts("UserSuccess")
        if "success" not in success_counts:
            success_counts["success"] = 0
        if "partial" not in success_counts:
            success_counts["partial"] = 0
        if "failure" not in success_counts:
            success_counts["failure"] = 0

        user_move_correctness = pg_view.copy()
        user_move_correctness = user_move_correctness.drop_duplicates(
            ["UserId", "UserSuccess", "GridValue"]
        )

        success_and_incorrect = user_move_correctness[
            user_move_correctness["UserSuccess"] == "success"
        ]
        success_and_incorrect = success_and_incorrect[
            success_and_incorrect["GridValue"] == "incorrect"
        ]

        view_stats = {}
        view_stats["num_users"] = len(user_view)
        if len(user_view) == 0:
            view_stats["num_success"] = 0
            view_stats["num_fail"] = 0
            view_stats["num_partial"] = 0
            view_stats["num_concede"] = 0
            view_stats["num_partial_of_concede"] = 0
            view_stats["num_had_error_of_success"] = 0
            view_stats["pct_success"] = 0
            view_stats["pct_fail"] = 0
            view_stats["pct_partial"] = 0
            view_stats["pct_concede"] = 0
        else:
            view_stats["num_success"] = int(success_counts["success"])
            view_stats["pct_success"] = float(success_counts["success"] / len(
                user_view
            ))
            view_stats["num_fail"] = int(success_counts["failure"])
            view_stats["pct_fail"] = float(success_counts["failure"] / len(
                user_view
            ))
            view_stats["num_partial"] = int(success_counts["partial"])
            view_stats["pct_partial"] = float(success_counts["partial"] / len(
                user_view
            ))
            view_stats["num_concede"] = int(
                success_counts["failure"] + success_counts["partial"]
            )
            view_stats["pct_concede"] = float((
                success_counts["failure"] + success_counts["partial"]
            ) / len(user_view))
        if success_counts["failure"] + success_counts["partial"] == 0:
            view_stats["pct_partial_of_concede"] = 0
        else:
            view_stats["pct_partial_of_concede"] = float(success_counts[
                "partial"
            ] / (success_counts["failure"] + success_counts["partial"]))
        if success_counts["success"] == 0:
            view_stats["num_had_error_of_success"] = 0
            view_stats["pct_had_error_of_success"] = 0
        else:
            view_stats["num_had_error_of_success"] = len(
                success_and_incorrect
            )
            view_stats["pct_had_error_of_success"] = float(
                len(success_and_incorrect) / success_counts["success"]
            )

        all_view = pg_view.copy()
        success_view = all_view.copy()
        success_view = success_view[
            success_view["UserSuccess"] == "success"
        ]
        concede_view = all_view.copy()
        concede_view = concede_view[
            concede_view["UserSuccess"] != "success"
        ]

        first_move = all_view[all_view["MoveNumber"] == 0]
        second_move = all_view[all_view["MoveNumber"] == 1]
        third_move = all_view[all_view["MoveNumber"] == 2]

        third_move_users = third_move["UserId"]
        if len(third_move_users) != len(third_move_users.unique()):
            print("EXTRA MOVES WERE FOUND")
            print(pid)
            print(third_move_users)

        first_move = first_move[
            first_move["UserId"].isin(third_move_users)
        ]
        second_move = second_move[
            second_move["UserId"].isin(third_move_users)
        ]

        if len(first_move) != len(second_move) or len(
            second_move
        ) != len(third_move):
            print("MOVES ARE NOT EQUAL")

            print(pid)
            print("first three moves")
            print(first_move[["UserId", "Target"]])
            print(second_move[["UserId", "Target"]])
            print(third_move[["UserId", "Target"]])

        first_move_counts = (
            first_move.value_counts("Target")
            .rename_axis("Target")
            .reset_index(name="target_first_move_count")
        )
        first_move_counts = pd.merge(
            first_move, first_move_counts, on="Target"
        )
        first_move_counts = first_move_counts[
            first_move_counts["target_first_move_count"] > 1
        ]

        second_move_counts = (
            second_move.value_counts("Target")
            .rename_axis("Target")
            .reset_index(name="target_second_move_count")
        )
        second_move_counts = pd.merge(
            second_move, second_move_counts, on="Target"
        )
        second_move_counts = second_move_counts[
            second_move_counts["target_second_move_count"] > 1
        ]

        third_move_counts = (
            third_move.value_counts("Target")
            .rename_axis("Target")
            .reset_index(name="target_third_move_count")
        )
        third_move_counts = pd.merge(
            third_move, third_move_counts, on="Target"
        )
        third_move_counts = third_move_counts[
            third_move_counts["target_third_move_count"] > 1
        ]

        last_move = all_view[all_view["MoveValue"] == ""]
        last_move_counts = (
            last_move.value_counts("Source")
            .rename_axis("Source")
            .reset_index(name="source_last_move_count")
        )
        last_move_counts = pd.merge(
            last_move, last_move_counts, on="Source"
        )
        last_move_counts = last_move_counts[
            last_move_counts["source_last_move_count"] > 1
        ]

        user_views = [
            ("success", success_view),
            ("concede", concede_view),
            ("all_users", all_view),
        ]
        for u_name, u_view in user_views:
            view_stats[u_name] = {}
            correct_states = u_view[u_view["GridValue"] == "correct"]
            incorrect_states = u_view[
                u_view["GridValue"] == "incorrect"
            ]
            real_moves = u_view[
                u_view["MoveValue"].isin(
                    ["correct", "incorrect", "neutral"]
                )
            ]
            correct_moves = u_view[u_view["MoveValue"] == "correct"]
            incorrect_moves = u_view[u_view["MoveValue"] == "incorrect"]
            neutral_moves = u_view[u_view["MoveValue"] == "neutral"]

            count_states = (
                real_moves.value_counts("UserId")
                .rename_axis("UserId")
                .reset_index(name="move_count")
            )
            count_correct_states = (
                correct_states.value_counts("UserId")
                .rename_axis("UserId")
                .reset_index(name="correct_state_count")
            )
            count_incorrect_states = (
                incorrect_states.value_counts("UserId")
                .rename_axis("UserId")
                .reset_index(name="incorrect_state_count")
            )

            count_correct_moves = (
                correct_moves.value_counts("UserId")
                .rename_axis("UserId")
                .reset_index(name="correct_move_count")
            )
            count_incorrect_moves = (
                incorrect_moves.value_counts("UserId")
                .rename_axis("UserId")
                .reset_index(name="incorrect_move_count")
            )
            count_neutral_moves = (
                neutral_moves.value_counts("UserId")
                .rename_axis("UserId")
                .reset_index(name="neutral_move_count")
            )

            user_counts = pd.merge(
                count_states,
                count_correct_states,
                on="UserId",
                how="outer",
            )
            user_counts = pd.merge(
                user_counts,
                count_incorrect_states,
                on="UserId",
                how="outer",
            )

            user_counts = pd.merge(
                user_counts,
                count_correct_moves,
                on="UserId",
                how="outer",
            )
            user_counts = pd.merge(
                user_counts,
                count_incorrect_moves,
                on="UserId",
                how="outer",
            )
            user_counts = pd.merge(
                user_counts,
                count_neutral_moves,
                on="UserId",
                how="outer",
            )

            user_counts = user_counts.fillna(0)
            if len(user_counts) == 0:
                view_stats[u_name] = {
                    "pct_correct_state": [],
                    "avg_pct_correct_state": 0,
                    "pct_incorrect_state": [],
                    "avg_pct_incorrect_state": 0,
                    "pct_correct_move": [],
                    "avg_pct_correct_move": 0,
                    "pct_incorrect_move": [],
                    "avg_pct_incorrect_move": 0,
                    "pct_neutral_move": [],
                    "avg_pct_neutral_move": 0,
                    "pct_insight": [],
                    "avg_pct_insight": 0,
                    "pct_unknown_correct": [],
                    "avg_pct_unknown_correct": 0,
                    "pct_unknown_incorrect": [],
                    "avg_pct_unknown_incorrect": 0,
                    "pct_unknown_neutral": [],
                    "avg_pct_unknown_neutral": 0,
                    "num_users_had_three_moves": 0,
                    "pct_users_share_first_move": 0,
                    "pct_users_share_second_move": 0,
                    "pct_users_share_third_move": 0,
                    "pct_users_share_last_move": 0,
                    "num_users_share_first_move": 0,
                    "num_users_share_second_move": 0,
                    "num_users_share_third_move": 0,
                    "num_users_share_last_move": 0
                }
                continue

            user_counts["PctCorrectState"] = (
                user_counts["correct_state_count"]
                / user_counts["move_count"]
            )
            user_counts["PctIncorrectState"] = (
                user_counts["incorrect_state_count"]
                / user_counts["move_count"]
            )

            user_counts["PctCorrectMove"] = (
                user_counts["correct_move_count"]
                / user_counts["move_count"]
            )
            user_counts["PctIncorrectMove"] = (
                user_counts["incorrect_move_count"]
                / user_counts["move_count"]
            )
            user_counts["PctNeutralMove"] = (
                user_counts["neutral_move_count"]
                / user_counts["move_count"]
            )

            view_stats[u_name]["pct_correct_state"] = user_counts[
                "PctCorrectState"
            ].tolist()
            view_stats[u_name]["avg_pct_correct_state"] = float(user_counts[
                "PctCorrectState"
            ].mean())
            view_stats[u_name]["pct_incorrect_state"] = user_counts[
                "PctIncorrectState"
            ].tolist()
            view_stats[u_name]["avg_pct_incorrect_state"] = float(user_counts[
                "PctIncorrectState"
            ].mean())

            view_stats[u_name]["pct_correct_move"] = user_counts[
                "PctCorrectMove"
            ].tolist()
            view_stats[u_name]["avg_pct_correct_move"] = float(user_counts[
                "PctCorrectMove"
            ].mean())
            view_stats[u_name]["pct_incorrect_move"] = user_counts[
                "PctIncorrectMove"
            ].tolist()
            view_stats[u_name]["avg_pct_incorrect_move"] = float(user_counts[
                "PctIncorrectMove"
            ].mean())
            view_stats[u_name]["pct_neutral_move"] = user_counts[
                "PctNeutralMove"
            ].tolist()
            view_stats[u_name]["avg_pct_neutral_move"] = float(user_counts[
                "PctNeutralMove"
            ].mean())

            u_view = u_view.replace({
                "SolverValue": {
                    "contradiction": "unknown-incorrect",
                    "uncertain": "insight",
                    "overconfident": "insight",
                }
            })
            insight_moves = u_view[u_view["SolverValue"] == "insight"]
            unknown_correct_moves = u_view[
                u_view["SolverValue"] == "unknown-correct"
            ]
            unknown_incorrect_moves = u_view[
                u_view["SolverValue"] == "unknown-incorrect"
            ]
            unknown_neutral_moves = u_view[
                u_view["SolverValue"] == "unknown-neutral"
            ]
            insight_move_count = (
                insight_moves.value_counts("UserId")
                .rename_axis("UserId")
                .reset_index(name="insight_move_count")
            )
            unknown_correct_move_count = (
                unknown_correct_moves.value_counts("UserId")
                .rename_axis("UserId")
                .reset_index(name="unknown_correct_move_count")
            )
            unknown_incorrect_move_count = (
                unknown_incorrect_moves.value_counts("UserId")
                .rename_axis("UserId")
                .reset_index(name="unknown_incorrect_move_count")
            )
            unknown_neutral_move_count = (
                unknown_neutral_moves.value_counts("UserId")
                .rename_axis("UserId")
                .reset_index(name="unknown_neutral_move_count")
            )

            user_counts = pd.merge(
                user_counts,
                insight_move_count,
                on="UserId",
                how="outer",
            )
            user_counts = pd.merge(
                user_counts,
                unknown_correct_move_count,
                on="UserId",
                how="outer",
            )
            user_counts = pd.merge(
                user_counts,
                unknown_incorrect_move_count,
                on="UserId",
                how="outer",
            )
            user_counts = pd.merge(
                user_counts,
                unknown_neutral_move_count,
                on="UserId",
                how="outer",
            )

            user_counts["PctInsight"] = (
                user_counts["insight_move_count"]
                / user_counts["move_count"]
            )
            user_counts["PctUnknownCorrect"] = (
                user_counts["unknown_correct_move_count"]
                / user_counts["move_count"]
            )
            user_counts["PctUnknownIncorrect"] = (
                user_counts["unknown_incorrect_move_count"]
                / user_counts["move_count"]
            )
            user_counts["PctUnknownNeutral"] = (
                user_counts["unknown_neutral_move_count"]
                / user_counts["move_count"]
            )
            user_counts = user_counts.fillna(0)

            view_stats[u_name]["pct_insight"] = user_counts[
                "PctInsight"
            ].tolist()
            view_stats[u_name]["avg_pct_insight"] = float(user_counts[
                "PctInsight"
            ].mean())
            view_stats[u_name]["pct_unknown_correct"] = user_counts[
                "PctUnknownCorrect"
            ].tolist()
            view_stats[u_name]["avg_pct_unknown_correct"] = float(user_counts[
                "PctUnknownCorrect"
            ].mean())
            view_stats[u_name]["pct_unknown_incorrect"] = user_counts[
                "PctUnknownIncorrect"
            ].tolist()
            view_stats[u_name]["avg_pct_unknown_incorrect"] = float(
                user_counts["PctUnknownIncorrect"].mean()
            )
            view_stats[u_name]["pct_unknown_neutral"] = user_counts[
                "PctUnknownNeutral"
            ].tolist()
            view_stats[u_name]["avg_pct_unknown_neutral"] = float(user_counts[
                "PctUnknownNeutral"
            ].mean())

            curr_users = u_view["UserId"].unique()
            three_moves_curr = third_move[
                third_move["UserId"].isin(curr_users)
            ]
            curr_users = three_moves_curr["UserId"]
            curr_num = len(curr_users)
            view_stats[u_name]["num_users_had_three_moves"] = curr_num
            if curr_num == 0:
                view_stats[u_name]["pct_users_share_first_move"] = 0
                view_stats[u_name]["pct_users_share_second_move"] = 0
                view_stats[u_name]["pct_users_share_third_move"] = 0
                view_stats[u_name]["pct_users_share_last_move"] = 0
                view_stats[u_name]["num_users_share_first_move"] = 0
                view_stats[u_name]["num_users_share_second_move"] = 0
                view_stats[u_name]["num_users_share_third_move"] = 0
                view_stats[u_name]["num_users_share_last_move"] = 0
                continue

            curr_first_moves = first_move_counts[
                first_move_counts["UserId"].isin(curr_users)
            ]
            first_users = curr_first_moves["UserId"]

            view_stats[u_name]["num_users_share_first_move"] = len(first_users)
            view_stats[u_name]["pct_users_share_first_move"] = (
                len(first_users) / curr_num
            )

            curr_second_moves = second_move_counts[
                second_move_counts["UserId"].isin(first_users)
            ]
            second_users = curr_second_moves["UserId"]

            view_stats[u_name]["num_users_share_second_move"] = len(second_users)
            view_stats[u_name]["pct_users_share_second_move"] = (
                len(second_users) / curr_num
            )

            curr_third_moves = third_move_counts[
                third_move_counts["UserId"].isin(second_users)
            ]
            third_users = curr_third_moves["UserId"]

            view_stats[u_name]["num_users_share_third_move"] = len(third_users)
            view_stats[u_name]["pct_users_share_third_move"] = (
                len(third_users) / curr_num
            )

            curr_last_moves = last_move_counts[
                last_move_counts["UserId"].isin(curr_users)
            ]
            last_users = curr_last_moves["UserId"]
            view_stats[u_name]["num_users_share_last_move"] = len(last_users)
            view_stats[u_name]["pct_users_share_last_move"] = (
                len(last_users) / curr_num
            )

        for sname, stat in view_stats.items():
            if sname not in ["success", "concede", "all_users"]:
                if isinstance(stat, list) and pd.isna(stat):
                    view_stats[sname] = 0
            else:
                for us_name, u_stat in stat.items():
                    if isinstance(stat, list) and pd.isna(u_stat):
                        view_stats[sname][us_name] = 0
        stats_by_pid[pid] = view_stats

        puzzle_groups = ["all", "spoke", "hub", "help"]

        stats_by_group = {}
        statlists_by_group = {}
        for group_name in puzzle_groups:
            group_stat_lists = {}

            for pid, stats in stats_by_pid.items():
                if pid == None or (
                    group_name != "all" and group_name not in pid
                ):
                    continue
                for sname, stat in stats.items():
                    if sname not in ["success", "concede", "all_users"]:
                        if sname not in group_stat_lists:
                            group_stat_lists[sname] = []
                        if isinstance(stat, list):
                            group_stat_lists[sname].extend(stat)
                        else:
                            group_stat_lists[sname].append(stat)
                    else:
                        if sname not in group_stat_lists:
                            group_stat_lists[sname] = {}
                        for us_name, u_stat in stat.items():
                            if us_name not in group_stat_lists[sname]:
                                group_stat_lists[sname][us_name] = []
                            if isinstance(u_stat, list):
                                group_stat_lists[sname][us_name].extend(u_stat)
                            else:
                                group_stat_lists[sname][us_name].append(u_stat)
            group_stats = {}
            for sname, statlist in group_stat_lists.items():
                if sname not in ["success", "concede", "all_users"]:
                    group_stats[sname] = mean(statlist)
                else:
                    group_stats[sname] = {}
                    for us_name, u_statlist in statlist.items():
                        if len(u_statlist) == 0:
                            group_stats[sname][us_name] = 0
                        else:
                            group_stats[sname][us_name] = mean(u_statlist)

            statlists_by_group[group_name] = group_stat_lists
            stats_by_group[group_name] = group_stats

        stats = {
            "endstate": "all",
            "prompts": "all",
            "levels": "all",
            "stats_by_pid": stats_by_pid,
            "stats_by_group": stats_by_group,
            "statlists_by_group": statlists_by_group
        }
        # if u != None:
        #     stats["endstate"] = u
        # if p != None:
        #     stats["prompts"] = p
        # if l != None:
        #     stats["levels"] = l

        with open(f"{dir}/stats{view_name}.json", "w") as f:
            json.dump(stats, f)


if __name__ == "__main__":
    node_df = pd.DataFrame(columns=["Id", "PuzzleId", "State", "GridValue", "MoveIds"])
    edge_df = pd.DataFrame(
        columns=[
            "Source",
            "Target",
            "UserId",
            "MoveNumber",
            "UserSuccess",
            "SolverValue",
            "MoveValue",
            "PromptMode",
            "LevelMode",
        ]
    )
    state_to_node_id = {}
    label_to_grid = {}
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
    clean_data, action_json = load_online_data(online_dir)
    session_outcome_json = {}
    puzzle_checks = {
        "hub2.1": 0,
        "hub2.2": 0,
        "hub2.3": 0
    }
    for user_id, user_data in clean_data.items():
        for puzzle_id, session in user_data["puzzles"].items():
            if puzzle_id in puzzle_checks:
                puzzle_checks[puzzle_id] = puzzle_checks[puzzle_id] + 1
            else:
                continue
            recovered_moves = recover_moves(
                puzzle_id,
                session["puzzle"],
                session["hints"],
                user_id,
                user_data["promptMode"],
                user_data["levelMode"],
                session["moves"],
                session["success"],
                state_to_node_id,
                node_df,
                edge_df,
                action_json,
                session["session_id"],
                session_outcome_json,
            )
            output_path = (
                f"{online_dir}/recovered_trees/{user_id}/recovered_tree_{puzzle_id}.txt"
            )
            output_file = Path(output_path)
            output_file.parent.mkdir(exist_ok=True, parents=True)
            move_file = open(output_path, "w")
            print_moves(move_file, session["puzzle"], session["hints"], recovered_moves)
    with open(f"{online_dir}/updated_action_data.json", "w") as f:
        json.dump(action_json, f)
    with open(f"{online_dir}/session_outcome.json", "w") as f:
        json.dump(session_outcome_json, f)
    print(puzzle_checks)

    dir = "user_data/online_puzzle_study"
    # edge_df.to_csv(f"{dir}/edgegraph.csv", index=False)
    # node_df.to_csv(f"{dir}/nodegraph.csv", index=False)
    edge_df = pd.read_csv(f"{dir}/edgegraph.csv")
    node_df = pd.read_csv(f"{dir}/nodegraph.csv")
    gen_data_views(dir, edge_df, node_df)
