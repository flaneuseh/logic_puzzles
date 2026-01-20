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

# %%
# Update this version to verify that .py and .ipynb are in sync.
# Version: 5.0

# %% colab={"base_uri": "https://localhost:8080/"} id="u9fPlqt1JIrO" outputId="046eb385-7b0d-4f86-ed8d-ccf802682a2d"
# !pip install parsimonious

# %% id="AzB0GRIux4lQ"
# Imports for DAAAYS
import itertools

# from parsimonious.grammar import Grammar
# from parsimonious.nodes import NodeVisitor
import random
from copy import deepcopy
from enum import Enum
import ultraimport

ultraimport("__dir__/HintToEnglish.py", package="main")
from main.HintToEnglish import clue_to_english


# %% [markdown] id="_98_qlHVJX47"
# # Murder Mystery Puzzle!

# %% [markdown] id="VAgqh9CTJaif"
# ## Defining a logic puzzle class
#
#
# ### Answer(cat1, cat2, ent1, ent2, symbol)
#
# Set the symbol (ex: "X") for ent1 in cat1 and ent2 in cat2
#
# ### is_valid()
# Return true if there are no logical contradictions in puzzle
#
# Types of contradicitons:
# * grid: more than 1 "O" in one row or column
# * truth: if scarlet has a knife and the knife is in the study, then scarlet should be in the study
#
# ### is_complete()
#
# Returns true if is_valid and there is exactly one "O" in each row and column.


# %% id="YxoXVU28JZaw"
class Category:
    def __init__(self, title, entities, is_numeric, increment=1):
        self.title = title
        self.entities = entities
        self.is_numeric = is_numeric
        self.increment = increment

    def __str__(self):
        return self.title


# %% id="EFhbSHGwKlRs"


class Grid:
    def __init__(self, categories):
        """
        Set up a blank puzzle

        The set up is a bit goofy but it works

        First determine which entities to put on the top, and which to put down the left

        This can be used to determine how to arrange grids so that each category
        is matched with each other exactly once

        In the dictory every pair of categories is represented as "cat1:cat2"
        where cat1 is the category on the top and cat2 is one the left. The value
        of the diction is a 2d array, such that grid[x][y] represents the symbol
        for the xth entitity in cat2 and the yth entity in cat1.
        """
        self.categories = categories
        self.left_right = self.categories[0 : len(categories) - 1]
        self.top_bottom = []
        for i in range(len(self.categories) - 1, 0, -1):
            self.top_bottom.append(self.categories[i])
        self.grids = {}

        rows = len(self.top_bottom)

        for top_category in self.left_right:
            for i in range(rows):
                left_cat = self.top_bottom[i]
                title = self._to_key(top_category, left_cat)
                array = []
                for i in range(len(left_cat.entities)):
                    array += [["*"] * len(top_category.entities)]
                self.grids[title] = array

            rows -= 1

    def get_category(self, entity):
        """
        return a category where entity
        belong to it
        """
        for cat in self.categories:
            if entity in cat.entites:
                return cat
        return None

    def get_grid(self, cat1, cat2):
        """
        Get the grid for cat1 and cat2
        assuming cat1 is the top category
        """
        if self._to_key(cat1, cat2) in self.grids:
            return self.grids[self._to_key(cat1, cat2)]
        else:
            return None

    def trim_ent(self, ent):
        """
        trim an entity to three character
        to be able to print
        """
        if len(ent) > 3:
            return ent[0:3]
        else:
            return ent

    def _to_key(self, cat1, cat2):
        """
        return a string key for cat1 and cat2
        where cat1 is the top category and cat2
        is the left
        """
        return cat1.title + ":" + cat2.title

    def answer(self, cat1, cat2, ent1, ent2, new_symbol):
        """
        given ent1 in cat1 and ent2 in cat1
        change the symbol in the grid.

        This works regardless of the order of cat1 and cat2
        ex: you don't need to put the top category first
        """

        diff = Grid(self.categories)
        if self.get_symbol(cat1, cat2, ent1, ent2) == new_symbol:
            return False, diff
        index1 = cat1.entities.index(ent1)
        index2 = cat2.entities.index(ent2)
        if self._to_key(cat1, cat2) in self.grids:
            grid = self.grids[self._to_key(cat1, cat2)]
            grid[index2][index1] = new_symbol
            diff_grid = diff.grids[self._to_key(cat1, cat2)]
            diff_grid[index2][index1] = new_symbol

        elif self._to_key(cat2, cat1) in self.grids:
            grid = self.grids[self._to_key(cat2, cat1)]
            grid[index1][index2] = new_symbol
            diff_grid = diff.grids[self._to_key(cat2, cat1)]
            diff_grid[index1][index2] = new_symbol

        return True, diff

    def _print_row(self, top_cats, cat2, remove_top=False):
        """
        return a singular row for the puzzle,
        given the columns (top_cats) and the row (cat2)
        should be used internally
        """

        top_ents = []
        for cat in top_cats:
            top_ents += cat.entities

        return_str = ""
        bar = "  " * 2 + "-" * (len(top_ents) * 5) + "\n"
        if not remove_top:
            top_string = " " * 4 + "  "
            top_string += "  ".join([self.trim_ent(ent) for ent in top_ents])
            return_str += top_string + "\n"
            return_str += bar

        grid1 = self.grids[top_cats[0].title + ":" + cat2.title]
        for i in range(len(grid1)):

            left_ent = self.trim_ent(cat2.entities[i]) + "| "
            return_str += left_ent
            for cat in top_cats:
                row = self.grids[cat.title + ":" + cat2.title][i]
                row_str = " " + "    ".join(row) + "  |"
                return_str += row_str
            return_str += "\n"

        return_str += bar

        return return_str

    def _print_row_small(self, top_cats, cat2):
        """
        return a singular row for the puzzle,
        given the columns (top_cats) and the row (cat2)
        should be used internally
        """

        top_ents = []
        for cat in top_cats:
            top_ents += cat.entities

        return_str = ""
        bar = "-" * (len(top_ents) + len(top_cats) + 1) + "\n"
        return_str += bar

        grid1 = self.grids[top_cats[0].title + ":" + cat2.title]
        for i in range(len(grid1)):

            left_ent = "|"
            return_str += left_ent
            for cat in top_cats:
                row = self.grids[cat.title + ":" + cat2.title][i]
                row_str = "".join(row) + "|"
                return_str += row_str
            return_str += "\n"

        return return_str

    def print_row(self, row, small=False):
        """
        find the top categories and the vertical categories
        for a single row
        """
        left_cat = self.top_bottom[row]
        num_top = len(self.left_right) - row
        if not small:
            remove_top = row > 0
            return self._print_row(self.left_right[0:num_top], left_cat, remove_top)
        else:
            return self._print_row_small(self.left_right[0:num_top], left_cat)

    def print_grid(self):
        """
        return the entire puzzle string
        """
        return_str = ""
        for i in range(len(self.top_bottom)):
            return_str += self.print_row(i)

        return return_str

    def print_grid_small(self):
        """
        return the entire puzzle string

        TODO: add category names?
        """
        return_str = ""
        for i in range(len(self.top_bottom)):
            return_str += self.print_row(i, True)

        return return_str

    def _grid_is_valid(self, grid):
        """
        Check that there are one or less "O"s
        for each row and column in a grid
        """
        # check rows
        rows_valid = [row.count("O") <= 1 for row in grid]
        if False in rows_valid:
            return False

        # check columns
        for i in range(len(grid[0])):
            c = 0
            for row in grid:
                if row[i] == "O":
                    c += 1
            if c > 1:
                return False

        return True

    def _grid_is_complete(self, grid):
        """
           Check that there is exactly 1 "O"
        for each row and column in a grid
        """
        # check rows
        rows_valid = [row.count("O") == 1 for row in grid]
        if False in rows_valid:
            return False

        # check columns
        for i in range(len(grid[0])):
            c = 0
            for row in grid:
                if row[i] == "O":
                    c += 1
            if c != 1:
                return False

        return True

    def cats_is_valid(self, cat1, cat2):
        """
        Return true if there is at most 1 "O"
        in each row and column
        """
        if self._to_key(cat1, cat2) in self.grids:
            grid = self.grids[self._to_key(cat1, cat2)]
        elif self._to_key(cat2, cat1) in self.grids:
            grid = self.grids[self._to_key(cat2, cat1)]

        return self._grid_is_valid(grid)

    def find_truths(self, category, ent):
        """
        return an dictionary where the
        keys are category names where the
        value of the entity is known, and the values
        are which entity in that category "ent" is
        connected to
        """
        truths = {}
        index = category.entities.index(ent)

        for cat2 in self.categories:
            if cat2 != category:
                if self._to_key(category, cat2) in self.grids:
                    grid = self.grids[self._to_key(category, cat2)]
                    answers = [grid[i][index] for i in range(len(grid))]

                elif self._to_key(cat2, category) in self.grids:
                    grid = self.grids[self._to_key(cat2, category)]
                    answers = grid[index]

                if "O" in answers:
                    truths[cat2.title] = cat2.entities[answers.index("O")]

        return truths

    def get_known_relations(self, category, ent):
        """
        return {
          category: {
            true: connected entity
            false: []not connected entities
            nil: []entities that are undetermined
          }
        }
        """
        relations = {}
        index = category.entities.index(ent)

        for cat2 in self.categories:
            relations[cat2] = {
                "true": None,
                "false": [],
                "nil": [],
            }
            if cat2 != category:
                if self._to_key(category, cat2) in self.grids:
                    grid = self.grids[self._to_key(category, cat2)]
                    answers = [grid[i][index] for i in range(len(grid))]

                elif self._to_key(cat2, category) in self.grids:
                    grid = self.grids[self._to_key(cat2, category)]
                    answers = grid[index]

                for i, val in enumerate(answers):
                    if val == "O":
                        relations[cat2]["true"] = cat2.entities[i]
                    elif val == "X":
                        relations[cat2]["false"].append(cat2.entities[i])
                    else:
                        relations[cat2]["nil"].append(cat2.entities[i])

        return relations

    def get_symbol(self, cat1, cat2, ent1, ent2):
        """
        return the symbol at ent1 and ent2
        """
        index1 = cat1.entities.index(ent1)
        index2 = cat2.entities.index(ent2)
        if self._to_key(cat1, cat2) in self.grids:
            grid = self.grids[self._to_key(cat1, cat2)]
            return grid[index2][index1]

        elif self._to_key(cat2, cat1) in self.grids:
            grid = self.grids[self._to_key(cat2, cat1)]
            return grid[index1][index2]

    def get_category(self, title):
        """
        get category object from title
        """
        titles = [cat.title for cat in self.categories]

        return self.categories[titles.index(title)]

    def _all_ents(self):
        """
        return a nested list
        with all categories and their
        entities
        """
        ents = []
        for cat in self.categories:
            for ent in cat.entities:
                ents.append([cat, ent])

        return ents

    def num_violations(self):
        """
        Return the number of truth violations
        in the puzzle
        """
        violations = 0
        count = 0
        for cat, ent in self._all_ents():
            truths = self.find_truths(cat, ent)
            if len(truths) > 1:
                pairs = list(itertools.combinations(truths.keys(), 2))
                count += len(pairs)
                for first, second in pairs:

                    # if these two entites are in the truth of ent
                    # then they should also be true
                    cat1 = self.get_category(first)
                    cat2 = self.get_category(second)
                    ent1 = truths[first]
                    ent2 = truths[second]

                    # The symbol should be "O" or empty ("*")
                    if self.get_symbol(cat1, cat2, ent1, ent2) == "X":
                        violations += 1

                    # make sure there is not a truth somewhere else
                    truths1 = self.find_truths(cat1, ent1)
                    if cat2.title in truths1 and truths1[cat2.title] != ent2:
                        violations += 1
                    truths2 = self.find_truths(cat2, ent2)
                    if cat1.title in truths2 and truths2[cat1.title] != ent1:
                        violations += 1
        return violations

    def _truths_valid(self):
        """
        Make sure there is not violations in
        truths of each entity

        There is absoluely a more efficent way to do this
        """
        for cat, ent in self._all_ents():
            truths = self.find_truths(cat, ent)
            if len(truths) > 1:
                pairs = itertools.combinations(truths.keys(), 2)
                for first, second in pairs:

                    # if these two entites are in the truth of ent
                    # then they should also be true
                    cat1 = self.get_category(first)
                    cat2 = self.get_category(second)
                    ent1 = truths[first]
                    ent2 = truths[second]

                    # The symbol should be "O" or empty ("*")
                    if self.get_symbol(cat1, cat2, ent1, ent2) == "X":
                        return False

                    # make sure there is not a truth somehwere else
                    truths1 = self.find_truths(cat1, ent1)
                    if cat2.title in truths1 and truths1[cat2.title] != ent2:
                        return False

                    truths2 = self.find_truths(cat2, ent2)
                    if cat1.title in truths2 and truths2[cat1.title] != ent1:
                        return False
        return True

    def is_valid(self):
        """
        return true if there there is at
        most 1 "O" for each column and row

        and if there are no truth violaitons
        """
        # make sure there is at most 1 truth
        # in each row and column
        for grid in self.grids.values():
            if not self._grid_is_valid(grid):
                return False

        # make sure truths have no violations
        return self._truths_valid()

    def is_complete(self):
        """
        return true if there is exactly 1 "O"
        in each row and column

        and there are no truth violations
        """
        if self.is_valid():
            for grid in self.grids.values():
                if not self._grid_is_complete(grid):
                    return False

            return True
        else:
            return False

    def _per_complete_grid(self, grid):
        s = 0
        v = 0  # amount of rows with exactly 1 "O"
        l = 0
        for row in grid:
            s += row.count("X") + row.count("O")
            if (row.count("O")) == 1:
                v += 1
            l += len(row)
        return s / l, v / (len(grid))

    def percent_complete(self):
        """
        return the ratio of cells that
        have an "X" or "O"
        """
        grid_sums = 0
        grid_len = 0
        valid_sums = 0
        for grid in self.grids.values():
            s, valid = self._per_complete_grid(grid)
            grid_sums += s
            valid_sums += valid
            grid_len += 1
        return grid_sums / grid_len, valid_sums / grid_len

class Puzzle:
    def __init__(self, categories, clues):
        self.grid = Grid(categories)
        self.clues = clues


# Rules people need to learn to successfully solve logic puzzles, based on our experience and
# ordered according to how difficult we estimate each insight is to learn (based on our intuition),
# with more difficult insights being numbered higher.
class Insight(Enum):
    NO_INSIGHT = 0
    CROSS_OUT = (
        1  # If there is an O in a row/column, the rest of the row/column must be X
    )
    OPENING = 2  # If a row/column has one opening and the rest are Xs, it must be O
    APPLY_IS = 3  # Apply an is clue
    APPLY_NOT = 4  # Apply a not clue
    APPLY_OR = 5  # Apply an or clue once one of the clauses has been answered.
    APPLY_BEFORE_ONE_SPOT = (
        6  # If A is answered and B is 1 after A, then answer B is one after A
    )
    APPLY_BEFORE_N_SPOTS = (
        7  # If A is answered and B is N after A, then answer B is N after A
    )
    APPLY_BEFORE_UNDEFINED_SPOTS = (
        8  # If A is answered then B must be one of the spots after A
    )
    SIMPLE_OR_SAME_CAT = (
        9  # If A or B from category 0 is C then no other entity from category 0 is C
    )
    SIMPLE_OR_DIFF_CAT = 10  # If A or B is C then A is not B
    BEFORE_DIFF_CAT = (
        11  # If A < B and A, B are not in the same category, then A is not B.
    )
    BEFORE_ONE_SPOT_NOINFO = 12  # The before entity can't be in the last spot (and vice versa for the after entity) Same for undefined spots
    BEFORE_N_SPOTS_NOINFO = 13  # The before entity can't be in the last N spots (and vice versa for the after entity)
    TRANS_ABC_TRUE = 14  # A -> B and B -> C, so A -> C
    TRANS_ABC_FALSE = 15  # A -> B and B !> C, so A !> C
    BEFORE_N_SPOTS_SHIFT = 16  # A streak of Xs at the beginning/end forces the first available position for the other entity to shift.
    BEFORE_N_SPOTS_CROSSCHECK = 17  # For a position to be a valid answer, the corresponding position +/- num must be valid for the other entity
    TRANS_SETS = 18  # A and B don't share any possibilities; A != B
    REPAIR = 100  # Repair broken puzzle

ALL_INSIGHTS = {insight for insight in Insight}


# ## Hint Grammar
#
# The clue grammar is represented as a dictionary where each key is a production rule and each value is the a nested list with the possible terms the production rule needs
#
# For example the "or" rule has two possible term sets:
# * ["cat1", "ent1", "cat1", "ent2", "cat2", "ent"]
# *  ["cat1", "ent", "cat2", "ent", "cat3", "ent"]
#
# The first term set describes two different entities from the same category, and one entity from a different category. This can be used to decribe the rule "Ms. White or Ms. Scarlet was in the study".
#
# The second term set describes three entites from different categories. This can be used to describe the rule "Ms. White or the person with the knife was in the study"

# define this grammar
# # cat is any category with no resitrictions, however cat1 and cat2 must be different
# similarly ent is any entity with in a caterogy (must have a cat immediately before), but ent1 and ent2 must be different
# num must be a numerical caterogy, alp must be an alaphetbic
# int is an integer 1-len(entities)
class Grammar:
    TERMINALS = [
        "cat",
        "ent",
        "cat1",
        "cat2",
        "cat3",
        "cat4",
        "cat5",
        "ent1",
        "ent2",
        "ent3",
        "ent4",
        "ent5",
        "num",
        "alp",
        "int",
    ]

    GRAMMAR = {
        "clue": {
            "is": [["cat1", "ent", "cat2", "ent"]],
            "not": [["is"]],
            "before": [
                ["alp", "ent1", "alp", "ent2", "num"],
                ["alp", "ent1", "alp", "ent2", "num", "int"],
            ],
            "simple_or": [
                ["cat1", "ent1", "cat1", "ent2", "cat2", "ent"],
                ["cat1", "ent", "cat2", "ent", "cat3", "ent"],
            ],
            "compound_or": [["is", "is"]],
        }
    }

    def __init__(self, categories):
        self.categories = categories

    # ## Creating Clues
    #
    # Create a clue involves two steps: generating a word from the grammar and filling in the word
    #
    # #### Generating a word
    # To generate a word, a random production rule is selected. The production rule defines terms that it needs, which will either be terminals or another production rule. If there are any production rules in the terms, the function will be called recursively (with selecting another production rule) until all remaining terms are filled in with terminals.
    #
    # #### Fill in the word
    # The first step will produce a dictionary with list of terms as values, which should all be terminals. For compound clues (ex: "or_clue"), the values are also dictionaries and this process is calledrecursively. This step replaces the terminal word (ex: "cat1") with approicate objects from the puzzle. For example if there were the terms: ["cat1", "ent", "cat2", "ent"], this step could replace it with ["rooms", "study", "suspects" ,"Ms. White"]. Note "rooms" would be the category object, not the string "rooms".


    def sub_grammar(grammar, rule):
        queue = []
        queue.append(grammar)
        while queue:
            grammar = queue.pop(0)
            if rule in list(grammar.keys()):
                return grammar[rule]
            for r in list(grammar.keys()):
                if isinstance(grammar[r], dict):
                    queue.append(grammar[r])
        return


    def generate_word(sub_grammar, grand_grammar=None):
        """
        randomly choice prodcution rules to create new clue base
        will fill out production rules until all terms are terminals
        """
        if grand_grammar is None:
            grand_grammar = sub_grammar
        rule = ""
        if isinstance(sub_grammar, dict):
            # Grammar has named rules; select one at random
            rule = random.choice(list(sub_grammar.keys()))
            if isinstance(sub_grammar[rule], dict):
                # Rule is a subgrammar with named rules itself; recurse
                return {rule: Grammar.generate_word(sub_grammar[rule], grand_grammar)}
            else:
                # Rule is a list of alternates
                sub_grammar = sub_grammar[rule]
        # Grammar is a list of alternates; select one at random
        production = random.choice(sub_grammar)
        terms = []
        for word in production:
            if word in Grammar.TERMINALS:
                terms.append(word)
            else:
                terms.append({
                    word: Grammar.generate_word(
                        Grammar.sub_grammar(grand_grammar, word), grand_grammar
                    )
                })
        if rule != "":
            return {rule: terms}
        else:
            return terms


    def shuffled_cat_list(self):
        """
        shuffle categories and entities within categories and return as a nested list
        ex: [[cat1, [ent1.1, ent1.2, ent1.2]], [cat2, [ent2.1, ent2.2, ent2.3]]]
        """
        li = self.categories[:]
        random.shuffle(li)
        cats = []
        for cat in li:
            shuf_ents = cat.entities[:]
            random.shuffle(shuf_ents)
            cats.append([cat, shuf_ents])
        return cats


    def get_alps(self):
        """
        return all alphabetic categories
        """
        return [cat for cat in self.categories if not cat[0].is_numeric]


    def get_num(self):
        """
        return all numeric categories
        """
        return [cat for cat in self.categories if cat[0].is_numeric]


    def fill_in_word(self, word):
        """
        Replace all terminal terms with random and appropriate
        categories, entities, or integers from a puzzle
        """
        filled_word = {}
        for key in word:
            value = word[key]
            if isinstance(value, dict):
                filled_word[key] = self.fill_in_word(word[key])
            else:
                new_terms = []
                cats = self.shuffled_cat_list()
                alps = self.get_alps()
                nums = self.get_num()
                last_cat = None

                for term in value:
                    if isinstance(term, dict):
                        new_terms.append(self.fill_in_word(term))
                    else:
                        if term == "cat":
                            last_cat = random.choice(cats)
                            new_terms.append(last_cat[0])
                        elif term == "cat1":
                            if len(cats) < 1:
                                raise Exception("CAT_COUNT")
                            else:
                                last_cat = cats[0]
                                new_terms.append(last_cat[0])
                        elif term == "cat2":
                            if len(cats) < 2:
                                raise Exception("CAT_COUNT")
                            else:
                                last_cat = cats[1]
                                new_terms.append(last_cat[0])
                        elif term == "cat3":
                            if len(cats) < 3:
                                raise Exception("CAT_COUNT")
                            else:
                                last_cat = cats[2]
                                new_terms.append(last_cat[0])
                        elif term == "alp":
                            if len(alps) == 0:
                                raise Exception("ALPH_COUNT")
                            else:
                                last_cat = random.choice(alps)
                                new_terms.append(last_cat[0])
                        elif term == "num":
                            if len(nums) == 0:
                                raise Exception("NUM_COUNT")
                            else:
                                last_cat = random.choice(nums)
                                new_terms.append(last_cat[0])
                        elif term == "ent":
                            new_terms.append(random.choice(last_cat[1]))
                        elif term == "ent1":
                            if len(last_cat[1]) < 1:
                                raise Exception("ENT_COUNT")
                            else:
                                new_terms.append(last_cat[1][0])
                        elif term == "ent2":
                            if len(last_cat[1]) < 2:
                                raise Exception("ENT_COUNT")
                            else:
                                new_terms.append(last_cat[1][1])
                        elif term == "ent3":
                            if len(last_cat[1]) < 3:
                                raise Exception("ENT_COUNT")
                            else:
                                new_terms.append(last_cat[1][2])
                        elif term == "int":
                            new_terms.append(
                                random.randrange(1, len(last_cat[1]) - 1)
                            )  # 2 spaces to make decision
                filled_word[key] = new_terms
        return filled_word


    def generate_clue(self):
        """
        given a puzzle generate a random, valid clue
        """
        word = Grammar.generate_word(Grammar.GRAMMAR)
        try:
            return self.fill_in_word(word)["clue"]
        except:
            return self.generate_clue()


    def str_clue(clue, str_so_far=""):
        if isinstance(clue, dict):
            rule = list(clue.keys())[0]
            str_so_far += rule + ": "
            return Grammar.str_clue(clue[rule], str_so_far)
        elif isinstance(clue, list):
            str_so_far += "[ "
            for i, term in enumerate(clue):
                str_so_far += Grammar.str_clue(term)
                if i != len(clue) - 1:
                    str_so_far += ", "
            str_so_far += " ]"
        else:
            str_so_far += str(clue)
        return str_so_far


    def str_clue(clue, str_so_far=""):
        if isinstance(clue, dict):
            rule = list(clue.keys())[0]
            str_so_far += rule + ": "
            return Grammar.str_clue(clue[rule], str_so_far)
        elif isinstance(clue, list):
            str_so_far += "[ "
            for i, term in enumerate(clue):
                str_so_far += Grammar.str_clue(term)
                if i != len(clue) - 1:
                    str_so_far += ", "
            str_so_far += " ]"
        else:
            str_so_far += str(clue)
        return str_so_far

# ## Using clues to solve puzzles
# Giving a list of clues you can solve the puzzle (as much as the information in the clues will allow). This can be done by iteratively applying indivual clues untill they are all completed (ex: the "not" rule is completed after putting an "X" on the board, but the "before" rule may still have information after placing a symbol) or the rules stopping changing the game state (ex: the "or" rule cannot change the same state if it doesn't know which rule is correct). Hint can also be invalid, which will terminate the process (ex: if there is a "not" rule over a spot that another clue already placed an "O).
#
#
# ```
# queue = all clues
#
# while game changed and is valid:
#   for clue in queue:
#     apply clue to game state
#     if clue or game state is invalid --> exit
#     if clue is complete clue remove from queue
#
#   if no clues changed gamestate --> exit
#
# ```
#
class Solver:
    def __init__(self):
        return

    def cross_out(puzzle, cat1, cat2, ent1, ent2):
        """
        places Xs in the all the rows and columns
        after you found a correct clue
        """
        is_valid = True
        applied = False

        steps = []
        update_puzzle = deepcopy(puzzle)

        # x out the cross sections
        for ent in cat1.entities:
            if ent != ent1:
                symb = puzzle.get_symbol(cat1, cat2, ent, ent2)
                if symb != "X":
                    move_applied, move_diff = update_puzzle.answer(
                        cat1, cat2, ent, ent2, "X"
                    )
                    if move_applied:
                        steps.append({
                            "result": update_puzzle,
                            "move_diff": move_diff,
                            "insights": {Insight.CROSS_OUT},
                            "repair": False,
                        })
                    applied = applied or move_applied
                    if symb == "O":
                        is_valid = False
                        move_applied, move_steps = uncross_repair(
                            update_puzzle, cat1, cat2, ent1, ent2
                        )
                        applied = applied or move_applied
                        if move_applied:
                            steps.extend(move_steps)
                        move_applied, move_steps = uncross_repair(
                            update_puzzle, cat1, cat2, ent, ent2
                        )
                        applied = applied or move_applied
                        if move_applied:
                            steps.extend(move_steps)

        for ent in cat2.entities:
            if ent != ent2:
                symb = puzzle.get_symbol(cat1, cat2, ent1, ent)
                if symb != "X":
                    move_applied, move_diff = update_puzzle.answer(
                        cat1, cat2, ent1, ent, "X"
                    )
                    if move_applied:
                        steps.append({
                            "result": update_puzzle,
                            "move_diff": move_diff,
                            "insights": {Insight.CROSS_OUT},
                            "repair": False,
                        })
                    applied = applied or move_applied
                    if symb == "O":
                        is_valid = False
                        move_applied, move_steps = uncross_repair(
                            update_puzzle, cat1, cat2, ent1, ent2
                        )
                        applied = applied or move_applied
                        if move_applied:
                            steps.extend(move_steps)
                        move_applied, move_steps = uncross_repair(
                            update_puzzle, cat1, cat2, ent1, ent
                        )
                        applied = applied or move_applied
                        if move_applied:
                            steps.extend(move_steps)

        puzzle.grids = update_puzzle.grids
        return applied, is_valid, steps


    def uncross_repair(puzzle, cat1, cat2, ent1, ent2):
        steps = []
        update_puzzle = deepcopy(puzzle)
        applied = False

        # x out the cross sections
        for ent in cat1.entities:
            symb = puzzle.get_symbol(cat1, cat2, ent, ent2)
            if symb != "*":
                move_applied, move_diff = update_puzzle.answer(cat1, cat2, ent, ent2, "*")
                applied = applied or move_applied
                if move_applied:
                    steps.append({
                        "result": update_puzzle,
                        "move_diff": move_diff,
                        "insights": {Insight.CROSS_OUT},
                        "repair": True,
                    })

        for ent in cat2.entities:
            symb = puzzle.get_symbol(cat1, cat2, ent1, ent)
            if symb != "*":
                move_applied, move_diff = update_puzzle.answer(cat1, cat2, ent1, ent, "*")
                applied = applied or move_applied
                if move_applied:
                    steps.append({
                        "result": update_puzzle,
                        "move_diff": move_diff,
                        "insights": {Insight.CROSS_OUT},
                        "repair": True,
                    })

        puzzle.grids = update_puzzle.grids
        return applied, steps


    # remove errors (discrepancies between the current puzzle and the canonical solution)
    def repair(puzzle, solution, apply=True):
        applied = False
        for cat1 in puzzle.left_right:
            for cat2 in puzzle.top_bottom:
                curr_grid = puzzle.get_grid(cat1, cat2)
                soln_grid = solution.get_grid(cat1, cat2)
                if curr_grid is None or soln_grid is None:
                    continue
                for ent2_idx in range(0, len(curr_grid)):
                    for ent1_idx in range(0, len(curr_grid[ent2_idx])):
                        if (
                            curr_grid[ent2_idx][ent1_idx] not in ["*", "Y", "N", "_"]
                            and curr_grid[ent2_idx][ent1_idx]
                            is not soln_grid[ent2_idx][ent1_idx]
                        ):
                            # The puzzle value does not match the canonical solution; unset subgrid and mark repair as applied
                            applied = True
                            if apply:
                                for ent1 in cat1.entities:
                                    for ent2 in cat2.entities:
                                        puzzle.answer(cat1, cat2, ent1, ent2, "*")
        return applied


    def apply_is(puzzle, terms, forbidden_insights=set()):
        """
        Apply the is rule to puzzle, will always complete in one step
        puzzle: the current state of the grid
        terms: the terms making up the is clue's grammar
        return: applied, is_valid, complete
        """
        applied = False
        is_valid = True
        complete = False
        insights = set()
        cat1 = terms[0]
        ent1 = terms[1]
        cat2 = terms[2]
        ent2 = terms[3]

        current_term = puzzle.get_symbol(cat1, cat2, ent1, ent2)

        steps = []
        update_puzzle = deepcopy(puzzle)

        if current_term != "O" and Insight.APPLY_IS not in forbidden_insights:
            complete = True
            move_applied, move_diff = update_puzzle.answer(cat1, cat2, ent1, ent2, "O")
            applied = applied or move_applied
            if move_applied:
                steps.append({
                    "result": update_puzzle,
                    "move_diff": move_diff,
                    "insights": {Insight.APPLY_IS},
                    "repair": False,
                })
                insights.add(Insight.APPLY_IS)
                c_applied, is_valid, cross_steps = cross_out(
                    update_puzzle, cat1, cat2, ent1, ent2
                )
                applied = applied or c_applied
                if c_applied:
                    for step in cross_steps:
                        step["insights"].add(Insight.APPLY_IS)
            steps.extend(cross_steps)

        if current_term == "X":
            # something logic error occured
            is_valid = False
            complete = True
            move_applied, move_diff = update_puzzle.answer(cat1, cat2, ent1, ent2, "O")
            if move_applied:
                steps.append({
                    "result": update_puzzle,
                    "move_diff": move_diff,
                    "insights": {Insight.APPLY_IS},
                    "repair": True,
                })
                applied = applied or move_applied
                cross_applied, is_valid, cross_steps = cross_out(
                    update_puzzle, cat1, cat2, ent1, ent2
                )
                if cross_applied:
                    for step in cross_steps:
                        step["insights"].add(Insight.APPLY_IS)
                        step["repair"] = True
            applied = applied or cross_applied

        elif current_term == "O":
            # someone already answered
            complete = True

        puzzle.grids = update_puzzle.grids
        return applied, is_valid, complete, insights, steps




    def apply_not(puzzle, terms, forbidden_insights=set()):
        """
        Apply the not rule to puzzle, will always complete in one step
        puzzle: the current state of the grid
        terms: the terms making up the is clue's grammar
        return: applied, is_valid, complete
        """
        applied = False
        is_valid = True
        complete = False
        insights = set()
        cat1 = terms[0]
        ent1 = terms[1]
        cat2 = terms[2]
        ent2 = terms[3]

        current_term = puzzle.get_symbol(cat1, cat2, ent1, ent2)
        steps = []
        update_puzzle = deepcopy(puzzle)

        if current_term != "X" and Insight.APPLY_NOT not in forbidden_insights:
            move_applied, move_diff = update_puzzle.answer(cat1, cat2, ent1, ent2, "X")
            if move_applied:
                steps.append({
                    "result": update_puzzle,
                    "move_diff": move_diff,
                    "insights": {Insight.APPLY_NOT},
                    "repair": False,
                })
                applied = applied or move_applied
                complete = True
                insights.add(Insight.APPLY_NOT)
                opening_puzzle = deepcopy(update_puzzle)
                o_applied, _, _, _, opening_steps = find_openings(opening_puzzle, forbidden_insights)
                if o_applied:
                    for o_step in opening_steps:
                        if "O" in o_step["move_diff"].print_grid():
                            o_step["insights"].add(Insight.APPLY_NOT)
                            steps.append(o_step)
        if current_term == "O":
            move_applied, move_steps = uncross_repair(update_puzzle, cat1, cat2, ent1, ent2)
            applied = applied or move_applied
            if move_applied:
                for step in move_steps:
                    step["insights"].add(Insight.APPLY_NOT)
                    steps.append(step)
            move_applied, move_diff = update_puzzle.answer(cat1, cat2, ent1, ent2, "X")
            applied = applied or move_applied
            if move_applied:
                steps.append({
                    "result": update_puzzle,
                    "move_diff": move_diff,
                    "insights": {Insight.APPLY_NOT},
                    "repair": True,
                })
            applied = applied or move_applied
            is_valid = False
            complete = True
        elif current_term == "X":
            complete = True

        puzzle.grids = update_puzzle.grids
        return applied, is_valid, complete, insights, steps




    def rowcol_repair(puzzle, cat1, cat2, ent):
        update_puzzle = deepcopy(puzzle)
        steps = []
        applied = False

        if ent not in cat1.entities:
            # Swap cat1 and cat2
            c = cat1
            cat1 = cat2
            cat2 = c

        for e in cat2.entities:
            symb = puzzle.get_symbol(cat1, cat2, ent, e)
            if symb != "*":
                move_applied, move_diff = update_puzzle.answer(cat1, cat2, ent, e, "*")
                applied = applied or move_applied
                if move_applied:
                    steps.append({
                        "result": update_puzzle,
                        "move_diff": move_diff,
                        "insights": {Insight.CROSS_OUT},
                        "repair": True,
                    })

        puzzle.grids = update_puzzle.grids
        return applied, steps


    # If a row/column has 1 O then fill the rest with X.
    # If a row/column has 1 * and the rest are X then fill out a O there.
    # If a row/column is all X or has more than one O then contradiction.
    # In "slow" mode, take care to only apply current openings, skipping any openings that may be found after filling in some of the openings.
    def find_openings(puzzle, forbidden_insights=set()):
        applied = False
        complete = False
        is_valid = True
        insights = set()
        # The puzzle to update. Update in place in normal mode; in slow mode update a copy.
        steps = []
        update_puzzle = deepcopy(puzzle)

        # For every combination of categories:
        for cat1 in puzzle.categories:
            for cat2 in puzzle.categories:
                grid = puzzle.get_grid(cat1, cat2)
                if grid != None:
                    # For each row:
                    for i, row in enumerate(grid):
                        blanks = [i for i in range(len(row)) if row[i] in ["*", "Y", "N"]]
                        os = [i for i in range(len(row)) if row[i] == "O"]
                        if len(blanks) == 0 and len(os) == 0:
                            # The row is all Xs; contradiction
                            is_valid = False
                            move_applied, move_steps = rowcol_repair(
                                update_puzzle, cat1, cat2, cat2.entities[i]
                            )
                            applied = applied or move_applied
                            if move_applied:
                                steps.extend(move_steps)
                        elif len(os) > 1:
                            # There are multiple Os; this is a contradiction
                            is_valid = False
                            applied = False
                        elif (
                            len(os) == 1
                            and len(blanks) >= 1
                            and Insight.CROSS_OUT not in forbidden_insights
                        ):
                            # There is an O; the rest of the row and column can be crossed out.
                            ent1 = cat1.entities[os[0]]
                            ent2 = cat2.entities[i]
                            insights.add(Insight.CROSS_OUT)
                            capplied, cis_valid, cross_steps = cross_out(
                                update_puzzle, cat1, cat2, ent1, ent2
                            )
                            is_valid = is_valid and cis_valid
                            applied = applied or capplied
                            if capplied:
                                steps.extend(cross_steps)
                        # If there is only 1 blank value:
                        elif len(blanks) == 1 and Insight.OPENING not in forbidden_insights:
                            ent1 = cat1.entities[blanks[0]]
                            ent2 = cat2.entities[i]
                            # Answer it as 0.
                            insights.add(Insight.OPENING)
                            move_applied, move_diff = update_puzzle.answer(
                                cat1, cat2, ent1, ent2, "O"
                            )
                            applied = applied or move_applied
                            if move_applied:
                                steps.append({
                                    "result": update_puzzle,
                                    "move_diff": move_diff,
                                    "insights": {Insight.OPENING},
                                    "repair": False,
                                })
                                x_applied, cis_valid, cross_steps = cross_out(
                                    update_puzzle, cat1, cat2, ent1, ent2
                                )
                                applied = applied or x_applied
                                is_valid = is_valid and cis_valid
                                if x_applied:
                                    for step in cross_steps:
                                        step["insights"].add(Insight.OPENING)
                                steps.extend(cross_steps)

                    # For each column:
                    for j in range(len(grid[0])):
                        blanks = [
                            i for i in range(len(grid)) if grid[i][j] in ["*", "Y", "N"]
                        ]
                        os = [i for i in range(len(grid)) if grid[i][j] == "O"]
                        if len(blanks) == 0 and len(os) == 0:
                            # The row is all Xs; contradiction
                            is_valid = False
                            move_applied, move_steps = rowcol_repair(
                                update_puzzle, cat1, cat2, cat1.entities[j]
                            )
                            applied = applied or move_applied
                            if move_applied:
                                steps.extend(move_steps)
                        elif len(os) > 1:
                            # There are multiple Os; this is a contradiction
                            is_valid = False
                            applied = False
                        elif (
                            len(os) == 1
                            and len(blanks) >= 1
                            and Insight.CROSS_OUT not in forbidden_insights
                        ):
                            # There is an O; the rest of the row and column can be crossed out.
                            ent1 = cat1.entities[j]
                            ent2 = cat2.entities[os[0]]

                            insights.add(Insight.CROSS_OUT)
                            capplied, cis_valid, cross_steps = cross_out(
                                update_puzzle, cat1, cat2, ent1, ent2
                            )
                            is_valid = is_valid and cis_valid
                            applied = applied or capplied
                            if capplied:
                                steps.extend(cross_steps)
                        # If there is only one blank value:
                        elif len(blanks) == 1 and Insight.OPENING not in forbidden_insights:
                            ent1 = cat1.entities[j]
                            ent2 = cat2.entities[blanks[0]]
                            insights.add(Insight.OPENING)
                            # Answer it as 0.
                            move_applied, move_diff = update_puzzle.answer(
                                cat1, cat2, ent1, ent2, "O"
                            )
                            applied = applied or move_applied
                            if move_applied:
                                steps.append({
                                    "result": update_puzzle,
                                    "move_diff": move_diff,
                                    "insights": {Insight.OPENING},
                                    "repair": False,
                                })
                                x_applied, cis_valid, cross_steps = cross_out(
                                    update_puzzle, cat1, cat2, ent1, ent2
                                )
                                applied = applied or x_applied
                                is_valid = is_valid and cis_valid
                                if x_applied:
                                    for step in cross_steps:
                                        step["insights"].add(Insight.OPENING)
                                steps.extend(cross_steps)

        # Apply updates.
        puzzle.grids = update_puzzle.grids
        return applied, is_valid, complete, insights, steps



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
                            )


    # If A is B and B is C then A is C
    # If A is B and B is not C then A is not C
    # ...
    def find_transitives(puzzle, forbidden_insights=set(), slow=False):
        """
        slow: set to True to apply only the first valid insight.
        """
        applied = False
        complete = False
        is_valid = True
        insights = set()

        steps = []
        update_puzzle = deepcopy(puzzle)

        # For every pair of related entities:
        #   If A == B and B == C then A == C
        #   If A == B and B != C then A != C
        for catA in puzzle.categories:
            for entA in catA.entities:
                # All known relations for A
                entA_relations = puzzle.get_known_relations(catA, entA)

                # For each category for which A has relations
                for catB, catB_relations in entA_relations.items():

                    # For A's truth value in catB, A and B share all relations
                    entB = catB_relations["true"]
                    if entB == None:
                        continue

                    # A is related to B, so A and B share relations for all other categories
                    # Get all realations for B
                    entB_relations = puzzle.get_known_relations(catB, entB)

                    # Relate A to B's truth and false values.
                    for catC, catC_relations in entB_relations.items():
                        if catC == catA:
                            continue
                        entC = catC_relations["true"]
                        if entC == None:
                            continue
                        # A -> B and B -> C, so A -> C
                        sy = puzzle.get_symbol(catA, catC, entA, entC)
                        if sy != "O" and Insight.TRANS_ABC_TRUE not in forbidden_insights:
                            insights.add(Insight.TRANS_ABC_TRUE)
                            move_applied, move_diff = update_puzzle.answer(
                                catA, catC, entA, entC, "O"
                            )
                            applied = applied or move_applied
                            if move_applied:
                                steps.append({
                                    "result": update_puzzle,
                                    "move_diff": move_diff,
                                    "insights": {Insight.TRANS_ABC_TRUE},
                                    "repair": False,
                                })
                                x_applied, cis_valid, cross_steps = cross_out(
                                    update_puzzle, catA, catC, entA, entC
                                )
                                applied = applied or x_applied
                                is_valid = is_valid and cis_valid
                                if x_applied:
                                    for step in cross_steps:
                                        step["insights"].add(Insight.TRANS_ABC_TRUE)
                                    steps.extend(cross_steps)
                            if slow:
                                puzzle.grids = update_puzzle.grids
                                return applied, is_valid, complete, insights, steps
                        if sy == "X":
                            # Can't link A to C
                            is_valid = False
                            move_applied, move_steps = uncross_repair(
                                puzzle, catA, catC, entA, entC
                            )
                            applied = applied or move_applied
                            if move_applied:
                                for step in move_steps:
                                    step["insights"].add(Insight.TRANS_ABC_TRUE)
                                steps.extend(move_steps)
                        # For all false values for B in category C
                        for entC in catC_relations["false"]:
                            if entC == None:
                                continue
                            # A -> B and B !> C, so A !> C
                            sy = puzzle.get_symbol(catA, catC, entA, entC)
                            if (
                                sy != "X"
                                and Insight.TRANS_ABC_FALSE not in forbidden_insights
                            ):
                                move_applied, move_diff = update_puzzle.answer(
                                    catA, catC, entA, entC, "X"
                                )
                                applied = applied or move_applied

                                if move_applied:
                                    insights.add(Insight.TRANS_ABC_FALSE)
                                    t_step = {
                                        "result": update_puzzle,
                                        "move_diff": move_diff,
                                        "insights": {Insight.TRANS_ABC_FALSE},
                                        "repair": False,
                                    }
                                    steps.append(t_step)
                                    opening_puzzle = deepcopy(puzzle)
                                    apply_move(opening_puzzle, t_step)
                                    o_applied, _, _, _, opening_steps = find_openings(
                                        opening_puzzle, forbidden_insights
                                    )
                                    if o_applied:
                                        for o_step in opening_steps:
                                            if "O" in o_step["move_diff"].print_grid():
                                                o_step["insights"].add(Insight.TRANS_ABC_FALSE)
                                                steps.append(o_step)
                                if slow:
                                    puzzle.grids = update_puzzle.grids
                                    return applied, is_valid, complete, insights, steps
                            if sy == "O":
                                # Can't reject A to C
                                is_valid = False
                                move_applied, move_steps = uncross_repair(
                                    puzzle, catA, catC, entA, entC
                                )
                                applied = applied or move_applied
                                if move_applied:
                                    for step in move_steps:
                                        step["insights"].add(Insight.TRANS_ABC_FALSE)
                                    steps.extend(move_steps)
        # For every pair of entities:
        #   If A and B don't share any possible values for category C, then A != B
        # This loop is separate to enforce that harder insights are only used when the easier insights have been exhausted.
        for catA in puzzle.categories:
            for entA in catA.entities:
                # All known relations for A
                entA_relations = puzzle.get_known_relations(catA, entA)

                # For each category for which A has relations
                for catB, catB_relations in entA_relations.items():
                    if catA == catB:
                        continue
                    # for A's indeterminate values in category B, if A and B can't be related in some category, then A != B
                    for entB in catB_relations["nil"]:
                        # All relations for B
                        entB_relations = puzzle.get_known_relations(catB, entB)
                        for catC, catCA_relations in entA_relations.items():
                            if catC not in [catA, catB]:
                                # catCA_relations are A's relations for category C.
                                # catCB_relations are B's relations for category C.
                                catCB_relations = entB_relations[catC]

                                A_possibles = catCA_relations["nil"].copy()
                                B_possibles = catCB_relations["nil"].copy()

                                entCA = catCA_relations["true"]
                                entCB = catCB_relations["true"]
                                if entCA != None:
                                    A_possibles.append(entCA)
                                if entCB != None:
                                    B_possibles.append(entCB)

                                # Now possibles include all positive or nil values for category C
                                # If A and B don't share any entities in their possible lists, then A != B
                                setA = set(A_possibles)
                                setB = set(B_possibles)
                                if (
                                    not (setA & setB)
                                    and Insight.TRANS_SETS not in forbidden_insights
                                ):
                                    # A and B don't share any possibilities; A != B
                                    sy = puzzle.get_symbol(catA, catB, entA, entB)
                                    if sy == "O":
                                        is_valid = False
                                        move_applied, move_steps = uncross_repair(
                                            puzzle, catA, catB, entA, entB
                                        )
                                        applied = applied or move_applied
                                        if move_applied:
                                            for step in move_steps:
                                                step["insights"].add(Insight.TRANS_SETS)
                                            steps.extend(move_steps)
                                    elif sy != "X":
                                        move_applied, move_diff = update_puzzle.answer(
                                            catA, catB, entA, entB, "X"
                                        )
                                        applied = applied or move_applied
                                        if move_applied:
                                            insights.add(Insight.TRANS_SETS)
                                            t_step = {
                                                "result": update_puzzle,
                                                "move_diff": move_diff,
                                                "insights": {Insight.TRANS_SETS},
                                                "repair": False,
                                            }
                                            steps.append(t_step)
                                            opening_puzzle = deepcopy(puzzle)
                                            apply_move(opening_puzzle, t_step)
                                            o_applied, _, _, _, opening_steps = find_openings(
                                                opening_puzzle, forbidden_insights
                                            )
                                            if o_applied:
                                                for o_step in opening_steps:
                                                    if "O" in o_step["move_diff"].print_grid():
                                                        o_step["insights"].add(Insight.TRANS_SETS)
                                                        steps.append(o_step)
                                        if slow:
                                            puzzle.grids = update_puzzle.grids
                                            return (
                                                applied,
                                                is_valid,
                                                complete,
                                                insights,
                                                steps,
                                            )

        puzzle.grids = update_puzzle.grids
        return applied, is_valid, complete, insights, steps




    def apply_before(puzzle, terms, forbidden_insights=set(), slow=False, allow_uncertain_moves=True):
        """
        apply the before rule to the puzzle
        puzzle: the current state of the grid
        terms: the terms making up the is clue's grammar
        slow: set to True to apply only the first insight
        return_steps: return each mark/insight as a separate move
        return: applied, is_valid, complete
        """
        applied = False
        complete = False
        is_valid = True
        insights = set()
        numbered = len(terms) == 6

        bef_cat = terms[0]
        bef_ent = terms[1]  # bef entity is before aft_ent
        aft_cat = terms[2]
        aft_ent = terms[3]

        num_cat = terms[4]

        num = 1
        if numbered:
            num = terms[5]

        update_puzzle = puzzle
        steps = []
        update_puzzle = deepcopy(puzzle)

        # If A < B and A, B are not in the same category, then A is not B.
        if bef_cat != aft_cat:
            sy = puzzle.get_symbol(bef_cat, aft_cat, bef_ent, aft_ent)
            if sy != "X" and Insight.BEFORE_DIFF_CAT not in forbidden_insights:
                move_applied, move_diff = update_puzzle.answer(
                    bef_cat, aft_cat, bef_ent, aft_ent, "X"
                )
                applied = applied or move_applied
                if move_applied:
                    insights.add(Insight.BEFORE_DIFF_CAT)
                    b_step = {
                        "result": update_puzzle,
                        "move_diff": move_diff,
                        "insights": {Insight.BEFORE_DIFF_CAT},
                        "repair": False,
                    }
                    steps.append(b_step)
                    opening_puzzle = deepcopy(puzzle)
                    apply_move(opening_puzzle, b_step)
                    o_applied, _, _, _, opening_steps = find_openings(
                        opening_puzzle, forbidden_insights
                    )
                    if o_applied:
                        for o_step in opening_steps:
                            if "O" in o_step["move_diff"].print_grid():
                                o_step["insights"].add(Insight.BEFORE_DIFF_CAT)
                                steps.append(o_step)
                if slow:
                    puzzle.grids = update_puzzle.grids
                    return applied, is_valid, complete, insights, steps
            if sy == "O":
                # Contradiction
                complete = True
                is_valid = False
                move_applied, move_steps = uncross_repair(
                    update_puzzle, bef_cat, aft_cat, bef_ent, aft_ent
                )
                applied = applied or move_applied
                if move_applied:
                    for step in move_steps:
                        step["insights"].add(Insight.BEFORE_DIFF_CAT)
                    steps.extend(move_steps)

        # Get all the current symbols for the two entities in the num category
        before_symbols = [
            puzzle.get_symbol(bef_cat, num_cat, bef_ent, ent) for ent in num_cat.entities
        ]
        after_symbols = [
            puzzle.get_symbol(aft_cat, num_cat, aft_ent, ent) for ent in num_cat.entities
        ]

        # if both entities have answer, we can determine if this rule is valid
        if "O" in before_symbols and "O" in after_symbols:
            complete = True
            is_valid = is_valid and before_symbols.index("O") < after_symbols.index("O")
            if numbered:
                is_valid = (
                    is_valid and after_symbols.index("O") - before_symbols.index("O") == num
                )
            if not is_valid:
                repair_steps = []
                for ent in num_cat.entities:
                    symb = puzzle.get_symbol(bef_cat, num_cat, bef_ent, ent)
                    if symb == "O":
                        move_applied, move_steps = uncross_repair(
                            update_puzzle, bef_cat, num_cat, bef_ent, ent
                        )
                        applied = applied or move_applied
                        if move_applied:
                            steps.extend(move_steps)
                    symb = puzzle.get_symbol(aft_cat, num_cat, aft_ent, ent)
                    if symb == "O":
                        move_applied, move_steps = uncross_repair(
                            update_puzzle, aft_cat, num_cat, aft_ent, ent
                        )
                        applied = applied or move_applied
                        if move_applied:
                            steps.extend(move_steps)

                for step in repair_steps:
                    insight = Insight.APPLY_BEFORE_UNDEFINED_SPOTS
                    if numbered:
                        insight = Insight.APPLY_BEFORE_N_SPOTS
                        if num == 1:
                            insight = Insight.APPLY_BEFORE_ONE_SPOT
                    step["insights"].add(insight)
                steps.extend(repair_steps)

        before_puzzle = deepcopy(puzzle)
        after_puzzle = deepcopy(puzzle)
        # determine the possible after entities if the before entity is solved
        if "O" in before_symbols:
            needed_insight = None
            bef_index = before_symbols.index("O")
            pos_aft_index = [
                i
                for i in list(range(bef_index + 1, len(after_symbols)))
                if after_symbols[i] != "X"
            ]
            if len(pos_aft_index) == 1:
                needed_insight = Insight.APPLY_BEFORE_UNDEFINED_SPOTS
            if numbered:
                if (
                    bef_index + num < len(after_symbols)
                    and after_symbols[bef_index + num] != "X"
                ):
                    pos_aft_index = [bef_index + num]
                    if needed_insight == None:
                        if num == 1:
                            needed_insight = Insight.APPLY_BEFORE_ONE_SPOT
                        else:
                            needed_insight = Insight.APPLY_BEFORE_N_SPOTS
                else:
                    pos_aft_index = []
            if len(pos_aft_index) == 0:
                needed_insight = Insight.APPLY_BEFORE_UNDEFINED_SPOTS
                complete = True
                is_valid = False
                repair_steps = []
                for ent in num_cat.entities:
                    symb = puzzle.get_symbol(bef_cat, num_cat, bef_ent, ent)
                    if symb == "O":
                        move_applied, move_steps = uncross_repair(
                            update_puzzle, bef_cat, num_cat, bef_ent, ent
                        )
                        applied = applied or move_applied
                        if move_applied:
                            repair_steps.extend(move_steps)
                for step in repair_steps:
                    step["insights"].add(needed_insight)
                steps.extend(repair_steps)
            elif len(pos_aft_index) == 1:
                if needed_insight not in forbidden_insights:
                    insights.add(needed_insight)
                    complete = True
                    aft_index = pos_aft_index[0]
                    move_applied, move_diff = update_puzzle.answer(
                        aft_cat, num_cat, aft_ent, num_cat.entities[aft_index], "O"
                    )
                    applied = applied or move_applied
                    if move_applied:
                        steps.append({
                            "result": update_puzzle,
                            "move_diff": move_diff,
                            "insights": {needed_insight},
                            "repair": False,
                        })
                    move_applied, cis_valid, cross_steps = cross_out(
                        update_puzzle,
                        aft_cat,
                        num_cat,
                        aft_ent,
                        num_cat.entities[aft_index],
                    )
                    applied = applied or move_applied
                    is_valid = is_valid and cis_valid
                    if move_applied:
                        for step in cross_steps:
                            step["insights"].add(needed_insight)
                        steps.extend(cross_steps)
                    if slow:
                        puzzle.grids = update_puzzle.grids
                        return applied, is_valid, complete, insights, steps
            else:
                b_steps = []
                for i in range(0, bef_index + 1):
                    sy = puzzle.get_symbol(aft_cat, num_cat, aft_ent, num_cat.entities[i])
                    if sy != "X":
                        move_applied, move_diff = update_puzzle.answer(
                            aft_cat, num_cat, aft_ent, num_cat.entities[i], "X"
                        )
                        applied = applied or move_applied
                        if move_applied:
                            insights.add(Insight.APPLY_BEFORE_UNDEFINED_SPOTS)
                            b_steps.append({
                                "result": update_puzzle,
                                "move_diff": move_diff,
                                "insights": {Insight.APPLY_BEFORE_UNDEFINED_SPOTS},
                                "repair": False,
                            })
                    if sy == "O":
                        complete = True
                        is_valid = False
                        move_applied, move_steps = uncross_repair(
                            puzzle, aft_cat, num_cat, aft_ent, num_cat.entities[i]
                        )
                        applied = applied or move_applied
                        if move_applied:
                            for step in move_steps:
                                step["insights"].add(Insight.APPLY_BEFORE_UNDEFINED_SPOTS)
                            steps.extend(move_steps)
                if len(b_steps) > 0:
                    steps.extend(b_steps)
                    for b_step in b_steps:
                        apply_move(after_puzzle, b_step)
                    _, _, _, _, opening_steps = find_openings(
                        after_puzzle, forbidden_insights
                    )
                    for o_step in opening_steps:
                        if "O" in o_step["move_diff"].print_grid():
                            o_step["insights"].add(Insight.APPLY_BEFORE_UNDEFINED_SPOTS)
                            steps.append(o_step)
                for i in pos_aft_index and allow_uncertain_moves:
                    # Make an uncertain mark for possible answers.
                    sy = puzzle.get_symbol(aft_cat, num_cat, aft_ent, num_cat.entities[i])
                    if sy == "*":
                        move_applied, move_diff = update_puzzle.answer(
                            aft_cat, num_cat, aft_ent, num_cat.entities[i], "Y"
                        )
                        applied = applied or move_applied
                        if move_applied:
                            insights.add(Insight.APPLY_BEFORE_UNDEFINED_SPOTS)
                            steps.append({
                                "result": update_puzzle,
                                "move_diff": move_diff,
                                "insights": {Insight.APPLY_BEFORE_UNDEFINED_SPOTS},
                                "repair": False,
                            })
                if applied and slow:
                    return applied, is_valid, complete, insights, steps

        # determine the possible before entities if the after entity is solved
        if "O" in after_symbols:
            needed_insight = None
            aft_index = after_symbols.index("O")
            pos_bef_index = [
                i for i in list(range(0, aft_index)) if before_symbols[i] != "X"
            ]
            if len(pos_bef_index) == 1:
                needed_insight = Insight.APPLY_BEFORE_UNDEFINED_SPOTS
            if numbered:
                if aft_index - num >= 0 and before_symbols[aft_index - num] != "X":
                    pos_bef_index = [aft_index - num]
                    if needed_insight == None:
                        if num == 1:
                            needed_insight = Insight.APPLY_BEFORE_ONE_SPOT
                        else:
                            needed_insight = Insight.APPLY_BEFORE_N_SPOTS
                else:
                    pos_bef_index = []

            if len(pos_bef_index) == 0:
                needed_insight = Insight.APPLY_BEFORE_UNDEFINED_SPOTS
                complete = True
                is_valid = False
                repair_steps = []
                for ent in num_cat.entities:
                    symb = puzzle.get_symbol(aft_cat, num_cat, aft_ent, ent)
                    if symb == "O":
                        move_applied, move_steps = uncross_repair(
                            update_puzzle, aft_cat, num_cat, aft_ent, ent
                        )
                        applied = applied or move_applied
                        if move_applied:
                            repair_steps.extend(move_steps)
                for step in repair_steps:
                    step["insights"].add(needed_insight)
                steps.extend(repair_steps)
            elif len(pos_bef_index) == 1:
                if needed_insight not in forbidden_insights:
                    complete = True
                    bef_index = pos_bef_index[0]
                    move_applied, move_diff = update_puzzle.answer(
                        bef_cat, num_cat, bef_ent, num_cat.entities[bef_index], "O"
                    )
                    applied = applied or move_applied
                    if move_applied:
                        insights.add(needed_insight)
                        steps.append({
                            "result": update_puzzle,
                            "move_diff": move_diff,
                            "insights": {needed_insight},
                            "repair": False,
                        })
                        x_applied, cis_valid, cross_steps = cross_out(
                            update_puzzle,
                            bef_cat,
                            num_cat,
                            bef_ent,
                            num_cat.entities[bef_index],
                        )
                        applied = applied or x_applied
                        is_valid = is_valid and cis_valid
                        if x_applied:
                            for step in cross_steps:
                                step["insights"].add(needed_insight)
                            steps.extend(cross_steps)
                    if slow:
                        puzzle.grids = update_puzzle.grids
                        return applied, is_valid, complete, insights, steps
            else:
                b_steps = []
                for i in range(aft_index, len(before_symbols)):
                    sy = puzzle.get_symbol(bef_cat, num_cat, bef_ent, num_cat.entities[i])
                    if sy != "X":
                        move_applied, move_diff = update_puzzle.answer(
                            bef_cat, num_cat, bef_ent, num_cat.entities[i], "X"
                        )
                        applied = applied or move_applied
                        if move_applied:
                            b_steps.append({
                                "result": update_puzzle,
                                "move_diff": move_diff,
                                "insights": {Insight.APPLY_BEFORE_UNDEFINED_SPOTS},
                                "repair": False,
                            })
                    if sy == "O":
                        complete = True
                        is_valid = False
                        move_applied, move_steps = uncross_repair(
                            puzzle, aft_cat, num_cat, bef_ent, num_cat.entities[i]
                        )
                        applied = applied or move_applied
                        if move_applied:
                            for step in move_steps:
                                step["insights"].add(Insight.APPLY_BEFORE_UNDEFINED_SPOTS)
                            steps.extend(move_steps)
                if len(b_steps) > 0:
                    steps.extend(b_steps)
                    for b_step in b_steps:
                        apply_move(before_puzzle, b_step)
                    o_applied, _, _, _, opening_steps = find_openings(
                        before_puzzle, forbidden_insights
                    )
                    if o_applied:
                        for o_step in opening_steps:
                            if "O" in o_step["move_diff"].print_grid():
                                o_step["insights"].add(Insight.APPLY_BEFORE_UNDEFINED_SPOTS)
                                steps.append(o_step)
                for i in pos_bef_index:
                    # Make an uncertain mark for possible answers.
                    sy = puzzle.get_symbol(aft_cat, num_cat, bef_ent, num_cat.entities[i])
                    if sy == "*":
                        move_applied, move_diff = update_puzzle.answer(
                            aft_cat, num_cat, bef_ent, num_cat.entities[i], "Y"
                        )
                        applied = applied or move_applied
                        if move_applied:
                            insights.add(Insight.APPLY_BEFORE_UNDEFINED_SPOTS)
                            steps.append({
                                "result": update_puzzle,
                                "move_diff": move_diff,
                                "insights": {Insight.APPLY_BEFORE_UNDEFINED_SPOTS},
                                "repair": False,
                            })
                if applied and slow:
                    puzzle.grids = update_puzzle.grids
                    return applied, is_valid, complete, insights, steps

        # Narrow down possiblities with no information for entities yet
        # The before entity can't be in the last num spots (or there won't be room for the after entity)
        for i in range(0, len(before_symbols) - num):
            sy = puzzle.get_symbol(bef_cat, num_cat, bef_ent, num_cat.entities[i])
            if sy == "*":
                move_applied, move_diff = update_puzzle.answer(
                    bef_cat, num_cat, bef_ent, num_cat.entities[i], "Y"
                )
                applied = applied or move_applied
                if move_applied:
                    steps.append({
                        "result": update_puzzle,
                        "move_diff": move_diff,
                        "insights": {Insight.BEFORE_ONE_SPOT_NOINFO},
                        "repair": False,
                    })
        b_steps = []
        for i in range(len(before_symbols) - num, len(before_symbols)):
            sy = puzzle.get_symbol(bef_cat, num_cat, bef_ent, num_cat.entities[i])
            needed_insight = Insight.BEFORE_ONE_SPOT_NOINFO
            if i > len(before_symbols) - num:
                needed_insight = Insight.BEFORE_N_SPOTS_NOINFO
            if sy not in ["X", "O"] and needed_insight not in forbidden_insights:
                move_applied, move_diff = update_puzzle.answer(
                    bef_cat, num_cat, bef_ent, num_cat.entities[i], "X"
                )
                applied = applied or move_applied
                if move_applied:
                    insights.add(needed_insight)
                    b_steps.append({
                        "result": update_puzzle,
                        "move_diff": move_diff,
                        "insights": {needed_insight},
                        "repair": False,
                    })
            elif sy == "O":
                complete = True
                is_valid = False
                move_applied, move_steps = uncross_repair(
                    puzzle, bef_cat, num_cat, bef_ent, num_cat.entities[i]
                )
                applied = applied or move_applied
                if move_applied:
                    for step in move_steps:
                        step["insights"].add(needed_insight)
                    steps.extend(move_steps)
        if len(b_steps) > 0:
            steps.extend(b_steps)
            needed_insight = Insight.BEFORE_ONE_SPOT_NOINFO
            for b_step in b_steps:
                apply_move(before_puzzle, b_step)
                if Insight.BEFORE_N_SPOTS_NOINFO in b_step["insights"]:
                    needed_insight = Insight.BEFORE_N_SPOTS_NOINFO
            _, _, _, _, opening_steps = find_openings(before_puzzle, forbidden_insights)
            for o_step in opening_steps:
                if "O" in o_step["move_diff"].print_grid():
                    o_step["insights"].add(needed_insight)
                    steps.append(o_step)
        # And the inverse is true for the after entity
        b_steps = []
        opening_puzzle = deepcopy(puzzle)
        for i in range(0, num):
            sy = puzzle.get_symbol(aft_cat, num_cat, aft_ent, num_cat.entities[i])
            needed_insight = Insight.BEFORE_ONE_SPOT_NOINFO
            if i > 0:
                needed_insight = Insight.BEFORE_N_SPOTS_NOINFO
            if sy not in ["X", "O"] and needed_insight not in forbidden_insights:
                move_applied, move_diff = update_puzzle.answer(
                    aft_cat, num_cat, aft_ent, num_cat.entities[i], "X"
                )
                applied = applied or move_applied
                if move_applied:
                    insights.add(needed_insight)
                    b_steps.append({
                        "result": update_puzzle,
                        "move_diff": move_diff,
                        "insights": {needed_insight},
                        "repair": False,
                    })
            elif sy == "O":
                complete = True
                is_valid = False
                move_applied, move_steps = uncross_repair(
                    puzzle, aft_cat, num_cat, aft_ent, num_cat.entities[i]
                )
                applied = applied or move_applied
                if move_applied:
                    for step in move_steps:
                        step["insights"].add(needed_insight)
                    steps.extend(move_steps)
        if len(b_steps) > 0:
            steps.extend(b_steps)
            needed_insight = Insight.BEFORE_ONE_SPOT_NOINFO
            for b_step in b_steps:
                apply_move(after_puzzle, b_step)
                if Insight.BEFORE_N_SPOTS_NOINFO in b_step["insights"]:
                    needed_insight = Insight.BEFORE_N_SPOTS_NOINFO
            _, _, _, _, opening_steps = find_openings(after_puzzle, forbidden_insights)
            for o_step in opening_steps:
                if "O" in o_step["move_diff"].print_grid():
                    o_step["insights"].add(needed_insight)
                    steps.append(o_step)
        for i in range(num, len(after_symbols)):
            sy = puzzle.get_symbol(aft_cat, num_cat, aft_ent, num_cat.entities[i])
            if sy == "*":
                move_applied, move_diff = update_puzzle.answer(
                    aft_cat, num_cat, aft_ent, num_cat.entities[i], "Y"
                )
                applied = applied or move_applied
                if move_applied:
                    steps.append({
                        "result": update_puzzle,
                        "move_diff": move_diff,
                        "insights": {Insight.BEFORE_ONE_SPOT_NOINFO},
                        "repair": False,
                    })
        if applied and slow:
            puzzle.grids = update_puzzle.grids
            return applied, is_valid, complete, insights, steps

        # Determine possible answers with constraints on either entity
        if "X" in before_symbols or "X" in after_symbols:
            b_steps = []
            # A streak of Xs at the beginning/end forces the first available position for the other entity to shift.
            for i in range(len(before_symbols) - num):
                if before_symbols[i] != "X":
                    break
                sy = puzzle.get_symbol(aft_cat, num_cat, aft_ent, num_cat.entities[i + num])
                if sy != "X" and Insight.BEFORE_N_SPOTS_SHIFT not in forbidden_insights:
                    move_applied, move_diff = update_puzzle.answer(
                        aft_cat, num_cat, aft_ent, num_cat.entities[i + num], "X"
                    )
                    applied = applied or move_applied
                    if move_applied:
                        insights.add(Insight.BEFORE_N_SPOTS_SHIFT)
                        b_steps.append({
                            "result": update_puzzle,
                            "move_diff": move_diff,
                            "insights": {Insight.BEFORE_N_SPOTS_SHIFT},
                            "repair": False,
                        })
            if len(b_steps) > 0:
                steps.extend(b_steps)
                opening_puzzle = deepcopy(puzzle)
                for b_step in b_steps:
                    apply_move(after_puzzle, b_step)
                _, _, _, _, opening_steps = find_openings(
                    after_puzzle, forbidden_insights
                )
                for o_step in opening_steps:
                    if "O" in o_step["move_diff"].print_grid():
                        o_step["insights"].add(Insight.BEFORE_N_SPOTS_SHIFT)
                        steps.append(o_step)
            b_steps = []
            for i in range(len(after_symbols) - 1, num - 1, -1):
                if after_symbols[i] != "X":
                    break
                sy = puzzle.get_symbol(bef_cat, num_cat, bef_ent, num_cat.entities[i - num])
                if sy != "X" and Insight.BEFORE_N_SPOTS_SHIFT not in forbidden_insights:
                    move_applied, move_diff = update_puzzle.answer(
                        bef_cat, num_cat, bef_ent, num_cat.entities[i - num], "X"
                    )
                    applied = applied or move_applied
                    if move_applied:
                        insights.add(Insight.BEFORE_N_SPOTS_SHIFT)
                        b_steps.append({
                            "result": update_puzzle,
                            "move_diff": move_diff,
                            "insights": {Insight.BEFORE_N_SPOTS_SHIFT},
                            "repair": False,
                        })
            if len(b_steps) > 0:
                steps.extend(b_steps)
                for b_step in b_steps:
                    apply_move(before_puzzle, b_step)
                _, _, _, _, opening_steps = find_openings(
                    before_puzzle, forbidden_insights
                )
                for o_step in opening_steps:
                    if "O" in o_step["move_diff"].print_grid():
                        o_step["insights"].add(Insight.BEFORE_N_SPOTS_SHIFT)
                        steps.append(o_step)

            if applied and slow:
                puzzle.grids = update_puzzle.grids
                return applied, is_valid, complete, insights, steps

            if numbered:
                # All Xs for the before entity where the index is valid (i+num exists).
                before_Xs = [
                    i
                    for i in range(len(before_symbols))
                    if before_symbols[i] == "X" and i + num < len(before_symbols) - 1
                ]
                # All Xs for the after entity where the index is valid (i-num exists).
                after_Xs = [
                    i
                    for i in range(len(after_symbols))
                    if after_symbols[i] == "X" and i - num > -1
                ]

                b_steps = []
                # For a position to be a valid answer, the corresponding position +/- num must be valid for the other entity
                for i in before_Xs:
                    sy = puzzle.get_symbol(
                        aft_cat, num_cat, aft_ent, num_cat.entities[i + num]
                    )
                    if (
                        sy != "X"
                        and Insight.BEFORE_N_SPOTS_CROSSCHECK not in forbidden_insights
                    ):
                        move_applied, move_diff = update_puzzle.answer(
                            aft_cat, num_cat, aft_ent, num_cat.entities[i + num], "X"
                        )
                        applied = applied or move_applied
                        if move_applied:
                            insights.add(Insight.BEFORE_N_SPOTS_CROSSCHECK)
                            b_steps.append({
                                "result": update_puzzle,
                                "move_diff": move_diff,
                                "insights": {Insight.BEFORE_N_SPOTS_CROSSCHECK},
                                "repair": False,
                            })
                if len(b_steps) > 0:
                    steps.extend(b_steps)
                    for b_step in b_steps:
                        apply_move(after_puzzle, b_step)
                    _, _, _, _, opening_steps = find_openings(
                        after_puzzle, forbidden_insights
                    )
                    for o_step in opening_steps:
                        if "O" in o_step["move_diff"].print_grid():
                            o_step["insights"].add(Insight.BEFORE_N_SPOTS_CROSSCHECK)
                            steps.append(o_step)
                b_steps = []
                for i in after_Xs:
                    sy = puzzle.get_symbol(
                        bef_cat, num_cat, bef_ent, num_cat.entities[i - num]
                    )
                    if (
                        sy != "X"
                        and Insight.BEFORE_N_SPOTS_CROSSCHECK not in forbidden_insights
                    ):
                        move_applied, move_diff = update_puzzle.answer(
                            bef_cat, num_cat, bef_ent, num_cat.entities[i - num], "X"
                        )
                        applied = applied or move_applied
                        if move_applied:
                            insights.add(Insight.BEFORE_N_SPOTS_CROSSCHECK)
                            b_steps.append({
                                "result": update_puzzle,
                                "move_diff": move_diff,
                                "insights": {Insight.BEFORE_N_SPOTS_CROSSCHECK},
                                "repair": False,
                            })
                if len(b_steps) > 0:
                    steps.extend(b_steps)
                    for b_step in b_steps:
                        apply_move(before_puzzle, b_step)
                    _, _, _, _, opening_steps = find_openings(
                        before_puzzle, forbidden_insights
                    )
                    for o_step in opening_steps:
                        if "O" in o_step["move_diff"].print_grid():
                            o_step["insights"].add(Insight.BEFORE_N_SPOTS_CROSSCHECK)
                            steps.append(o_step)
                if applied and slow:
                    puzzle.grids = update_puzzle.grids
                    return applied, is_valid, complete, insights, steps

        puzzle.grids = update_puzzle.grids
        return applied, is_valid, complete, insights, steps




    def apply_simple_or(puzzle, terms, forbidden_insights=set(), slow=False):
        """
        Apply the or rule to puzzle, will be incomplete if not enough information is known
        slow: set to True to apply only the first valid insight
        return_steps: return each mark as its own move with the insight
        return: applied, is_valid, complete
        """
        applied = False
        is_valid = True
        complete = False
        insights = set()

        steps = []
        update_puzzle = deepcopy(puzzle)

        pos_cat1 = terms[0]
        pos_ent1 = terms[1]  # either ent1 or ent2 = ans_ent
        pos_cat2 = terms[2]
        pos_ent2 = terms[3]

        ans_cat = terms[4]
        ans_ent = terms[5]

        pos_symb1 = puzzle.get_symbol(pos_cat1, ans_cat, pos_ent1, ans_ent)
        pos_symb2 = puzzle.get_symbol(pos_cat2, ans_cat, pos_ent2, ans_ent)

        if pos_symb1 not in ["O", "X"] and pos_symb2 not in ["O", "X"]:
            # we can't apply clue yet (don't have enough information)
            complete = False
            if pos_symb1 == "*":
                move_applied, move_diff = update_puzzle.answer(
                    pos_cat1, ans_cat, pos_ent1, ans_ent, "Y"
                )
                applied = applied or move_applied
                if move_applied:
                    steps.append({
                        "result": update_puzzle,
                        "move_diff": move_diff,
                        "insights": {Insight.APPLY_OR},
                        "repair": False,
                    })
            if pos_symb2 == "*":
                move_applied, move_diff = update_puzzle.answer(
                    pos_cat2, ans_cat, pos_ent2, ans_ent, "Y"
                )
                applied = applied or move_applied
                if move_applied:
                    steps.append({
                        "result": update_puzzle,
                        "move_diff": move_diff,
                        "insights": {Insight.APPLY_OR},
                        "repair": False,
                    })
        elif pos_symb1 == pos_symb2:
            # this rule can't be applied (both are true or both are false)
            complete = True
            is_valid = False
            repair_steps = []
            move_applied, move_steps = uncross_repair(
                update_puzzle, pos_cat1, ans_cat, pos_ent1, ans_ent
            )
            applied = applied or move_applied
            if move_applied:
                repair_steps.extend(move_steps)
            move_applied, move_steps = uncross_repair(
                update_puzzle, pos_cat2, ans_cat, pos_ent2, ans_ent
            )
            applied = applied or move_applied
            if move_applied:
                repair_steps.extend(move_steps)
            for step in repair_steps:
                step["insights"].add(Insight.APPLY_OR)
            steps.extend(repair_steps)
            return applied, is_valid, complete, insights, steps
        elif pos_symb1 == "O":
            # clue says that ent2 cannot be the answer ent
            if pos_symb2 != "X" and Insight.APPLY_OR not in forbidden_insights:
                # we can change game state
                complete = True
                move_applied, move_diff = update_puzzle.answer(
                    pos_cat2, ans_cat, pos_ent2, ans_ent, "X"
                )
                applied = applied or move_applied
                if move_applied:
                    or_step = {
                        "result": update_puzzle,
                        "move_diff": move_diff,
                        "insights": {Insight.APPLY_OR},
                        "repair": False,
                    }
                    steps.append(or_step)
                    opening_puzzle = deepcopy(puzzle)
                    apply_move(opening_puzzle, or_step)
                    o_applied, _, _, _, opening_steps = find_openings(
                        opening_puzzle, forbidden_insights
                    )
                    if o_applied:
                        for o_step in opening_steps:
                            if "O" in o_step["move_diff"].print_grid():
                                o_step["insights"].add(Insight.APPLY_OR)
                                steps.append(o_step)
                    insights.add(Insight.APPLY_OR)
                puzzle.grids = update_puzzle.grids
                return applied, is_valid, complete, insights, steps
            elif pos_symb2 == "X":
                # game state is correct, but nothing to change
                complete = True
        elif pos_symb1 == "X":
            # clue says that ent2 must be the answer ent
            if pos_symb2 != "O" and Insight.APPLY_OR not in forbidden_insights:
                # we can change the game state
                complete = True
                move_applied, move_diff = update_puzzle.answer(
                    pos_cat2, ans_cat, pos_ent2, ans_ent, "O"
                )
                applied = applied or move_applied
                if move_applied:
                    insights.add(Insight.APPLY_OR)
                    steps.append({
                        "result": update_puzzle,
                        "move_diff": move_diff,
                        "insights": {Insight.APPLY_OR},
                        "repair": False,
                    })
                    x_applied, cis_valid, cross_steps = cross_out(
                        update_puzzle, pos_cat2, ans_cat, pos_ent2, ans_ent
                    )
                    applied = applied or x_applied
                    is_valid = is_valid and cis_valid
                    if x_applied:
                        for step in cross_steps:
                            step["insights"].add(Insight.APPLY_OR)
                        steps.extend(cross_steps)
                puzzle.grids = update_puzzle.grids
                return applied, is_valid, complete, insights, steps
            elif pos_symb2 == "O":
                # game state is correct, but we cannot change
                complete = True
        elif pos_symb1 not in ["O", "X"]:
            if pos_symb2 == "O" and Insight.APPLY_OR not in forbidden_insights:
                # clue says ent1 is not ans_ent and we can change this
                complete = True
                move_applied, move_diff = update_puzzle.answer(
                    pos_cat1, ans_cat, pos_ent1, ans_ent, "X"
                )
                applied = applied or move_applied
                if move_applied:
                    or_step = {
                        "result": update_puzzle,
                        "move_diff": move_diff,
                        "insights": {Insight.APPLY_OR},
                        "repair": False,
                    }
                    steps.append(or_step)
                    opening_puzzle = deepcopy(puzzle)
                    apply_move(opening_puzzle, or_step)
                    o_applied, _, _, _, opening_steps = find_openings(
                        opening_puzzle, forbidden_insights
                    )
                    if o_applied:
                        for o_step in opening_steps:
                            if "O" in o_step["move_diff"].print_grid():
                                o_step["insights"].add(Insight.APPLY_OR)
                                steps.append(o_step)
                    insights.add(Insight.APPLY_OR)
                puzzle.grids = update_puzzle.grids
                return applied, is_valid, complete, insights, steps
            elif pos_symb2 == "X" and Insight.APPLY_OR not in forbidden_insights:
                # clue says ent1 is ans_ent and we can change this
                applied = True
                complete = True
                move_applied, move_diff = update_puzzle.answer(
                    pos_cat1, ans_cat, pos_ent1, ans_ent, "O"
                )
                applied = applied or move_applied
                if move_applied:
                    steps.append({
                        "result": update_puzzle,
                        "move_diff": move_diff,
                        "insights": {Insight.APPLY_OR},
                        "repair": False,
                    })
                    insights.add(Insight.APPLY_OR)
                    x_applied, cis_valid, cross_steps = cross_out(
                        update_puzzle, pos_cat1, ans_cat, pos_ent1, ans_ent
                    )
                    applied = applied or x_applied
                    is_valid = is_valid and cis_valid
                    if x_applied:
                        for step in cross_steps:
                            step["insights"].add(Insight.APPLY_OR)
                        steps.extend(cross_steps)

                puzzle.grids = update_puzzle.grids
                return applied, is_valid, complete, insights, steps

        if pos_cat1 != pos_cat2:
            if Insight.SIMPLE_OR_DIFF_CAT not in forbidden_insights:
                # A and B are in different categories
                # If A or B is C then A is not B
                sy = puzzle.get_symbol(pos_cat1, pos_cat2, pos_ent1, pos_ent2)
                if sy == "O":
                    is_valid = False
                    move_applied, move_steps = uncross_repair(
                        update_puzzle, pos_cat1, pos_cat2, pos_ent1, pos_ent2
                    )
                    applied = applied or move_applied
                    if move_applied:
                        for step in move_steps:
                            step["insights"].add(Insight.SIMPLE_OR_DIFF_CAT)
                        steps.extend(move_steps)
                elif sy != "X":
                    move_applied, move_diff = update_puzzle.answer(
                        pos_cat1, pos_cat2, pos_ent1, pos_ent2, "X"
                    )
                    applied = applied or move_applied
                    if move_applied:
                        or_step = {
                            "result": update_puzzle,
                            "move_diff": move_diff,
                            "insights": {Insight.SIMPLE_OR_DIFF_CAT},
                            "repair": False,
                        }
                        steps.append(or_step)
                        opening_puzzle = deepcopy(puzzle)
                        apply_move(opening_puzzle, or_step)
                        o_applied, _, _, _, opening_steps = find_openings(
                            opening_puzzle, forbidden_insights
                        )
                        if o_applied:
                            for o_step in opening_steps:
                                if "O" in o_step["move_diff"].print_grid():
                                    o_step["insights"].add(Insight.SIMPLE_OR_DIFF_CAT)
                                    steps.append(o_step)
                        insights.add(Insight.SIMPLE_OR_DIFF_CAT)
                if slow:
                    puzzle.grids = update_puzzle.grids
                    return applied, is_valid, complete, insights, steps
        else:
            # A and B are in the same category
            # If A or B from category 0 is C then no other entity from category 0 is C
            for ent in pos_cat1.entities:
                if ent not in [pos_ent1, pos_ent2]:
                    sy = puzzle.get_symbol(pos_cat1, ans_cat, ent, ans_ent)
                    if sy == "O":
                        # Logical error.
                        is_valid = False
                        complete = True
                        move_applied, move_steps = uncross_repair(
                            update_puzzle, pos_cat1, ans_cat, ent, ans_ent
                        )
                        applied = applied or move_applied
                        if move_applied:
                            for step in move_steps:
                                step["insights"].add(Insight.SIMPLE_OR_SAME_CAT)
                            steps.extend(move_steps)
                    elif sy != "X" and Insight.SIMPLE_OR_SAME_CAT not in forbidden_insights:
                        # No other entity from cat1 is ans_ent
                        move_applied, move_diff = update_puzzle.answer(
                            pos_cat1, ans_cat, ent, ans_ent, "X"
                        )
                        applied = applied or move_applied
                        if move_applied:
                            insights.add(Insight.SIMPLE_OR_SAME_CAT)
                            or_step = {
                                "result": update_puzzle,
                                "move_diff": move_diff,
                                "insights": {Insight.SIMPLE_OR_SAME_CAT},
                                "repair": False,
                            }
                            steps.append(or_step)
                            opening_puzzle = deepcopy(puzzle)
                            apply_move(opening_puzzle, or_step)
                            o_applied, _, _, _, opening_steps = find_openings(
                                opening_puzzle, forbidden_insights
                            )
                            if o_applied:
                                for o_step in opening_steps:
                                    if "O" in o_step["move_diff"].print_grid():
                                        o_step["insights"].add(Insight.SIMPLE_OR_SAME_CAT)
                                        steps.append(o_step)
            if applied and slow:
                puzzle.grids = update_puzzle.grids
                return applied, is_valid, complete, insights, steps

        puzzle.grids = update_puzzle.grids
        return applied, is_valid, complete, insights, steps




    def apply_compound_or(puzzle, options, forbidden_insights=set()):
        """
        Apply the compound or rule to puzzle, will be incomplete if not enough information is known
        return: applied, is_valid, complete
        """
        applied = False
        complete = False
        is_valid = True
        insights = (
            set()
        )  # There are no insights for compound or, but keep the return signature consistent

        update_puzzle = deepcopy(puzzle)
        steps = []

        optionA = options[0]
        catA1 = optionA[0]
        entA1 = optionA[1]
        catA2 = optionA[2]
        entA2 = optionA[3]
        currentA = puzzle.get_symbol(catA1, catA2, entA1, entA2)

        optionB = options[1]
        catB1 = optionB[0]
        entB1 = optionB[1]
        catB2 = optionB[2]
        entB2 = optionB[3]
        currentB = puzzle.get_symbol(catB1, catB2, entB1, entB2)

        currents = [currentA, currentB]
        if "X" in currents and "O" in currents:
            # Someone already answered.
            complete = True
            return applied, is_valid, complete, insights, steps

        if currentA == currentB:
            if currentA in ["O", "X"]:
                # Both can't be true or false, something has gone wrong.
                is_valid = False
                complete = True
                repair_steps = []
                move_applied, move_steps = uncross_repair(
                    update_puzzle, catA1, catA2, entA1, entA2
                )
                applied = applied or move_applied
                if move_applied:
                    repair_steps.extend(move_steps)
                move_applied, move_steps = uncross_repair(
                    update_puzzle, catB1, catB2, entB1, entB2
                )
                applied = applied or move_applied
                if move_applied:
                    repair_steps.extend(move_steps)
                    for step in repair_steps:
                        step["insights"].add(Insight.APPLY_OR)
                steps.extend(repair_steps)

        elif (
            currentA in ["O", "X"]
            or currentB in ["O", "X"]
            and Insight.APPLY_OR not in forbidden_insights
        ):
            # At least one term is answered; the clue is guaranteed complete.
            complete = True

            # One is answered and the other is not; we are guaranteed to apply.
            applied = True

            if currentA == "X":
                move_applied, move_diff = update_puzzle.answer(
                    catB1, catB2, entB1, entB2, "O"
                )
                applied = applied or move_applied
                insights.add(Insight.APPLY_OR)
                if move_applied:
                    steps.append({
                        "result": update_puzzle,
                        "move_diff": move_diff,
                        "insights": {Insight.APPLY_OR},
                        "repair": False,
                    })
                    x_applied, cis_valid, cross_steps = cross_out(
                        update_puzzle, catB1, catB2, entB1, entB2
                    )
                    applied = applied or x_applied
                    is_valid = is_valid and cis_valid
                    if x_applied:
                        for step in cross_steps:
                            step["insights"].add(Insight.APPLY_OR)
                        steps.extend(cross_steps)
            elif currentB == "X":
                move_applied, move_diff = update_puzzle.answer(
                    catA1, catA2, entA1, entA2, "O"
                )
                applied = applied or move_applied
                if move_applied:
                    insights.add(Insight.APPLY_OR)
                    steps.append({
                        "result": update_puzzle,
                        "move_diff": move_diff,
                        "insights": {Insight.APPLY_OR},
                        "repair": False,
                    })
                    x_applied, cis_valid, cross_steps = cross_out(
                        update_puzzle, catA1, catA2, entA1, entA2
                    )
                    applied = applied or x_applied
                    is_valid = is_valid and cis_valid
                    if x_applied:
                        for step in cross_steps:
                            step["insights"].add(Insight.APPLY_OR)
                        steps.extend(cross_steps)
            elif currentA == "O":
                move_applied, move_diff = update_puzzle.answer(
                    catB1, catB2, entB1, entB2, "X"
                )
                applied = applied or move_applied
                if move_applied:
                    insights.add(Insight.APPLY_OR)
                    steps.append({
                        "result": update_puzzle,
                        "move_diff": move_diff,
                        "insights": {Insight.APPLY_OR},
                        "repair": False,
                    })
            elif currentB == "O":
                move_applied, move_diff = update_puzzle.answer(
                    catA1, catA2, entA1, entA2, "X"
                )
                applied = applied or move_applied
                if move_applied:
                    insights.add(Insight.APPLY_OR)
                    or_step = {
                        "result": update_puzzle,
                        "move_diff": move_diff,
                        "insights": {Insight.APPLY_OR},
                        "repair": False,
                    }
                    steps.append(or_step)
                    opening_puzzle = deepcopy(puzzle)
                    apply_move(opening_puzzle, or_step)
                    o_applied, _, _, _, opening_steps = find_openings(
                        opening_puzzle, forbidden_insights
                    )
                    if o_applied:
                        for o_step in opening_steps:
                            if "O" in o_step["move_diff"].print_grid():
                                o_step["insights"].add(Insight.APPLY_OR)
                                steps.append(o_step)
        else:
            if currentA == "*":
                move_applied, move_diff = update_puzzle.answer(
                    catA1, catA2, entA1, entA2, "Y"
                )
                applied = applied or move_applied
                if move_applied:
                    steps.append({
                        "result": update_puzzle,
                        "move_diff": move_diff,
                        "insights": {Insight.APPLY_OR},
                        "repair": False,
                    })
            if currentB == "*":
                move_applied, move_diff = update_puzzle.answer(
                    catB1, catB2, entB1, entB2, "Y"
                )
                applied = applied or move_applied
                if move_applied:
                    steps.append({
                        "result": update_puzzle,
                        "move_diff": move_diff,
                        "insights": {Insight.APPLY_OR},
                        "repair": False,
                    })

        puzzle.grids = update_puzzle.grids
        return applied, is_valid, complete, insights, steps




    def apply_clue(puzzle, clue, forbidden_insights=set(), slow=False):
        """
        Given a clue dictionary and a puzzle, apply next step of the clue to the puzzle

        forbidden_insights: insights the solution can't use
        slow: set to True to apply only the first insight for the clue
        return:
        applied  = whether the clue changed the state
        is_valid = whether the clue contradicts the current state
        complete = whether the clue has no more information to offer
        contradiction = the contradiction if the clue is invalid
        insights = the insights required for the move
        """

        applied = False
        complete = False
        is_valid = True
        insights = set()
        steps = []

        rule = list(clue.keys())[0]
        terms = clue[rule]
        if rule == "simple_clue":
            rule = list(clue.keys())[0]
        if rule == "is":
            applied, is_valid, complete, insights, steps = apply_is(
                puzzle, terms, forbidden_insights=forbidden_insights
            )
        elif rule == "not":
            applied, is_valid, complete, insights, steps = apply_not(
                puzzle, terms[0]["is"], forbidden_insights=forbidden_insights
            )
        elif rule == "before":
            applied, is_valid, complete, insights, steps = apply_before(
                puzzle, terms, forbidden_insights=forbidden_insights, slow=slow
            )
        elif rule == "simple_or":
            applied, is_valid, complete, insights, steps = apply_simple_or(
                puzzle, terms, forbidden_insights=forbidden_insights, slow=slow
            )
        elif rule == "compound_or":
            applied, is_valid, complete, insights, steps = apply_compound_or(
                puzzle,
                [terms[0]["is"], terms[1]["is"]],
                forbidden_insights=forbidden_insights,
            )
        else:
            print(
                "This clue has no apply rules! Something has gone horribly wrong. The offending clue: "
                + str_clue(clue)
            )

        return applied, is_valid, complete, insights, steps

    def get_available_moves(puzzle, clues, as_steps=False):
        """
        get all possible next moves in the solution:
            any openings
            any transitive moves possible in order
            all currently applicable clues and their moves in order
            any insights needed
            if the current board is invalid, get the most salient contradiction (highlight the cell(s) that create the contradiction)
        """
        moves = []
        solution, is_valid, _, _ = apply_clues(puzzle, clues)
        if not is_valid:
            # The puzzle itself is broken. this should never happen.
            raise Exception("INVALID_PUZZLE")

        result = deepcopy(puzzle)
        broken_state = repair(result, solution)
        state_is_valid = not broken_state

        result = deepcopy(puzzle)
        applied, is_valid, _, insights, steps = find_openings(result)
        if len(insights) == 0:
            insights = {Insight.NO_INSIGHT}
        if applied:
            if not as_steps:
                move_diff, _ = get_move_diff(puzzle, result)
                moves.append({
                    "type": "openings",
                    "result": result,
                    "move_diff": move_diff,
                    "insights": insights,
                    "repair": not is_valid,
                })
            else:
                for step in steps:
                    step["type"] = "openings"
                moves.extend(steps)
        result = deepcopy(puzzle)
        applied, is_valid, _, insights, steps = find_transitives(result)
        if len(insights) == 0:
            insights = {Insight.NO_INSIGHT}
        if applied:
            if not as_steps:
                move_diff, _ = get_move_diff(puzzle, result)
                moves.append({
                    "type": "transitives",
                    "result": result,
                    "move_diff": move_diff,
                    "insights": insights,
                    "repair": not is_valid,
                })
            else:
                for step in steps:
                    step["type"] = "transitives"
                moves.extend(steps)
        for idx, clue in enumerate(clues):
            result = deepcopy(puzzle)
            applied, is_valid, _, insights, steps = apply_clue(result, clue)
            if len(insights) == 0:
                insights = {Insight.NO_INSIGHT}
            if applied:
                if not as_steps:
                    move_diff, _ = get_move_diff(puzzle, result)
                    moves.append({
                        "type": "clue",
                        "indexed_clue": {"idx": idx, "clue": clue},
                        "result": result,
                        "move_diff": move_diff,
                        "insights": insights,
                        "repair": not is_valid,
                    })
                else:
                    for step in steps:
                        step["type"] = "clue"
                        step["indexed_clue"] = {"idx": idx, "clue": clue}
                    moves.extend(steps)
        return state_is_valid, moves


    def get_move_diff(before, after, changes_only=False):
        diff = deepcopy(after)
        changed = False
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
                            if not changes_only:
                                diff.answer(
                                    cat1,
                                    cat2,
                                    cat1.entities[ent1_idx],
                                    cat2.entities[ent2_idx],
                                    lowercase_grid_symbol(after_grid[ent2_idx][ent1_idx]),
                                )
                            else:
                                diff.answer(
                                    cat1,
                                    cat2,
                                    cat1.entities[ent1_idx],
                                    cat2.entities[ent2_idx],
                                    "*",
                                )
                        else:
                            changed = True
                            if after_grid[ent2_idx][ent1_idx] == "*":
                                # This is a repair operation
                                diff.answer(
                                    cat1,
                                    cat2,
                                    cat1.entities[ent1_idx],
                                    cat2.entities[ent2_idx],
                                    "_",
                                )
        return diff, changed


    def lowercase_grid_symbol(S):
        if S == "X":
            return "x"
        elif S == "O":
            return "o"
        elif S == "*" or S == "_":
            return "*"
        elif S == "N":
            return "n"
        elif S == "Y":
            return "y"
        return ""


    def apply_clues(puzzle, clues, print_soln=False, forbidden_insights=set()):
        """
        solver
        """
        is_valid = True
        copy = Puzzle(puzzle.categories)
        queue = clues[:]
        # trace = {}
        backlog = []
        applied = True
        insights = set()
        loop = 0
        if len(clues) == 0:
            is_valid = False
            return copy, is_valid, loop, insights
        while is_valid and applied and len(queue) > 0:
            applied = False
            loop += 1

            for clue in queue:
                og = deepcopy(copy)
                a, is_valid, complete, clue_insights, _ = apply_clue(
                    copy, clue, forbidden_insights=forbidden_insights
                )
                applied = applied or a
                insights = insights | clue_insights
                if not complete:
                    backlog.append(clue)
                elif print_soln:
                    print("HINT NO LONGER NEEDED: ", clue_to_english(clue))
                if not is_valid:
                    return copy, is_valid, loop, insights

                # Apply additional logic
                if a:
                    a_2 = True
                    a_3 = True
                    while a_2 or a_3:
                        # Apply openings and transitives as many times as you can.
                        a_2, is_valid, complete, opening_insights, _ = find_openings(
                            copy, forbidden_insights=forbidden_insights
                        )
                        if not is_valid:
                            return copy, is_valid, loop, insights
                        a_3, is_valid, complete, trans_insights, _ = find_transitives(
                            copy, forbidden_insights=forbidden_insights
                        )
                        if not is_valid:
                            return copy, is_valid, loop, insights
                        applied = applied or a_2 or a_3  # test if anything was changed
                        clue_insights = clue_insights | trans_insights | opening_insights
                        insights = insights | clue_insights
                    if not is_valid:
                        return copy, is_valid, loop, insights
                if print_soln and a:
                    print("clue: ", clue_to_english(clue))
                    print("insights: ", clue_insights)
                    print("updated grid: ")
                    move_diff, _ = get_move_diff(og, copy)
                    print(move_diff.print_grid())
            queue = backlog
            backlog = []

        return copy, is_valid, loop, insights


    def get_needed(puzzle, clues, print_soln=False):
        if print_soln:
            print("Initial solution")
        completed_puzzle, is_valid, _, _ = apply_clues(puzzle, clues, print_soln=print_soln)
        assert completed_puzzle.is_complete() and is_valid

        needed = set()
        unneeded = ALL_INSIGHTS.copy()

        assert not can_solve_without_forbidden(
            puzzle, clues, unneeded
        ), "No insights are needed to solve the puzzle; something has gone wrong somewhere."

        # Add insights easiest first until the puzzle can be solved.
        completed_without_maybe = can_solve_without_forbidden(
            puzzle, clues, unneeded, print_soln
        )
        for insight in Insight:
            if not completed_without_maybe:
                unneeded = unneeded - {insight}
                completed_without_maybe = can_solve_without_forbidden(
                    puzzle, clues, unneeded, print_soln
                )
            else:
                break
        needed = ALL_INSIGHTS - unneeded
        assert len(needed & unneeded) == 0
        assert len(needed | unneeded) == len(ALL_INSIGHTS)
        assert can_solve_without_forbidden(
            puzzle, clues, unneeded, print_soln
        ), "can't solve without some of the insights judged unneeded: {}".format(unneeded)
        # Remove any insights that don't result in the puzzle breaking, starting from the hardest
        for insight in reversed(Insight):
            if insight in needed:
                needed = needed - {insight}
                unneeded = ALL_INSIGHTS - needed
                # Test whether the insight is really needed
                completed_without_maybe = can_solve_without_forbidden(
                    puzzle, clues, unneeded, print_soln
                )

                if not completed_without_maybe:
                    # The insight is needed, add it back
                    needed = needed | {insight}
        unneeded = ALL_INSIGHTS - needed
        assert len(needed | unneeded) == len(ALL_INSIGHTS)
        assert len(needed & unneeded) == 0
        assert can_solve_without_forbidden(
            puzzle, clues, ALL_INSIGHTS - needed, print_soln
        ), "can't solve without some of the insights judged as unneeded: {}".format(
            unneeded
        )
        return needed


    def can_solve_without_forbidden(puzzle, clues, forbidden_insights, print_soln=False):
        if print_soln:
            print("Soln without {}".format(forbidden_insights))
        completed_puzzle, is_valid, _, used_insights = apply_clues(
            puzzle, clues, print_soln=print_soln, forbidden_insights=forbidden_insights
        )
        assert (
            len(used_insights & forbidden_insights) == 0
        ), "insights: {} includes forbidden: {}".format(
            used_insights, used_insights & forbidden_insights
        )
        assert is_valid, "not valid with forbidden {}".format(forbidden_insights)
        return completed_puzzle.is_complete()



