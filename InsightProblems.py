import ultraimport
from copy import deepcopy

ultraimport("__dir__/LogicPuzzles.py", package="main")
from main.LogicPuzzles import Solver, Insight


# Given a valid puzzle and an insight, find an insight problem if possible.
# The insight problem is a partially solved puzzle for which the next move can 
# only be the insight, and no subsequent insights can be made using the same hint.
# Return the insight problem and the next move
def get_insight_problem(puzzle, hints, insight):
    copy = deepcopy(puzzle)
    # Do as much of the puzzle as possible without the insight (or its descendants).
    forbidden_insights = Insight.sub_dag(insight)
    solver = Solver(forbidden_insights, allow_uncertain = False)
    puzzle_before_insight, _, _, _ = solver.apply_hints(
        copy, hints
    )

    _, available_moves = solver.get_available_moves(
        puzzle_before_insight,
        hints
    )

    if len(available_moves) != 1:
        return None
    
    move = available_moves[0]
    if insight not in move["insights"]:
        return None
    
    post_move = deepcopy(copy)
    solver.apply_move(post_move, move)

    _, new_available = solver.get_available_moves(post_move, hints)
    for next_move in new_available:
        if move["type"] == next_move["type"]:
            if move["type"] == "clue" and move["indexed_clue"]["idx"] == next_move["indexed_clue"]["idx"]:
                # Subsequent moves can also be made using the same clue.
                return None

    return
