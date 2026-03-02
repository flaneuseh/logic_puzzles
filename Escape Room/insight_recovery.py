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
import arrow
from datetime import timezone


ultraimport("__dir__/../LogicPuzzles.py", package="main")
from main.LogicPuzzles import (
    Solver,
    Category,
    Puzzle,
    Insight,
    CONFIDENT_MARKS,
    TENTATIVE_MARKS,
    MOVE_MARKS,
    YES_MARKS,
    NO_MARKS, 
    BLANK_MARKS,
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


SOLVER = Solver()

# Determine whether move is correct, incorrect, or neutral,
# with respect to the solution grid (not the solution-blind insights)
def get_move_value(curr_state, move, solution):
    value = "neutral"
    loc, move_sy = move
    curr_sy = curr_state.get_symbol(*loc)
    soln_sy = solution.get_symbol(*loc)
    # The cell is part of the current move.
    if move_sy == soln_sy:
        value = "correct"
    elif move_sy in CONFIDENT_MARKS:
        value = "incorrect"
    elif curr_sy in CONFIDENT_MARKS and curr_sy != soln_sy:
            # The current cell is wrong.
            if move_sy == "_" or (move_sy in YES_MARKS and soln_sy in YES_MARKS) or (move_sy in NO_MARKS and soln_sy in NO_MARKS):
                # The move is correcting a mistake.
                value = "correct"

    return value

def breakdown_move(move_diff):
    breakdown = []
    for cat1 in move_diff.categories:
        for cat2 in move_diff.categories:
            if cat1 == cat2:
                continue
            for ent1 in cat1.entities:
                for ent2 in cat2.entities:
                    sy = move_diff.get_symbol(cat1, cat2, ent1, ent2)
                    if sy == None:
                        continue
                    if sy in MOVE_MARKS:
                        loc = (cat1, cat2, ent1, ent2)
                        breakdown.append((loc, sy))
    return breakdown

# Get the node at grid_id, creating it if it does not already exist.
def get_grid_node_id(puzzle_id, grid_id, value, grid_to_label, node_df):
    if grid_id in grid_to_label:
        # Return the existing node
        return grid_to_label[grid_id]
    node_id = randint(10000, 99999)
    while node_id in grid_to_label.values():
        node_id = randint(10000, 99999)
    grid_to_label[grid_id] = node_id
    node_row = [node_id, puzzle_id, grid_id, value]
    node_df.loc[len(node_df)] = node_row
    return node_id

def get_grid_id(puzzle_id, state):
    grid_str = state.print_grid()
    grid_id = f"{puzzle_id}:{grid_str}"
    return grid_id

def get_composite_moves(puzzle_id, curr_state, solution, s_moves):
    # Moves that reach the same grid state are collapsed to only the move that is the highest in the insight DAG
    collapsed_moves = {}
    for s_move in s_moves:
        move = s_move["move"]
        move_state = deepcopy(curr_state)
        move_state.answer(*move)
            
        grid_id = get_grid_id(puzzle_id, move_state)
        insight = s_move["insight"]
        comparison_insight = None
        if grid_id in collapsed_moves:
            comparison_insight = collapsed_moves[grid_id]["insight"]
        if (
            grid_id not in collapsed_moves
            or insight < comparison_insight
        ):
            # Keep the move with the lowest ranked insight, as before
            grid_value = get_move_value(curr_state, move, solution)
            collapsed_moves[grid_id] = {
                "hint_idx": s_move["hint_idx"],
                "insight": s_move["insight"],
                "state": move_state,
                "grid_value": grid_value,
                "move": move,
            }
            if s_move["repair"]:
                collapsed_moves[grid_id]["solver_value"] = "repair"
            else:
                collapsed_moves[grid_id]["solver_value"] = "insight"
        if comparison_insight and insight != comparison_insight and insight.depth() == comparison_insight.depth():
            # If this ever triggers, we will have to decide how to handle the edge case
            print(f"found equivalent moves with equally ranked different insights: {insight} vs {comparison_insight}")

    for c_move in collapsed_moves.copy().values():
        # Find alternative states by setting the changed symbol to the other options.
        # This is either overconfidence (e.g. marking O when the solver would mark Y),
        # uncertainty (e.g. marking Y when the solver would mark O), or
        # contradiction (e.g. marking X when the solver would mark O).
        move = c_move["move"]
        loc, og_sy = move
        alt_moves = {}
        if og_sy == "O":
            # alt_moves["X"] = "contradiction"
            alt_moves["Y"] = "uncertain"
            # alt_moves["N"] = "contradiction"
        elif og_sy == "X":
            # alt_moves["O"] = "contradiction"
            # alt_moves["Y"] = "contradiction"
            alt_moves["N"] = "uncertain"
        elif og_sy == "Y":
            alt_moves["O"] = "overconfident"
            # Since this is an uncertain move, don't mark a contradiction.
        elif og_sy == "N":
            # Currently, the solver never marks "N", but include this case for completeness
            alt_moves["X"] = "overconfident"
            # Since this is an uncertain move, don't mark a contradiction.

        for alt_sy, solver_value in alt_moves.items():
            # Create a full copy of the collapsed move and replace relevant values with alternates.
            alt_move = deepcopy(c_move)
            alt_move["move"] = (loc, alt_sy)
            alt_move["og_sy"] = og_sy
            grid_value = get_move_value(curr_state, alt_move["move"], solution)
            alt_move["solver_value"] = solver_value
            alt_move["grid_value"] = grid_value

            alt_state = deepcopy(curr_state)
            alt_state.answer(*move)
            grid_id = get_grid_id(puzzle_id, alt_state)
            if grid_id not in collapsed_moves:
                collapsed_moves[grid_id] = alt_move
            else:
                # Collapse equivalent grid ids, taking into account the confidence of the respective moves
                # as well as their insight rankings.
                ex_move = collapsed_moves[grid_id]
                ex_solver_value = ex_move["solver_value"]
                alt_solver_value = alt_move["solver_value"]
                ex_insight = ex_move["insight"]
                alt_insight = alt_move["insight"]
                if "og_sy" in ex_move:
                    # The comparison move is also an alternative.
                    if og_sy == ex_move["og_sy"] or alt_solver_value == ex_solver_value:
                        # The moves are the same symbol, or they have the same confidence;
                        # take the lower-depth insight.
                        if alt_insight < ex_insight:
                            collapsed_moves[grid_id] = alt_move
                            continue
                        if alt_insight != ex_insight and alt_insight.depth() == ex_insight.depth:
                            # Again, we will handle this edge case if it triggers. 
                            print(f"found equivalent moves with equally ranked different insights: {insight} vs {comparison_insight}")       
                    else:
                        # Different og_sy and different solver_values.
                        if alt_solver_value in ["overconfident", "uncertain"] and ex_solver_value == "contradiction":
                            # ex_solver_value must be "contradiction", as they have the same symbol (uncertain marks may not be overconfident; X and O cannot be uncertain)
                            # Contradictions always "lose".
                            collapsed_moves[grid_id] = alt_move
                            continue
                else:
                    # The alternative matches one of the moves suggested by the solver.
                    if alt_sy in CONFIDENT_MARKS:
                        # The move matches an insight already discovered by the solver, give credit to that insight.
                        continue

                    if alt_solver_value == "uncertain":
                        # When the solver and the move are both uncertain, use the lowest ranked insight.
                        if alt_insight.value < ex_insight.value:
                            collapsed_moves[grid_id] = alt_move
                            continue
                    # Otherwise, the solver is uncertain and the move is a contradiction; contradictions always "lose".

    # Find collapsed moves that are equivalent (same type, insight, hint, and solver_value, different grid ids)
    composite_moves = {}
    grid_id_to_comp_id = {}
    for grid_id, c_move in collapsed_moves.items():
        hint_idx = c_move["hint_idx"]
        insight = c_move["insight"]
        solver_value = c_move["solver_value"]
        comp_id = f"{insight}:hint-{hint_idx}:{solver_value}"

        if comp_id not in composite_moves:
            composite_moves[comp_id] = {
                "insight": insight,
                "hint_idx": hint_idx,
                "solver_value": solver_value,
                "moves": {},
            }
        composite_moves[comp_id]["moves"][grid_id] = {
            "grid_value": c_move["grid_value"],
            "move": c_move["move"],
        }
        grid_id_to_comp_id[grid_id] = comp_id

    return composite_moves, grid_id_to_comp_id


def get_solver_moves(puzzle, hints):
    # Get all conceivable moves for the puzzle state. Include moves from the "opened"(crossed out) version of the puzzle,
    # as the user could be holding this information in their head (particularly if they are in a puzzle that doesn't allow X marks or a very easy puzzle), and we want to catch as many possible insights as we can.
    opened_puzzle = deepcopy(puzzle)
    SOLVER.apply_cross_out(opened_puzzle, True)
    _, s_moves = SOLVER.get_available_moves(puzzle, hints)
    _, opened_moves = SOLVER.get_available_moves(opened_puzzle, hints)
    dedupe_moves = s_moves
    dedupe_o_moves = []
    for o_move in opened_moves:
        duplicate = False
        for s_move in s_moves:
            if (
                o_move["hint_idx"] == s_move["hint_idx"]
                and o_move["insight"] == s_move["insight"]
                and o_move["move"] == s_move["move"]
            ):
                duplicate = True
                break
        if not duplicate:
            # o_move["type"] = f"(after filling in openings) {o_move['type']}"
            dedupe_o_moves.append(o_move)
    dedupe_moves.extend(dedupe_o_moves)
    return dedupe_moves


def get_possible_moves(puzzle, move, available_moves):
    possible_moves = []
    recovered = False

    changed, _ = puzzle.answer(*move)
    (u_loc, u_sy) = move
    if not changed:
        return possible_moves

    for s_move in available_moves:
        (s_loc, s_sy) = s_move["move"] 
        
        if u_loc == s_loc:
            # The moves affect the same grid location and have symbols in the same "sign"
            if (
                (
                    u_sy in YES_MARKS
                    and s_sy in YES_MARKS
                )
                or (
                    u_sy in NO_MARKS
                    and s_sy in NO_MARKS
                )
                or (u_sy == "_" and s_sy == "_")
            ):
                poss_move = {
                    "hint_idx": s_move["hint_idx"],
                    "insight": s_move["insight"],
                    "repair": s_move["repair"],
                    "move": move,
                    "violation": False,
                    "confidence": "confident",
                }
                if u_sy in TENTATIVE_MARKS or s_sy in TENTATIVE_MARKS:
                    # At least one of the two marked a tentative mark, so the insight is tentative.
                    poss_move["confidence"] = "tentative"
                    if u_sy not in TENTATIVE_MARKS:
                        # The user marked a confident mark, while the solver was tentative.
                        poss_move["confidence"] = (
                            "overconfident"
                        )
                    elif s_sy not in TENTATIVE_MARKS:
                        # The user marked a tentative mark, while the solver was certain.
                        poss_move["confidence"] = (
                            "uncertain"
                        )
                if "indexed_hint" in s_move:
                    poss_move["indexed_hint"] = s_move[
                        "indexed_hint"
                    ]
                if (u_sy == "_" and s_sy == "_"):
                    print("POSSIBLE ERASE INSIGHT FOUND")
                    print(poss_move)
                possible_moves.append(poss_move)
                recovered = True
            elif u_sy != "_" and s_sy in CONFIDENT_MARKS:
                # The user made a move that contradicts the solver.
                poss_move = {
                    "hint_idx": s_move["hint_idx"],
                    "insight": None,
                    "repair": False,
                    "violation": True,
                    "violated_insight": s_move["insight"],
                    "move": move,
                    "confidence": "contradiction",
                }
                if "indexed_hint" in s_move:
                    poss_move["indexed_hint"] = s_move[
                        "indexed_hint"
                    ]
                possible_moves.append(poss_move)
                recovered = True
    if not recovered:
        possible_moves.append({
            "hint_idx": -100,
            "insight": None,
            "repair": False,
            "move": move,
            "violation": False,
            "confidence": "unknown",
        })

    return possible_moves


def get_insight_node_id(
    user_history, curr_grid_value, puzzle_id, node_df, state_to_node_id, curr_move_id
):
    # Sort all the hint insights the user has made so that users reaching insights in different orders are considered to reach the same state.

    move_ids = {curr_move_id}
    for move_id, _ in user_history.values():
        if (
            "unknown" not in move_id
            and "OPENING" not in move_id
            and "CROSS_OUT" not in move_id
        ):      
            # Only save the current unknown/opening/cross_out
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

def get_type_str(hint_idx):
    typestr = "hint"
    if hint_idx == -3:
        typestr = "transitives"
    elif hint_idx == -2:
        typestr = "cross outs"
    elif hint_idx == -1:
        typestr = "openings"
    return typestr

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
    source_id = get_insight_node_id(
        user_history, "start", puzzle_id, node_df, state_to_node_id, "start"
    )
    success_id = get_insight_node_id(
        user_history, "success", puzzle_id, node_df, state_to_node_id, "success"
    )
    failure_id = get_insight_node_id(
        user_history, "failure", puzzle_id, node_df, state_to_node_id, "failure"
    )
    partial_id = get_insight_node_id(
        user_history, "partial", puzzle_id, node_df, state_to_node_id, "partial"
    )

    blank_puzzle = deepcopy(puzzle)

    solution, _, _ = SOLVER.apply_hints(puzzle, hints)

    r_moves = []
    mi = 0
    for time, raw_str, rec_moves in u_moves:
        result = deepcopy(puzzle)  # copy that will have current move applied

        available_moves = get_solver_moves(puzzle, hints)  # All solver-aware moves
        composite_moves, grid_id_to_comp_id = get_composite_moves(
            puzzle_id, puzzle, solution, available_moves
        )  # Available solver moves collapsed into individual insights

        for move in rec_moves:
            result.answer(*move)
        u_move_diff, changed = SOLVER.get_move_diff(puzzle, result, True)

        if not changed:
            continue

        if result.print_grid() == blank_puzzle.print_grid():
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

        # Reset result to apply rec_moves one at a time.
        result = deepcopy(puzzle)
        for rec_move in rec_moves:
            possible_moves = get_possible_moves(result, rec_move, available_moves)
    
            board_state = result.print_grid()
            move_value = get_move_value(u_move_diff, rec_move, solution)
            r_move = {
                "puzzle_state": deepcopy(result),
                "board_state": board_state,
                "move": rec_move,
                "possible_moves": possible_moves,
                "value": move_value,
            }

            r_moves.append((time, raw_str, r_move))

            grid_id = get_grid_id(puzzle_id, result)

            solver_value = f"unknown-{move_value}"

            diff_loc, diff_sy = rec_move
            diff_loc_str = get_diff_loc_str(diff_loc)
            move_id = f"{solver_value}:{diff_loc_str}:{diff_sy}"
            if grid_id in grid_id_to_comp_id:
                comp_id = grid_id_to_comp_id[grid_id]
                composite = composite_moves[comp_id]
                # In the future, consider the case of the same hint having the same insight applied multiple times
                # A "composite grid" in that case is defined to be the total of all moves that can be applied with
                # the current insight and hint, *including moves that may have already been applied in an earlier state*
                # composite_grid = get_composite_grid(composite)
                hint_idx = composite["hint_idx"]
                typestr = get_type_str(hint_idx)
                insight_str = f"{composite['insight']}"
                hint = hints[hint_idx]
                if composite["solver_value"] != "contradiction":
                    solver_value = composite["solver_value"]
                    if solver_value in ["uncertain", "overconfident"]:
                        solver_value = f"insight-{solver_value}"

                    # Add the insight to the action JSON.
                    move_idx = 0
                    for i, move_data in enumerate(action_json[session_id]):
                        if move_data["time"] == time:
                            move_idx = i
                            break
                    action_json[session_id][move_idx]["insight"] = insight_str
                    move_id = f"{typestr}:{hint}:{insight_str}"
                else:
                    move_id = f"{typestr}:{hint}:unknown"

            curr_grid_value = "correct"
            if SOLVER.repair(result, solution, False):
                curr_grid_value = "incorrect"

            diff_loc_str = f"diff_loc"
            if diff_loc_str in user_history:
                _, h_sy = user_history[diff_loc_str]
                if h_sy != diff_sy:
                    user_history[diff_loc_str] = (move_id, diff_sy)
            else:
                user_history[diff_loc_str] = (move_id, diff_sy)
            target_id = get_insight_node_id(
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
                available_insights.add(f"{s_move['insight']}")

        session_outcome_json[session_id] = {
            "outcome": u_success,
            "available_insights": list(available_insights),
        }

        if (edge_df == edge_row).all(1).any():
            # Only add an edge once per user (while user retracing their steps could be interesting if looking at single user, we are interested in comparing users.)
            return r_moves
        edge_df.loc[len(edge_df)] = edge_row
    return r_moves


def clean_vr_data(raw_df, start_time):
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

    for [puzzle_id, raw_puzzle_id] in puzzle_name_mapping.items():
        raw_session_df = raw_df[
            raw_df["ParentChain"].str.contains(raw_puzzle_id)
        ].copy()
        raw_moves = list(
            raw_session_df[["TimeStampUTC", "PuzzleUniqueID"]].itertuples(
                index=False, name=None
            )
        )

        start_dt = arrow.get(start_time).datetime
        start_secs = start_dt.replace(tzinfo=timezone.utc).timestamp()
        timed_moves = []
        for time, raw_move in raw_moves:
            dt = arrow.get(time).datetime
            secs = dt.replace(tzinfo=timezone.utc).timestamp() - start_secs
            timed_moves.append((secs, raw_move))
        clean_data[puzzle_id] = clean_vr_moves(puzzle_id, timed_moves)

    return clean_data


def clean_online_moves(puzzle, hints, raw_moves):
    user_puzzle = deepcopy(puzzle)
    clean_moves = []
    raw_moves = list(
        filter(
            lambda rm: rm["type"] == "cellChange"
            or (rm["type"] == "button" and rm["button"] == "clear"),
            raw_moves,
        )
    )
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
                            moves.append(((cat1, cat2, ent1, ent2), new_symbol))
        for move in moves:
            user_puzzle.answer(*move)

        clean_moves.append((time, puzzle_str, moves))
    solution, _, _ = SOLVER.apply_hints(puzzle, hints)
    correct = not SOLVER.repair(user_puzzle, solution, False)
    user_success = "failure"
    if correct:
        if user_puzzle.is_complete():
            user_success = "success"
        else:
            user_success = "partial"
    return clean_moves, user_success


def clean_vr_moves(clean_key, raw_moves):
    match clean_key:
        case "spoke_pasta":
            session = _clean_vr_moves__spoke_pasta(raw_moves)
        case "spoke_sunlight":
            session = _clean_vr_moves__spoke_sunlight(raw_moves)
        case "spoke_water":
            session = _clean_vr_moves__spoke_water(raw_moves)
        case "spoke_protein":
            session = _clean_vr_moves__spoke_protein(raw_moves)
        case "hub_soup":
            session = _clean_vr_moves__hub_soup(raw_moves)
    solution, is_valid, _ = SOLVER.apply_hints(session["puzzle"], session["hints"])
    assert is_valid
    user_puzzle = deepcopy(session["puzzle"])
    for move in session["moves"]:
        _, _, rec_moves = move
        for rec_move in rec_moves:
            user_puzzle.answer(*rec_move)
    correct = not SOLVER.repair(user_puzzle, solution, False)
    user_success = "failure"
    if correct:
        if user_puzzle.is_complete():
            user_success = "success"
        else:
            user_success = "partial"
    session["success"] = user_success

    return session


def _clean_vr_moves__spoke_pasta(raw_moves):
    puzzle = PUZZLE_DEFS["spoke_pasta"]["puzzle"]
    hints = PUZZLE_DEFS["spoke_pasta"]["hints"]
    clean_moves = []

    for time, raw_move in raw_moves:
        entities = raw_move.split("Pasta Bowl - ")
        if len(entities) == 1:
            entities = raw_move.split("Pata Bowl - ")
        if len(entities) == 1:
            entities = raw_move.split("Pata Bowl  - ")
        if len(entities) == 1:
            entities = raw_move.split("Pasta Bowl  - ")

        ordered_moves = []
        for sauce in PASTA_SAUCES.entities:
            ordered_moves.append((
                time,
                f"{raw_move} ({entities[0]}, {sauce}, *)",
                [((PASTA_SHAPES, PASTA_SAUCES, entities[0], sauce), "*")],
            ))
        if entities[1] != "Reset":
            non_os = []
            for sauce in PASTA_SAUCES.entities:
                loc = (PASTA_SHAPES, PASTA_SAUCES, entities[0], sauce)
                if sauce == entities[1]:
                    ordered_moves.append((time, f"{raw_move} ({entities[0]}, {sauce}, O)", [(loc, "O")]))
                else:
                    # Each pasta can only have one sauce at a time.
                    non_os.append((time, f"{raw_move} ({entities[0]}, {sauce}, X)", [(loc, "X")]))
            ordered_moves.extend(non_os)
            for i, move in enumerate(ordered_moves):
                move = list(move)
                time = move[0]
                move[0] = f"{time}:{i}"
                clean_moves.append(tuple(move))

    return {
        "puzzle": puzzle,
        "hints": hints,
        "moves": clean_moves,
    }


def _clean_vr_moves__spoke_sunlight(raw_moves):
    puzzle = PUZZLE_DEFS["spoke_sunlight"]["puzzle"]
    hints = PUZZLE_DEFS["spoke_sunlight"]["hints"]
    clean_moves = []

    for time, raw_move in raw_moves:
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

        ordered_moves = []
        for h in SUNLIGHT_HOURS.entities:
            ordered_moves.append((
                time,
                f"{raw_move} ({h}, {plant}, *)",
                [((SUNLIGHT_HOURS, SUNLIGHT_PLANTS, h, plant), "*")],
            ))
        if len(plant_parts) != 3:
            non_os = []
            for h in SUNLIGHT_HOURS.entities:
                loc = (SUNLIGHT_HOURS, SUNLIGHT_PLANTS, h, plant)
                if h == hr:
                    ordered_moves.append((time, f"{raw_move} ({h}, {plant}, O)", [(loc, "O")]))
                else:
                    non_os.append((time, f"{raw_move} ({h}, {plant}, X)", [(loc, "X")]))
            ordered_moves.extend(non_os)
        for i, move in enumerate(ordered_moves):
            move = list(move)
            time = move[0]
            move[0] = f"{time}:{i}"
            clean_moves.append(tuple(move))

    return {
        "puzzle": puzzle,
        "hints": hints,
        "moves": clean_moves,
    }


def _clean_vr_moves__spoke_water(raw_moves):
    puzzle = PUZZLE_DEFS["spoke_water"]["puzzle"]
    hints = PUZZLE_DEFS["spoke_water"]["hints"]
    clean_moves = []

    for time, raw_move in raw_moves:
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
        ordered_moves = []
        for o in ["20oz", "40oz", "60oz", "80oz"]:
            ordered_moves.append(
                (time, f"{raw_move} ({plant}, {o}, *)", [((WATER_PLANTS, WATER_OZ, plant, o), "*")])
            )
        non_os = []
        for o in ["20oz", "40oz", "60oz", "80oz"]:
            loc = (WATER_PLANTS, WATER_OZ, plant, o)
            if o == oz:
                ordered_moves.append((time, f"{raw_move} ({plant}, {o}, O)", [(loc, "O")]))
            else:
                non_os.append((time, f"{raw_move} ({plant}, {o}, X)", [(loc, "X")]))
        ordered_moves.extend(non_os)
        for i, move in enumerate(ordered_moves):
            move = list(move)
            time = move[0]
            move[0] = f"{time}:{i}"
            clean_moves.append(tuple(move))

    return {
        "puzzle": puzzle,
        "hints": hints,
        "moves": clean_moves,
    }


def _clean_vr_moves__spoke_protein(raw_moves):
    puzzle = PUZZLE_DEFS["spoke_protein"]["puzzle"]
    hints = PUZZLE_DEFS["spoke_protein"]["hints"]
    clean_moves = []

    for time, raw_move in raw_moves:
        parts = raw_move.split(" - ")
        entity_parts = parts[0].split(" Token Socket ")
        food = entity_parts[0]
        if food == "Penuts":
            food = "Peanuts"
        grams_idx = int(entity_parts[1].strip("()")) - 1
        grams = PROTEIN_GRAMS.entities[grams_idx]
        loc = (PROTEIN_FOODS, PROTEIN_GRAMS, food, grams)

        sy = "*"
        if parts[1] == "Filled":
            sy = "O"

        clean_moves.append((f"{time}:0", raw_move, [(loc, sy)]))

    return {
        "puzzle": puzzle,
        "hints": hints,
        "moves": clean_moves,
    }


def _clean_vr_moves__hub_soup(raw_moves):
    puzzle = PUZZLE_DEFS["hub_soup_alt"]["puzzle"]
    hints = PUZZLE_DEFS["hub_soup_alt"]["hints"]
    clean_moves = []

    for time, raw_move in raw_moves:
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

        loc = [cat1, cat2, ent1, ent2]
        sy = ""
        match parts[1]:
            case "Filled GreenPin":
                sy = "O"
            case "Removed GreenPin":
                sy = "*"
            case "Filled RedPin":
                sy = "X"
            case "Removed RedPin":
                sy = "*"
            case _:
                continue

        clean_moves.append((f"{time}:0", raw_move, [(loc, sy)]))

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

    pre = deepcopy(puzzle)
    post = deepcopy(puzzle)

    for idx, (time, raw_state, move) in enumerate(moves):
        if move == None:
            file.write(f"{time}: User Move {idx+1} (Wrong, Ignored): {raw_state}\n")
        else:
            file.write(f"User Move {idx+1} ({move['value']}): {raw_state}\n")
            post.answer(*move["move"])
            move_diff, _ = SOLVER.get_move_diff(pre, post, False)
            pre = deepcopy(post)
            board_str = move_diff.print_grid().splitlines()
            for line in board_str:
                file.write(f"{line}\n")

            file.write("Possible Reasonings: \n")
            for i, poss_move in enumerate(move["possible_moves"]):
                typestr = get_type_str(poss_move["hint_idx"])
                if poss_move["repair"]:
                    typestr += " (repair)"
                if poss_move["confidence"] != "confident":
                    typestr += f" ({poss_move['confidence']})"
                if poss_move["violation"]:
                    typestr += " (violation)"

                if "typestr" == "hint":
                    typestr += (
                        f" - \"{hint_to_english(hints['poss_move']['hint_idx'])}\""
                    )
                file.write(f"{i+1}: {typestr} - {poss_move['insight']}\n")

        file.write(f"\n\n")


def load_vr_data(file):
    df = pd.read_csv(file)

    first_move = df.iloc[0]
    if first_move["PuzzleUniqueID"] != "GameStart" or first_move["ElementType"] != "Scene":
        print("FIRST MOVE IN UNEXPECTED FORMAT:")
        print(first_move)
    
    start_time = first_move["TimeStampUTC"]

    df = df[df["ElementType"] == "Interaction"].copy()
    # df = df[df["Outcome"] != "WrongMove"].copy()
    df = df.drop(
        columns=[
            "TimeFromLastMove",
            "ElementType",
            "IsCompleted",
            "Outcome",
        ]
    )

    return df, start_time


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
    combined_view = pd.merge(edge_view, node_view, left_on="Target", right_on="Id")
    # % successful, % concede, % success but failed at least once, % concede while partially correct

    puzzle_ids = list(combined_view["PuzzleId"].unique())

    stats_by_pid = {}
    for pid in puzzle_ids:
        pg_view = combined_view.copy()
        pg_view = pg_view[pg_view["PuzzleId"] == pid]
        real_moves = pg_view[
            pg_view["MoveValue"].isin(["correct", "incorrect", "neutral"])
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
            view_stats["pct_success"] = float(
                success_counts["success"] / len(user_view)
            )
            view_stats["num_fail"] = int(success_counts["failure"])
            view_stats["pct_fail"] = float(success_counts["failure"] / len(user_view))
            view_stats["num_partial"] = int(success_counts["partial"])
            view_stats["pct_partial"] = float(
                success_counts["partial"] / len(user_view)
            )
            view_stats["num_concede"] = int(
                success_counts["failure"] + success_counts["partial"]
            )
            view_stats["pct_concede"] = float(
                (success_counts["failure"] + success_counts["partial"]) / len(user_view)
            )
        if success_counts["failure"] + success_counts["partial"] == 0:
            view_stats["pct_partial_of_concede"] = 0
        else:
            view_stats["pct_partial_of_concede"] = float(
                success_counts["partial"]
                / (success_counts["failure"] + success_counts["partial"])
            )
        if success_counts["success"] == 0:
            view_stats["num_had_error_of_success"] = 0
            view_stats["pct_had_error_of_success"] = 0
        else:
            view_stats["num_had_error_of_success"] = len(success_and_incorrect)
            view_stats["pct_had_error_of_success"] = float(
                len(success_and_incorrect) / success_counts["success"]
            )

        all_view = pg_view.copy()
        success_view = all_view.copy()
        success_view = success_view[success_view["UserSuccess"] == "success"]
        concede_view = all_view.copy()
        concede_view = concede_view[concede_view["UserSuccess"] != "success"]

        first_move = all_view[all_view["MoveNumber"] == 0]
        second_move = all_view[all_view["MoveNumber"] == 1]
        third_move = all_view[all_view["MoveNumber"] == 2]

        third_move_users = third_move["UserId"]
        if len(third_move_users) != len(third_move_users.unique()):
            print("EXTRA MOVES WERE FOUND")
            print(pid)
            print(third_move_users)

        first_move = first_move[first_move["UserId"].isin(third_move_users)]
        second_move = second_move[second_move["UserId"].isin(third_move_users)]

        if len(first_move) != len(second_move) or len(second_move) != len(third_move):
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
        first_move_counts = pd.merge(first_move, first_move_counts, on="Target")
        first_move_counts = first_move_counts[
            first_move_counts["target_first_move_count"] > 1
        ]

        second_move_counts = (
            second_move.value_counts("Target")
            .rename_axis("Target")
            .reset_index(name="target_second_move_count")
        )
        second_move_counts = pd.merge(second_move, second_move_counts, on="Target")
        second_move_counts = second_move_counts[
            second_move_counts["target_second_move_count"] > 1
        ]

        third_move_counts = (
            third_move.value_counts("Target")
            .rename_axis("Target")
            .reset_index(name="target_third_move_count")
        )
        third_move_counts = pd.merge(third_move, third_move_counts, on="Target")
        third_move_counts = third_move_counts[
            third_move_counts["target_third_move_count"] > 1
        ]

        last_move = all_view[all_view["MoveValue"] == ""]
        last_move_counts = (
            last_move.value_counts("Source")
            .rename_axis("Source")
            .reset_index(name="source_last_move_count")
        )
        last_move_counts = pd.merge(last_move, last_move_counts, on="Source")
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
            incorrect_states = u_view[u_view["GridValue"] == "incorrect"]
            real_moves = u_view[
                u_view["MoveValue"].isin(["correct", "incorrect", "neutral"])
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
                    "per_user_pct_correct_state": [],
                    "avg_pct_correct_state": 0,
                    "per_user_pct_incorrect_state": [],
                    "avg_pct_incorrect_state": 0,
                    "per_user_pct_correct_move": [],
                    "avg_pct_correct_move": 0,
                    "per_user_pct_incorrect_move": [],
                    "avg_pct_incorrect_move": 0,
                    "per_user_pct_neutral_move": [],
                    "avg_pct_neutral_move": 0,
                    "per_user_pct_insight": [],
                    "avg_pct_insight": 0,
                    "per_user_pct_unknown_correct": [],
                    "avg_pct_unknown_correct": 0,
                    "per_user_pct_unknown_incorrect": [],
                    "avg_pct_unknown_incorrect": 0,
                    "per_user_pct_unknown_neutral": [],
                    "avg_pct_unknown_neutral": 0,
                    "num_users_had_three_moves": 0,
                    "pct_users_share_first_move": 0,
                    "pct_users_share_second_move": 0,
                    "pct_users_share_third_move": 0,
                    "pct_users_share_last_move": 0,
                    "num_users_share_first_move": 0,
                    "num_users_share_second_move": 0,
                    "num_users_share_third_move": 0,
                    "num_users_share_last_move": 0,
                }
                continue

            user_counts["PctCorrectState"] = (
                user_counts["correct_state_count"] / user_counts["move_count"]
            )
            user_counts["PctIncorrectState"] = (
                user_counts["incorrect_state_count"] / user_counts["move_count"]
            )

            user_counts["PctCorrectMove"] = (
                user_counts["correct_move_count"] / user_counts["move_count"]
            )
            user_counts["PctIncorrectMove"] = (
                user_counts["incorrect_move_count"] / user_counts["move_count"]
            )
            user_counts["PctNeutralMove"] = (
                user_counts["neutral_move_count"] / user_counts["move_count"]
            )

            view_stats[u_name]["per_user_pct_correct_state"] = user_counts[
                "PctCorrectState"
            ].tolist()
            view_stats[u_name]["avg_pct_correct_state"] = float(
                user_counts["PctCorrectState"].mean()
            )
            view_stats[u_name]["per_user_pct_incorrect_state"] = user_counts[
                "PctIncorrectState"
            ].tolist()
            view_stats[u_name]["avg_pct_incorrect_state"] = float(
                user_counts["PctIncorrectState"].mean()
            )

            view_stats[u_name]["per_user_pct_correct_move"] = user_counts[
                "PctCorrectMove"
            ].tolist()
            view_stats[u_name]["avg_pct_correct_move"] = float(
                user_counts["PctCorrectMove"].mean()
            )
            view_stats[u_name]["per_user_pct_incorrect_move"] = user_counts[
                "PctIncorrectMove"
            ].tolist()
            view_stats[u_name]["avg_pct_incorrect_move"] = float(
                user_counts["PctIncorrectMove"].mean()
            )
            view_stats[u_name]["per_user_pct_neutral_move"] = user_counts[
                "PctNeutralMove"
            ].tolist()
            view_stats[u_name]["avg_pct_neutral_move"] = float(
                user_counts["PctNeutralMove"].mean()
            )

            u_view = u_view.replace({
                "SolverValue": {
                    "contradiction": "unknown-incorrect",
                    "uncertain": "insight",
                    "overconfident": "insight",
                }
            })
            insight_moves = u_view[u_view["SolverValue"] == "insight"]
            unknown_correct_moves = u_view[u_view["SolverValue"] == "unknown-correct"]
            unknown_incorrect_moves = u_view[
                u_view["SolverValue"] == "unknown-incorrect"
            ]
            unknown_neutral_moves = u_view[u_view["SolverValue"] == "unknown-neutral"]
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
                user_counts["insight_move_count"] / user_counts["move_count"]
            )
            user_counts["PctUnknownCorrect"] = (
                user_counts["unknown_correct_move_count"] / user_counts["move_count"]
            )
            user_counts["PctUnknownIncorrect"] = (
                user_counts["unknown_incorrect_move_count"] / user_counts["move_count"]
            )
            user_counts["PctUnknownNeutral"] = (
                user_counts["unknown_neutral_move_count"] / user_counts["move_count"]
            )
            user_counts = user_counts.fillna(0)

            view_stats[u_name]["per_user_pct_insight"] = user_counts["PctInsight"].tolist()
            view_stats[u_name]["avg_pct_insight"] = float(
                user_counts["PctInsight"].mean()
            )
            view_stats[u_name]["per_user_pct_unknown_correct"] = user_counts[
                "PctUnknownCorrect"
            ].tolist()
            view_stats[u_name]["avg_pct_unknown_correct"] = float(
                user_counts["PctUnknownCorrect"].mean()
            )
            view_stats[u_name]["per_user_pct_unknown_incorrect"] = user_counts[
                "PctUnknownIncorrect"
            ].tolist()
            view_stats[u_name]["avg_pct_unknown_incorrect"] = float(
                user_counts["PctUnknownIncorrect"].mean()
            )
            view_stats[u_name]["per_user_pct_unknown_neutral"] = user_counts[
                "PctUnknownNeutral"
            ].tolist()
            view_stats[u_name]["avg_pct_unknown_neutral"] = float(
                user_counts["PctUnknownNeutral"].mean()
            )

            curr_users = u_view["UserId"].unique()
            three_moves_curr = third_move[third_move["UserId"].isin(curr_users)]
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
            view_stats[u_name]["pct_users_share_last_move"] = len(last_users) / curr_num

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
                if pid == None or (group_name != "all" and group_name not in pid):
                    continue
                for sname, stat in stats.items():
                    if sname not in ["success", "concede", "all_users"]:
                        g_name = f"per_puzzle_{sname}"
                        if g_name not in group_stat_lists:
                            group_stat_lists[g_name] = []
                        group_stat_lists[g_name].append(stat)
                    else:
                        if sname not in group_stat_lists:
                            group_stat_lists[sname] = {}
                        for us_name, u_stat in stat.items():
                            per_user_name = f"{us_name}"
                            per_puzzle_name = f"puzzle_{us_name}"
                            
                            if isinstance(u_stat, list):
                                if per_user_name not in group_stat_lists[sname]:
                                    group_stat_lists[sname][per_user_name] = []
                                group_stat_lists[sname][per_user_name].extend(u_stat)
                            else:
                                if per_puzzle_name not in group_stat_lists[sname]:
                                    group_stat_lists[sname][per_puzzle_name] = []
                                group_stat_lists[sname][per_puzzle_name].append(u_stat)
            group_stats = {}
            for sname, statlist in group_stat_lists.items():
                if sname not in ["success", "concede", "all_users"]:
                    g_name = f"avg_{sname}"
                    group_stats[g_name] = mean(statlist)
                else:
                    group_stats[sname] = {}
                    for us_name, u_statlist in statlist.items():
                        g_name = f"avg_{us_name}"
                        if len(u_statlist) == 0:
                            group_stats[sname][g_name] = 0
                        else:
                            group_stats[sname][g_name] = mean(u_statlist)

            statlists_by_group[group_name] = group_stat_lists
            stats_by_group[group_name] = group_stats

        stats = {
            "endstate": "all",
            "prompts": "all",
            "levels": "all",
            "stats_by_pid": stats_by_pid,
            "stats_by_group": stats_by_group,
            "statlists_by_group": statlists_by_group,
        }
        # if u != None:
        #     stats["endstate"] = u
        # if p != None:
        #     stats["prompts"] = p
        # if l != None:
        #     stats["levels"] = l

        with open(f"{dir}/stats{view_name}.json", "w") as f:
            json.dump(stats, f)


def action_json_movelist_from_moves(moves):
    action_list = []
    for time, raw_move, _ in moves:
        action_list.append({
            "time": time,
            "raw_move": raw_move,
        })
    return action_list

def reformat_vr_action_json(action_json):
    for session in action_json.values():
        for move_data in session:
            time = move_data["time"]
            real_time = time[:-2]
            move_no = time[-1]
            move_data["time"] = real_time
            move_data["move_no"] = move_no
    return action_json
    

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
    vr_dir = "user_data/vr_study"
    vr_users = [f.name for f in os.scandir("user_data/vr_study") if f.is_dir()]
    session_outcome_json = {}
    action_json = {}
    for user in vr_users:
        print(user)
        userfile = f"{vr_dir}/{user}/{user}_PuzzleLogs.csv"
        raw_df, start_time = load_vr_data(userfile)

        clean_data = clean_vr_data(raw_df, start_time)
        for puzzle_id, session in clean_data.items():
            session_id = f"{user}:{puzzle_id}"
            action_json[session_id] = action_json_movelist_from_moves(session["moves"])
            recovered_moves = recover_moves(
                puzzle_id,
                session["puzzle"],
                session["hints"],
                user,
                "",
                "",
                session["moves"],
                session["success"],
                state_to_node_id,
                node_df,
                edge_df,
                action_json,
                session_id,
                session_outcome_json,
            )
            output_path = f"{vr_dir}/{user}/recovered_tree_{puzzle_id}.txt"
            output_file = Path(output_path)
            output_file.parent.mkdir(exist_ok=True, parents=True)
            move_file = open(output_path, "w")
            print_moves(move_file, session["puzzle"], session["hints"], recovered_moves)

    dir = "user_data/vr_study"
    edge_df.to_csv(f"{vr_dir}/edgegraph.csv", index=False)
    node_df.to_csv(f"{vr_dir}/nodegraph.csv", index=False)
    action_json = reformat_vr_action_json(action_json)
    with open(f"{vr_dir}/updated_action_data.json", "w") as f:
        json.dump(action_json, f)
    with open(f"{dir}/session_outcome.json", "w") as f:
        json.dump(session_outcome_json, f)
    edge_df = pd.read_csv(f"{vr_dir}/edgegraph.csv")
    node_df = pd.read_csv(f"{vr_dir}/nodegraph.csv")
    gen_data_views(vr_dir, edge_df, node_df)

    online_dir = "user_data/online_puzzle_study"
    clean_data, action_json = load_online_data(online_dir)
    session_outcome_json = {}
    for user_id, user_data in clean_data.items():
        for puzzle_id, session in user_data["puzzles"].items():
            if session["session_id"] != "689b5a0a6bc6c32c3cb589a9":
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

    # edge_df.to_csv(f"{online_dir}/edgegraph.csv", index=False)
    # node_df.to_csv(f"{online_dir}/nodegraph.csv", index=False)
    edge_df = pd.read_csv(f"{online_dir}/edgegraph.csv")
    node_df = pd.read_csv(f"{online_dir}/nodegraph.csv")
    gen_data_views(online_dir, edge_df, node_df)
