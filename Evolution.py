# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.15.2
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Evolution
#
# An evolutionary Algorithm to evolve logic puzzles

# %%
# !pip install import_ipynb

# %%
# Imports Baby
# import import_ipynb
from LogicPuzzles import (
    Puzzle,
    generate_hint,
    str_hint,
    Category,
    apply_hint,
    find_openings,
    find_transitives,
    ALL_INSIGHTS,
    repair,
    Insight,
)
from HintToEnglish import hint_to_english

# from DataVisualization import plot_history
import random
import math
import numpy.random as npr
import pickle
from itertools import combinations
from HintToEnglish import hint_to_english
from copy import deepcopy


# %%
def decide(rate):
    return random.random() < rate


# %% [markdown]
# ## Representation
#
# ### Mutation
#
# The following kinds of mutation are implemented:
# 1. Add new hint
# 2. Remove a hint
#
# ### Cross-over
# Randomly add hints to each of children
#
# ### Heuristic
#
# #### Feasibility
# The fesability heuristic is the percentage of empty (unsolved). A valid puzzle is completely filled, but if the hints are incomplete or inlogical the resulting puzzle will have many empty pieces. This assumes that the hints will stop being applied when an invalid hint is attempted.

#  We are hoping to optimize for challenge. Certain hint types are more challenging then others, and this is our estimate of the difficulty of different hint types (hardest being higher). This way harder hints (ex: before, simple or) can be selected over easier hints (ex: is).
HINT_VALUES = {
    "is": 0.2,
    "not": 0.4,
    "before": 0.7,
    "simple_or": 0.7,
    "compound_or": 0.1,
}


def get_available_moves(puzzle, hints):
    """
    get all possible next moves in the solution:
        any openings
        any transitive moves possible in order
        all currently applicable hints and their moves in order
        any insights needed
        if the current board is invalid, get the most salient contradiction (highlight the cell(s) that create the contradiction)
    """
    moves = []
    solution, is_valid, _, _ = apply_hints(puzzle, hints)
    if not is_valid:
        # The puzzle itself is broken. this should never happen.
        raise Exception("INVALID_PUZZLE")

    result = deepcopy(puzzle)
    broken_state = repair(result, solution)
    if broken_state:
        # If there are any errors, the only valid move is to remove all invalid marks.
        moves.append({
            "type": "repair",
            "result": result,
            "move_diff": get_move_diff(puzzle, result),
            "insights": [Insight.REPAIR],
        })

    state_is_valid = not broken_state

    # We know that so far the puzzle is correct.
    result = deepcopy(puzzle)
    applied, is_valid, _, insights = find_openings(result, slow=True)
    if len(insights) == 0:
        insights = [Insight.NO_INSIGHT]
    if applied and is_valid:
        moves.append({
            "type": "openings",
            "result": result,
            "move_diff": get_move_diff(puzzle, result),
            "insights": insights,
        })
    result = deepcopy(puzzle)
    applied, is_valid, _, insights = find_transitives(result, slow=True)
    if len(insights) == 0:
        insights = [Insight.NO_INSIGHT]
    if applied and is_valid:
        moves.append({
            "type": "transitives",
            "result": result,
            "move_diff": get_move_diff(puzzle, result),
            "insights": insights,
        })
    for idx, hint in enumerate(hints):
        result = deepcopy(puzzle)
        applied, is_valid, _, insights = apply_hint(result, hint, slow=True)
        if len(insights) == 0:
            insights = [Insight.NO_INSIGHT]
        if applied and is_valid:
            moves.append({
                "type": "hint",
                "indexed_hint": {"idx": idx, "hint": hint},
                "result": result,
                "move_diff": get_move_diff(puzzle, result),
                "insights": insights,
            })
    return state_is_valid, moves


def get_move_diff(before, after):
    diff = deepcopy(after)

    for cat1 in before.left_right:
        for cat2 in before.top_bottom:
            before_grid = before.get_grid(cat1, cat2)
            after_grid = after.get_grid(cat1, cat2)
            if before_grid is None or after_grid is None:
                continue
            for ent2_idx in range(0, len(before_grid)):
                for ent1_idx in range(0, len(before_grid[ent2_idx])):
                    if (
                        before_grid[ent2_idx][ent1_idx]
                        == after_grid[ent2_idx][ent1_idx]
                    ):
                        diff.answer(
                            cat1,
                            cat2,
                            cat1.entities[ent1_idx],
                            cat2.entities[ent2_idx],
                            lowercase_grid_symbol(after_grid[ent2_idx][ent1_idx]),
                        )
                    elif after_grid[ent2_idx][ent1_idx] == "*":
                        # This is a repair operation
                        diff.answer(
                            cat1,
                            cat2,
                            cat1.entities[ent1_idx],
                            cat2.entities[ent2_idx],
                            "_",
                        )
    return diff


def lowercase_grid_symbol(S):
    if S == "X":
        return "x"
    elif S == "O":
        return "o"
    elif S == "*":
        return "*"
    return "__"


# %%
def apply_hints(puzzle, hints, print_soln=False, forbidden_insights=set()):
    """
    solver
    """
    is_valid = True
    copy = Puzzle(puzzle.categories)
    queue = hints[:]
    # trace = {}
    backlog = []
    applied = True
    insights = set()
    loop = 0
    if len(hints) == 0:
        is_valid = False
        return copy, is_valid, loop, insights
    while is_valid and applied and len(queue) > 0:
        applied = False
        loop += 1

        for hint in queue:
            a, is_valid, complete, hint_insights = apply_hint(
                copy, hint, forbidden_insights=forbidden_insights
            )
            applied = applied or a
            insights = insights | hint_insights
            if not complete:
                backlog.append(hint)
            elif print_soln:
                print("HINT NO LONGER NEEDED: ", hint_to_english(hint))
            if not is_valid:
                return copy, is_valid, loop, insights

            # Apply additional logic
            if a:
                a_2 = True
                a_3 = True
                while a_2 or a_3:
                    # Apply openings and transitives as many times as you can.
                    a_2, is_valid, complete, opening_insights = find_openings(
                        copy, forbidden_insights=forbidden_insights
                    )
                    if not is_valid:
                        return copy, is_valid, loop, insights
                    a_3, is_valid, complete, trans_insights = find_transitives(
                        copy, forbidden_insights=forbidden_insights
                    )
                    if not is_valid:
                        return copy, is_valid, loop, insights
                    applied = applied or a_2 or a_3  # test if anything was changed
                    insights = insights | trans_insights | opening_insights
                if not is_valid:
                    return copy, is_valid, loop, insights
            if print_soln and a:
                print("hint: ", hint_to_english(hint))
                print("updated grid: ")
                print(copy.print_grid())
        queue = backlog
        backlog = []

    return copy, is_valid, loop, insights


def get_needed(puzzle, hints):
    completed_puzzle, is_valid, _, _ = apply_hints(
        puzzle, hints, print_soln=False
    )
    assert(completed_puzzle.is_complete() and is_valid)

    needed = set()
    unneeded = ALL_INSIGHTS.copy()

    # Add insights easiest first until the puzzle can be solved.
    completed_without_maybe = can_solve_without_forbidden(
        puzzle, hints, unneeded
    )
    for insight in Insight:
        if not completed_without_maybe:
            needed = needed | {insight}
            unneeded = unneeded - {insight}
            completed_without_maybe = can_solve_without_forbidden(
                puzzle, hints, unneeded
            )
    assert len(needed | unneeded) == len(ALL_INSIGHTS)
    assert can_solve_without_forbidden(puzzle, hints, unneeded), "can't solve without some of {}".format(unneeded)
    assert not can_solve_without_forbidden(puzzle, hints, needed), "can solve without {}".format(needed)
    # Remove any insights that don't result in the puzzle breaking, starting from the hardest
    for insight in reversed(Insight):
        if insight in needed:
            needed = needed - {insight}
            completed_without_maybe = can_solve_without_forbidden(
                puzzle, hints, ALL_INSIGHTS - needed
            )
            
            if not completed_without_maybe:
                needed = needed | {insight}
            else:
                unneeded = unneeded | {insight}
    assert len(needed | unneeded) == len(ALL_INSIGHTS)
    assert len(ALL_INSIGHTS - needed) == len(unneeded)
    assert can_solve_without_forbidden(puzzle, hints, ALL_INSIGHTS - needed), "can't solve without some of {}".format(ALL_INSIGHTS - needed)
    assert not can_solve_without_forbidden(puzzle, hints, needed), "can solve without {}".format(needed)
    return needed


def can_solve_without_forbidden(puzzle, hints, forbidden_insights):
    completed_puzzle, is_valid, _, used_insights = apply_hints(
        puzzle, hints, print_soln=False, forbidden_insights=forbidden_insights
    )
    assert (
        len(used_insights & forbidden_insights) == 0
    ), "insights: {} includes forbidden: {}".format(
        used_insights, used_insights & forbidden_insights
    )
    assert is_valid, "not valid with forbidden {}".format(forbidden_insights)
    return completed_puzzle.is_complete()


# %%
class HintSet:
    def __init__(
        self, hints, puzzle, required_insights=set(), forbidden_insights=set()
    ) -> None:
        self.hints = hints
        self.puzzle = puzzle  # assumed to be blank
        self.required_insights = required_insights
        self.require_insight = len(self.required_insights) > 0
        self.forbidden_insights = forbidden_insights
        self.completed_puzzle, self.valid, self.loops, self.solver_insights = (
            apply_hints(
                self.puzzle,
                self.non_duplicates(),
            )
        )

        self.insights = set()
        if self.valid and self.completed_puzzle.is_complete():
            self.insights = get_needed(self.puzzle, self.hints)

    def follows_insight_requirements(self):
        # Should be solvable without the forbidden insights, 
        # and should not be solvable without the required insights
        if not self.valid or not self.completed_puzzle.is_complete():
            return True
        return can_solve_without_forbidden(
            self.puzzle, self.hints, self.forbidden_insights
        ) and len(self.insights & self.required_insights) == len(self.required_insights)

    def get_duplicates(self):
        english_dict = {}
        for hint in self.hints:
            english = hint_to_english(hint)
            if english in english_dict:
                english_dict[english] += 1
            else:
                english_dict[english] = 1
        duplicates = {}
        for key, value in english_dict.items():
            if value > 1:
                duplicates[key] = value

        return duplicates

    def num_duplicates(self):
        duplicates = self.get_duplicates()
        s = 0
        for key in duplicates:
            s += duplicates[key]
        return s

    def non_duplicates(self):
        english_hints = []
        non_duplicates = []
        for hint in self.hints:
            english = hint_to_english(hint)
            if not english in english_hints:
                non_duplicates.append(hint)
                english_hints.append(english)

        final_puzzle_without_duplicates, valid_without_duplicates, _, _ = (
            apply_hints(
                self.puzzle,
                non_duplicates,
            )
        )
        final_puzzle_with_duplicates, valid_with_duplicates, _, _ = (
            apply_hints(
                self.puzzle,
                self.hints,
            )
        )
        # print("--------------------------------------")
        # print("original hints ", [hint_to_english(hint) for hint in self.hints])
        # print("non duplicates: ", [hint_to_english(hint) for hint in non_duplicates])
        # print("with dupes complete ", final_puzzle_with_duplicates.is_complete())
        # print("without dupes complete ", final_puzzle_without_duplicates.is_complete())
        # print("with dupes grid")
        # print(final_puzzle_with_duplicates.print_grid())
        # print("without dupes grid")
        # print(final_puzzle_without_duplicates.print_grid())
        # print("with dupes valid ", valid_with_duplicates)
        # print("without dupes valid ", valid_without_duplicates)
        
        # if valid_with_duplicates != valid_without_duplicates or valid_with_duplicates and final_puzzle_with_duplicates.is_complete() != final_puzzle_without_duplicates.is_complete():
        #     print("WITHOUT DUPES SOLVER")
        #     apply_hints(
        #         self.puzzle,
        #         non_duplicates,
        #         print_soln = True
        #     )
        #     print("WITH DUPES SOLVER")
        #     apply_hints(
        #         self.puzzle,
        #         self.hints,
        #         print_soln = True
        #     )
        assert(valid_with_duplicates == valid_without_duplicates)
        if valid_with_duplicates:
            assert(final_puzzle_with_duplicates.is_complete() == final_puzzle_without_duplicates.is_complete())

        return non_duplicates

    def mutate(self, add_rate):
        hint_copy = self.hints[:]
        roll = random.random()
        if ((roll < 0.45) and len(hint_copy) <= 20) or len(hint_copy) <= 0:
            new_hint = generate_hint(self.puzzle)
            hint_copy.append(new_hint)
        elif roll < 0.90:
            index = random.randint(0, len(hint_copy) - 1)
            del hint_copy[index]
        else:
            self.swap_hints()

        return HintSet(
            hint_copy,
            self.puzzle,
            self.required_insights,
            self.forbidden_insights,
        )

    def swap_hints(self):
        i = random.randint(0, len(self.hints) - 1)
        j = random.randint(0, len(self.hints) - 1)
        temp = self.hints[i]
        self.hints[i] = self.hints[j]
        self.hints[j] = temp

    def cross_over(self, other):
        hints = self.hints[:] + other.hints[:]
        random.shuffle(hints)
        threshold = math.floor(len(hints) / 2)

        return HintSet(
            hints[0:threshold],
            self.puzzle,
            self.required_insights,
            self.forbidden_insights,
        ), HintSet(
            hints[threshold : len(hints)],
            self.puzzle,
            self.required_insights,
            self.forbidden_insights,
        )

    def get_hint_counts(self, hints):
        total_counts = {
            "is": 0,
            "not": 0,
            "before": 0,
            "simple_or": 0,
            "compound_or": 0,
        }

        for hint in hints:
            kind = next(iter(hint))
            total_counts[kind] += 1

        return total_counts

    def hint_ratios(self):
        counts = self.get_hint_counts(self.non_duplicates())
        values = list(counts.values())
        pairs = combinations(counts.keys(), 2)

        diff_sum = 0
        l = 0

        for first, second in pairs:
            diff_sum += abs(counts[first] - counts[second])
            l += 1

        mad = (diff_sum / l) / (sum(values) / len(values))
        return 0.5 * mad

    def is_feasible(self):
        valid = (
            len(self.hints) > 0
            and self.valid
            and self.completed_puzzle.is_complete()
            and self.follows_insight_requirements()
        )

        return valid

    def _violations_fun(self, violations):
        if violations > 10:
            return 0
        elif violations <= 0:
            return 1
        else:
            return 1 - (violations / 10)

    def weighted_feasiblility(self, complete_w, valid_w, violation_w):
        complete, valid = self.completed_puzzle.percent_complete()
        violations = self.completed_puzzle.num_violations()

        return (
            (complete_w * complete)
            + (valid_w * valid)
            + (violation_w * self._violations_fun(violations))
        )

    def feasibility(self):
        complete, valid = self.completed_puzzle.percent_complete()
        # violations = self.completed_puzzle.num_violations()
        #return (0.5 * complete) + (0.5 * valid)
        if not self.require_insight or not valid or not self.completed_puzzle.is_complete():
            return (0.5 * complete) + (0.5 * valid)
        else:
            return (
                (0.45 * complete)
                + (0.45 * valid)
                + (0.1 * self.follows_insight_requirements())
            )

    def solver_loops(self):
        if len(self.hints) == 0:
            return 0

        return self.loops

    def hint_size(self):
        return len(self.hints)

    def optimize_func(self):
        if len(self.hints) == 0:
            return 0

        score = 0
        for hint in self.hints:
            rule = list(hint.keys())[0]
            if rule == "simple_hint":
                rule = list(hint.keys())[0]
            score += HINT_VALUES[rule]

        num_loops = self.loops

        # Fn 1: optimize by hint type and number of hints
        # return (0.5 * score / len(self.hints)) + (0.5 * (1 - (len(self.hints) / 20)))

        # Fn 2: optimize by number of solver loops and number of hints
        # return (0.5 * min(num_loops, 10) / 10) + (0.5 * (1 - (len(self.hints) / 20)))

        # Fn 3: optimize by number of loops only
        # return num_loops

        # Fn 4: optimize by number of hints only
        # return 1 - (len(self.hints) / 20)

        # Fn 5: optimize using insights
        return (0.45 * min(num_loops, 10) / 10) + (0.45 * (1 - (len(self.hints) / 20)) + .1 * self.follows_insight_requirements())


class History:
    def __init__(self):
        self.num_feasible = []
        self.feasible_fitness = []
        self.infeasible_fitness = []

    def update_history(self, feasible, infeasible):
        self.num_feasible.append(len(feasible))

        if len(feasible) == 0:
            self.feasible_fitness.append(0)
        else:
            self.feasible_fitness.append(feasible[0][0])

        if len(infeasible) == 0:
            self.infeasible_fitness.append(0)
        else:
            self.infeasible_fitness.append(infeasible[0][0])


# %%
def random_hint_set(puzzle, required_insights=set(), forbidden_insights=set()):
    num = random.randint(1, 5)
    hints = [generate_hint(puzzle) for i in range(num)]
    return HintSet(hints, puzzle, required_insights, forbidden_insights)


# %% [markdown]
# ## Evolution

# %%


def select(population):
    m = sum([c[0] for c in population])
    if m == 0:
        selection_probs = [1 / len(population) for c in population]
    else:
        selection_probs = [c[0] / m for c in population]
    return population[npr.choice(len(population), p=selection_probs)]


# %%
def _add_child(hints, feasible, infeasible):
    """
    if hint set is valid, add to feasible pop with optmiziation fitness,
    otherwise add to infeasible pop with feasibility fitness
    """
    if hints.is_feasible():
        fitness = hints.optimize_func()
        feasible.append((fitness, hints))
    else:
        fitness = hints.feasibility()
        infeasible.append((fitness, hints))


def evolve(
    puzzle,
    generations,
    pop_size,
    x_rate,
    mut_rate,
    add_rate,
    elits,
    required_insights=set(),
    forbidden_insights=set(),
):
    feasible = []
    infeasible = []
    history = History()

    # Create initial population
    for i in range(pop_size):
        hints = random_hint_set(puzzle, required_insights, forbidden_insights)
        _add_child(hints, feasible, infeasible)

    for gen in range(generations):

        new_feasible = []
        new_infeasible = []

        feasible.sort(reverse=True, key=lambda a: a[0])
        infeasible.sort(reverse=True, key=lambda a: a[0])

        history.update_history(feasible, infeasible)

        if gen % 50 == 0:
            print("-" * 40)
            print("GENERATION " + str(gen))
            print("-" * 80)
            if len(infeasible) > 0:
                print("Infeasible")
                print(infeasible[0])
                print(infeasible[0][1].completed_puzzle.print_grid())
                print(infeasible[0][1].completed_puzzle.num_violations())
            if len(feasible) > 0:
                print("feasible:")
                print(feasible[0])
                print(feasible[0][1].completed_puzzle.print_grid())
            print("-" * 80)

        # elitism
        if len(feasible) > 0:
            new_feasible = feasible[:elits]
        if len(infeasible) > 0:
            new_infeasible = infeasible[:elits]

        # create new population
        while len(new_feasible) + len(new_infeasible) < pop_size:

            # Selection
            # Not clear to me how to choose which pop to select from,
            # right now am deciding randomly based on size of two pops

            if decide(len(feasible) / (len(feasible) + len(infeasible))):
                # selecting from feasible
                indiv1 = select(feasible)[1]
                indiv2 = select(feasible)[1]
            else:
                indiv1 = select(infeasible)[1]
                indiv2 = select(infeasible)[1]

            # cross over
            if decide(x_rate):
                indiv1, indiv2 = indiv1.cross_over(indiv2)

            # mutation
            if decide(mut_rate):
                child1 = indiv1.mutate(add_rate)
                child2 = indiv2.mutate(add_rate)
            else:
                child1 = indiv1
                child2 = indiv2

            # add children
            _add_child(child1, new_feasible, new_infeasible)

            if len(new_feasible) + len(new_infeasible) < pop_size:
                _add_child(child2, new_feasible, new_infeasible)

        feasible = new_feasible
        infeasible = new_infeasible
    for child in feasible:
        assert len(child.insights & required_insights) == len(
            required_insights
        ), "insights: {} does not include all of: {}".format(
            child.insights, required_insights
        )
        assert can_solve_without_forbidden(
            child.puzzle, child.hints, child.forbidden_insights
        ), "can't solve without forbidden insights {}".format(forbidden_insights)
    return feasible, infeasible, history


# %%
if __name__ == "__main__":
    suspects = Category("suspect", ["Scarlet", "White", "Mustard", "Plum"], False)
    weapons = Category("weapon", ["Knife", "Rope", "Candle Stick", "Wrench"], False)
    rooms = Category("room", ["Ball room", "Living Room", "Kitchen", "Study"], False)
    time = Category("hour", ["1:00", "2:00", "3:00", "4:00"], True)

    puzzle = Puzzle([suspects, weapons, rooms, time])

    pop = evolve(puzzle, 100, 50, 0.2, 1, 0.5, 2, required_insights=ALL_INSIGHTS)

    file = open("InsightExp/pop.p", "wb")
    pickle.dump(pop, file)
    feasible = pop[0]
    infeasible = pop[1]
    history = pop[2]

    print(feasible)
    print(feasible[0][1].completed_puzzle.print_grid())
    print(len(feasible[0][1].hints))
    print([hint_to_english(hint) for hint in feasible[0][1].hints])
    print("\n\n")
    print(infeasible)
    # plot_history(history, "Insight_Exp")
    """hints = random_hint_set(puzzle) 
    for hint in hints.hints:
        print(hint)
    
    print(hints.hint_ratios())"""

# %%
# if __name__ == "__main__":
#     file = open("Experiement1/pop1.p", "wb")
#     pickle.dump(pop, file)
#     feasible = pop[0]
#     infeasible = pop[1]
#     history = pop[2]

#     print(feasible)
#     print(feasible[0][1].completed_puzzle.print_grid())
#     print(len(feasible[0][1].hints))
#     print([hint_to_english(hint) for hint in feasible[0][1].hints])
#     print("\n\n")
#     print(infeasible)
#     plot_history(history, "Experiement1")
