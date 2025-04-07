from copy import deepcopy

from Evolution import get_available_moves
from HintToEnglish import hint_to_english
from LogicPuzzles import Category, Puzzle, Insight


# Get insights found by the solver from the current state to the end.
def gen_move_tree(curr_state, hints, choose_fn):
    curr_hint_idx = 0
    tree = {
        "curr_state": deepcopy(curr_state),
        "moves_from_here": r_gen_move_tree(
            deepcopy(curr_state), hints, curr_hint_idx, choose_fn
        ),
    }

    return tree


# Recursively get the move tree for the next move as chosen by choose_fn
def r_gen_move_tree(curr_state, hints, curr_hint_idx, choose_fn):
    children = []
    _, available_moves = get_available_moves(curr_state, hints)
    if len(available_moves) == 0:
        return []

    chosen_move = choose_fn(available_moves, curr_hint_idx)
    chosen_hint_idx = get_hint_idx(chosen_move)

    for move in available_moves:
        if get_hint_idx(move) == chosen_hint_idx:
            move["chosen_by_fn"] = True
            if chosen_hint_idx != curr_hint_idx:
                if chosen_hint_idx >= 0 and chosen_hint_idx < 100:
                    # use whatever the new index is.
                    curr_hint_idx = chosen_hint_idx
                else:
                    # move on to the next hint
                    curr_hint_idx += 1
            move["moves_from_here"] = r_gen_move_tree(
                deepcopy(move["result"]), hints, curr_hint_idx, choose_fn
            )
        children.append(move)
    return children


# Sequence of moves similar to the OG solver, following the hints in order and making all insights at each hint before moving on
def choose_move_ordered(available_moves, curr_hint_idx):
    best_move = available_moves[0]
    best_move_hint_idx = get_hint_idx(best_move)

    for move in available_moves:
        chosen = False

        if move["type"] != "repair":
            move_hint_idx = get_hint_idx(move)

            if best_move_hint_idx != curr_hint_idx:
                if move_hint_idx == curr_hint_idx:
                    # Do the current move until there are no insights left to make
                    chosen = True
                elif move_hint_idx < 0:
                    # After the current move, find any openings.
                    chosen = True
                elif best_move_hint_idx >= 0 and best_move_hint_idx < 100:
                    if move_hint_idx >= 100:
                        # Do transitives after every move.
                        chosen = True
                    elif best_move_hint_idx >= curr_hint_idx:
                        # Try to pick a move as close as possible to the curr_hint_idx while being larger.
                        if (
                            move_hint_idx >= curr_hint_idx
                            and move_hint_idx < best_move_hint_idx
                        ):
                            chosen = True
                    else:
                        # We have wrapped around the list and just want the smallest possible hint index.
                        if curr_hint_idx < best_move_hint_idx:
                            chosen = True

        if chosen:
            best_move = move
            best_move_hint_idx = move_hint_idx

    return best_move


# Sequence of moves as made by a lazy solver choosing the first easiest insight available
def choose_move_lazy(available_moves, curr_hint_idx):
    best_move = available_moves[0]
    best_move_hint_idx = get_hint_idx(best_move)
    best_move_hardest_insight = get_hardest_insight(best_move)

    for move in available_moves:
        chosen = False

        if move["type"] != "repair":
            move_hint_idx = get_hint_idx(move)
            move_hardest_insight = get_hardest_insight(move)

            if move_hardest_insight.value < best_move_hardest_insight.value:
                # Always choose an easier move
                chosen = True
            elif move_hardest_insight.value == best_move_hardest_insight.value:
                # Among equally easy moves, choose the next in an ordered sequence.
                if move_hint_idx < 0:
                    # Always do openings first.
                    chosen = True
                elif best_move_hint_idx >= curr_hint_idx and best_move_hint_idx < 100:
                    # Try to pick a move as close as possible to the curr_hint_idx while being larger.
                    # Transitives always go last (100)
                    if (
                        move_hint_idx >= curr_hint_idx
                        and move_hint_idx < best_move_hint_idx
                    ):
                        chosen = True
                else:
                    # We have wrapped around the list and just want the smallest possible hint index.
                    if curr_hint_idx < best_move_hint_idx:
                        chosen = True

        if chosen:
            best_move = move
            best_move_hardest_insight = move_hardest_insight
            best_move_hint_idx = move_hint_idx

    return best_move


# hint_idx is the idx of the hint. openings and transitives are given a high idx to ensure they come after the hints.
def get_hint_idx(move):
    if "indexed_hint" in move:
        return move["indexed_hint"]["idx"]
    elif move["type"] == "openings":
        return -1
    elif move["type"] == "transitives":
        return 100
    return 1000


# Usually a move will only have one insight, but in case it doesn't, set the difficulty by the hardest insight it requires.
def get_hardest_insight(move):
    move_hardest_insight = list(move["insights"])[0]
    for insight in move["insights"]:
        if insight.value > move_hardest_insight.value:
            move_hardest_insight = insight
    return move_hardest_insight


def save_move_tree(puzzle, hints, choose_fn, name):
    file = open("tree_{}.txt".format(name), "w")
    file.write("Puzzle:\n")
    file.write(puzzle.print_grid())
    file.write("Hints:\n")
    for hint in hints:
        file.write(hint_to_english(hint) + "\n")

    tree = gen_move_tree(puzzle, hints, choose_fn)
    next_moves = tree["moves_from_here"]
    if len(next_moves) > 0:
        r_print_moves(file, next_moves)

    file.close()
    return


def r_print_moves(file, moves):
    next_move = moves[0]
    move_liness = []
    max_lines = 0
    max_line_len = 0
    for move in moves:
        move_lines = move["move_diff"].print_grid().splitlines()
        if "indexed_hint" in move:
            hint = move["indexed_hint"]["hint"]
            move_lines.append("hint: {}".format(hint_to_english(hint)))
        else:
            move_lines.append(move["type"])
        move_lines.append("insights: {}".format(insights_to_string(move["insights"])))
        if "chosen_by_fn" in move:
            next_move = move
            move_lines.append("CHOSEN BY SOLVER")
        else:
            move_lines.append("")
        move_liness.append(move_lines)
        if len(move_lines) > max_lines:
            max_lines = len(move_lines)
        for line in move_lines:
            if len(line) > max_line_len:
                max_line_len = len(line)

    for i in range(max_lines):
        line_str = ""
        for move in move_liness:
            line_str += move[i].ljust(max_line_len + 5)
        file.write(line_str + "\n")

    if len(next_move["moves_from_here"]) > 0:
        r_print_moves(file, next_move["moves_from_here"])
    return


def insights_to_string(insights):
    str = ""
    for insight in insights:
        str += f"{insight.name} ({insight.value}), "
    return str


if __name__ == "__main__":
    order = Category("order", ["1st", "2nd", "3rd", "4th"], True)
    quantity = Category("cup", ["1 cup", "2 cups", "3 cups", "4 cups"], True)
    food = Category("ingredient", ["Beans", "Pasta", "Tomato", "Carrots"], False)
    puzzle = Puzzle([order, quantity, food])

    hints = [
        {"before": [food, "Pasta", food, "Beans", order, 2]},
        {"before": [food, "Tomato", food, "Beans", quantity, 2]},
        {"is": [food, "Tomato", order, "4th"]},
        {"before": [food, "Beans", food, "Carrots", quantity, 1]},
    ]

    save_move_tree(puzzle, hints, choose_move_ordered, "ordered")
    save_move_tree(puzzle, hints, choose_move_lazy, "lazy")
