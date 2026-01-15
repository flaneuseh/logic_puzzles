import ultraimport

ultraimport("__dir__/LogicPuzzles.py", package="main")
from main.LogicPuzzles import apply_hints, get_available_moves


class Insight:
    dag = []

    # Maintain an insight DAG in which each node points to its descendants (and its parents)
    def __init__(self, name, parents):
        self.name = name
        self.parents = parents
        self.children = []
        for parent in parents:
            parent.children.append(self)
        Insight.dag.append(self)

    # An insight and all its descendants in the DAG.
    # WARNING: This will infinitely loop if there is a cycle in the insight graph.
    # I could avoid the infinite loop with a counter, but I don't care to.
    def sub_dag(insight):
        to_visit = [insight]
        sub_dag = []
        while to_visit:
            curr_node = to_visit.pop()
            to_visit.extend(curr_node.children)
            sub_dag.append(curr_node)

        return sub_dag


# If there is an O in a row/column, the rest of the row/column must be X (given)
CROSS_OUT = Insight("CROSS_OUT", [])
# If a row/column has one opening and the rest are Xs, it must be O (given)
OPENING = Insight("OPENING", [])
# Every row/column must have an O (given)
MUST_O = Insight("MUST_O", [])
# The transitive property applies (A -> B and B -> C, so A -> C) (given)
TRANS_ABC_TRUE = Insight("TRANS_ABC_TRUE", [])

# Apply an is hint (given)
APPLY_IS = Insight("APPLY_IS", [])
# Apply a not hint (given)
APPLY_NOT = Insight("APPLY_NOT", [])
# Apply an or hint once one of the clauses has been answered. (given)
APPLY_OR = Insight("APPLY_OR", [])
# If A is answered and B is N after A, then answer B is N after A (given)
APPLY_BEFORE_N_SPOTS = Insight("APPLY_BEFORE_N_SPOTS", [])

# If A is answered then B must be one of the spots after A and vice versa (X where that is not true)
# Can be derived from APPLY_BEFORE_N_SPOTS by considering the possible values for N and finding that regardless of the N,
# this must be true.
APPLY_BEFORE_UNDEFINED_SPOTS = Insight(
    "APPLY_BEFORE_UNDEFINED_SPOTS", [APPLY_BEFORE_N_SPOTS]
)
# A -> B and B !> C, so A !> C (given)
# Can be derived from TRANS_ABC_TRUE (if A -> B and A -> C then B -> C, which is a contradiction)
TRANS_ABC_FALSE = Insight("TRANS_ABC_FALSE", [TRANS_ABC_TRUE])
# If A or B from category 0 is C then no other entity from category 0 is C
# Can be derived by considering A -> C and B -> C and seeing that either way, all other entities from 0 are X.
SIMPLE_OR_SAME_CAT = Insight("SIMPLE_OR_SAME_CAT", [APPLY_OR, CROSS_OUT])
# If A or B is C then A is not B
# Can be derived by applying the OR rule in turn and seeing that by TRANS_ABC_FALSE, A is not B either way.
SIMPLE_OR_DIFF_CAT = Insight("SIMPLE_OR_DIFF_CAT", [APPLY_OR, TRANS_ABC_FALSE])
# If A < B and A, B are not in the same category, then A is not B.
# Can be derived by considering each possible value for A with APPLY_BEFORE_UNDEFINED_SPOTS and applying TRANS_ABC_FALSE
BEFORE_DIFF_CAT = Insight(
    "BEFORE_DIFF_CAT", [(APPLY_BEFORE_UNDEFINED_SPOTS, TRANS_ABC_FALSE)]
)
# The before entity can't be in the last spot (and vice versa for the after entity) Same for undefined spots
# Can be derived by considering each possible value for A with APPLY_BEFORE_UNDEFINED_SPOTS and seeing that in the last spot,
# there is no remaining possible value for B.
BEFORE_NOINFO = Insight("BEFORE_NOINFO", [(APPLY_BEFORE_UNDEFINED_SPOTS, MUST_O)])
# The before entity can't be in the last N spots (and vice versa for the after entity)
# The general case of BEFORE_NOINFO. It could also be derived directly from APPLY_BEFORE_N_SPOTS,
# but expert knowledge suggests it will be easier for users to encounter BEFORE_NOINFO first.
BEFORE_N_SPOTS_NOINFO = Insight("BEFORE_N_SPOTS_NOINFO", [BEFORE_NOINFO])

# A streak of Xs at the beginning/end forces the first available position for the other entity to shift.
# Can be derived in the same way as BEFORE_N_SPOTS_NOINFO;
# again, it will be easier for users to encounter BEFORE_N_SPOTS_NOINFO first.
BEFORE_N_SPOTS_SHIFT = Insight("BEFORE_N_SPOTS_SHIFT", [BEFORE_N_SPOTS_NOINFO])
# For a position to be a valid answer, the corresponding position +/- num must be valid for the other entity
# The most complex case of BEFORE_NOINFO.
BEFORE_N_SPOTS_CROSSCHECK = Insight("BEFORE_N_SPOTS_CROSSCHECK", [BEFORE_N_SPOTS_SHIFT])
# A and B don't share any possibilities; A != B
# Can be derived by considering all possible values for A and applying TRANS_ABC_FALSE.
# Another kind of crosscheck.
TRANS_SETS = Insight("TRANS_SETS", [TRANS_ABC_FALSE])


# Get a partially solved puzzle for which the next logical move can only be the given insight,
# and no further insights can be made using the same hint as the move
# Return the insight problem (or None), the next move plus OPENING and CROSS_OUT, and the hint associated with it
def get_insight_problem(puzzle, hints, insight):
    # Do as much of the puzzle as possible without the insight (or its descendants).
    forbidden_insights = Insight.sub_dag(insight)
    puzzle_before_insight, is_valid, _, _ = apply_hints(
        puzzle, hints, print_soln=False, forbidden_insights=forbidden_insights
    )
    if puzzle_before_insight.is_complete() or not is_valid:
        # The puzzle can be solved without the insight, or it is a broken puzzle.
        return None

    _, available_moves = get_available_moves(
        puzzle_before_insight,
        hints,
        as_steps=False,
        forbidden_insights=forbidden_insights,
        allow_uncertain_moves=False,
    )

    return
