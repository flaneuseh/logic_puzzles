import ultraimport
from copy import deepcopy

ultraimport("__dir__/LogicPuzzles.py", package="main")
from main.LogicPuzzles import Solver, Insight

# All moves for the same hint/insight go into one super-move.
def collapse_moves(moves):
    solver = Solver()
    collapsed_moves = []
    for move in moves:
        collapsed = False
        for c_move in collapsed_moves:
            if move["type"] == "clue" and c_move["type"] != "clue":
                continue
            if move["type"] == "clue" and move["indexed_clue"]["idx"] != c_move["indexed_clue"]["idx"]:
                continue
            for insight in move["insights"]:
                if insight in c_move["insights"]:
                    collapsed = True
                    solver.apply_move(c_move["move_diff"], move)
        if not collapsed:
            collapsed_moves.append(move)
    return collapsed_moves


# Given a valid puzzle and an insight, find an insight problem if possible.
# The insight problem is a partially solved puzzle for which the next move can 
# only be the insight, and no subsequent insights can be made using the same hint.
# Return the insight problem and the next move
def get_insight_problem(puzzle, hints, insight):
    solver = Solver()
    assert solver.can_solve_without_forbidden(puzzle, hints), "can't solve with all insights available"
    required_insights = {insight}
    forbidden_insights = insight.sub_dag() - {insight}
    solver = Solver(required_insights | forbidden_insights)
    assert not solver.can_solve_without_forbidden(
        puzzle, hints
    ), "can solve without required insight: {}".format(required_insights)
    solver = Solver(forbidden_insights)
    assert solver.can_solve_without_forbidden(
        puzzle, hints
    ), "can't solve without forbidden insights {}".format(forbidden_insights)

    required_insights = {insight}
    forbidden_insights = insight.sub_dag() - {insight}
    solver = Solver()
    assert solver.can_solve_without_forbidden(puzzle, hints), "can't solve with all insights available"
    solver = Solver(forbidden_insights)
    assert solver.can_solve_without_forbidden(
        puzzle, hints
    ), "can't solve without forbidden insights {}".format(forbidden_insights)
    solver = Solver(required_insights | forbidden_insights)
    assert not solver.can_solve_without_forbidden(
        puzzle, hints
    ), "can solve without required insight: {}".format(required_insights)

    # Do as much of the puzzle as possible without the insight (or its descendants).
    #print("Fast forward without insight")
    puzzle_before_insight, _ = solver.fast_forward(
        puzzle, hints
    )

    assert not solver.can_solve_without_forbidden(
        puzzle_before_insight, hints
    ), "can solve without required insight {}".format(insight)

    solver = Solver(forbidden_insights)
    assert solver.can_solve_without_forbidden(
        puzzle_before_insight, hints
    ), "can't solve without forbidden insights {}".format(forbidden_insights)
    _, available_moves = solver.get_available_moves(
        puzzle_before_insight,
        hints
    )

    if len(available_moves) == 0:
        return None, None

    for move in available_moves:
        if insight not in move["insights"]:
            # We don't want ambiguity in what insight to apply.
            return None, None
        
    available_moves = collapse_moves(available_moves)
    
    # There may be multiple hints using the same insight, but that's ok because we don't have to show all of them. In fact, if there are multiple that might in the future allow us to show examples of insights. For now, just pick the first one available.
    move = available_moves[0]
    
    post_move = deepcopy(puzzle_before_insight)
    solver.apply_move(post_move, move)

    final_puzzle, is_valid, _, _ = solver.apply_hints(post_move, hints)
    assert final_puzzle.is_complete() and is_valid, f"can't solve without forbidden insights {forbidden_insights - {insight}}. Puzzle: {final_puzzle}{hints}"

    # solver.can_solve_without_forbidden(
    #     post_move, hints
    # )

    _, new_available = solver.get_available_moves(post_move, hints)
    for next_move in new_available:
        if move["type"] == next_move["type"]:
            if move["type"] == "clue" and move["indexed_clue"]["idx"] == next_move["indexed_clue"]["idx"]:
                # Subsequent moves can also be made using the same clue.
                return None, None

    return puzzle_before_insight, move
