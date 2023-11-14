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
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor
import random
from copy import deepcopy


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
  def __init__(self, title, entities, is_numeric):
    self.title = title
    self.entities = entities
    self.is_numeric = is_numeric
  def __str__(self):
    return self.title


# %% id="EFhbSHGwKlRs"

class Puzzle:
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
    self.left_right = self.categories[0: len(categories) - 1]
    self.top_buttom = []
    for i in range(len(self.categories) - 1, 0, -1):
      self.top_buttom.append(self.categories[i])
    self.grids = {}

    rows = len(self.top_buttom)

    for top_category in self.left_right:
      for i in range(rows):
        left_cat = self.top_buttom[i]
        title = self._to_key(top_category, left_cat)
        array =[]
        for i in range(len(left_cat.entities)):
          array += [["*"]  * len(top_category.entities)]
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
    assuming cat is the top category

    Not sure if this ended up actually be useful, could delete
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
    index1 = cat1.entities.index(ent1)
    index2 = cat2.entities.index(ent2)
    if self._to_key(cat1, cat2) in self.grids:
      grid = self.grids[self._to_key(cat1, cat2)]
      grid[index2][index1] = new_symbol

    elif self._to_key(cat2, cat1) in self.grids:
      grid = self.grids[self._to_key(cat2, cat1)]
      grid[index1][index2] = new_symbol

  def _print_row(self, top_cats, cat2, remove_top = False):
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
        row_str =  " " + "    ".join(row) + "  |"
        return_str += row_str
      return_str += "\n"

    return_str += bar

    return return_str


  def print_row(self, row):
    """
    find the top categories and the vertical categories
    for a single row
    """
    left_cat = self.top_buttom[row]
    num_top = len(self.left_right) - row
    remove_top = row > 0
    return self._print_row(self.left_right[0:num_top], left_cat, remove_top)

  def print_grid(self):
    """
    return the entire puzzle string

    TODO: add category names?
    """
    return_str = ""
    for i in range(len(self.top_buttom)):
      return_str += self.print_row(i)

    return return_str

  def _grid_is_valid(self, grid):
    """
    Check that there are one or less "O"s
    for each row and column in a grid
    """
    #check rows
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
       Check that there is exactly 1 "O"s
    for each row and column in a grid
    """
    #check rows
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
    value of the entity is know, and the values
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
          if val == "0":
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

  def _truths_valid(self):
    """
    Make sure there is not violations in
    truths of each entity

    There is absoluely a more efficent way to do this
    """
    for cat, ent in self._all_ents():
      truths = self.find_truths(cat, ent)
      if len(truths) >= 2:
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

          #make sure there is not a truth somehwere else
          truths1 = self.find_truths(cat1, ent1)
          if cat2.title in truths1 and truths1[cat2.title] != ent2:
              return False

          truths2 = self.find_truths(cat2, ent2)
          if cat1.title in truths2 and truths2[cat1.title] != ent1:
              return False
    return True

  def is_valid(self):
    """
    return true of there there is at
    most 1 "O" for each column and row

    and if there are no truth violaitons
    """
    #make sure there is at most 1 truth
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
    l = 0 
    for row in grid: 
      s += row.count("X") + row.count("O")
      l += len(row)
    return s / l

  def percent_complete(self):
    """
          return the ratio of cells that
          have an "X" or "O"
    """
    grid_sums = 0 
    grid_len = 0 
    for grid in self.grids.values(): 
      grid_sums += self._per_complete_grid(grid)
      grid_len += 1
      return grid_sums / grid_len

  def apply_hints(self, hints):
    """
    Return a copy of the puzzle
    here all hints in a list are
    applied
    Starts with a blank verison
    of the puzzle (i.e. does not copy grids)
    """
    return


# %% [markdown] id="wGi_U2rSy8Iu"
# ### Test puzzles


# %% id="YVzai91mLX_9"
if __name__ == "__main__":
  suspects = Category("suspects", ["Scarlet", "White", "Mustard", "Plum"], False)
  weapons = Category("weapons", ["Knife", "Rope", "Candle Stick", "Wrench"], False)
  rooms = Category("rooms", ["Ball room", "Living Room", "Kitchen", "Study"], False)
  time = Category("Time", ["1:00", "2:00", "3:00", "4:00"], True)

  puzzle = Puzzle([suspects, weapons, rooms, time])

# %% colab={"base_uri": "https://localhost:8080/"} id="i0iWKiURMcWG" outputId="c37df34f-453d-4128-8966-e66129961c3d"
if __name__ == "__main__": 
  print(" " * 7 + " ".join([str(ent) for ent in puzzle.left_right]))
  print("\n".join([str(ent) for ent in puzzle.top_buttom]))

# %% colab={"base_uri": "https://localhost:8080/"} id="tMBRR7f3PO7G" outputId="a1e70faa-0efc-4226-efcc-783cb3af82ee"
if __name__ == "__main__": 
  print(puzzle.print_grid())

# %% colab={"base_uri": "https://localhost:8080/"} id="5y0jCd1KcEO3" outputId="0c5dae69-7b4f-4467-e76e-291ebb128933"
if __name__ == "__main__": 
  puzzle.answer(weapons, rooms, "Knife", "Study", "O")
  puzzle.answer(weapons, suspects, "Knife", "Scarlet", "O")

  #puzzle.answer(weapons, rooms, "Knife", "Ball room", "O")
  print(puzzle.print_grid())
  print("\n")

  print(puzzle.find_truths(weapons, "Knife"))
  print("\n")
  print(puzzle.find_truths(rooms, "Study"))
  print("\n")
  print(puzzle.is_valid())
  print(puzzle.is_complete())

# %% colab={"base_uri": "https://localhost:8080/"} id="HZ-W4nrF0PUo" outputId="aa2427a3-a09d-4ac3-8709-a7f90ab02187"
if __name__ == "__main__": 
  puzzle.answer(rooms, suspects, "Study", "White", "O")
  print(puzzle.print_grid())
  print(puzzle._truths_valid())

# %% colab={"base_uri": "https://localhost:8080/"} id="NnIeuhBBcHWS" outputId="b6239c41-3d1f-41f6-e2b5-587f79017ed3"
if __name__ == "__main__": 
  suspects2 = Category("suspects", ["Scarlet", "White", "Mustard"], False)
  weapons2 = Category("weapons", ["Knife", "Rope", "Candle Stick"], False)
  rooms2 = Category("rooms", ["Ball room", "Living Room", "Kitchen"], False)


  puzzle2 = Puzzle([suspects2, weapons2, rooms2])
  print(puzzle2.print_grid())

# %% colab={"base_uri": "https://localhost:8080/"} id="eTC-G36i3Tgs" outputId="be584ad7-9b58-43a0-aebd-32cb6b65097a"
if __name__ == "__main__": 
  puzzle2.answer(rooms2, suspects2, "Ball room", "White", "O")
  puzzle2.answer(rooms2, suspects2, "Living Room", "Mustard", "O")
  puzzle2.answer(rooms2, suspects2, "Kitchen", "Scarlet", "O")

  puzzle2.answer(rooms2, weapons2, "Ball room", "Knife", "O")
  puzzle2.answer(rooms2, weapons2, "Living Room", "Rope", "O")
  puzzle2.answer(rooms2,weapons2, "Kitchen", "Candle Stick", "O")

  puzzle2.answer(suspects2, weapons2, "White", "Knife", "O")
  puzzle2.answer(suspects2, weapons2, "Mustard", "Rope", "O")
  puzzle2.answer(suspects2,weapons2, "Scarlet", "Candle Stick", "O")
  print(puzzle2.print_grid())
  print(puzzle2.is_complete())

# %% [markdown] id="c75UQI2AKbXn"
# ## Hint Grammar
#
# The hint grammar is represented as a dictionary where each key is a production rule and each value is the a nested list with the possible terms the production rule needs
#
# For example the "or" rule has two possible term sets:
# * ["cat1", "ent1", "cat1", "ent2", "cat2", "ent"]
# *  ["cat1", "ent", "cat2", "ent", "cat3", "ent"]
#
# The first term set describes two different entities from the same category, and one entity from a different category. This can be used to decribe the rule "Ms. White or Ms. Scarlet was in the study".
#
# The second term set describes three entites from different categories. This can be used to describe the rule "Ms. White or the person with the knife was in the study"

# %% id="xeRLVh4VKj8A"
# Test puzzle
if __name__ == "__main__": 
  suspects = Category("suspects", ["Scarlet", "White", "Mustard", "Plum"], False)
  weapons = Category("weapons", ["Knife", "Rope", "Candle Stick", "Wrench"], False)
  rooms = Category("rooms", ["Ball room", "Living Room", "Kitchen", "Study"], False)
  time = Category("Time", ["1:00", "2:00", "3:00", "4:00"], True)

  puzzle = Puzzle([suspects, weapons, rooms, time])

# %% id="wLYt5NqArCIt"
# define this grammar
# # cat is any category with no resitrictions, however cat1 and cat2 must be different
# similarly ent is any entity with in a caterogy (must have a cat immediately before), but ent1 and ent2 must be different
# num must be a numerical caterogy, alp must be an alaphetbic
# int is an integer 1-len(entities)
terminals = ["cat", "ent", "cat1", "cat2", "cat3", "cat4", "cat5", "ent1", "ent2", "ent3", "ent4", "ent5", "num", "alp", "int"]

hint_grammar = {
  "hint": {
    "is": [["cat1","ent" , "cat2", "ent"]],
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

# # subset for testing
# hint_grammar = {"hint": {
#                           "not": [["cat1", "ent", "cat2", "ent"]],
#                           "is":[ ["cat1","ent" , "cat2", "ent"]],
#                           "or": [["cat1", "ent1", "cat1", "ent2", "cat2", "ent"], ["cat1", "ent", "cat2", "ent", "cat3", "ent"]]
#                          }}


# %% [markdown] id="JV1-3af6q7ej"
# ## Creating Hints
#
# Create a hint involves two steps: generating a word from the grammar and filling in the word
#
# #### Generating a word
# To generate a word, a random production rule is selected. The production rule defines terms that it needs, which will either be terminals or another production rule. If there are any production rules in the terms, the function will be called recursively (with selecting another production rule) until all remaining terms are filled in with terminals.
#
# #### Fill in the word
# The first step will produce a dictionary with list of terms as values, which should all be terminals. For compound hints (ex: "or_hint"), the values are also dictionaries and this process is calledrecursively. This step replaces the terminal word (ex: "cat1") with approicate objects from the puzzle. For example if there were the terms: ["cat1", "ent", "cat2", "ent"], this step could replace it with ["rooms", "study", "suspects" ,"Ms. White"]. Note "rooms" would be the category object, not the string "rooms".  

# %% colab={"base_uri": "https://localhost:8080/"} id="H8bn0PnRYFWr" outputId="3d099582-c31c-4faf-9fc4-87d89553d461"
def sub_grammar(grammar, rule):
  queue = [];
  queue.append(grammar);
  while queue:
    grammar = queue.pop(0)
    if rule in list(grammar.keys()):
      return grammar[rule]
    for r in list(grammar.keys()):
      if isinstance(grammar[r], dict):
        queue.append(grammar[r])
  return

def generate_word(grammar, terminals, grand_grammar = None):
  """
  randomly choice prodcution rules to create new hint base
  will fill out production rules until all terms are terminals
  """
  if grand_grammar is None:
    grand_grammar = grammar
  rule = ""
  if isinstance(grammar, dict):
    # Grammar has named rules; select one at random
    rule = random.choice(list(grammar.keys()))
    if isinstance(grammar[rule], dict):
      # Rule is a subgrammar with named rules itself; recurse
      return {rule : generate_word(grammar[rule], terminals, grand_grammar)}
    else:
      # Rule is a list of alternates
      grammar = grammar[rule]
  # Grammar is a list of alternates; select one at random
  production = random.choice(grammar)
  terms = []
  for word in production:
    if word in terminals:
      terms.append(word)
    else:
      terms.append({word: generate_word(sub_grammar(grand_grammar, word), terminals, grand_grammar)})
  if rule != "":
    return {rule : terms}
  else:
    return terms

def create_cats(puzzle):
  """
  shuffle categories and entities within categories and return as a nested list
  ex: [[cat1, [ent1.1, ent1.2, ent1.2]], [cat2, [ent2.1, ent2.2, ent2.3]]]
  """
  li = puzzle.categories[:]
  random.shuffle(li)
  cats = []
  for cat in li:
    shuf_ents = cat.entities[:]
    random.shuffle(shuf_ents)
    cats.append([cat, shuf_ents])
  return cats

def get_alps(cats):
  """
  return all alphabetic categories
  """
  return [cat for cat in cats if not cat[0].is_numeric]

def get_num(cats):
  """
  return all numeric categories
  """
  return [cat for cat in cats if cat[0].is_numeric]

def fill_in_word(puzzle, word):
  """
  Replace all terminal terms with random and appropriate
  categories, entities, or integers from a puzzle
  """
  filled_word = {}
  for key in word:
    value = word[key]
    if isinstance(value, dict):
      filled_word[key] = fill_in_word(puzzle, word[key])
    else:
      new_terms = []
      cats = create_cats(puzzle)
      alps = get_alps(cats)
      nums = get_num(cats)
      last_cat = None

      i = 0
      for term in  value:
        if isinstance(term, dict):
          new_terms.append(fill_in_word(puzzle, term))
        else:
          if term == "cat":
            last_cat = random.choice(cats)
            new_terms.append(last_cat[0])
          elif term == "cat1":
            if len(cats) < 1:
              raise  Exception("Not enough categories in puzzle")
            else:
              last_cat = cats[0]
              new_terms.append(last_cat[0])
          elif term == "cat2":
            if len(cats) < 2:
              raise  Exception("Not enough categories in puzzle")
            else:
              last_cat = cats[1]
              new_terms.append(last_cat[0])
          elif term == "cat3":
            if len(cats) < 3:
              raise  Exception("Not enough categories in puzzle")
            else:
              last_cat = cats[2]
              new_terms.append(last_cat[0])
          elif term == "alp":
            if len(alps) == 0:
              raise  Exception("Not enough alphetabetic catgories")
            else:
              last_cat = random.choice(alps)
              new_terms.append(last_cat[0])
          elif term == "num":
            if len(nums) == 0:
              raise  Exception("Not enough numeric catgories")
            else:
              last_cat = random.choice(nums)
              new_terms.append(last_cat[0])
          elif term == "ent":
              new_terms.append(random.choice(last_cat[1]))
          elif term == "ent1":
            if len(last_cat[1]) < 1:
              raise  Exception("Not enough enties in puzzle")
            else:
              new_terms.append(last_cat[1][0])
          elif term == "ent2":
            if len(last_cat[1]) < 2:
              raise  Exception("Not enough enties in puzzle")
            else:
              new_terms.append(last_cat[1][1])
          elif term == "ent3":
            if len(last_cat[1]) < 3:
              raise  Exception("Not enough enties in puzzle")
            else:
              new_terms.append(last_cat[1][2])
          elif term == "int":
            new_terms.append(random.randrange(1, len(last_cat[1])))
      filled_word[key] = new_terms
  return filled_word


def generate_hint(puzzle):
  """
  given a puzzle generate a random, valid hint
  """
  word = generate_word(hint_grammar, terminals)
  return fill_in_word(puzzle, word)["hint"]

def str_hint(hint, str_so_far = ""):
  if isinstance(hint, dict):
    rule = list(hint.keys())[0]
    str_so_far += rule + ": "
    return str_hint(hint[rule], str_so_far)
  elif isinstance(hint, list):
    str_so_far += "[ "
    for i, term in enumerate(hint):
      str_so_far += str_hint(term)
      if i != len(hint) - 1:
        str_so_far += ", "
    str_so_far += " ]"
  else:
    str_so_far += str(hint)
  return str_so_far


if __name__ == "__main__": 
  print(str_hint(generate_hint(puzzle)))



# %% [markdown] id="xQm1YGjBsN8k"
# ## Using hints to solve puzzles
# Giving a list of hints you can solve the puzzle (as much as the information in the hints will allow). This can be done by iteratively applying indivual hints untill they are all completed (ex: the "not" rule is completed after putting an "X" on the board, but the "before" rule may still have information after placing a symbol) or the rules stopping changing the game state (ex: the "or" rule cannot change the same state if it doesn't know which rule is correct). Hint can also be invalid, which will terminate the process (ex: if there is a "not" rule over a spot that another hint already placed an "O).
#
#
# ```
# queue = all hints
#
# while game changed and is valid:
#   for hint in queue:
#     apply hint to game state
#     if hint or game state is invalid --> exit
#     if hint is complete hint remove from queue
#   
#   if no hints changed gamestate --> exit
#   
# ```
#
#
#
#

# %% colab={"base_uri": "https://localhost:8080/", "height": 143} id="suJQHIxpSFEZ" outputId="0f9190cf-07af-4e22-8006-46fc71cde693"
def cross_out(puzzle, cat1, cat2, ent1, ent2):
  """
  places Xs in the all the rows and columns
  after you found a correct hint
  """
  is_valid =  True

   # x out the cross sections
  for ent in cat1.entities:
    if ent != ent1:
      symb = puzzle.get_symbol(cat1, cat2, ent, ent2)
      if symb == "*":
        puzzle.answer(cat1, cat2, ent, ent2, "X")
      elif symb == "O":
        is_valid = False

  for ent in cat2.entities:
    if ent != ent2:
      symb = puzzle.get_symbol(cat1, cat2, ent1, ent)
      if symb == "*":
        puzzle.answer(cat1, cat2, ent1, ent, "X")
      elif symb == "O":
            is_valid = False
  return is_valid


# %% colab={"base_uri": "https://localhost:8080/", "height": 143} id="suJQHIxpSFEZ" outputId="0f9190cf-07af-4e22-8006-46fc71cde693"
# If A is B and B is C then A is C
# If A is B and B is not C then A is not C
# ...
def find_transitives(puzzle):
  applied = False
  complete = False
  is_valid = True
  
  # For every pair of related entities:
  #   check all other category relations for X and 0
  #   fill in accordingly
  for catA in puzzle.categories:
    for entA in catA.entities:
      # All known relations for A
      entA_relations = puzzle.get_known_relations(catA, entA)

      # For each category for which A has relations
      for catB, catB_relations in entA_relations.items():

        # For A's truth value in catB, A and B share all relations
        entB = catB_relations["true"]
        if entB != None:
          # A is related to B, so A and B share relations for all other categories
          # Get all realations for B
          entB_relations = puzzle.get_known_relations(catB, entB)
          # Relate A to B's truth and false values.
          for catC, catC_relations in entB_relations.items():
            entC = catC_relations["true"]
            if entC != None:
              # A -> B and B -> C, so A -> C
              sy = puzzle.get_symbol(catA, catC, entA, entC)
              if sy == "*":
                applied = True
                puzzle.answer(catA, catC, entA, entC, "O")
                is_valid = cross_out(puzzle, catA, catC, entA, entC)
                if not is_valid:
                  return applied, is_valid, complete
              elif sy == "X":
                # Can't link A to C
                is_valid = False
                return applied, is_valid, complete
            # For all false values for B in category C
            for entC in catC_relations["false"]:
              # A -> B and B !> C, so A !> C
              sy = puzzle.get_symbol(catA, catC, entA, entC)
              if sy == "*":
                applied = True
                puzzle.answer(catA, catC, entA, entC, "X")
              elif sy == "O":
                # Can't reject A to C
                is_valid = False
                return applied, is_valid, complete
          # Relate B to A's truth and false values
          for catC, catC_relations in entA_relations.items():
            entC = catC_relations["true"]
            if entC != None:
              # A -> B and A -> C so B -> C
              sy = puzzle.get_symbol(catB, catC, entB, entC)
              if sy == "*":
                applied = True
                puzzle.answer(catB, catC, entB, entC, "O")
                is_valid = cross_out(puzzle, catB, catC, entB, entC)
                if not is_valid:
                  return applied, is_valid, complete
              elif sy == "X":
                # Can't link B to C
                is_valid = False
                return applied, is_valid, complete
            for entC in catC_relations["false"]:
              # A -> B and A !> C so B !> C
              sy = puzzle.get_symbol(catB, catC, entB, entC)
              if sy == "*":
                applied = True
                puzzle.answer(catB, catC, entB, entC, "X")
              elif sy == "O":
                # Can't reject B to C
                is_valid = False
                return applied, is_valid, complete    

        # for A's false values in category B, A is negatively related to anything B is related to.
        for entB in catB_relations["false"]:
          # A is not related to B, A is not related to anything B is related to.
          # Get all relations for B
          entB_relations = puzzle.get_known_relations(catB, entB)
          # Relate A to B's truth and false values.
          for catC, catC_relations in entB_relations.items():
            entC = catC_relations["true"]
            if entC != None:
              # A !> B and B -> C, so A !> C
              sy = puzzle.get_symbol(catA, catC, entA, entC)
              if sy == "*":
                applied = True
                puzzle.answer(catA, catC, entA, entC, "X")
              elif sy == "O":
                # Can't reject A to C
                is_valid = False
                return applied, is_valid, complete
            
          # Relate B to A's truth and false values
          for catC, catC_relations in entA_relations.items():
            entC = catC_relations["true"]
            if entC != None:
              # A !> B and A -> C so B !> C
              sy = puzzle.get_symbol(catB, catC, entB, entC)
              if sy == "*":
                applied = True
                puzzle.answer(catB, catC, entB, entC, "X")
              elif sy == "O":
                # Can't reject B to C
                is_valid = False

        # for A's indeterminate values in category B, if A and B can't be related in some category, then A !> B
        for entB in catB_relations["nil"]:
          # All relations for B
          entB_relations = puzzle.get_known_relations(catB, entB)
          for catC, catCA_relations in entA_relations.items():
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
            # If A and B don't share any entities in their possible lists, then A !> B
            setA = set(A_possibles)
            setB = set(B_possibles)
            if not (setA & setB):
              # A and B don't share any possibilities; A !> B
              applied = True
              puzzle.answer(catA, catB, entA, entB, "X")
          
  return applied, is_valid, complete


# %%
# Test find_transitives

# A -> B and B -> C, so A -> C
puzzle = Puzzle([suspects, weapons, rooms, time])
apply_is(puzzle, [suspects, "Scarlet", time, "1:00"])
apply_is(puzzle, [time, "1:00", rooms, "Study"])
print(puzzle.print_grid())

print("Scarlet -> 1:00 and 1:00 -> Study so Scarlet -> Study")
applied, is_valid, complete = find_transitives(puzzle)
print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
print(puzzle.print_grid())
assert (applied, is_valid, complete) == (True, True, False)

# A -> B and B -> C, but can't A -> C => contradiction
puzzle = Puzzle([suspects, weapons, rooms, time])
apply_is(puzzle, [suspects, "Scarlet", time, "1:00"])
apply_is(puzzle, [time, "1:00", rooms, "Study"])
apply_not(puzzle, [suspects, "Scarlet", rooms, "Study"])
print(puzzle.print_grid())

print("Scarlet -> 1:00 and 1:00 -> Study but Scarlet !> Study => contradiction")
applied, is_valid, complete = find_transitives(puzzle)
print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
print(puzzle.print_grid())
assert (applied, is_valid, complete) == (False, False, False)

# A -> B and B !> C, so A !> C
puzzle = Puzzle([suspects, weapons, rooms, time])
apply_is(puzzle, [suspects, "Scarlet", time, "1:00"])
apply_not(puzzle, [time, "1:00", rooms, "Study"])
print(puzzle.print_grid())

print("Scarlet -> 1:00 and 1:00 !> Study so Scarlet !> Study")
applied, is_valid, complete = find_transitives(puzzle)
print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
print(puzzle.print_grid())
assert (applied, is_valid, complete) == (True, True, False)

# A -> B and B !> C, but can't A !> C => contradiction
puzzle = Puzzle([suspects, weapons, rooms, time])
apply_is(puzzle, [suspects, "Scarlet", time, "1:00"])
apply_not(puzzle, [time, "1:00", rooms, "Study"])
apply_is(puzzle, [suspects, "Scarlet", rooms, "Study"])
print(puzzle.print_grid())

print("Scarlet -> 1:00 and 1:00 -> Study but Scarlet !> Study => contradiction")
applied, is_valid, complete = find_transitives(puzzle)
print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
print(puzzle.print_grid())
assert (applied, is_valid, complete) == (False, False, False)

# A -> B and A -> C so B -> C
puzzle = Puzzle([suspects, weapons, rooms, time])
apply_is(puzzle, [suspects, "Scarlet", time, "1:00"])
apply_is(puzzle, [suspects, "Scarlet", rooms, "Study"])
print(puzzle.print_grid())

print("Scarlet -> 1:00 and Scarlet -> Study so 1:00 -> Study")
applied, is_valid, complete = find_transitives(puzzle)
print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
print(puzzle.print_grid())
assert (applied, is_valid, complete) == (True, True, False)

# A -> B and A -> C, but can't B -> C => contradiction
puzzle = Puzzle([suspects, weapons, rooms, time])
apply_is(puzzle, [suspects, "Scarlet", time, "1:00"])
apply_is(puzzle, [suspects, "Scarlet", rooms, "Study"])
apply_not(puzzle, [time, "1:00", rooms, "Study"])
print(puzzle.print_grid())

print("Scarlet -> 1:00 and Scarlet -> Study but 1:00 !> Study => contradiction")
applied, is_valid, complete = find_transitives(puzzle)
print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
print(puzzle.print_grid())
assert (applied, is_valid, complete) == (False, False, False)

# A -> B and A !> C so B !> C
puzzle = Puzzle([suspects, weapons, rooms, time])
apply_is(puzzle, [suspects, "Scarlet", time, "1:00"])
apply_not(puzzle, [suspects, "Scarlet", rooms, "Study"])
print(puzzle.print_grid())

print("Scarlet -> 1:00 and Scarlet !> Study so 1:00 !> Study")
applied, is_valid, complete = find_transitives(puzzle)
print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
print(puzzle.print_grid())
assert (applied, is_valid, complete) == (True, True, False)

# A -> B and A !> C, but can't B !> C => contradiction
puzzle = Puzzle([suspects, weapons, rooms, time])
apply_is(puzzle, [suspects, "Scarlet", time, "1:00"])
apply_not(puzzle, [suspects, "Scarlet", rooms, "Study"])
apply_is(puzzle, [time, "1:00", rooms, "Study"])
print(puzzle.print_grid())

print("Scarlet -> 1:00 and Scarlet !> Study but 1:00 -> Study => contradiction")
applied, is_valid, complete = find_transitives(puzzle)
print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
print(puzzle.print_grid())
assert (applied, is_valid, complete) == (False, False, False)

# A !> B and B -> C, so A !> C
puzzle = Puzzle([suspects, weapons, rooms, time])
apply_not(puzzle, [suspects, "Scarlet", time, "1:00"])
apply_is(puzzle, [time, "1:00", rooms, "Study"])
print(puzzle.print_grid())

print("Scarlet !> 1:00 and 1:00 -> Study so Scarlet !> Study")
applied, is_valid, complete = find_transitives(puzzle)
print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
print(puzzle.print_grid())
assert (applied, is_valid, complete) == (True, True, False)

# A !> B and B -> C, , but can't reject A to C => contradiction
puzzle = Puzzle([suspects, weapons, rooms, time])
apply_not(puzzle, [suspects, "Scarlet", time, "1:00"])
apply_is(puzzle, [time, "1:00", rooms, "Study"])
apply_is(puzzle, [suspects, "Scarlet", rooms, "Study"])
print(puzzle.print_grid())

print("Scarlet !> 1:00 and 1:00 -> Study, but Scarlet -> Study => contradiction")
applied, is_valid, complete = find_transitives(puzzle)
print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
print(puzzle.print_grid())
assert (applied, is_valid, complete) == (False, False, False)

# A !> B and A -> C so B !> C
puzzle = Puzzle([suspects, weapons, rooms, time])
apply_not(puzzle, [suspects, "Scarlet", time, "1:00"])
apply_is(puzzle, [suspects, "Scarlet", rooms, "Study"])
print(puzzle.print_grid())

print("Scarlet !> 1:00 and Scarlet -> Study so 1:00 !> Study")
applied, is_valid, complete = find_transitives(puzzle)
print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
print(puzzle.print_grid())
assert (applied, is_valid, complete) == (True, True, False)

# A !> B and A -> C so B !> C, but can't reject B to C => contradiction
puzzle = Puzzle([suspects, weapons, rooms, time])
apply_not(puzzle, [suspects, "Scarlet", time, "1:00"])
apply_is(puzzle, [suspects, "Scarlet", rooms, "Study"])
apply_is(puzzle, [time, "1:00", rooms, "Study"])
print(puzzle.print_grid())

print("Scarlet !> 1:00 and Scarlet -> Study, but 1:00 -> Study => contradiction")
applied, is_valid, complete = find_transitives(puzzle)
print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
print(puzzle.print_grid())
assert (applied, is_valid, complete) == (False, False, False)

# A and B don't share any possibilities; A !> B
puzzle = Puzzle([suspects, weapons, rooms, time])
apply_not(puzzle, [suspects, "Scarlet", time, "1:00"])
apply_not(puzzle, [suspects, "Scarlet", time, "2:00"])
apply_not(puzzle, [weapons, "Rope", time, "3:00"])
apply_not(puzzle, [weapons, "Rope", time, "4:00"])

print(puzzle.print_grid())

## Neither Scarlet nor Rope has a O time
print("Scarlet and Rope don't share any compatible times, so Scarlet !> Rope")
applied, is_valid, complete = find_transitives(puzzle)
print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
print(puzzle.print_grid())
assert (applied, is_valid, complete) == (True, True, False)

# Wrench has a O time and Scarlet can't go to that time.
apply_is(weapons, "Wrench", time, "1:00")
print(puzzle.print_grid())

print("Scarlet and Wrench don't share any compatible times, so Scarlet !> Wrench")
applied, is_valid, complete = find_transitives(puzzle)
print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
print(puzzle.print_grid())
assert (applied, is_valid, complete) == (True, True, False)


# %% colab={"base_uri": "https://localhost:8080/", "height": 143} id="suJQHIxpSFEZ" outputId="0f9190cf-07af-4e22-8006-46fc71cde693"
# If a row/column has 1 * and the rest are X then fill out a O there.
# If a row/column is all X then contradiction.
def find_openings(puzzle):
  applied = False
  complete = False
  is_valid = True
  # For every combination of categories:
  for cat1 in puzzle.categories:
    for cat2 in puzzle.categories:
      grid = puzzle.get_grid(cat1, cat2)
      if grid != None:
        # For each row:
        for i, row in enumerate(grid):
          blanks = [i for i in range(len(row)) if row[i] == "*"]
          # If there is only 1 blank value:
          if len(blanks) == 1:
            ent1 = cat1.entities[blanks[0]]
            ent2 = cat2.entities[i]
            applied = True
            # Answer it as 0.
            puzzle.answer(cat1, cat2, ent1, ent2, "O")
            is_valid = cross_out(puzzle, cat1, cat2, ent1, ent2)
            if not is_valid:
              return applied, is_valid, complete
          # Check if all values are X
          truths = [i for i in range(len(row)) if row[i] == "O"]
          if len(blanks) == 0 and len(truths) == 0:
            # There are no openings! Contradiction
            is_valid = False
            return applied, is_valid, complete
        # For each column:
        for j in range(len(grid[0])):
          blanks = [i for i in range(len(grid)) if grid[i][j] == "*"]
          # If there is only one blank value:
          if len(blanks) == 1:
            ent1 = cat1.entities[j]
            ent2 = cat2.entities[blanks[0]]
            applied = True
            # Answer it as 0.
            puzzle.answer(cat1, cat2, ent1, ent2, "O")
            is_valid = cross_out(puzzle, cat1, cat2, ent1, ent2)
            if not is_valid:
              return applied, is_valid, complete
          # Check if all values are X
          truths = [i for i in range(len(grid)) if grid[i][j] == "O"]
          if len(blanks) == 0 and len(truths) == 0:
            # There are no openings! Contradiction
            is_valid = False
            return applied, is_valid, complete
        
  return applied, is_valid, complete


# %%
# Test find_openings
if __name__ == "__main__": 
  puzzle = Puzzle([suspects, weapons, rooms, time])
  print(puzzle.print_grid())

  print("Set up find openings")
  apply_not(puzzle, [suspects, "Scarlet", time, "1:00"])
  apply_not(puzzle, [suspects, "Scarlet", time, "4:00"])
  apply_not(puzzle, [weapons, "Knife", time, "1:00"])
  apply_not(puzzle, [weapons, "Rope", time, "1:00"])
  print(puzzle.print_grid())

  # Find openings when there are no openings
  print("Find openings when there are no openings")
  applied, is_valid, complete = find_openings(puzzle)
  assert (applied, is_valid, complete) == (False, True, False)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())

  # There is an opening in a column
  print("Set Mustard to 2:00")
  apply_is(puzzle, [suspects, "Mustard", time, "2:00"])
  print(puzzle.print_grid())
  print("Find an opening in a column")
  applied, is_valid, complete = find_openings(puzzle)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (True, True, False)

  # There is an opening in a row
  print("Set Wrench to 3:00")
  apply_is(puzzle, [weapons, "Wrench", time, "3:00"])
  print(puzzle.print_grid())
  print("Find an opening in a row")
  applied, is_valid, complete = find_openings(puzzle)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (True, True, False)

  # There is a row of all X => contradiction
  print("Set row to all X => contradiction")
  puzzle = Puzzle([suspects, weapons, rooms, time])
  apply_not(puzzle, [suspects, "Scarlet", time, "1:00"])
  apply_not(puzzle, [suspects, "White", time, "1:00"])
  apply_not(puzzle, [suspects, "Mustard", time, "1:00"])
  apply_not(puzzle, [suspects, "Plum", time, "1:00"])
  applied, is_valid, complete = find_openings(puzzle)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (False, False, False)

  # There is a column of all X => contradiction
  print("Set col to all X => contradiction")
  puzzle = Puzzle([suspects, weapons, rooms, time])
  apply_not(puzzle, [suspects, "Scarlet", time, "1:00"])
  apply_not(puzzle, [suspects, "Scarlet", time, "2:00"])
  apply_not(puzzle, [suspects, "Scarlet", time, "3:00"])
  apply_not(puzzle, [suspects, "Scarlet", time, "4:00"])
  applied, is_valid, complete = find_openings(puzzle)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (False, False, False)


# %% colab={"base_uri": "https://localhost:8080/", "height": 143} id="suJQHIxpSFEZ" outputId="0f9190cf-07af-4e22-8006-46fc71cde693"
def apply_is(puzzle, terms):
  """
  Apply the is rule to puzzle, will always complete in one step
  return: applied, is_valid, complete
  """
  applied = False
  is_valid = True
  complete = True # this rule can only be applied once
  cat1 = terms[0]
  ent1 = terms[1]
  cat2 = terms[2]
  ent2 = terms[3]

  current_term = puzzle.get_symbol(cat1, cat2, ent1, ent2)

  if current_term == "*":
    applied = True
    puzzle.answer(cat1, cat2, ent1, ent2, "O")
    is_valid = cross_out(puzzle, cat1, cat2, ent1, ent2)

  elif current_term == "X":
    # something logic error occured
    is_valid = False
    applied = False

  elif current_term == "O":
    # someone already answered
    applied = False

  return applied, is_valid, complete


# %%
# Test is
if __name__ == "__main__": 
  puzzle = Puzzle([suspects, weapons, rooms, time])
  print(puzzle.print_grid())

  # Apply when it is still blank
  print("Testing IS")
  print("New IS: Scarlet IS Knife")
  terms = [suspects, "Scarlet", weapons, "Knife"]
  applied, is_valid, complete = apply_is(puzzle, terms)
  assert (applied, is_valid, complete) == (True, True, True)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())

  # Skip when it has already been answered O
  print("PreAnswered: Scarlet IS Knife")
  applied, is_valid, complete = apply_is(puzzle, terms)
  assert (applied, is_valid, complete) == (False, True, True)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())

  # Contradiction when it has already been answered X
  print("Contradiction: Scarlet IS Rope")
  terms[3] = "Rope"
  applied, is_valid, complete = apply_is(puzzle, terms)
  assert (applied, is_valid, complete) == (False, False, True)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())


# %% colab={"base_uri": "https://localhost:8080/", "height": 143} id="suJQHIxpSFEZ" outputId="0f9190cf-07af-4e22-8006-46fc71cde693"
def apply_not(puzzle, terms):
  """
  Apply the not rule to puzzle, will always complete in one step
  return: applied, is_valid, complete
  """
  applied = False
  is_valid = True
  complete = True # this rule can only be applied once
  cat1 = terms[0]
  ent1 = terms[1]
  cat2 = terms[2]
  ent2 = terms[3]

  current_term = puzzle.get_symbol(cat1, cat2, ent1, ent2)

  if current_term == "*":
    puzzle.answer(cat1, cat2, ent1, ent2, "X")
    applied = True
  elif current_term == "O":
    applied = False
    is_valid = False
  elif current_term == "X":
    applied = False

  return applied, is_valid, complete


# %%
# Test not
if __name__ == "__main__": 
  puzzle = Puzzle([suspects, weapons, rooms, time])
  print(puzzle.print_grid())

  terms = [suspects, "Scarlet", weapons, "Knife"]

  # Apply when it is still blank
  print("Testing NOT")
  print("New NOT: Scarlet NOT Knife")
  applied, is_valid, complete = apply_not(puzzle, terms)
  assert (applied, is_valid, complete) == (True, True, True)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())

  # Skip when it has already been answered O
  print("PreAnswered: Scarlet NOT Knife")
  applied, is_valid, complete = apply_not(puzzle, terms)
  assert (applied, is_valid, complete) == (False, True, True)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())

  # Contradiction when it has already been answered X
  print("Set Plum is Knife")
  terms[1] = "Plum"
  apply_is(puzzle, terms)
  print("Contradiction: Plum NOT Knife")
  applied, is_valid, complete = apply_not(puzzle, terms)
  assert (applied, is_valid, complete) == (False, False, True)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())


# %% colab={"base_uri": "https://localhost:8080/", "height": 143} id="suJQHIxpSFEZ" outputId="0f9190cf-07af-4e22-8006-46fc71cde693"
def apply_before(puzzle, terms):
  """
  apply the before rule to the puzzle
  """
  applied = False
  complete = False
  is_valid = True
  numbered = len(terms) == 6

  bef_cat = terms[0]
  bef_ent = terms[1] # bef entity is before aft_ent
  aft_cat = terms[2]
  aft_ent = terms[3]

  num_cat = terms[4]

  num = 1
  if numbered:
    num = terms[5]

  # If A < B and A, B are not in the same category, then A is not B.
  if bef_cat != aft_cat:
    sy = puzzle.get_symbol(bef_cat, aft_cat, bef_ent, aft_ent)
    if sy == "*":
      applied = True
      puzzle.answer(bef_cat, aft_cat, bef_ent, aft_ent, "X")
    elif sy == "O":
      # Contradiction
      complete = True
      is_valid = False
      return applied, is_valid, complete

  # Get all the current symbols for the two entities in the num category
  before_symbols = [puzzle.get_symbol(bef_cat, num_cat, bef_ent, ent) for ent in num_cat.entities]
  after_symbols = [puzzle.get_symbol(aft_cat, num_cat, aft_ent, ent) for ent in num_cat.entities]

  # Narrow down possiblities with no information for entities yet
  # The before entity can't be in the last num spots (or there won't be room for the after entity)
  for i in range(len(before_symbols) - num, len(before_symbols)):
    sy = puzzle.get_symbol(bef_cat, num_cat, bef_ent, num_cat.entities[i])
    if sy == "*":
      applied = True
      puzzle.answer(bef_cat, num_cat, bef_ent, num_cat.entities[i], "X")
    elif sy == "O":
      complete = True
      is_valid = False
      return applied, is_valid, complete
  # And the inverse is true for the after entity
  for i in range(0, num):
    sy = puzzle.get_symbol(aft_cat, num_cat, aft_ent, num_cat.entities[i])
    if sy == "*":
      applied = True
      puzzle.answer(aft_cat, num_cat, aft_ent, num_cat.entities[i], "X")
    elif sy == "O":
      complete = True
      is_valid = False
      return applied, is_valid, complete

  # if both entities have answer, we can determine if this rule valid
  if "O" in before_symbols and "O" in after_symbols:
    applied = False
    complete = True
    if numbered:
      is_valid = after_symbols.index("O") - before_symbols.index("O") == num
    else:
      is_valid = before_symbols.index("O") < after_symbols.index("O")
    return applied, is_valid, complete

  # determine the possible after entities if the before entity is solved
  if "O" in before_symbols:
    bef_index = before_symbols.index("O")
    if numbered:
      if after_symbols[bef_index + num] == "*":
        pos_aft_index = [bef_index + num]
      else:
        pos_aft_index = []
    else:
      pos_aft_index = [i for i in list(range(bef_index, len(after_symbols))) if after_symbols[i] == "*"]

    if len(pos_aft_index) == 0:
      complete = True
      is_valid = False
      return applied, is_valid, complete
    elif len(pos_aft_index) == 1:
      complete = True
      aft_index = pos_aft_index[0]
      applied = True
      puzzle.answer(aft_cat, num_cat, aft_ent, num_cat.entities[aft_index], "O")
      is_valid = cross_out(puzzle, aft_cat, num_cat, aft_ent, num_cat.entities[aft_index])
      if not is_valid:
        return applied, is_valid, complete
    else:
      for i in range(0, bef_index):
        sy = puzzle.get_symbol(aft_cat, num_cat, aft_ent, num_cat.entities[i])
        if sy == "*":
          applied = True
          puzzle.answer(aft_cat, num_cat, aft_ent, num_cat.entities[i], "X")
        elif sy == "O":
          complete = True
          is_valid = False
          return applied, is_valid, complete

  # determine the possible after entities if the after before is solved
  if "O" in after_symbols:
    aft_index = after_symbols.index("O")
    if numbered:
      if before_symbols[aft_index - num] == "*":
        pos_bef_index =  [aft_index - num]
      else:
        pos_bef_index = []
    else:
      pos_bef_index = [i for i in list(range(0, aft_index)) if before_symbols[i] == "*"]

    if len(pos_bef_index) == 0:
      complete = True
      is_valid = False
      return applied, is_valid, complete
    elif len(pos_bef_index) == 1:
      complete = True
      bef_index = pos_bef_index[0]
      applied = True
      puzzle.answer(bef_cat, num_cat, bef_ent, num_cat.entities[bef_index], "O")
      is_valid = cross_out(puzzle, bef_cat, num_cat, bef_ent, num_cat.entities[bef_index])
      if not is_valid:
        return applied, is_valid, complete
    else:
      for i in range(aft_index, len(before_symbols)):
        sy = puzzle.get_symbol(bef_cat, num_cat, bef_ent, num_cat.entities[i])
        if sy == "*":
          applied = True
          puzzle.answer(bef_cat, num_cat, bef_ent, num_cat.entities[i], "X")
        elif sy == "O":
          complete = True
          is_valid = False
          return applied, is_valid, complete

  # Determine possible answers with constraints on either entity
  if "X" in before_symbols or "X" in after_symbols:
    if numbered:
      # All Xs for the before entity where the index is valid (i+num exists).
      before_Xs = [i for i in range(len(before_symbols)) if before_symbols[i] == "X" and i+num < len(before_symbols) - 1]
      # All Xs for the after entity where the index is valid (i-num exists).
      after_Xs = [i for i in range(len(after_symbols)) if after_symbols[i] == "X" and i-num > -1]
      
      # For a position to be a valid answer, the corresponding position +/- num must be valid for the other entity
      for i in before_Xs:
        sy = puzzle.get_symbol(aft_cat, num_cat, aft_ent, num_cat.entities[i+num])
        if sy == "*":
          applied = True
          puzzle.answer(aft_cat, num_cat, aft_ent, num_cat.entities[i+num], "X")
      for i in after_Xs:
        sy = puzzle.get_symbol(bef_cat, num_cat, bef_ent, num_cat.entities[i-num])
        if sy == "*":
          applied = True
          puzzle.answer(bef_cat, num_cat, bef_ent, num_cat.entities[i-num], "X")

    # A streak of Xs at the beginning/end forces the first available position for the other entity to shift.
    for i in range(len(before_symbols) - 1):
      if before_symbols[i] != "X":
        break
      sy = puzzle.get_symbol(aft_cat, num_cat, aft_ent, num_cat.entities[i+1])
      if sy == "*":
        applied = True
        puzzle.answer(aft_cat, num_cat, aft_ent, num_cat.entities[i+1], "X")

    for i in range(len(after_symbols) - 1, 1, -1):
      if after_symbols[i] != "X":
        break
      sy = puzzle.get_symbol(bef_cat, num_cat, bef_ent, num_cat.entities[i-1])
      if sy == "*":
        applied = True
        puzzle.answer(bef_cat, num_cat, bef_ent, num_cat.entities[i-1], "X")
  return applied, is_valid, complete


# %%
# Test before
if __name__ == "__main__": 
  print("Testing simple BEFORE")
  puzzle = Puzzle([suspects, weapons, rooms, time])
  print(puzzle.print_grid())
  terms = [suspects, "Scarlet", suspects, "White", time]

  # No current information; simple before
  print("Scarlet BEFORE White")
  applied, is_valid, complete = apply_before(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  assert (applied, is_valid, complete) == (True, True, False)
  print(puzzle.print_grid())

  # Additional constraint on After's time
  print("White NOT 4:00 => Scarlet NOT 3:00")
  apply_not(puzzle, [suspects, "White", time, "4:00"])
  applied, is_valid, complete = apply_before(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (True, True, False)

  # After is set
  print("White IS 2:00 => Scarlet IS 1:00; finished hint")
  apply_is(puzzle, [suspects, "White", time, "2:00"])
  applied, is_valid, complete = apply_before(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (True, True, True)

  # Already satisfied
  print("Already satisfied; no further changes")
  applied, is_valid, complete = apply_before(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (False, True, True)

  # Constraints on both
  print("Mustard BEFORE Plum => narrow down both")
  terms[1] = "Mustard"
  terms[3] = "Plum"
  applied, is_valid, complete = apply_before(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (True, True, False)

  # Single answer
  print("Plum IS 4:00 => Mustard IS 3:00")
  apply_is(puzzle, [suspects, "Plum", time, "4:00"])
  applied, is_valid, complete = apply_before(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (True, True, True)

  print("Candle Stick IS 3:00 and Candle Stick BEFORE Rope => Rope IS 4:00")
  apply_is(puzzle, [weapons, "Candle Stick", time, "3:00"])
  applied, is_valid, complete = apply_before(puzzle, [weapons, "Candle Stick", weapons, "Rope", time])
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (True, True, True)

  # Reset puzzle
  puzzle = Puzzle([suspects, weapons, rooms, time])
  print(puzzle.print_grid())

  # Constraint on Before's time.
  print("Knife before Rope; Knife NOT 1:00 => Rope NOT 2:00")
  terms = [weapons, "Knife", weapons, "Rope", time]
  apply_not(puzzle, [weapons, "Knife", time, "1:00"])
  applied, is_valid, complete = apply_before(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (True, True, False)

  # Simple contradiction
  print("Candle is 3:00 and Wrench is 2:00; Candle BEFORE Wrench is contradictory")
  apply_is(puzzle, [weapons, "Candle Stick", time, "3:00"])
  apply_is(puzzle, [weapons, "Wrench", time, "2:00"])
  applied, is_valid, complete = apply_before(puzzle, [weapons, "Candle Stick", weapons, "Wrench", time])
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (False, False, True)

  # If A and B are not in the same category, A is not B
  print("White is before Ballroom, so White is not Ballroom")
  applied, is_valid, complete = apply_before(puzzle, [suspects, "White", rooms, "Ball room", time])
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (True, True, False)

  # Contradiction for before O
  print("Kitchen IS 4:00, so Kitchen before Study contradicts")
  apply_is(puzzle, [rooms, "Kitchen", time, "4:00"])
  applied, is_valid, complete = apply_before(puzzle, [rooms, "Kitchen", rooms, "Study", time])
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (False, False, True)

  # Contradiction for after 0
  print("Living room IS 1:00, so Study before Living room contradicts")
  apply_is(puzzle, [rooms, "Living Room", time, "1:00"])
  applied, is_valid, complete = apply_before(puzzle, [rooms, "Study", rooms, "Living Room", time])
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (False, False, True)

  # Numerical or tests
  print("Test numbered BEFORE")
  puzzle = Puzzle([suspects, weapons, rooms, time])
  print(puzzle.print_grid())
  terms = [suspects, "Scarlet", suspects, "White", time, 2]

  # No current info, numbered
  print("Scarlet 2 BEFORE White")
  applied, is_valid, complete = apply_before(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  assert (applied, is_valid, complete) == (True, True, False)
  print(puzzle.print_grid())

  # Before entity has X
  print("Scarlet NOT 1:00 and Scarlet 2 BEFORE White")
  apply_not(puzzle, [suspects, "Scarlet", time, "1:00"])
  applied, is_valid, complete = apply_before(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  assert (applied, is_valid, complete) == (True, True, False)
  print(puzzle.print_grid())

  # Before entity is set
  print("Scarlet IS 2:00 and Scarlet 2 BEFORE White")
  apply_is(puzzle, [suspects, "Scarlet", time, "2:00"])
  applied, is_valid, complete = apply_before(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  assert (applied, is_valid, complete) == (True, True, True)
  print(puzzle.print_grid())

  # After entity has X
  terms[1] = "Mustard"
  terms[3] = "Plum"
  print("Plum NOT 4:00 and Mustard 2 before Plum")
  apply_not(puzzle, [suspects, "Plum", time, "4:00"])
  applied, is_valid, complete = apply_before(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  assert (applied, is_valid, complete) == (True, True, False)
  print(puzzle.print_grid())

  # After entity is set
  print("Plum IS 3:00 and Mustard 2 before Plum")
  apply_is(puzzle, [suspects, "Plum", time, "3:00"])
  applied, is_valid, complete = apply_before(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  assert (applied, is_valid, complete) == (True, True, True)
  print(puzzle.print_grid())

  # Both set, ok
  print("Both set; Mustard 2 before Plum")
  applied, is_valid, complete = apply_before(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  assert (applied, is_valid, complete) == (False, True, True)
  print(puzzle.print_grid())

  # Before set, contradiction
  print("Knife IS 2:00; Rope NOT 4:00; Knife 2 before Rope => contradiction")
  terms = [weapons, "Knife", weapons, "Rope", time, 2]
  apply_is(puzzle, [weapons, "Knife", time, "2:00"])
  apply_not(puzzle, [weapons, "Rope", time, "4:00"])
  applied, is_valid, complete = apply_before(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (True, False, True)

  # After set, contradiction
  print("Wrench IS 3:00; Candle Stick NOT 1:00; Candle Stick 2 before Wrench => contradiction")
  terms[1] = "Candle Stick"
  terms[3] = "Wrench"
  apply_is(puzzle, [weapons, "Wrench", time, "3:00"])
  apply_not(puzzle, [weapons, "Candle Stick", time, "1:00"])
  applied, is_valid, complete = apply_before(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (True, False, True)

  # Both set, contradiction
  print("Kitchen IS 1:00, Study IS 2:00; Kitchen 2 before Study is contradictory")
  apply_is(puzzle, [rooms, "Kitchen", time, "1:00"])
  apply_is(puzzle, [rooms, "Study", time, "2:00"])
  applied, is_valid, complete = apply_before(puzzle, [rooms, "Kitchen", rooms, "Study", time, 2])
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (False, False, True)


# %% colab={"base_uri": "https://localhost:8080/", "height": 143} id="suJQHIxpSFEZ" outputId="0f9190cf-07af-4e22-8006-46fc71cde693"
def apply_simple_or(puzzle, terms):
  """
  Apply the or rule to puzzle, will be incomplete if not enough information is known
  return: applied, is_valid, complete
  """
  applied = False
  is_valid = True
  complete = False

  pos_cat1 = terms[0]
  pos_ent1 = terms[1] # either ent1 or ent2 = ans_ent
  pos_cat2 = terms[2]
  pos_ent2 = terms[3]

  ans_cat = terms[4]
  ans_ent = terms[5]

  if pos_cat1 != pos_cat2:
    # A and B are in different categories
    # If A or B is C then A is not B
    applied, is_valid, complete = apply_not(puzzle, [ pos_cat1, pos_ent1, pos_cat2, pos_ent2 ])
    if not is_valid:
      return applied, is_valid, complete
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
          return applied, is_valid, complete
        elif sy == "*":
          # No other entity from cat1 is ans_ent
          applied = True
          puzzle.answer(pos_cat1, ans_cat, ent, ans_ent, "X")

  pos_symb1 = puzzle.get_symbol(pos_cat1, ans_cat, pos_ent1, ans_ent)
  pos_symb2 = puzzle.get_symbol(pos_cat2, ans_cat, pos_ent2, ans_ent)

  if pos_symb1 == "*" and pos_symb2 == "*":
    # we can't apply hint yet (don't have enough information)
    complete = False
  elif pos_symb1 == pos_symb2:
    # this rule can't be applied (both are true or both are false)
    complete = True
    is_valid = False
    return applied, is_valid, complete
  elif pos_symb1 == "O":
    # hint says that ent2 cannot be the answer ent
    if pos_symb2 == "*":
      # we can change game state
      applied = True
      complete = True
      puzzle.answer(pos_cat2, ans_cat, pos_ent2, ans_ent, "X")
    elif pos_symb2 == "X":
      # game state is correct, but nothing to change
      complete = True
  elif pos_symb1 == "X":
    # hint says that ent2 must be the answer ent
    if pos_symb2 == "*":
      # we can change the game state
      applied = True
      complete = True
      puzzle.answer(pos_cat2, ans_cat, pos_ent2, ans_ent, "O")
      is_valid = cross_out(puzzle, pos_cat2, ans_cat, pos_ent2, ans_ent)
      if not is_valid:
        return applied, is_valid, complete
    elif pos_symb2 == "O":
      # game state is correct, but we cannot change
      complete = True
  elif pos_symb1 == "*":
    if pos_symb2 == "O":
      # hint says ent1 is not ans_ent and we can change this
      applied = True
      complete = True
      puzzle.answer(pos_cat1, ans_cat, pos_ent1, ans_ent, "X")
    elif pos_symb2 == "X":
      # hint says ent1 is ans_ent and we can change this
      applied = True
      complete = True
      puzzle.answer(pos_cat1, ans_cat, pos_ent1, ans_ent, "O")
      is_valid = cross_out(puzzle, pos_cat1, ans_cat, pos_ent1, ans_ent)
      if not is_valid:
        return applied, is_valid, complete
  return applied, is_valid, complete


# %%
if __name__ == "__main__": 
  # Test simple or
  print("Testing simple OR")
  puzzle = Puzzle([suspects, weapons, rooms, time])
  print(puzzle.print_grid())

  # A and B in diff categories; no info
  terms = [suspects, "White", weapons, "Knife", rooms, "Study"]
  print("Either Mrs. White OR the Knife was in the Study => Mrs. White did NOT have the Knife")
  applied, is_valid, complete = apply_simple_or(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (True, True, False)

  # A and B in same category; no info
  terms = [rooms, "Kitchen", rooms, "Study", time, "1:00"]
  print("Either the Kitchen OR the Study was at 1:00 => no other room can be at 1:00")
  applied, is_valid, complete = apply_simple_or(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (True, True, False)

  # A and B in same category and a different item has the value.
  print("Knife was at 1:00 and Rope OR Wrench was at 1:00 => contradiction")
  apply_is(puzzle, [weapons, "Knife", time, "1:00"])
  terms = [weapons, "Rope", weapons, "Wrench", time, "1:00"]
  applied, is_valid, complete = apply_simple_or(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (False, False, True)

  # A and B are both true => contradiction
  print("White IS 2:00 and Rope IS 2:00; Either White OR Rope is 2:00 => contradiction")
  apply_is(puzzle, [suspects, "White", time, "2:00"])
  apply_is(puzzle, [weapons, "Rope", time, "2:00"])
  terms = [weapons, "Rope", suspects, "White", time, "2:00"]
  applied, is_valid, complete = apply_simple_or(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (True, False, True)

  terms = [suspects, "Scarlet", rooms, "Kitchen", weapons, "Knife"]
  # A is O and B is * => Set B to X
  print("Scarlet has the Knife and either Scarlet OR Kitchen has the Knife => Kitchen does not have the Knife")
  puzzle = Puzzle([suspects, weapons, rooms, time])
  apply_is(puzzle, [suspects, "Scarlet", weapons, "Knife"])
  applied, is_valid, complete = apply_simple_or(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (True, True, True)

  # A is O and B is X => ok
  print("Scarlet or Kitchen has the Knife; already applied")
  applied, is_valid, complete = apply_simple_or(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (False, True, True)

  # A is X and B is * => Set B to O
  puzzle = Puzzle([suspects, weapons, rooms, time])
  print("Scarlet does not have the Knife and either Scarlet OR Kitchen has the Knife => Kitchen has the Knife")
  puzzle = Puzzle([suspects, weapons, rooms, time])
  apply_not(puzzle, [suspects, "Scarlet", weapons, "Knife"])
  applied, is_valid, complete = apply_simple_or(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (True, True, True)

  # A is X and B is O => ok
  print("Scarlet or Kitchen has the Knife; already applied")
  applied, is_valid, complete = apply_simple_or(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (False, True, True)

  # A is * and B is X => Set A to O
  puzzle = Puzzle([suspects, weapons, rooms, time])
  print("Kitchen does not have the Knife and either Scarlet OR Kitchen has the Knife => Scarlet has the Knife")
  puzzle = Puzzle([suspects, weapons, rooms, time])
  apply_not(puzzle, [rooms, "Kitchen", weapons, "Knife"])
  applied, is_valid, complete = apply_simple_or(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (True, True, True)

  # A is * and B is O => Set A to X
  puzzle = Puzzle([suspects, weapons, rooms, time])
  print("Kitchen has the Knife and either Scarlet OR Kitchen has the Knife => Scarlet does not have the Knife")
  puzzle = Puzzle([suspects, weapons, rooms, time])
  apply_is(puzzle, [rooms, "Kitchen", weapons, "Knife"])
  applied, is_valid, complete = apply_simple_or(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (True, True, True)


# %% colab={"base_uri": "https://localhost:8080/", "height": 143} id="suJQHIxpSFEZ" outputId="0f9190cf-07af-4e22-8006-46fc71cde693"
def apply_compound_or(puzzle, options):
  """
  Apply the compound or rule to puzzle, will be incomplete if not enough information is known
  return: applied, is_valid, complete
  """
  applied = False
  complete = False
  is_valid = True

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

  if currentA == currentB:
    if currentA != "*":
      # Both can't be true or false, something has gone wrong.
      is_valid = False
      complete = True
    # There is no info to apply.
    return applied, is_valid, complete

  # At least one term is answered; the hint is guaranteed complete.
  complete = True

  currents = [currentA, currentB]
  if "X" in currents and "O" in currents:
    # Someone already answered.
    return applied, is_valid, complete

  # One is answered and the other is not; we are guaranteed to apply.
  applied = True
  
  if currentA == "X":
    puzzle.answer(catB1, catB2, entB1, entB2, "O")
    is_valid = cross_out(puzzle, catB1, catB2, entB1, entB2)
  elif currentB == "X":
    puzzle.answer(catA1, catA2, entA1, entA2, "O")
    is_valid = cross_out(puzzle, catA1, catA2, entA1, entA2)
  elif currentA == "O":
    puzzle.answer(catB1, catB2, entB1, entB2, "X")
  elif currentB == "O":
    puzzle.answer(catA1, catA2, entA1, entA2, "X")

  return applied, is_valid, complete


# %%
if __name__ == "__main__": 
  # Test compound or
  print("Testing compound OR")
  puzzle = Puzzle([suspects, weapons, rooms, time])
  print(puzzle.print_grid())
  terms = [[suspects, "White", rooms, "Kitchen"], [weapons, "Knife", time, "2:00"]]

  # No info
  print("Either White is in the Kitchen OR the Knife is at 2:00; no info")
  applied, is_valid, complete = apply_compound_or(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (False, True, False)

  # A and B are both true => contradiction
  print("White IS Kitchen and Knife IS 2:00; Either White is in the Kitchen OR the Knife is at 2:00 => contradiction")
  apply_is(puzzle, [suspects, "White", rooms, "Kitchen"])
  apply_is(puzzle, [weapons, "Knife", time, "2:00"])
  applied, is_valid, complete = apply_compound_or(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (False, False, True)

  # A is O and B is * => Set B to X
  puzzle = Puzzle([suspects, weapons, rooms, time])
  print("White IS Kitchen; Either White is in the Kitchen OR the Knife is at 2:00 => Knife is not 2:00")
  apply_is(puzzle, [suspects, "White", rooms, "Kitchen"])
  applied, is_valid, complete = apply_compound_or(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (True, True, True)

  # A is O and B is X => ok
  print("Either White is in the Kitchen OR the Knife is at 2:00; already applied")
  apply_is(puzzle, [suspects, "White", rooms, "Kitchen"])
  applied, is_valid, complete = apply_compound_or(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (False, True, True)

  # A is X and B is * => Set B to O
  puzzle = Puzzle([suspects, weapons, rooms, time])
  print("White is NOT Kitchen; Either White is in the Kitchen OR the Knife is at 2:00 => Knife is 2:00")
  apply_not(puzzle, [suspects, "White", rooms, "Kitchen"])
  applied, is_valid, complete = apply_compound_or(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (True, True, True)

  # A is * and B is O => Set A to X
  puzzle = Puzzle([suspects, weapons, rooms, time])
  print("Knife is 2:00; Either White is in the Kitchen OR the Knife is at 2:00 => White is not in the Kitchen")
  apply_is(puzzle, [weapons, "Knife", time, "2:00"])
  applied, is_valid, complete = apply_compound_or(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (True, True, True)

  # A is * and B is X => Set A to O
  puzzle = Puzzle([suspects, weapons, rooms, time])
  print("Knife is not 2:00; Either White is in the Kitchen OR the Knife is at 2:00 => White is in the Kitchen")
  apply_not(puzzle, [weapons, "Knife", time, "2:00"])
  applied, is_valid, complete = apply_compound_or(puzzle, terms)
  print("(Applied, Is Valid, Complete): ", (applied, is_valid, complete))
  print(puzzle.print_grid())
  assert (applied, is_valid, complete) == (True, True, True)


# %% colab={"base_uri": "https://localhost:8080/", "height": 143} id="suJQHIxpSFEZ" outputId="0f9190cf-07af-4e22-8006-46fc71cde693"
def apply_hint(puzzle, hint):
  """
   Given a hint dictionary and a puzzle, apply next step of the hint to the puzzle

   return:
    applied  = whether the hint changed the state
    complete = whether the hint has no more information to offer
    is_valid = whether the hint contradicts the current state
  """

  applied = False
  complete = False
  is_valid = True

  rule = list(hint.keys())[0]
  terms = hint[rule]
  if rule == "simple_hint":
    rule = list(hint.keys())[0]
  if rule == "is":
    return apply_is(puzzle, terms)
  elif rule == "not":
    return apply_not(puzzle, terms[0]["is"])
  elif rule == "before":
    return apply_before(puzzle, terms)
  elif rule == "simple_or":
    return apply_simple_or(puzzle, terms)
  elif rule == "compound_or":
    return apply_compound_or(puzzle, [terms[0]["is"], terms[1]["is"]])
  else:
    print("This hint has no apply rules! Something has gone horribly wrong. The offending hint: " + str_hint(hint))

  return applied, is_valid, complete


# %% colab={"base_uri": "https://localhost:8080/"} id="cIlFA0mXSH5R" outputId="274d1a0b-cd33-4b36-c0eb-6214b679cec5"
# apply some randomly generated hints and print results

if __name__ == "__main__": 
  puzzle = Puzzle([suspects, weapons, rooms, time])
  print(puzzle.print_grid())

  for i in range(30):
    hint = generate_hint(puzzle)
    print("Hint: ", str_hint(hint))
    print("(Applied, Is Valid, Complete)")
    applied, is_valid, complete = apply_hint(puzzle, hint)
    print("Apply: ", (applied, is_valid, complete))
    if applied:
      print("Openings: ", find_openings(puzzle))
      print("Transitives: ", find_transitives(puzzle))
    print(puzzle.print_grid())

