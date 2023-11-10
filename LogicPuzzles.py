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

# %% colab={"base_uri": "https://localhost:8080/"} id="u9fPlqt1JIrO" outputId="046eb385-7b0d-4f86-ed8d-ccf802682a2d"
# !pip install parsimonious

# %% id="AzB0GRIux4lQ"
# Imports for DAAAYS
import itertools
#from parsimonious.grammar import Grammar
#from parsimonious.nodes import NodeVisitor
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
      relations[cat2.title]["true"] = None
      relations[cat2.title]["false"] = []
      relations[cat2.title]["nil"] = []
      if cat2 != category:
        if self._to_key(category, cat2) in self.grids:
          grid = self.grids[self._to_key(category, cat2)]
          answers = [grid[i][index] for i in range(len(grid))]

        elif self._to_key(cat2, category) in self.grids:
          grid = self.grids[self._to_key(cat2, category)]
          answers = grid[index]

        for i, val in enumerate(answers):
          if val == "0":
            relations[cat2.title]["true"] = cat2.entities[i]
          elif val == "X":
            relations[cat2.title]["false"].append(cat2.entities[i])
          else:
            relations[cat2.title]["nil"].append(cat2.entities[i])
        if "O" in answers:
            relations[cat2.title] = cat2.entities[answers.index("O")]

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
def find_contradictions(puzzle):
  return

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

# If A is B and B is C then A is C
# If A is B and B is not C then A is not C
def find_transitives(puzzle):
  applied = False
  complete = False
  is_valid = True
  # For every pair of related entities:
  #   check all other category relations for X and 0
  #   fill in accordingly
  for catA in puzzle.categories:
    for entA in catA.entities:
      entA_relations = puzzle.get_known_relations(catA, entA)
      for catB, catB_relations in enumerate(entA_relations):
        entB = catB_relations["true"]
        if entB != None:
          entB_relations = puzzle.get_known_relations(catB, entB)
          for catC, catC_relations in enumerate(entB_relations):
            entC = catC_relations["true"]
            if entC != None:
              sy = puzzle.get_symbol(catA, entA, catC, entC)
              if sy == "*":
                applied = True
                puzzle.answer(catA, entA, catC, entC, "O")
                is_valid = cross_out(puzzle, catA, catC, entA, entC)
              elif sy == "X":
                # Can't link A to C
                is_valid = False
            for entC in catC_relations["false"]:
              sy = puzzle.get_symbol(catA, entA, catC, entC)
              if sy == "*":
                applied = True
                puzzle.answer(catA, entA, catC, entC, "X")
              elif sy == "O":
                # Can't reject A to C
                is_valid = False
          for catC, catC_relations in enumerate(entA_relations):
            entC = catC_relations["true"]
            if entC != None:
              sy = puzzle.get_symbol(catB, entB, catC, entC)
              if sy == "*":
                applied = True
                puzzle.answer(catB, entB, catC, entC, "O")
                is_valid = cross_out(puzzle, catB, catC, entB, entC)
              elif sy == "X":
                # Can't link A to C
                is_valid = False
            for entC in catC_relations["false"]:
              sy = puzzle.get_symbol(catB, entB, catC, entC)
              if sy == "*":
                applied = True
                puzzle.answer(catB, entB, catC, entC, "X")
              elif sy == "O":
                # Can't reject A to C
                is_valid = False
  return applied, is_valid, complete

# If a row/column has 1 * and the rest are X then fill out a O there.
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
            ent2 = cat2[i]
            applied = True
            # Answer it as 0.
            puzzle.answer(cat1, ent1, cat2, ent2, "0")
            is_valid = cross_out(puzzle, cat1, cat2, ent1, ent2)
        # For each column:
        for j in range(len(grid[0])):
          blanks = [i for i in range(len(grid)) if grid[i][j] == "*"]
          # If there is only one blank value:
          if len(blanks) == 1:
            ent1 = cat1[j]
            ent2 = cat2[blanks[0]]
            applied = True
            # Answer it as 0.
            puzzle.answer(cat1, ent1, cat2, ent2, "0")
            is_valid = cross_out(puzzle, cat1, cat2, ent1, ent2)
        
  return applied, is_valid, complete

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

def apply_before(puzzle, terms):
  """
  apply the before rule to the puzzle

  Not fully implemented!
  """
  applied = False
  complete = False
  is_valid = True
  numbered = len(terms) == 6

  bef_cat = terms[0]
  bef_ent = terms[1] # bef entity is before the after entity
  aft_cat = terms[2]
  aft_ent = terms[3]

  num_cat = terms[4]

  num = 1
  if numbered:
    num = terms[5]

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
  # And the inverse is true for the after entity
  for i in range(0, num):
    sy = puzzle.get_symbol(aft_cat, num_cat, aft_ent, num_cat.entities[i])
    if sy == "*":
      applied = True
      puzzle.answer(aft_cat, num_cat, aft_ent, num_cat.entities[i], "X")
    elif sy == "O":
      complete = True
      is_valid = False

  # if both entities have answer, we can deterimine if this rule valid
  if "O" in before_symbols and "O" in after_symbols:
    applied = False
    if numbered:
      is_valid = after_symbols.index("O") - before_symbols.index("O") == num
    else:
      is_valid = before_symbols.index("O") < after_symbols.index("O")

  # determine the possible after entities if the before entity is solved
  if "O" in before_symbols:
    bef_index = before_symbols.index("O")
    if numbered:
      if after_symbols[bef_index + num] == "*":
        pos_aft_index =  [bef_index + num]
      else:
        pos_aft_index = []
    else:
      pos_aft_index = [i for i in list(range(bef_index, len(after_symbols))) if after_symbols[i] == "*"]

    if len(pos_aft_index) == 0:
      complete = True
      is_valid = False
    elif len(pos_aft_index) == 1:
      complete = True
      aft_index = pos_aft_index[0]
      applied = True
      puzzle.answer(aft_cat, num_cat, aft_ent, num_cat.entities[aft_index], "O")
      is_valid = cross_out(puzzle, aft_cat, num_cat, aft_ent, num_cat.entities[aft_index])
    else:
      for i in range(0, bef_index):
        sy = puzzle.get_symbol(aft_cat, num_cat, aft_ent, num_cat.entities[i])
        if sy == "*":
          applied = True
          puzzle.answer(aft_cat, num_cat, aft_ent, num_cat.entities[i], "X")
        elif sy == "O":
          complete = True
          is_valid = False

  # determine the possible after entities if the after entity is solved
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
    elif len(pos_bef_index) == 1:
      complete = True
      bef_index = pos_bef_index[0]
      applied = True
      puzzle.answer(bef_cat, num_cat, bef_ent, num_cat.entities[bef_index], "O")
      is_valid = cross_out(puzzle, bef_cat, num_cat, bef_ent, num_cat.entities[bef_index])
    else:
      for i in range(aft_index, len(before_symbols)):
        sy = puzzle.get_symbol(bef_cat, num_cat, bef_ent, num_cat.entities[i])
        if sy == "*":
          applied = True
          puzzle.answer(bef_cat, num_cat, bef_ent, num_cat.entities[i], "X")
        elif sy == "O":
          complete = True
          is_valid = False

    if "X" in before_symbols or "X" in after_symbols:
      before_Xs = [i for i in range(len(before_symbols)) if before_symbols[i] == "X" and i+num < len(before_symbols) - 1]
      after_Xs = [i for i in range(len(after_symbols)) if after_symbols[i] == "X" and i-num > -1]

      if numbered:
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

      for i in range(len(before_symbols) - 1):
        if before_symbols[i] != "X":
          break
        sy = puzzle.get_symbol(bef_cat, num_cat, bef_ent, num_cat.entities[i-1])
        if sy == "*":
          applied = True
          puzzle.answer(aft_cat, num_cat, aft_ent, num_cat.entities[i-1], "X")
  return applied, is_valid, complete


def apply_simple_or(puzzle, terms):
  """
  Apply the or rule to puzzle, will be incomplete if not enough information is known
  return: applied, is_valid, complete
  """
  applied = False
  complete = False
  is_valid = True

  pos_cat1 = terms[0]
  pos_ent1 = terms[1] # either ent1 or ent2 = ans_ent
  pos_cat2 = terms[2]
  pos_ent2 = terms[3]

  ans_cat = terms[4]
  ans_ent = terms[5]

  pos_symb1 = puzzle.get_symbol(pos_cat1, ans_cat, pos_ent1, ans_ent)
  pos_symb2 = puzzle.get_symbol(pos_cat2, ans_cat, pos_ent2, ans_ent)

  if pos_symb1 == "*" and pos_symb2 == "*":
    # we can't apply hint yet (don't have enough information)
    applied = False
    complete = False
  elif pos_symb1 == pos_symb2:
    # this rule can't be applied (both are true or false)
    applied = False
    complete = False
    is_valid = False

  elif pos_symb1 == "O":
    # hint says that ent2 cannot be the answer ent
    if pos_symb2 == "*":
      # we can change game state
      applied = True
      complete = True
      is_valid = True
      puzzle.answer(pos_cat2, ans_cat, pos_ent2, ans_ent, "X")
    elif pos_symb2 == "X":
      # game state is correct, but nothing to change
      applied = False
      complete = True
      is_valid = True
  elif pos_symb1 == "X":
    # hint says that ent2 must be the answer ent
    if pos_symb2 == "*":
      # we can change the game state
      applied = True
      complete = True
      puzzle.answer(pos_cat2, ans_cat, pos_ent2, ans_ent, "O")
      is_valid = cross_out(puzzle, pos_cat2, ans_cat, pos_ent2, ans_ent)
    elif pos_symb2 == "O":
      # game state is correct, but we cannot change
      applied = False
      complete = True
      is_valid = True
  elif pos_symb1 == "*":
    if pos_symb2 == "O":
      # hint says ent1 is not ans_ent and we can change this
      applied = True
      complete = True
      is_valid = True
      puzzle.answer(pos_cat1, ans_cat, pos_ent1, ans_ent, "X")
    elif pos_symb2 == "x":
      # hint says ent1 is ans_ent and we can change this
      applied = True
      complete = True
      puzzle.answer(pos_cat1, ans_cat, pos_cat1, ans_ent, "O")
      is_valid = cross_out(puzzle, pos_cat1, ans_cat, pos_ent1, ans_ent)
  return applied, is_valid, complete

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
    # There is no info to apply.
    return applied, is_valid, complete

  currents = [currentA, currentB]
  if "X" in currents and "O" in currents:
    # Someone already answered.
    return applied, is_valid, complete

  if currentA == "X":
    applied = True
    puzzle.answer(catB1, catB2, entB1, entB2, "O")
    is_valid = cross_out(puzzle, catB1, catB2, entB1, entB2)

  if currentB == "X":
    applied = True
    puzzle.answer(catA1, catA2, entA1, entA2, "O")
    is_valid = cross_out(puzzle, catA1, catA2, entA1, entA2)

  if currentA == "O":
    applied = True
    puzzle.answer(catB1, catB2, entB1, entB2, "X")

  if currentB == "O":
    applied = True
    puzzle.answer(catA1, catA2, entA1, entA2, "X")

  return applied, is_valid, complete

def apply_hint(puzzle, hint):
  """
   Given a hint dictionary and a puzzle, apply next step of the hint to the puzzle

   return:
    applied = whether the hint changed the state
    complete = whether the hint as no more information to offer
    is_valid = whether hint could apply to current puzzle state
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
    return apply_not(puzzle, terms)
  elif rule == "before":
    return apply_before(puzzle, terms)
  elif rule == "simple_or":
    return apply_simple_or(puzzle, terms)
  elif rule == "compound_or":
    return apply_compound_or(puzzle, terms)
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
    print(str_hint(hint))
    print(apply_hint(puzzle, hint))
    print(find_openings(puzzle))
    print(find_transitives(puzzle))
    print(puzzle.print_grid())
    print("The ME should update!!")

