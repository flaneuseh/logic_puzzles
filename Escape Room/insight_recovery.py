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

ultraimport("__dir__/../Insights/PuzzleAgent.py", package="insights")
from insights.PuzzleAgent import PuzzleAgent

SOLVER = Solver(set(), True)


def get_move_list_value(curr_state, moves, solution):
    value = "neutral"
    for move in moves:
        move_value = get_move_value(curr_state, move, solution)
        if move_value == "incorrect" or value == "neutral":
            # incorrect > correct > neutral
            value = move_value
    return value


# Determine whether move is correct, incorrect, or neutral,
# with respect to the solution grid (not the solution-blind insights)
def get_move_value(curr_state, move, solution):
    value = "neutral"
    loc, move_sy = move
    curr_sy = curr_state.get_symbol(*loc)
    soln_sy = solution.get_symbol(*loc)
    if move_sy == curr_sy:
        # The move is not actually a change.
        value = "neutral"
    elif move_sy == soln_sy:
        value = "correct"
    elif curr_sy == soln_sy:
        # The move is replacing a correct mark.
        value = "incorrect"
    elif move_sy in CONFIDENT_MARKS:
        value = "incorrect"
    elif curr_sy in CONFIDENT_MARKS and curr_sy != soln_sy:
        # The current cell is wrong.
        if (
            move_sy in BLANK_MARKS
            or (move_sy in YES_MARKS and soln_sy in YES_MARKS)
            or (move_sy in NO_MARKS and soln_sy in NO_MARKS)
        ):
            # The move is erasing a mistake.
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


def get_composite_moves(puzzle_id, curr_state, solution, multi_moves):
    # Moves that reach the same grid state are collapsed to only the move that is the highest in the insight DAG / lowest in the insight ordering
    collapsed_moves = {}
    for multi_move in multi_moves:
        move_state = deepcopy(curr_state)
        SOLVER.apply_multi_move(move_state, multi_move)

        grid_id = get_grid_id(puzzle_id, move_state)
        insight = multi_move["insight"]
        comparison_insight = None
        if grid_id in collapsed_moves:
            comparison_insight = collapsed_moves[grid_id]["insight"]
        if grid_id not in collapsed_moves or insight < comparison_insight:
            # Keep the move with the lowest ranked insight, as before
            grid_value = get_move_list_value(curr_state, multi_move["moves"], solution)
            collapsed_moves[grid_id] = {
                "hint_idx": multi_move["hint_idx"],
                "insight": multi_move["insight"],
                "state": move_state,
                "grid_value": grid_value,
                "moves": multi_move["moves"],
            }
            collapsed_moves[grid_id]["solver_value"] = "insight"

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
            "moves": c_move["moves"],
        }
        grid_id_to_comp_id[grid_id] = comp_id

    return composite_moves, grid_id_to_comp_id


def dedupe_moves(multi_moves):
    dedupe_moves = []
    for multi_move in multi_moves:
        duplicate = False
        for dd_move in dedupe_moves:
            if (
                dd_move["hint_idx"] == multi_move["hint_idx"]
                and dd_move["insight"] == multi_move["insight"]
            ):
                duplicate = True
                for m_move in multi_move["moves"]:
                    dupe_found = False
                    for d_move in dd_move["moves"]:
                        if moves_are_equal(m_move, d_move):
                            dupe_found = True
                            break
                    if not dupe_found:
                        duplicate = False
                        break
                if duplicate:
                    break
        if not duplicate:
            dedupe_moves.append(multi_move)
    return dedupe_moves


def all_x(moves):
    for move in moves:
        _, sy = move
        if sy != "X":
            return False
    return True


def get_solver_moves(puzzle, hints):
    # Get all conceivable moves for the puzzle state.
    # Include moves from the "opened"(crossed out) version of the puzzle,
    # as the user could be holding this information in their head
    # (particularly if they are in a puzzle that doesn't allow X marks or a very easy puzzle),
    # and we want to catch as many possible insights as we can.
    opened_puzzle = deepcopy(puzzle)
    SOLVER.apply_cross_out(opened_puzzle, True)
    _, s_moves = SOLVER.get_available_moves(puzzle, hints)
    _, opened_moves = SOLVER.get_available_moves(opened_puzzle, hints)
    s_moves.extend(opened_moves)
    for move in s_moves:
        if all_x(move["moves"]):
            # Also, if a move of xs creates an opening, the user may skip ahead to that O.
            applied_puzzle = deepcopy(puzzle)
            SOLVER.apply_multi_move(applied_puzzle, move)
            _, applied_openings = SOLVER.apply_opening(applied_puzzle, True)
            for o_move in applied_openings:
                o_move["hint_idx"] = -3
            s_moves.extend(applied_openings)
    d_moves = dedupe_moves(s_moves)
    return d_moves


# True if the categories and entities are the same (even if transposed), False otherwise.
def loc_are_equal(loc_a, loc_b):
    a_cat1, a_cat2, a_ent1, a_ent2 = loc_a
    b_cat1, b_cat2, b_ent1, b_ent2 = loc_b

    if a_cat1 == b_cat1 and a_ent1 == b_ent1:
        if a_cat2 == b_cat2 and a_ent2 == b_ent2:
            return True
    elif a_cat1 == b_cat2 and a_ent1 == b_ent2:
        if a_cat2 == b_cat1 and a_ent2 == b_ent1:
            return True
    return False


def moves_are_equal(move_a, move_b):
    loc_a, sy_a = move_a
    loc_b, sy_b = move_b
    if loc_are_equal(loc_a, loc_b) and sy_a == sy_b:
        return True
    return False


def choose_likeliest_move(moves):
    best_move = moves[0]
    for move in moves:
        if best_move["insight"] == None and move["insight"] != None:
            # Prefer labeling moves.
            best_move = move
        elif move["insight"] and best_move["insight"]:
            if len(move["min_moves"]) > len(best_move["min_moves"]):
                # Prefer longer move sequences.
                best_move = move
            elif (
                len(move["min_moves"]) == len(best_move["min_moves"])
                and move["insight"] < best_move["insight"]
            ):
                # Prefer insights lower in the DAG.
                best_move = move
    return best_move


# When checking a move, it could label that move + up to n future moves.
# How to account for this? We get available moves at a certain move,
# and replace n moves ONLY IF THEY ALL MATCH...then we must skip those moves.
def get_possible_labeled_moves_at_state(
    curr_state, u_move_idx, available_moves, match_on_one=False
):
    possible_moves = []
    recovered = False

    u_moves, i = u_move_idx
    (_, _, next_rec_moves) = u_moves[i]

    for s_multi_move in available_moves:
        changed = False
        update = deepcopy(curr_state)
        s_moves = s_multi_move["moves"]
        real_s_moves = []
        for s_move in s_moves:
            s_changed, _ = update.answer(*s_move)
            changed = changed or s_changed
            if s_changed:
                real_s_moves.append(s_move)
        if not changed:
            continue
        if len(next_rec_moves) > 1 and len(real_s_moves) != len(next_rec_moves):
            continue

        check_moves_ok = True
        check_moves = []
        if len(next_rec_moves) > 1:
            check_moves = next_rec_moves
        else:
            if i + len(real_s_moves) > len(u_moves) - 1:
                continue
            for m in range(i, i + len(real_s_moves)):
                (_, _, rec_moves) = u_moves[m]
                if len(rec_moves) > 1:
                    check_moves_ok = False
                    break
                check_moves.append(rec_moves[0])
        if not check_moves_ok:
            continue

        match_all = True
        num_matches = 0
        for u_move in check_moves:
            match_found = False
            for s_move in real_s_moves:
                if moves_are_equal(s_move, u_move):
                    match_found = True
                    num_matches += 1
                    break
            if not match_found:
                match_all = False
                break

        if num_matches == 0 or (not match_all and not match_on_one):
            continue

        # the sequence of user moves starting at i (or the recorded moves for one user move) matches the sequence of solver moves

        next_u_moves = []
        if len(next_rec_moves) > 1:
            next_u_moves = [u_moves[i]]
        else:
            next_u_moves = u_moves[i : i + num_matches]

        poss_move = {
            "hint_idx": s_multi_move["hint_idx"],
            "insight": s_multi_move["insight"],
            "full_moves": next_u_moves,
            "min_moves": check_moves,
            "violation": False,
            "confidence": "confident",
            "result": update,
        }
        if "indexed_hint" in s_multi_move:
            poss_move["indexed_hint"] = s_multi_move["indexed_hint"]
        else:
            poss_move["indexed_hint"] = None
        possible_moves.append(poss_move)
        recovered = True
    if not recovered:
        (_, _, next_rec_moves) = u_moves[i]
        update = deepcopy(curr_state)
        SOLVER.apply_multi_move(update, {"moves": next_rec_moves})
        possible_moves.append({
            "hint_idx": -100,
            "insight": None,
            "full_moves": [u_moves[i]],
            "min_moves": next_rec_moves,
            "violation": False,
            "confidence": "unknown",
            "result": update,
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


def get_loc_str(loc):
    (cat1, cat2, ent1_idx, ent2_idx) = loc
    return f"{cat1.title}:{cat2.title}:{ent1_idx}:{ent2_idx}"


def get_type_str(hint_idx):
    typestr = "hint"
    if hint_idx == -100:
        typestr = "unknown"
    if hint_idx == -3:
        typestr = "transitives"
    elif hint_idx == -2:
        typestr = "cross outs"
    elif hint_idx == -1:
        typestr = "openings"
    return typestr


# Only keep user moves that change the puzzle state.
def dedupe_user_moves(puzzle, u_moves):
    blank_puzzle = deepcopy(puzzle)
    result = deepcopy(puzzle)
    deduped_u_moves = []
    for time, raw_str, rec_moves in u_moves:
        deduped_rec_moves = []
        for rec_move in rec_moves:
            changed = False
            loc, sy = rec_move
            if loc == None and sy == "*":
                # clear move
                result = deepcopy(blank_puzzle)
                _, changed = SOLVER.get_move_diff(puzzle, result)
            else:
                _, changed = result.answer(*rec_move)

            if changed:
                deduped_rec_moves.append(rec_move)
        if len(deduped_rec_moves) > 0:
            deduped_u_moves.append((time, raw_str, deduped_rec_moves))
    return deduped_u_moves


def get_move_list_str(moves):
    move_str = ""
    for move in moves:
        loc, sy = move
        loc_str = get_loc_str(loc)
        move_str += f"({loc_str}, {sy}),"
    return move_str[:-1]


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
    match_on_one=False,
):
    u_moves = dedupe_user_moves(puzzle, u_moves)

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
    i = 0
    while i < len(u_moves):
        # for i, (time, raw_str, rec_moves) in enumerate(u_moves):
        # Copy that will have moves applied.
        result = deepcopy(puzzle)
        available_moves = get_solver_moves(puzzle, hints)  # All solver-aware moves
        composite_moves, _ = get_composite_moves(
            puzzle_id, puzzle, solution, available_moves
        )  # Available solver moves collapsed into individual insights

        possible_moves = []
        move_value = "neutral"

        (time, raw_str, rec_moves) = u_moves[i]
        loc, sy = rec_moves[0]
        if loc == None and sy == "*":
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
                "unknown",
                prompt_mode,
                level_mode,
            ]
            mi = mi + 1
            edge_df.loc[len(edge_df)] = edge_row  # adding a row
            source_id = target_id
            possible_moves = [{
                "hint_idx": -100,
                "insight": None,
                "repair": False,
                "move": rec_moves[0],
                "violation": False,
                "confidence": "unknown",
            }]
            result = deepcopy(blank_puzzle)
            board_state = result.print_grid()
            r_move = {
                "puzzle_state": deepcopy(result),
                "board_state": board_state,
                "move": rec_moves[0],
                "possible_moves": possible_moves,
                "value": move_value,
                "likely_move_str": f"clear",
                "likely_move": None,
            }

            r_moves.append((time, raw_str, r_move))
            i += 1
            continue

        possible_moves = get_possible_labeled_moves_at_state(
            result, (u_moves, i), available_moves, match_on_one=match_on_one
        )
        likely_move = choose_likeliest_move(possible_moves)

        for t, raw_s, rec_moves in likely_move["full_moves"]:
            move_value = get_move_list_value(result, rec_moves, solution)
            SOLVER.apply_multi_move(result, {"moves": rec_moves})
            r_move = {
                "puzzle_state": deepcopy(result),
                "board_state": result.print_grid(),
                "u_moves": rec_moves,
                "possible_moves": possible_moves,
                "value": move_value,
            }

            r_moves.append((t, raw_s, r_move))

            solver_value = f"unknown-{move_value}"

            move_str = get_move_list_str(rec_moves)
            move_id = f"{solver_value}:{move_str}"

            # Move index from action json
            move_idx = 0
            for m, move_data in enumerate(action_json[session_id]):
                if move_data["time"] == t:
                    move_idx = m
                    break

            action_json[session_id][move_idx]["insight"] = None
            likely_insight = None
            if likely_move != None:
                hint_idx = likely_move["hint_idx"]
                typestr = get_type_str(hint_idx)
                likely_insight = likely_move["insight"]
                insight_str = f"{likely_insight}"
                hint_str = ""
                if typestr == "hint":
                    hint = hints[hint_idx]
                    hint_str = hint_to_english(hint)
                if likely_insight != None:
                    solver_value = "insight"

                action_json[session_id][move_idx]["insight"] = insight_str
                move_id = f"{typestr}:{hint_str}:{insight_str}"

            r_move["likely_move_str"] = f"{move_id} ({solver_value})"
            r_move["likely_move"] = likely_move
            r_move["likely_insight"] = likely_insight
            action_json[session_id][move_idx]["solver_value"] = solver_value
            action_json[session_id][move_idx]["move_value"] = move_value

            curr_grid_value = "correct"
            contradiction, _ = SOLVER.repair(result, solution, False)
            if contradiction:
                curr_grid_value = "incorrect"

            for move in likely_move["min_moves"]:
                loc, sy = move
                loc_str = get_loc_str(loc)
                user_history[loc_str] = (move_id, sy)

            target_id = get_insight_node_id(
                user_history,
                curr_grid_value,
                puzzle_id,
                node_df,
                state_to_node_id,
                move_id,
            )

            edge_row = [
                source_id,
                target_id,
                user_id,
                mi,
                u_success,
                solver_value,
                r_move["value"],
                likely_insight,
                prompt_mode,
                level_mode,
            ]
            mi = mi + 1
            edge_df.loc[len(edge_df)] = edge_row  # adding a row
            source_id = target_id

            puzzle = deepcopy(result)
            i += 1

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
        "",
        prompt_mode,
        level_mode,
    ]

    # Get available insights at the end.
    available_insights = set()
    if u_success != "success":
        # If the user was successful, ignore any optional insights.
        available_moves = get_solver_moves(puzzle, hints)  # All solver-aware moves
        composite_moves, _ = get_composite_moves(
            puzzle_id, puzzle, solution, available_moves
        )  # Available solver moves collapsed into individual insights
        for s_move in composite_moves.values():
            available_insights.add(f"{s_move['insight']}")

    session_outcome_json[session_id] = {
        "outcome": u_success,
        "available_insights": list(available_insights),
    }

    edge_df.loc[len(edge_df)] = edge_row
    return u_success, r_moves


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

        puzzle_str = puzzle.print_grid()
        if raw_move["type"] == "button" and raw_move["button"] == "clear":
            # Reset
            user_puzzle = deepcopy(puzzle)
            clean_moves.append((time, puzzle_str, [(None, "*")]))
            continue
        if raw_move["type"] == "cellChange":
            puzzle_str = raw_move["puzzleState"]
        moves = []
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
    contradiction, _ = SOLVER.repair(user_puzzle, solution, False)
    correct = not contradiction
    user_success = "failure"
    if correct:
        if user_puzzle.is_complete():
            user_success = "success"
        else:
            user_success = "partial"
    return clean_moves, user_success


def clean_vr_moves(clean_key, raw_moves):
    session = None
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
    contradiction, _ = SOLVER.repair(user_puzzle, solution, False)
    correct = not contradiction
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
        reset_move = []
        for sauce in PASTA_SAUCES.entities:
            reset_move.append(((PASTA_SHAPES, PASTA_SAUCES, entities[0], sauce), "*"))
        ordered_moves.append((
            time,
            f"{raw_move} (reset)",
            reset_move,
        ))
        if entities[1] != "Reset":
            xout = []
            for sauce in PASTA_SAUCES.entities:
                loc = (PASTA_SHAPES, PASTA_SAUCES, entities[0], sauce)
                if sauce == entities[1]:
                    ordered_moves.append(
                        (time, f"{raw_move} ({entities[0]}, {sauce}, O)", [(loc, "O")])
                    )
                else:
                    # Each pasta can only have one sauce at a time.
                    xout.append((loc, "X"))
            ordered_moves.append((time, f"{raw_move} (cross out)", xout))
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
        reset_move = []
        for h in SUNLIGHT_HOURS.entities:
            reset_move.append(((SUNLIGHT_HOURS, SUNLIGHT_PLANTS, h, plant), "*"))
        ordered_moves.append((
            time,
            f"{raw_move} (reset)",
            reset_move,
        ))
        if len(plant_parts) != 3:
            xout = []
            for h in SUNLIGHT_HOURS.entities:
                loc = (SUNLIGHT_HOURS, SUNLIGHT_PLANTS, h, plant)
                if h == hr:
                    ordered_moves.append(
                        (time, f"{raw_move} ({h}, {plant}, O)", [(loc, "O")])
                    )
                else:
                    xout.append((loc, "X"))
            ordered_moves.append((time, f"{raw_move} (cross out)", xout))
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
        reset_move = []
        for o in ["20oz", "40oz", "60oz", "80oz"]:
            reset_move.append(((WATER_PLANTS, WATER_OZ, plant, o), "*"))
        ordered_moves.append((
            time,
            f"{raw_move} (reset)",
            reset_move,
        ))
        xout = []
        for o in ["20oz", "40oz", "60oz", "80oz"]:
            loc = (WATER_PLANTS, WATER_OZ, plant, o)
            if o == oz:
                ordered_moves.append(
                    (time, f"{raw_move} ({plant}, {o}, O)", [(loc, "O")])
                )
            else:
                xout.append((loc, "X"))
        ordered_moves.append((time, f"{raw_move} (cross out)", xout))
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

        if (
            cat1 not in puzzle.categories
            or cat2 not in puzzle.categories
            or ent1 not in cat1.entities
            or ent2 not in cat2.entities
        ):
            print(f"Unable to process move {raw_move}")
            continue
        loc = (cat1, cat2, ent1, ent2)
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
                print(f"Unable to process move: {raw_move}")
                continue

        clean_moves.append((f"{time}:0", raw_move, [(loc, sy)]))

    return {
        "puzzle": puzzle,
        "hints": hints,
        "moves": clean_moves,
    }


def print_moves(file, puzzle, hints, moves, insight_contexts):
    file.write("Puzzle:\n")
    file.write(puzzle.print_grid())
    file.write("Hints:\n")
    for i, hint in enumerate(hints):
        file.write(f"{i}. {hint_to_english(hint)} \n")
    file.write("\n")

    pre = deepcopy(puzzle)
    post = deepcopy(puzzle)

    for idx, (time, raw_state, move) in enumerate(moves):
        if move == None:
            file.write(f"{time}: User Move {idx+1} (Wrong, Ignored): {raw_state}\n")
        else:
            file.write(f"User Move {idx+1} ({move['value']}): {raw_state}\n")
            loc, sy = move["u_moves"][0]
            if loc == None and sy == "*":
                post = deepcopy(puzzle)
            else:
                SOLVER.apply_multi_move(post, {"moves": move["u_moves"]})

            s_multi_moves = get_solver_moves(pre, hints)
            file.write("Available Moves: \n")
            for s_multi_move in s_multi_moves:
                file.write(
                    f"{s_multi_move['hint_idx']}:{s_multi_move['insight']} - {s_multi_move['moves']}"
                )

            move_diff, _ = SOLVER.get_move_diff(pre, post, changes_only=False)
            pre = deepcopy(post)
            board_str = move_diff.print_grid().splitlines()
            for line in board_str:
                file.write(f"{line}\n")
            file.write("Possible Reasonings: \n")
            for i, poss_move in enumerate(move["possible_moves"]):
                typestr = get_type_str(poss_move["hint_idx"])

                if "hint" in typestr:
                    typestr += f" - \"{hint_to_english(hints[poss_move['hint_idx']])}\""
                insight = poss_move["insight"]
                file.write(f"{i+1}: {typestr} - {insight}\n")

                if insight != None:
                    if insight.name not in insight_contexts:
                        insight_contexts[insight.name] = {}
                        for o_insight in Insight.ALL_INSIGHTS:
                            insight_contexts[insight.name][o_insight.name] = 0
                    insights_seen = {insight}
                    for o_move in move["possible_moves"]:
                        o_insight = o_move["insight"]
                        if o_insight != None and o_insight not in insights_seen:
                            insights_seen.add(o_insight)
                            insight_contexts[insight.name][o_insight.name] += 1
                    if len(insights_seen) == 1:
                        # this is the only insight seen.
                        insight_contexts[insight.name][insight.name] += 1

            file.write(f"Likely Reasoning: {move['likely_move_str']}\n")

        file.write(f"\n\n")


def load_vr_data(file):
    df = pd.read_csv(file)

    first_move = df.iloc[0]
    if (
        first_move["PuzzleUniqueID"] != "GameStart"
        or first_move["ElementType"] != "Scene"
    ):
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


def load_online_puzzles(dir):
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
    return puzzles


def load_online_data(dir):
    action_json = None
    with open(f"{dir}/action_data.json") as f:
        action_json = json.load(f)

    gameplay_df = pd.read_csv(f"{dir}/gameplay_data.csv")
    puzzles = load_online_puzzles(dir)
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
    print("generating data views")
    print(edge_df)
    edge_view = edge_df.copy()
    view_name = "ALL"
    node_view_name = f"nodegraph{view_name}"
    edge_nodes = list(edge_view["Source"])
    edge_nodes.extend(list(edge_view["Target"]))
    node_view = node_df[node_df["Id"].isin(edge_nodes)]
    edge_view_name = f"edgegraph{view_name}"
    edge_view.to_csv(f"{dir}/{edge_view_name}.csv", index=False)
    node_view.to_csv(f"{dir}/{node_view_name}.csv", index=False)

    user_success_lookup = {}

    combined_view = pd.merge(edge_view, node_view, left_on="Target", right_on="Id")

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
        p_users = pg_view["UserId"].unique()
        for user in pg_all:
            if user not in p_users:
                print(f"{user} not in {pid}")

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

        if pid not in user_success_lookup:
            user_success_lookup[pid] = {}
        for p_user in p_users:
            user_moves = user_view[user_view["UserId"] == p_user]
            success = user_moves["UserSuccess"].unique()[0]
            user_success_lookup[pid][p_user] = success

        user_move_correctness = pg_view.copy()

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
        assert len(third_move_users) == len(
            third_move_users.unique()
        ), f"Duplicate third moves: {third_move_users}"

        first_move = first_move[first_move["UserId"].isin(third_move_users)]
        first_move_users = first_move["UserId"]
        assert len(first_move_users) == len(
            first_move_users.unique()
        ), f"Duplicate first moves: {first_move_users}"

        second_move = second_move[second_move["UserId"].isin(third_move_users)]
        second_move_users = second_move["UserId"]
        assert len(second_move_users) == len(
            second_move_users.unique()
        ), f"Duplicate second moves: {second_move_users}"

        assert len(first_move) == len(second_move) and len(second_move) == len(
            third_move
        ), f'Unequal lengths of moves between 1st, 2nd, 3rd: first-\n{first_move[["UserId", "Source", "Target", "PuzzleId", "MoveNumber"]]}; second-\n{second_move[["UserId", "Source", "Target", "PuzzleId", "MoveNumber"]]}; third-\n{third_move[["UserId", "Source", "Target", "PuzzleId", "MoveNumber"]]}'

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
                    "per_user_pct_full_insight": [],
                    "avg_pct_full_insight": 0,
                    "per_user_pct_uncertain": [],
                    "avg_pct_uncertain": 0,
                    "per_user_pct_overconfident": [],
                    "avg_pct_overconfident": 0,
                    "per_user_pct_tentative": [],
                    "avg_pct_tentative": 0,
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

            u_view = u_view.replace(
                {
                    "SolverValue": {
                        "contradiction": "unknown-incorrect",
                    }
                }
            )
            full_insight_moves = u_view[u_view["SolverValue"] == "insight"]
            uncertain_moves = u_view[u_view["SolverValue"] == "insight-uncertain"]
            overconfident_moves = u_view[
                u_view["SolverValue"] == "insight-overconfident"
            ]
            tentative_moves = u_view[u_view["SolverValue"] == "insight-tentative"]
            unknown_correct_moves = u_view[u_view["SolverValue"] == "unknown-correct"]
            unknown_incorrect_moves = u_view[
                u_view["SolverValue"] == "unknown-incorrect"
            ]
            unknown_neutral_moves = u_view[u_view["SolverValue"] == "unknown-neutral"]

            full_insight_move_count = (
                full_insight_moves.value_counts("UserId")
                .rename_axis("UserId")
                .reset_index(name="full_insight_move_count")
            )
            uncertain_move_count = (
                uncertain_moves.value_counts("UserId")
                .rename_axis("UserId")
                .reset_index(name="uncertain_move_count")
            )
            overconfident_move_count = (
                overconfident_moves.value_counts("UserId")
                .rename_axis("UserId")
                .reset_index(name="overconfident_move_count")
            )
            tentative_move_count = (
                tentative_moves.value_counts("UserId")
                .rename_axis("UserId")
                .reset_index(name="tentative_move_count")
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
                full_insight_move_count,
                on="UserId",
                how="outer",
            )
            user_counts = pd.merge(
                user_counts,
                uncertain_move_count,
                on="UserId",
                how="outer",
            )
            user_counts = pd.merge(
                user_counts,
                overconfident_move_count,
                on="UserId",
                how="outer",
            )
            user_counts = pd.merge(
                user_counts,
                tentative_move_count,
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

            user_counts["PctFullInsight"] = (
                user_counts["full_insight_move_count"] / user_counts["move_count"]
            )
            user_counts["PctUncertain"] = (
                user_counts["uncertain_move_count"] / user_counts["move_count"]
            )
            user_counts["PctOverconfident"] = (
                user_counts["overconfident_move_count"] / user_counts["move_count"]
            )
            user_counts["PctTentative"] = (
                user_counts["tentative_move_count"] / user_counts["move_count"]
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

            view_stats[u_name]["per_user_pct_full_insight"] = user_counts[
                "PctFullInsight"
            ].tolist()
            view_stats[u_name]["avg_pct_full_insight"] = float(
                user_counts["PctFullInsight"].mean()
            )
            view_stats[u_name]["per_user_pct_uncertain"] = user_counts[
                "PctUncertain"
            ].tolist()
            view_stats[u_name]["avg_pct_uncertain"] = float(
                user_counts["PctUncertain"].mean()
            )
            view_stats[u_name]["per_user_pct_overconfident"] = user_counts[
                "PctOverconfident"
            ].tolist()
            view_stats[u_name]["avg_pct_overconfident"] = float(
                user_counts["PctOverconfident"].mean()
            )
            view_stats[u_name]["per_user_pct_tentative"] = user_counts[
                "PctTentative"
            ].tolist()
            view_stats[u_name]["avg_pct_tentative"] = float(
                user_counts["PctTentative"].mean()
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

        with open(f"{dir}/stats{view_name}.json", "w") as f:
            json.dump(stats, f)

    return user_success_lookup


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


def inc_insight_counts(insight_counts, puzzle_id, success, moves):
    if puzzle_id not in insight_counts:
        insight_counts[puzzle_id] = {}
        for insight in Insight.ALL_INSIGHTS:
            insight_counts[puzzle_id][insight.name] = {
                "success": 0,
                "partial": 0,
                "failure": 0,
                "available_at_concede": 0,
            }
    insights_seen = set()
    for move in moves:
        if "insight" in move and move["insight"] != "None":
            insight = move["insight"]
            if insight in insights_seen:
                # Only increment insights once per session.
                continue
            insights_seen.add(insight)
            insight_counts[puzzle_id][insight][success] += 1


def insight_recovery__vr(vr_dir, match_on_one=False):
    howmany = "many"
    if match_on_one:
        howmany = "one"
    counts = {}
    insight_contexts = {}
    vr_node_df = pd.DataFrame(
        columns=["Id", "PuzzleId", "State", "GridValue", "MoveIds"]
    )
    vr_edge_df = pd.DataFrame(
        columns=[
            "Source",
            "Target",
            "UserId",
            "MoveNumber",
            "UserSuccess",
            "SolverValue",
            "MoveValue",
            "LabeledInsight",
            "PromptMode",
            "LevelMode",
        ]
    )
    vr_state_to_node_id = {}
    vr_users = [f.name for f in os.scandir("user_data/vr_study") if f.is_dir()]
    vr_session_outcome_json = {}
    vr_action_json = {}
    for user in vr_users[:2]:
        print(user)
        userfile = f"{vr_dir}/{user}/{user}_PuzzleLogs.csv"
        raw_df, start_time = load_vr_data(userfile)

        vr_clean_data = clean_vr_data(raw_df, start_time)
        for puzzle_id, session in vr_clean_data.items():
            if puzzle_id not in counts:
                counts[puzzle_id] = {"user_stats": {}}
            if user not in counts[puzzle_id]:
                counts[puzzle_id]["user_stats"][user] = {}
            session_id = f"{user}:{puzzle_id}"
            print(session_id)
            vr_action_json[session_id] = action_json_movelist_from_moves(
                session["moves"]
            )
            u_success, recovered_moves = recover_moves(
                puzzle_id,
                session["puzzle"],
                session["hints"],
                user,
                "",
                "",
                session["moves"],
                session["success"],
                vr_state_to_node_id,
                vr_node_df,
                vr_edge_df,
                vr_action_json,
                session_id,
                vr_session_outcome_json,
                match_on_one=match_on_one,
            )
            assert "end_state" not in counts[puzzle_id]["user_stats"][user]
            counts[puzzle_id]["user_stats"][user]["end_state"] = u_success
            counts[puzzle_id]["user_stats"][user]["counts"] = get_counts(
                recovered_moves
            )

            output_path = f"{vr_dir}/{user}/recovered_moves_{puzzle_id}_{howmany}.txt"
            output_file = Path(output_path)
            output_file.parent.mkdir(exist_ok=True, parents=True)
            move_file = open(output_path, "w")
            print_moves(
                move_file,
                session["puzzle"],
                session["hints"],
                recovered_moves,
                insight_contexts,
            )

    vr_dir = "user_data/vr_study"
    vr_edge_df.to_csv(f"{vr_dir}/edgegraph_{howmany}.csv", index=False)
    vr_node_df.to_csv(f"{vr_dir}/nodegraph_{howmany}.csv", index=False)
    vr_action_json = reformat_vr_action_json(vr_action_json)
    with open(f"{vr_dir}/updated_action_data_{howmany}.json", "w") as f:
        json.dump(vr_action_json, f)
    with open(f"{vr_dir}/session_outcome_{howmany}.json", "w") as f:
        json.dump(vr_session_outcome_json, f)
    vr_edge_df = pd.read_csv(f"{vr_dir}/edgegraph_{howmany}.csv")
    vr_node_df = pd.read_csv(f"{vr_dir}/nodegraph_{howmany}.csv")
    vr_success_lookup = gen_data_views(vr_dir, vr_edge_df, vr_node_df)
    with open(f"{vr_dir}/insight_contexts.json", "w") as f:
        json.dump(insight_contexts, f)
    vr_action_json = None
    vr_session_outcome_json = None

    with open(f"{vr_dir}/updated_action_data_{howmany}.json") as f:
        vr_action_json = json.load(f)

    with open(f"{vr_dir}/session_outcome_{howmany}.json") as f:
        vr_session_outcome_json = json.load(f)

    insight_counts = {}
    for user in vr_users:
        userfile = f"{vr_dir}/{user}/{user}_PuzzleLogs.csv"
        raw_df, start_time = load_vr_data(userfile)

        vr_clean_data = clean_vr_data(raw_df, start_time)
        for puzzle_id, session in vr_clean_data.items():
            session_id = f"{user}:{puzzle_id}"
            if session_id not in vr_session_outcome_json:
                continue
            moves = vr_action_json[session_id]
            success = vr_session_outcome_json[session_id]["outcome"]
            inc_insight_counts(insight_counts, puzzle_id, success, moves)
            available_at_end = vr_session_outcome_json[session_id]["available_insights"]
            counts[puzzle_id]["user_stats"][user]["available_at_end"] = available_at_end
            for insight in available_at_end:
                insight_counts[puzzle_id]["user_stats"][insight][
                    "available_at_concede"
                ] += 1
    with open(f"{vr_dir}/insight_counts_{howmany}.json", "w") as f:
        json.dump(insight_counts, f)
    return counts


def insight_recovery__online(online_dir, match_on_one=False):
    counts = {}
    howmany = "many"
    if match_on_one:
        howmany = "one"
    insight_contexts = {}
    on_clean_data, on_action_json = load_online_data(online_dir)
    on_session_outcome_json = {}
    on_node_df = pd.DataFrame(
        columns=["Id", "PuzzleId", "State", "GridValue", "MoveIds"]
    )
    on_edge_df = pd.DataFrame(
        columns=[
            "Source",
            "Target",
            "UserId",
            "MoveNumber",
            "UserSuccess",
            "SolverValue",
            "MoveValue",
            "LabeledInsight",
            "PromptMode",
            "LevelMode",
        ]
    )
    on_state_to_node_id = {}
    for user_id, user_data in on_clean_data.items():
        print(user_id)
        for puzzle_id, session in user_data["puzzles"].items():
            print(f"{user_id}:{puzzle_id}")
            if puzzle_id not in counts:
                counts[puzzle_id] = {"user_stats": {}}
            if user_id not in counts[puzzle_id]:
                counts[puzzle_id]["user_stats"][user_id] = {}
            u_success, recovered_moves = recover_moves(
                puzzle_id,
                session["puzzle"],
                session["hints"],
                user_id,
                user_data["promptMode"],
                user_data["levelMode"],
                session["moves"],
                session["success"],
                on_state_to_node_id,
                on_node_df,
                on_edge_df,
                on_action_json,
                session["session_id"],
                on_session_outcome_json,
                match_on_one=match_on_one,
            )
            assert "end_state" not in counts[puzzle_id]["user_stats"][user_id]
            counts[puzzle_id]["user_stats"][user_id]["end_state"] = u_success
            counts[puzzle_id]["user_stats"][user_id]["counts"] = get_counts(
                recovered_moves
            )
            output_path = f"{online_dir}/recovered_moves/{user_id}/recovered_moves_{puzzle_id}_{howmany}.txt"
            output_file = Path(output_path)
            output_file.parent.mkdir(exist_ok=True, parents=True)
            move_file = open(output_path, "w")
            print_moves(
                move_file,
                session["puzzle"],
                session["hints"],
                recovered_moves,
                insight_contexts,
            )
    with open(f"{online_dir}/updated_action_data_{howmany}.json", "w") as f:
        json.dump(on_action_json, f)
    with open(f"{online_dir}/session_outcome_{howmany}.json", "w") as f:
        json.dump(on_session_outcome_json, f)
    with open(f"{online_dir}/insight_contexts_{howmany}.json", "w") as f:
        json.dump(insight_contexts, f)

    on_edge_df.to_csv(f"{online_dir}/edgegraph_{howmany}.csv", index=False)
    on_node_df.to_csv(f"{online_dir}/nodegraph_{howmany}.csv", index=False)
    on_edge_df = pd.read_csv(f"{online_dir}/edgegraph_{howmany}.csv")
    on_node_df = pd.read_csv(f"{online_dir}/nodegraph_{howmany}.csv")
    on_success_lookup = gen_data_views(online_dir, on_edge_df, on_node_df)
    on_action_json = None
    on_session_outcome_json = None
    with open(f"{online_dir}/updated_action_data.json") as f:
        on_action_json = json.load(f)
    with open(f"{online_dir}/session_outcome.json") as f:
        on_session_outcome_json = json.load(f)
    insight_counts = {}
    for user_id, user_data in on_clean_data.items():
        for puzzle_id, session in user_data["puzzles"].items():
            session_id = session["session_id"]
            if session_id not in on_session_outcome_json:
                continue
            moves = on_action_json[session_id]
            success = on_session_outcome_json[session_id]["outcome"]
            moves = list(
                filter(
                    lambda rm: rm["type"] == "cellChange"
                    or (rm["type"] == "button" and rm["button"] == "clear"),
                    moves,
                )
            )
            inc_insight_counts(insight_counts, puzzle_id, success, moves)
            available_at_end = on_session_outcome_json[session_id]["available_insights"]
            counts[puzzle_id]["user_stats"][user_id][
                "available_at_end"
            ] = available_at_end
            insights_seen = set()
            for insight in available_at_end:
                if insight in insights_seen:
                    continue
                insights_seen.add(insight)
                insight_counts[puzzle_id]["user_stats"][insight][
                    "available_at_concede"
                ] += 1
    with open(f"{online_dir}/insight_counts_{howmany}.json", "w") as f:
        json.dump(insight_counts, f)
    return counts


def insight_recovery__agents(agent_dir, agents, puzzles, match_on_one=False):
    ground_truth = {}
    for agent in agents:
        ground_truth[agent.name] = {}
        for puzzle_id, puzzle_info in puzzles.items():
            moves = agent.play_puzzle(
                puzzle_info["puzzle"], puzzle_info["solution"], puzzle_info["hints"]
            )
            ground_truth[agent.name][puzzle_id] = moves
    insight_recovery__ground_truth_data(
        agent_dir, ground_truth, puzzles, match_on_one=match_on_one
    )


def insight_recovery__experts(expert_dir, experts, puzzles, match_on_one=False):
    ground_truth = {}
    for expert in experts:
        ground_truth[expert] = {}
        for puzzle_id, puzzle_info in puzzles.items():
            trace_json = None
            with open(f"{expert_dir}/{expert}/{puzzle_id}_ground.json") as f:
                print(f"{expert_dir}/{expert}/{puzzle_id}_ground.json")
                trace_json = json.load(f)

            trace = []
            for move in trace_json:
                insight_str = move["insight_str"]
                for insight in Insight.ALL_INSIGHTS:
                    if insight.name == insight_str:
                        move["insight"] = insight
                (cat1_title, cat2_title, ent1, ent2), sy = move["move_str"]
                cat1 = None
                cat2 = None
                for cat in puzzle_info["puzzle"].categories:
                    if cat.title == cat1_title:
                        cat1 = cat
                    if cat.title == cat2_title:
                        cat2 = cat
                move["move"] = ((cat1, cat2, ent1, ent2), sy)
                {
                    "insight": None,
                    "move": move,
                    "repair": False,
                    "hint_idx": None,
                }
                trace.append(move)
            ground_truth[expert][puzzle_id] = trace
    insight_recovery__ground_truth_data(
        expert_dir, ground_truth, puzzles, match_on_one=match_on_one
    )


def insight_recovery__ground_truth_data(
    ground_dir, ground_truth, puzzles, match_on_one=False
):
    howmany = "many"
    if match_on_one:
        howmany = "one"
    insight_contexts = {}
    g_session_outcome_json = {}
    g_node_df = pd.DataFrame(
        columns=["Id", "PuzzleId", "State", "GridValue", "MoveIds"]
    )
    g_edge_df = pd.DataFrame(
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
    g_state_to_node_id = {}
    g_action_json = {}
    blank_by_insight = {}
    for insight in Insight.ALL_INSIGHTS:
        blank_by_insight[insight.name] = 0
    blank_recovery_data = {
        "cnt_total_moves": 0,
        "cnt_total_moves_recovered": 0,
        "pct_total_moves_recovered": 0,
        "cnt_random_moves": 0,
        "cnt_random_moves_recovered": 0,
        "pct_random_moves_recovered": 0,
        "cnt_insight_moves": 0,
        "cnt_insight_moves_recovered": 0,
        "pct_insight_moves_recovered": 0,
        "cnt_moves_by_insight": deepcopy(blank_by_insight),
        "cnt_moves_by_insight_recovered": deepcopy(blank_by_insight),
        "pct_moves_by_insight_recovered": deepcopy(blank_by_insight),
    }
    for agent_name, agent_data in ground_truth.items():
        print(f"recovering data for {agent_name}")
        recovery_data = {"totals": deepcopy(blank_recovery_data)}
        for puzzle_id, moves in agent_data.items():
            recovery_data[puzzle_id] = deepcopy(blank_recovery_data)
            session_id = f"{agent_name}:{puzzle_id}"
            print(f"recovering {session_id}")
            print(f"recovering {agent_name}:{puzzle_id}")
            puzzle_info = puzzles[puzzle_id]
            clean_moves = []
            curr_state = deepcopy(puzzle_info["puzzle"])
            for i, move in enumerate(moves):
                curr_state.answer(*move["move"])
                clean_moves.append((f"{i}", curr_state.print_grid(), [move["move"]]))

            g_action_json[session_id] = action_json_movelist_from_moves(clean_moves)

            contradiction, _ = SOLVER.repair(curr_state, solution, False)
            correct = not contradiction
            agent_success = "failure"
            if correct:
                if curr_state.is_complete():
                    agent_success = "success"
                else:
                    agent_success = "partial"

            _, recovered_moves = recover_moves(
                puzzle_id,
                puzzle_info["puzzle"],
                puzzle_info["hints"],
                agent_name,
                "",
                "",
                clean_moves,
                agent_success,
                g_state_to_node_id,
                g_node_df,
                g_edge_df,
                g_action_json,
                session_id,
                g_session_outcome_json,
                match_on_one=match_on_one,
            )

            output_path = (
                f"{ground_dir}/{agent_name}/recovered_moves_{puzzle_id}_{howmany}.txt"
            )
            output_file = Path(output_path)
            output_file.parent.mkdir(exist_ok=True, parents=True)
            move_file = open(output_path, "w")
            print_moves(
                move_file,
                puzzle_info["puzzle"],
                puzzle_info["hints"],
                recovered_moves,
                insight_contexts,
            )
            for i, (_, _, r_move) in enumerate(recovered_moves):
                ground_truth = moves[i]
                compare_to = r_move["likely_move"]

                recovered = False
                if ground_truth["insight"] == None:
                    recovery_data[puzzle_id]["cnt_random_moves"] += 1
                    if compare_to == None:
                        recovered = True
                        recovery_data[puzzle_id]["cnt_random_moves_recovered"] += 1

                elif compare_to != None:
                    recovery_data[puzzle_id]["cnt_moves_by_insight"][
                        ground_truth["insight"].name
                    ] += 1
                    if (
                        compare_to["insight"] == ground_truth["insight"]
                        and compare_to["hint_idx"] == ground_truth["hint_idx"]
                    ):
                        recovered = True
                        recovery_data[puzzle_id]["cnt_moves_by_insight_recovered"][
                            ground_truth["insight"].name
                        ] += 1

                if not recovered:
                    print(f"Ground truth: {ground_truth}")
                    print(f"Tracked move: {compare_to}")
                    _ = input("continue: ")

            for insight in Insight.ALL_INSIGHTS:
                if recovery_data[puzzle_id]["cnt_moves_by_insight"][insight.name] > 0:
                    recovery_data[puzzle_id]["pct_moves_by_insight_recovered"][
                        insight.name
                    ] = (
                        recovery_data[puzzle_id]["cnt_moves_by_insight_recovered"][
                            insight.name
                        ]
                        / recovery_data[puzzle_id]["cnt_moves_by_insight"][insight.name]
                    )

                recovery_data["totals"]["cnt_moves_by_insight"][
                    insight.name
                ] += recovery_data[puzzle_id]["cnt_moves_by_insight"][insight.name]
                recovery_data["totals"]["cnt_moves_by_insight_recovered"][
                    insight.name
                ] += recovery_data[puzzle_id]["cnt_moves_by_insight_recovered"][
                    insight.name
                ]

            recovery_data[puzzle_id]["cnt_insight_moves"] = sum(
                recovery_data[puzzle_id]["cnt_moves_by_insight"].values()
            )
            recovery_data[puzzle_id]["cnt_insight_moves_recovered"] = sum(
                recovery_data[puzzle_id]["cnt_moves_by_insight_recovered"].values()
            )

            recovery_data[puzzle_id]["cnt_total_moves"] = (
                recovery_data[puzzle_id]["cnt_random_moves"]
                + recovery_data[puzzle_id]["cnt_insight_moves"]
            )
            recovery_data[puzzle_id]["cnt_total_moves_recovered"] = (
                recovery_data[puzzle_id]["cnt_random_moves_recovered"]
                + recovery_data[puzzle_id]["cnt_insight_moves_recovered"]
            )

            for move_type in ["total", "random", "insight"]:
                if recovery_data[puzzle_id][f"cnt_{move_type}_moves"] > 0:
                    recovery_data[puzzle_id][f"pct_{move_type}_moves_recovered"] = (
                        recovery_data[puzzle_id][f"cnt_{move_type}_moves_recovered"]
                        / recovery_data[puzzle_id][f"cnt_{move_type}_moves"]
                    )

                recovery_data["totals"][f"cnt_{move_type}_moves"] += recovery_data[
                    puzzle_id
                ][f"cnt_{move_type}_moves"]
                recovery_data["totals"][
                    f"cnt_{move_type}_moves_recovered"
                ] += recovery_data[puzzle_id][f"cnt_{move_type}_moves_recovered"]

        for insight in Insight.ALL_INSIGHTS:
            if recovery_data["totals"]["cnt_moves_by_insight"][insight.name] > 0:
                recovery_data["totals"]["pct_moves_by_insight_recovered"][
                    insight.name
                ] = (
                    recovery_data["totals"]["cnt_moves_by_insight_recovered"][
                        insight.name
                    ]
                    / recovery_data["totals"]["cnt_moves_by_insight"][insight.name]
                )

        for move_type in ["total", "random", "insight"]:
            if recovery_data["totals"][f"cnt_{move_type}_moves"] > 0:
                recovery_data["totals"][f"pct_{move_type}_moves_recovered"] = (
                    recovery_data["totals"][f"cnt_{move_type}_moves_recovered"]
                    / recovery_data["totals"][f"cnt_{move_type}_moves"]
                )

        with open(f"{ground_dir}/{agent_name}/recovery_data_{howmany}.json", "w") as f:
            json.dump(recovery_data, f)

    g_action_json = reformat_vr_action_json(g_action_json)
    with open(f"{ground_dir}/updated_action_data_{howmany}.json", "w") as f:
        json.dump(g_action_json, f)
    with open(f"{ground_dir}/session_outcome_{howmany}.json", "w") as f:
        json.dump(g_session_outcome_json, f)
    with open(f"{ground_dir}/insight_contexts_{howmany}.json", "w") as f:
        json.dump(insight_contexts, f)

    g_edge_df.to_csv(f"{ground_dir}/edgegraph_{howmany}.csv", index=False)
    g_node_df.to_csv(f"{ground_dir}/nodegraph_{howmany}.csv", index=False)
    g_edge_df = pd.read_csv(f"{ground_dir}/edgegraph_{howmany}.csv")
    g_node_df = pd.read_csv(f"{ground_dir}/nodegraph_{howmany}.csv")
    g_success_lookup = gen_data_views(ground_dir, g_edge_df, g_node_df)
    g_action_json = None
    g_session_outcome_json = None
    with open(f"{ground_dir}/updated_action_data_{howmany}.json") as f:
        g_action_json = json.load(f)
    with open(f"{ground_dir}/session_outcome_{howmany}.json") as f:
        g_session_outcome_json = json.load(f)
    insight_counts = {}
    for agent in ground_truth.keys():
        for puzzle_id, puzzle_info in puzzles.items():
            session_id = f"{agent}:{puzzle_id}"
            if session_id not in g_session_outcome_json:
                continue
            moves = g_action_json[session_id]
            success = g_session_outcome_json[session_id]["outcome"]
            inc_insight_counts(insight_counts, puzzle_id, success, moves)
            available_at_end = g_session_outcome_json[session_id]["available_insights"]
            insights_seen = set()
            for insight in available_at_end:
                if insight in insights_seen:
                    continue
                insights_seen.add(insight)
                insight_counts[puzzle_id][insight]["available_at_concede"] += 1
    with open(f"{ground_dir}/insight_counts_{howmany}.json", "w") as f:
        json.dump(insight_counts, f)

    return


def new_stat_block():
    new_stat_block = {
        "total_moves": 0,
        "cnt_labelled": 0,
        "cnt_unlabelled": 0,
        "label_breakdown": {},
    }
    for insight in Insight.ALL_INSIGHTS:
        new_stat_block["label_breakdown"][f"cnt_{insight.name}"] = 0
    return new_stat_block


move_values = ["correct", "incorrect", "neutral"]
end_states = ["success", "concede", "partial"]


def get_counts(moves):
    counts = new_stat_block()
    for val in move_values:
        counts[val] = new_stat_block()
        counts[f"cnt_{val}"] = 0
        for insight in Insight.ALL_INSIGHTS:
            counts[val]["label_breakdown"][f"cnt_{insight.name}"] = 0
    for _, _, move in moves:
        insight = move["likely_insight"]
        if insight == None:
            counts[move["value"]]["cnt_unlabelled"] += 1
        else:
            counts[move["value"]]["label_breakdown"][f"cnt_{insight.name}"] += 1
    return counts


def div0(num, den):
    if den > 0:
        return num / den
    else:
        return None


def gen_stats(stats, dir, match_on_one=False):
    howmany = "many"
    if match_on_one:
        howmany = "one"
    for puzzle, puzzle_stats in deepcopy(stats).items():
        puzzle_stats["counts"] = new_stat_block()
        puzzle_counts = puzzle_stats["counts"]
        puzzle_counts["success"] = new_stat_block()
        puzzle_counts["concede"] = new_stat_block()
        puzzle_stats["agg_counts"] = {
            "cnt_success": 0,
            "cnt_concede": 0,
            "insight_agreement": {
                "success": {},
                "concede": {},
                "available_at_concede": {},
            },
        }
        puzzle_agg_counts = puzzle_stats["agg_counts"]
        puzzle_user_stats = puzzle_stats["user_stats"]
        for user, user_stats in deepcopy(puzzle_user_stats).items():
            user_counts = user_stats["counts"]
            for key, key_counts in deepcopy(user_counts).items():
                if key not in move_values:
                    continue
                key_counts["cnt_labelled"] = sum(key_counts["label_breakdown"].values())
                key_counts["total_moves"] = (
                    key_counts["cnt_unlabelled"] + key_counts["cnt_labelled"]
                )
                user_counts["total_moves"] += key_counts["total_moves"]
                user_counts[f"cnt_{key}"] = key_counts["total_moves"]
                user_counts[f"cnt_unlabelled"] += key_counts["cnt_unlabelled"]
                user_counts[f"cnt_labelled"] += key_counts["cnt_labelled"]
                for insight, insight_count in deepcopy(
                    key_counts["label_breakdown"]
                ).items():
                    stat_name = insight.removeprefix("cnt_")
                    key_counts["label_breakdown"][f"pct_{stat_name}"] = div0(
                        insight_count, key_counts["cnt_labelled"]
                    )
                    user_counts["label_breakdown"][insight] += insight_count
                for label, cnt in deepcopy(key_counts).items():
                    if label.startswith("cnt_"):
                        stat_name = label.removeprefix("cnt_")
                        key_counts[f"pct_{stat_name}"] = div0(
                            cnt, key_counts["total_moves"]
                        )
                user_counts[key] = key_counts

            end_state = user_stats["end_state"]
            if end_state != "success":
                end_state = "concede"
            puzzle_agg_counts[f"cnt_{end_state}"] += 1
            for key, key_counts in deepcopy(user_counts).items():
                if key in move_values:
                    if key not in puzzle_counts:
                        puzzle_counts[key] = new_stat_block()
                        puzzle_counts["success"][key] = new_stat_block()
                        puzzle_counts["concede"][key] = new_stat_block()
                    for label, cnt in deepcopy(key_counts).items():
                        if label.startswith("cnt_") or label.startswith("total_"):
                            puzzle_counts[key][label] += cnt
                            puzzle_counts[end_state][key][label] += cnt
                    for insight, insight_count in deepcopy(
                        key_counts["label_breakdown"]
                    ).items():
                        if insight.startswith("cnt_"):
                            puzzle_counts[key]["label_breakdown"][
                                insight
                            ] += insight_count
                            puzzle_counts[end_state]["label_breakdown"][
                                insight
                            ] += insight_count
                            puzzle_counts[end_state][key]["label_breakdown"][
                                insight
                            ] += insight_count
                else:
                    if key.startswith("cnt_") or key.startswith("total_"):
                        if key not in puzzle_counts:
                            puzzle_counts[key] = 0
                        if key not in puzzle_counts[end_state]:
                            puzzle_counts[end_state][key] = 0
                        puzzle_counts[key] += key_counts
                        puzzle_counts[end_state][key] += key_counts
                        if key.startswith("cnt"):
                            stat_name = key.removeprefix("cnt_")
                            user_counts[f"pct_{stat_name}"] = (
                                key_counts / user_counts["total_moves"]
                            )

            for insight, insight_count in deepcopy(
                user_counts["label_breakdown"]
            ).items():
                stat_name = insight.removeprefix("cnt_")
                if insight.startswith("cnt_"):
                    puzzle_counts["label_breakdown"][insight] += insight_count
                    user_counts["label_breakdown"][f"pct_{stat_name}"] = div0(
                        insight_count, user_counts["cnt_labelled"]
                    )
                if insight_count > 0:
                    if (
                        stat_name
                        not in puzzle_agg_counts["insight_agreement"][end_state]
                    ):
                        puzzle_agg_counts["insight_agreement"][end_state][insight] = 0
                    puzzle_agg_counts["insight_agreement"][end_state][insight] += 1

            puzzle_user_stats[user] = user_stats

        puzzle_stats["user_stats"] = puzzle_user_stats

        for key, val in deepcopy(puzzle_counts).items():
            if key.startswith("cnt_"):
                stat_name = key.removeprefix("cnt_")
                puzzle_counts[f"pct_{stat_name}"] = div0(
                    val, puzzle_counts["total_moves"]
                )
            elif key in move_values or key in end_states or key == "label_breakdown":
                for key2, val2 in deepcopy(val).items():
                    if key2.startswith("cnt_"):
                        total_moves = 0
                        if key == "label_breakdown":
                            total_moves = puzzle_counts["cnt_labelled"]
                        else:
                            total_moves = val["total_moves"]
                        stat_name = key2.removeprefix("cnt_")
                        puzzle_counts[key][f"pct_{stat_name}"] = div0(val2, total_moves)
                    elif key2 in move_values or key2 == "label_breakdown":
                        for key3, val3 in deepcopy(val2).items():
                            if key3.startswith("cnt_"):
                                total_moves = 0
                                if key2 == "label_breakdown":
                                    total_moves = val["cnt_labelled"]
                                else:
                                    total_moves = val2["total_moves"]
                                stat_name = key3.removeprefix("cnt_")
                                puzzle_counts[key][key2][f"pct_{stat_name}"] = div0(
                                    val3, total_moves
                                )
                            elif key3 == "label_breakdown":
                                for key4, val4 in deepcopy(val3).items():
                                    if key4.startswith("cnt_"):
                                        stat_name = key4.removeprefix("cnt_")
                                        puzzle_counts[key][key2][key3][
                                            f"pct_{stat_name}"
                                        ] = div0(val4, val2["cnt_labelled"])

        puzzle_agg_counts["total_users"] = (
            puzzle_agg_counts["cnt_success"] + puzzle_agg_counts["cnt_concede"]
        )
        for key, cnt in deepcopy(puzzle_agg_counts).items():
            if key.startswith("cnt_"):
                stat_name = key.removeprefix("cnt_")
                puzzle_agg_counts[f"pct_{stat_name}"] = div0(
                    cnt, puzzle_agg_counts["total_users"]
                )

        for user, user_stats in puzzle_user_stats.items():
            end_state = user_stats["end_state"]
            user_counts = user_stats["counts"]
            for key, val in user_counts.items():
                if key.startswith("pct_"):
                    if f"calc_{key}" not in puzzle_agg_counts:
                        puzzle_agg_counts[f"calc_{key}"] = {"num": 0, "den": 0}
                    if f"calc_{key}" not in puzzle_agg_counts[end_state]:
                        puzzle_agg_counts[end_state][f"calc_{key}"] = {
                            "num": 0,
                            "den": 0,
                        }
                    if val != None:
                        puzzle_agg_counts[f"calc_{key}"]["num"] += val
                        puzzle_agg_counts[end_state][f"calc_{key}"]["num"] += val
                        puzzle_agg_counts[f"calc_{key}"]["den"] += 1
                        puzzle_agg_counts[end_state][f"calc_{key}"]["den"] += 1
                elif key in move_values:
                    for label, cnt in val.items():
                        if label.startswith("pct_"):
                            if key not in puzzle_agg_counts:
                                puzzle_agg_counts[key] = {}
                            if f"calc_{label}" not in puzzle_agg_counts[key]:
                                puzzle_agg_counts[key][f"calc_{label}"] = {
                                    "num": 0,
                                    "den": 0,
                                }
                            if end_state not in puzzle_agg_counts:
                                puzzle_agg_counts[end_state] = {}
                            if key not in puzzle_agg_counts[end_state]:
                                puzzle_agg_counts[end_state][key] = {}
                            if f"calc_{label}" not in puzzle_agg_counts[end_state][key]:
                                puzzle_agg_counts[end_state][key][f"calc_{label}"] = {
                                    "num": 0,
                                    "den": 0,
                                }
                            if cnt != None:
                                puzzle_agg_counts[key][f"calc_{label}"]["num"] += cnt
                                puzzle_agg_counts[end_state][key][f"calc_{label}"][
                                    "num"
                                ] += cnt
                                puzzle_agg_counts[key][f"calc_{label}"]["den"] += 1
                                puzzle_agg_counts[end_state][key][f"calc_{label}"][
                                    "den"
                                ] += 1
                    for insight, insight_count in val["label_breakdown"].items():
                        if insight.startswith("pct_"):
                            if "label_breakdown" not in puzzle_agg_counts[key]:
                                puzzle_agg_counts[key]["label_breakdown"] = {}
                            if (
                                f"calc_{insight}"
                                not in puzzle_agg_counts[key]["label_breakdown"]
                            ):
                                puzzle_agg_counts[key]["label_breakdown"][
                                    f"calc_{insight}"
                                ] = {"num": 0, "den": 0}

                            if end_state not in puzzle_agg_counts:
                                puzzle_agg_counts[end_state] = {}
                            if key not in puzzle_agg_counts[end_state]:
                                puzzle_agg_counts[end_state][key] = {}
                            if (
                                "label_breakdown"
                                not in puzzle_agg_counts[end_state][key]
                            ):
                                puzzle_agg_counts[end_state][key][
                                    "label_breakdown"
                                ] = {}
                            if (
                                f"calc_{insight}"
                                not in puzzle_agg_counts[end_state][key][
                                    "label_breakdown"
                                ]
                            ):
                                puzzle_agg_counts[end_state][key]["label_breakdown"][
                                    f"calc_{insight}"
                                ] = {"num": 0, "den": 0}

                            if insight_count != None:
                                puzzle_agg_counts[key]["label_breakdown"][
                                    f"calc_{insight}"
                                ]["num"] += insight_count
                                puzzle_agg_counts[end_state][key]["label_breakdown"][
                                    f"calc_{insight}"
                                ]["num"] += insight_count
                                puzzle_agg_counts[key]["label_breakdown"][
                                    f"calc_{insight}"
                                ]["den"] += 1
                                puzzle_agg_counts[end_state][key]["label_breakdown"][
                                    f"calc_{insight}"
                                ]["den"] += 1

            for insight, insight_count in user_counts["label_breakdown"].items():
                if insight.startswith("pct_"):
                    if "label_breakdown" not in puzzle_agg_counts:
                        puzzle_agg_counts["label_breakdown"] = {}
                    if f"calc_{insight}" not in puzzle_agg_counts["label_breakdown"]:
                        puzzle_agg_counts["label_breakdown"][f"calc_{insight}"] = {
                            "num": 0,
                            "den": 0,
                        }

                    if "label_breakdown" not in puzzle_agg_counts[end_state]:
                        puzzle_agg_counts[end_state]["label_breakdown"] = {}
                    if (
                        f"calc_{insight}"
                        not in puzzle_agg_counts[end_state]["label_breakdown"]
                    ):
                        puzzle_agg_counts[end_state]["label_breakdown"][
                            f"calc_{insight}"
                        ] = {"num": 0, "den": 0}
                    puzzle_agg_counts[end_state]["label_breakdown"][f"calc_{insight}"][
                        "num"
                    ] += insight_count
                    puzzle_agg_counts["label_breakdown"][f"calc_{insight}"][
                        "num"
                    ] += insight_count
                    puzzle_agg_counts[end_state]["label_breakdown"][f"calc_{insight}"][
                        "den"
                    ] += 1
                    puzzle_agg_counts["label_breakdown"][f"calc_{insight}"]["den"] += 1

        for key, val in deepcopy(puzzle_agg_counts).items():
            if key.startswith("calc_"):
                stat_name = key.removeprefix("calc_")
                puzzle_agg_counts[f"avg_{stat_name}"] = div0(val["num"], val["den"])
            elif key in move_values or key in end_states:
                for label, cnt in val.items():
                    if label.startswith("calc_"):
                        stat_name = label.removeprefix("calc_")
                        puzzle_agg_counts[key][f"avg_{stat_name}"] = div0(
                            cnt["num"], cnt["den"]
                        )
                    elif label in move_values:
                        for sub_label, sub_cnt in cnt.items():
                            if sub_label.startswith("calc_"):
                                stat_name = sub_label.removeprefix("calc_")
                                puzzle_agg_counts[key][label][f"avg_{stat_name}"] = (
                                    div0(sub_cnt["num"], sub_cnt["den"])
                                )
                        for insight, insight_count in cnt["label_breakdown"].items():
                            if insight.startswith("calc_"):
                                stat_name = insight.removeprefix("calc_")
                                puzzle_agg_counts[key][label]["label_breakdown"][
                                    f"avg_{stat_name}"
                                ] = div0(insight_count["num"], insight_count["den"])
                for insight, insight_count in val["label_breakdown"].items():
                    if insight.startswith("calc_"):
                        stat_name = insight.removeprefix("calc_")
                        puzzle_agg_counts[key]["label_breakdown"][
                            f"avg_{stat_name}"
                        ] = div0(insight_count["num"], insight_count["den"])

        for insight, insight_count in deepcopy(
            puzzle_agg_counts["label_breakdown"]
        ).items():
            if insight.startswith("calc_"):
                stat_name = insight.removeprefix("calc_")
                puzzle_agg_counts["label_breakdown"][f"avg_{stat_name}"] = div0(
                    insight_count["num"], insight_count["den"]
                )

        for end_state, insight_agreement in deepcopy(
            puzzle_agg_counts["insight_agreement"]
        ).items():
            insight_agreement["calc_pct"] = {"num": 0, "den": 0}
            for insight, insight_count in deepcopy(insight_agreement).items():
                if insight.startswith("cnt_"):
                    stat_name = insight.removeprefix("cnt_")
                    insight_agreement[f"pct_{stat_name}"] = div0(
                        insight_count, puzzle_agg_counts[f"cnt_{end_state}"]
                    )
                    if insight_agreement[f"pct_{stat_name}"] != None:
                        insight_agreement["calc_pct"]["num"] += insight_agreement[
                            f"pct_{stat_name}"
                        ]
                        insight_agreement["calc_pct"]["den"] += 1
            insight_agreement["avg_pct"] = div0(
                insight_agreement["calc_pct"]["num"],
                insight_agreement["calc_pct"]["den"],
            )
            puzzle_agg_counts["insight_agreement"][end_state] = insight_agreement

        puzzle_stats["agg_counts"] = puzzle_agg_counts
        stats[puzzle] = puzzle_stats

    stats["agg"] = {}
    for puzzle, puzzle_stats in deepcopy(stats).items():
        if puzzle == "agg":
            continue
        puzzle_counts = puzzle_stats["counts"]
        puzzle_agg_counts = puzzle_stats["agg_counts"]
        for key, val in puzzle_counts.items():
            if key.startswith("cnt_") or key.startswith("total_"):
                if key not in stats["agg"]:
                    stats["agg"][key] = 0
                stats["agg"][key] += val
            elif key.startswith("pct_"):
                if f"calc_{key}" not in stats["agg"]:
                    stats["agg"][f"calc_{key}"] = {
                        "num": 0,
                        "den": 0,
                    }
                if val != None:
                    stats["agg"][f"calc_{key}"]["num"] += val
                    stats["agg"][f"calc_{key}"]["den"] += 1
            elif key in move_values or key in end_states:
                for key2, val2 in val.items():
                    if key2.startswith("cnt_") or key2.startswith("total_"):
                        if key not in stats["agg"]:
                            stats["agg"][key] = {}
                        if key2 not in stats["agg"][key]:
                            stats["agg"][key][key2] = 0
                        stats["agg"][key][key2] += val2
                    elif key2.startswith("pct_"):
                        if key not in stats["agg"]:
                            stats["agg"][key] = {}
                        if f"calc_{key2}" not in stats["agg"][key]:
                            stats["agg"][key][f"calc_{key2}"] = {
                                "num": 0,
                                "den": 0,
                            }
                            if val2 != None:
                                stats["agg"][key][f"calc_{key2}"]["num"] += val2
                                stats["agg"][key][f"calc_{key2}"]["den"] += 1
                    elif key2 in move_values:
                        for key3, val3 in val2.items():
                            if key3.startswith("cnt_") or key3.startswith("total_"):
                                if key not in stats["agg"]:
                                    stats["agg"][key] = {}
                                if key2 not in stats["agg"][key]:
                                    stats["agg"][key][key2] = {}
                                if key3 not in stats["agg"][key][key2]:
                                    stats["agg"][key][key2][key3] = 0
                                stats["agg"][key][key2][key3] += val3
                            elif key3.startswith("pct_"):
                                if key not in stats["agg"]:
                                    stats["agg"][key] = {}
                                if key2 not in stats["agg"][key]:
                                    stats["agg"][key][key2] = {}
                                if f"calc_{key3}" not in stats["agg"][key][key2]:
                                    stats["agg"][key][key2][f"calc_{key3}"] = {
                                        "num": 0,
                                        "den": 0,
                                    }
                                if val3 != None:
                                    stats["agg"][key][key2][f"calc_{key3}"][
                                        "num"
                                    ] += val3
                                    stats["agg"][key][key2][f"calc_{key3}"][
                                        "den"
                                    ] += val3
                        for key3, val3 in val2["label_breakdown"].items():
                            if key3.startswith("cnt_"):
                                if key not in stats["agg"]:
                                    stats["agg"][key] = {}
                                if key2 not in stats["agg"][key]:
                                    stats["agg"][key][key2] = {}
                                if "label_breakdown" not in stats["agg"][key][key2]:
                                    stats["agg"][key][key2]["label_breakdown"] = {}
                                if (
                                    key3
                                    not in stats["agg"][key][key2]["label_breakdown"]
                                ):
                                    stats["agg"][key][key2]["label_breakdown"][key3] = 0
                                stats["agg"][key][key2]["label_breakdown"][key3] += val3
                            elif key3.startswith("pct_"):
                                if key not in stats["agg"]:
                                    stats["agg"][key] = {}
                                if key2 not in stats["agg"][key]:
                                    stats["agg"][key][key2] = {}
                                if "label_breakdown" not in stats["agg"][key][key2]:
                                    stats["agg"][key][key2]["label_breakdown"] = {}
                                if (
                                    f"calc_{key3}"
                                    not in stats["agg"][key][key2]["label_breakdown"]
                                ):
                                    stats["agg"][key][key2]["label_breakdown"][
                                        f"calc_{key3}"
                                    ] = {"num": 0, "den": 0}
                                if val3 != None:
                                    stats["agg"][key][key2]["label_breakdown"][
                                        f"calc_{key3}"
                                    ]["num"] += val3
                                    stats["agg"][key][key2]["label_breakdown"][
                                        f"calc_{key3}"
                                    ]["den"] += 1
                for key2, val2 in val["label_breakdown"].items():
                    if key2.startswith("cnt_"):
                        if key not in stats["agg"]:
                            stats["agg"][key] = {}
                        if "label_breakdown" not in stats["agg"][key]:
                            stats["agg"][key]["label_breakdown"] = {}
                        if key2 not in stats["agg"][key]["label_breakdown"]:
                            stats["agg"][key]["label_breakdown"][key2] = 0
                        stats["agg"][key]["label_breakdown"][key2] += val2
                    elif key2.startswith("pct_"):
                        if key not in stats["agg"]:
                            stats["agg"][key] = {}
                        if "label_breakdown" not in stats["agg"][key]:
                            stats["agg"][key]["label_breakdown"] = {}
                        if f"calc_{key2}" not in stats["agg"][key]["label_breakdown"]:
                            stats["agg"][key]["label_breakdown"][f"calc_{key2}"] = {
                                "num": 0,
                                "den": 0,
                            }
                        if val2 != None:
                            stats["agg"][key]["label_breakdown"][f"calc_{key2}"][
                                "num"
                            ] += val2
                            stats["agg"][key]["label_breakdown"][f"calc_{key2}"][
                                "den"
                            ] += val2
        for key, val in puzzle_counts["label_breakdown"].items():
            if key.startswith("cnt_"):
                if "label_breakdown" not in stats["agg"]:
                    stats["agg"]["label_breakdown"] = {}
                if key not in stats["agg"]["label_breakdown"]:
                    stats["agg"]["label_breakdown"][key] = 0
                stats["agg"]["label_breakdown"][key] += val
            elif key.startswith("pct_"):
                if "label_breakdown" not in stats["agg"]:
                    stats["agg"]["label_breakdown"] = {}
                if f"calc_{key}" not in stats["agg"]["label_breakdown"]:
                    stats["agg"]["label_breakdown"][f"calc_{key}"] = {
                        "num": 0,
                        "den": 0,
                    }
                if val != None:
                    stats["agg"]["label_breakdown"][f"calc_{key}"]["num"] += val
                    stats["agg"]["label_breakdown"][f"calc_{key}"]["den"] += 1
        for key, val in puzzle_agg_counts.items():
            if key.startswith("cnt_"):
                if key not in stats["agg"]:
                    stats["agg"][key] = 0
                stats["agg"][key] += val
            elif key.startswith("pct_") or key.startswith("avg_"):
                if f"calc_{key}" not in stats["agg"]:
                    stats["agg"][f"calc_{key}"] = {
                        "num": 0,
                        "den": 0,
                    }
                if val != None:
                    stats["agg"][f"calc_{key}"]["num"] += val
                    stats["agg"][f"calc_{key}"]["den"] += 1
            elif key in end_states or key in move_values or key == "label_breakdown":
                if key not in stats["agg"]:
                    stats["agg"][key] = {}
                for key2, val2 in val.items():
                    if key2.startswith("avg_"):
                        if f"calc_{key2}" not in stats["agg"][key]:
                            stats["agg"][key][f"calc_{key2}"] = {
                                "num": 0,
                                "den": 0,
                            }
                        if val2 != None:
                            stats["agg"][key][f"calc_{key2}"]["num"] += val2
                            stats["agg"][key][f"calc_{key2}"]["den"] += 1
                    elif key2 in move_values or key2 == "label_breakdown":
                        if key2 not in stats["agg"][key]:
                            stats["agg"][key][key2] = {}
                        for key3, val3 in val2.items():
                            if key3.startswith("avg_"):
                                if f"calc_{key3}" not in stats["agg"][key][key2]:
                                    stats["agg"][key][key2][f"calc_{key3}"] = {
                                        "num": 0,
                                        "den": 0,
                                    }
                                if val3 != None:
                                    stats["agg"][key][key2][f"calc_{key3}"][
                                        "num"
                                    ] += val3
                                    stats["agg"][key][key2][f"calc_{key3}"]["den"] += 1
                            elif key3 == "label_breakdown":
                                if key3 not in stats["agg"][key]:
                                    stats["agg"][key][key2][key3] = {}
                                for key4, val4 in val3.items():
                                    if key4.startswith("avg_"):
                                        if (
                                            f"calc_{key4}"
                                            not in stats["agg"][key][key2][key3]
                                        ):
                                            stats["agg"][key][key2][key3][
                                                f"calc_{key4}"
                                            ] = {
                                                "num": 0,
                                                "den": 0,
                                            }
                                        if val4 != None:
                                            stats["agg"][key][key2][key3][
                                                f"calc_{key4}"
                                            ]["num"] += val4
                                            stats["agg"][key][key2][key3][
                                                f"calc_{key4}"
                                            ]["den"] += 1

        if "insight_agreement" not in stats["agg"]:
            stats["agg"]["insight_agreement"] = {}
        for key, vals in puzzle_agg_counts["insight_agreement"].items():
            if key not in stats["agg"]["insight_agreement"]:
                stats["agg"]["insight_agreement"][key] = {}
            for key2, val2 in vals.items():
                if key2.startswith("cnt_"):
                    if key2 not in stats["agg"]["insight_agreement"][key]:
                        stats["agg"]["insight_agreement"][key][key2] = 0
                    stats["agg"]["insight_agreement"][key][key2] += val2
                elif key2.startswith("avg"):
                    if f"calc_{key2}" not in stats["agg"]["insight_agreement"][key]:
                        stats["agg"]["insight_agreement"][key][f"calc_{key2}"] = {
                            "num": 0,
                            "den": 0,
                        }
                    if val2 != None:
                        stats["agg"]["insight_agreement"][key][f"calc_{key2}"][
                            "num"
                        ] += val2
                        stats["agg"]["insight_agreement"][key][f"calc_{key2}"][
                            "den"
                        ] += 1

    for key, val in deepcopy(stats["agg"]).items():
        if key.startswith("cnt_"):
            stat_name = key.removeprefix("cnt_")
            stats["agg"][f"pct_{stat_name}"] = div0(val, stats["agg"]["total_moves"])
        elif key.startswith("calc_"):
            stat_name = key.removeprefix("calc_")
            stats["agg"][f"avg_{stat_name}"] = div0(val["num"], val["den"])
        elif key in move_values or key in end_states or key == "label_breakdown":
            for key2, val2 in val.items():
                if key2.startswith("cnt_"):
                    stat_name = key2.removeprefix("cnt_")
                    total_moves = 0
                    if key == "label_breakdown":
                        total_moves = stats["agg"]["cnt_labelled"]
                    else:
                        total_moves = stats["agg"][key]["total_moves"]
                    stats["agg"][key][f"pct_{stat_name}"] = div0(val2, total_moves)
                elif key2.startswith("calc_"):
                    stat_name = key2.removeprefix("calc_")
                    stats["agg"][key][f"avg_{stat_name}"] = div0(
                        val2["num"], val2["den"]
                    )
                elif key2 in move_values or key2 == "label_breakdown":
                    for key3, val3 in val2.items():
                        if key3.startswith("cnt_"):
                            total_moves = 0
                            if key2 == "label_breakdown":
                                total_moves = stats["agg"][key]["cnt_labelled"]
                            else:
                                total_moves = stats["agg"][key][key2]["total_moves"]
                            stat_name = key3.removeprefix("cnt_")
                            stats["agg"][key][key2][f"pct_{stat_name}"] = div0(
                                val3, total_moves
                            )
                        elif key3.startswith("calc_"):
                            stat_name = key3.removeprefix("calc_")
                            stats["agg"][key][key2][f"avg_{stat_name}"] = div0(
                                val3["num"], val3["den"]
                            )
                        elif key3 == "label_breakdown":
                            for key4, val4 in val3.items():
                                if key4.startswith("cnt_"):
                                    total_moves = 0
                                    if key3 == "label_breakdown":
                                        total_moves = stats["agg"][key][key2][
                                            "cnt_labelled"
                                        ]
                                    else:
                                        total_moves = stats["agg"][key][key2][key3][
                                            "total_moves"
                                        ]
                                    stat_name = key4.removeprefix("cnt_")
                                    stats["agg"][key][key2][key3][
                                        f"pct_{stat_name}"
                                    ] = div0(val4, total_moves)
                                elif key4.startswith("calc_"):
                                    stat_name = key4.removeprefix("calc_")
                                    stats["agg"][key][key2][key3][
                                        f"avg_{stat_name}"
                                    ] = div0(val4["num"], val4["den"])

    for end_state, vals in deepcopy(stats["agg"]["insight_agreement"]).items():
        for key, val in vals.items():
            if key.startswith("cnt_"):
                stat_name = key.removeprefix("cnt_")
                stats["agg"]["insight_agreement"][end_state][f"pct_{stat_name}"] = div0(
                    val, stats["agg"][f"cnt_{end_state}"]
                )
            elif key.startswith("avg"):
                if f"calc_{key}" not in stats["agg"]["insight_agreement"][end_state]:
                    stats["agg"]["insight_agreement"][end_state][f"calc_{key}"] = {
                        "num": 0,
                        "den": 0,
                    }
                if val != None:
                    stats["agg"]["insight_agreement"][end_state][f"calc_{key}"][
                        "num"
                    ] += val
                    stats["agg"]["insight_agreement"][end_state][f"calc_{key}"][
                        "den"
                    ] += 1

    for end_state, vals in deepcopy(stats["agg"]["insight_agreement"]).items():
        for key, val in vals.items():
            if key.startswith("calc_"):
                stat_name = key.removeprefix("calc_")
                stats["agg"]["insight_agreement"][end_state][f"avg_{stat_name}"] = div0(
                    val["num"], val["den"]
                )

    with open(f"{dir}/stats_{howmany}.json", "w") as f:
        json.dump(stats, f)


if __name__ == "__main__":
    vr_dir = "user_data/vr_study"
    online_dir = "user_data/online_puzzle_study"
    agent_dir = "agent_data"
    expert_dir = "expert_data"

    agents = PuzzleAgent.Agents.values()
    experts = ["e1_kf"]

    puzzles = PUZZLE_DEFS | load_online_puzzles(online_dir)
    for puzzle_id, puzzle_info in puzzles.items():
        solution, _, _ = SOLVER.apply_hints(puzzle_info["puzzle"], puzzle_info["hints"])
        puzzles[puzzle_id]["solution"] = solution

    expert_many_counts = insight_recovery__experts(
        expert_dir, experts, puzzles, match_on_one=False
    )
    gen_stats(expert_many_counts, match_on_one=False)

    expert_one_counts = insight_recovery__experts(
        expert_dir, experts, puzzles, match_on_one=True
    )
    gen_stats(expert_one_counts, match_on_one=True)

    agent_many_counts = insight_recovery__agents(
        agent_dir, agents, puzzles, match_on_one=False
    )
    gen_stats(agent_many_counts, match_on_one=False)

    agent_one_counts = insight_recovery__agents(
        agent_dir, agents, puzzles, match_on_one=True
    )
    gen_stats(agent_one_counts, match_on_one=True)

    vr_many_counts = insight_recovery__vr(vr_dir, match_on_one=False)
    gen_stats(vr_many_counts, vr_dir, match_on_one=False)

    vr_one_counts = insight_recovery__vr(vr_dir, match_on_one=True)
    gen_stats(vr_one_counts, vr_dir, match_on_one=True)

    online_many_counts = insight_recovery__online(online_dir, match_on_one=False)
    gen_stats(online_many_counts, online_dir, match_on_one=False)

    online_one_counts = insight_recovery__online(online_dir, match_on_one=True)
    gen_stats(online_one_counts, online_dir, match_on_one=True)
