import ultraimport
from copy import deepcopy
from itertools import permutations
from collections import deque
import jsons

ultraimport("__dir__/LogicPuzzles.py", package="main")
from main.LogicPuzzles import Grammar, Puzzle, Category, Solver
SOLVER = Solver()

def expand_grammar(sub_grammar, grand_grammar=None):
        """
        exhaustively generate all possible words for a grammar
        """
        words = []
        if grand_grammar is None:
            grand_grammar = sub_grammar
        if isinstance(sub_grammar, dict):
            # Grammar has named rules
            for rule, rule_grammar in sub_grammar.items():
                rule_words = expand_grammar(rule_grammar, grand_grammar)
                for rule_word in rule_words:
                    words.append({rule: rule_word})
        else:
            # Grammar is a list of alternates
            for alt in sub_grammar:
                alt_words = [[]]
                for token in alt:
                    if token in Grammar.TERMINALS:
                        for word in alt_words:
                            word.append(token)
                    else:
                        token_words = expand_grammar(Grammar.sub_grammar(grand_grammar, token), grand_grammar)
                        duped_alt_words = []
                        for alt_word in alt_words:
                            for prod_word in token_words:
                                dupe_word = deepcopy(alt_word)
                                dupe_word.append({token: prod_word})
                                duped_alt_words.append(dupe_word)
                        alt_words = duped_alt_words
                words.extend(alt_words)
        return words

def ext_fill_in_word(word, categories):
        """
        Exhaustively replace all terminal terms with appropriate
        categories, entities, or integers from a puzzle
        """
        filled_words = [{"fill": {}, "terms": {}, "last_cat": ""}]
        for key, token in word.items():
            if isinstance(token, dict):
                # Token is a sub-word.
                alt_words = ext_fill_in_word(token, categories)
                duped_filled_words = []
                for word in filled_words:
                    for alt_word in alt_words:
                        dupe_word = deepcopy(word)
                        dupe_word["fill"][key] = alt_word
                        duped_filled_words.append(dupe_word)
                filled_words = duped_filled_words
            else:
                # Token is a list of terms.
                cat_dict = {}
                alp_dict = {}
                num_dict = {}
                for cat in categories:
                    cat_dict[cat.title] = cat.entities
                    if cat.is_numeric:
                        num_dict[cat.title] = cat.entities
                    else:
                        alp_dict[cat.title] = cat.entities
                for word in filled_words:
                    word["fill"][key] = []

                for term in token:
                    if isinstance(term, dict):
                        # Term is a sub-word
                        alt_words = ext_fill_in_word(term, categories)
                        duped_filled_words = []
                        for word in filled_words:
                            for alt_word in alt_words:
                                dupe_word = deepcopy(word)
                                dupe_word["fill"][key].append(alt_word)
                                duped_filled_words.append(dupe_word)
                        filled_words = duped_filled_words
                    else:
                        # Term is a grammar term
                        if "cat" in term or "alp" in term or "num" in term:
                            duped_filled_words = []
                            for word in filled_words:
                                if term != "cat" and term in word["terms"]:
                                    # cat1/cat2/cat3 have permanent values within a phrase.
                                    word["fill"][key].append(word["terms"][term])
                                    word["last_cat"] = word["terms"][term]
                                else:
                                    perm_cats = [] # track which categories have been assigned to permanent keys (e.g cat1)
                                    loose_cats = [] # track which categories have been assigned to impermanent keys (cat, alp, num)
                                    for t, fill in word["terms"].items():
                                        if "cat" in t or "alp" in t or "num" in t:
                                            if t not in ["cat", "alp", "num"]:
                                                perm_cats.append(fill)
                                            else:
                                                loose_cats.append(fill)

                                    rel_dict = {}
                                    if "cat" in term:
                                        rel_dict = cat_dict
                                    if "alp" in term:
                                        rel_dict = alp_dict
                                    if "num" in term:
                                        rel_dict = num_dict
                                    for cat in rel_dict.keys():
                                        if cat not in perm_cats:
                                            # Don't allow a permanently assigned cat to be assigned to any other key
                                            if term in ["cat", "alp", "num"] or cat not in loose_cats:
                                                # And, don't allow a permanent key to be assigned to a category that has been used by an impermanent key.
                                                dupe_word = deepcopy(word)
                                                dupe_word["fill"][key].append(cat)
                                                dupe_word["last_cat"] = cat
                                                # record use of value so it doesn't get assigned to a permanent key
                                                if term in ["cat", "alp", "num"]:
                                                    if term not in dupe_word["terms"]:
                                                        dupe_word["terms"][term] = []
                                                    dupe_word["terms"][term].append(cat)
                                                else:
                                                    dupe_word["terms"][term] = cat
                                                duped_filled_words.append(dupe_word)
                            filled_words = duped_filled_words
                        elif "ent" in term:
                            # TODO: ent should be part of last cat and should not be the same as any other if it is ent1 etc.
                            duped_filled_words = []
                            for word in filled_words:
                                if term != "ent" and term in word["terms"]:
                                    # ent1/ent2/ent3 have permanent values within a category/phrase.
                                    word["fill"][key].append(word["terms"][term])
                                else:
                                    perm_ents = [] # track which categories have been assigned to permanent keys (e.g cat1)
                                    loose_ents = [] # track which categories have been assigned to impermanent keys (cat, alp, num)
                                    for t, fill in word["terms"].items():
                                        if "ent" in t:
                                            if t != "ent":
                                                perm_cats.append(fill)
                                            else:
                                                loose_cats.append(fill)

                                    for ent in cat_dict[word["last_cat"]]:
                                        if ent not in perm_ents:
                                            # Don't allow a permanently assigned ent to be assigned to any other key
                                            if term == "ent" or ent not in loose_ents:
                                                # And, don't allow a permanent key to be assigned to an entity that has been used by an impermanent key.
                                                dupe_word = deepcopy(word)
                                                dupe_word["fill"][key].append(ent)
                                                # record use of value so it doesn't get assigned to a permanent key
                                                if term == "ent":
                                                    if term not in dupe_word["terms"]:
                                                        dupe_word["terms"][term] = []
                                                    dupe_word["terms"][term].append(ent)
                                                else:
                                                    dupe_word["terms"][term] = ent
                                                duped_filled_words.append(dupe_word)
                            filled_words = duped_filled_words
                        elif term == "int":
                            duped_filled_words = []
                            for word in filled_words:
                                for i in range(1, len(cat_dict[word["last_cat"]]) - 1):
                                    dupe_word = deepcopy(word)
                                    dupe_word["fill"][key].append(i)
                                    duped_filled_words.append(dupe_word)
                            filled_words = duped_filled_words
        fills_only = []
        for filled_word in filled_words:
            fills_only.append(filled_word["fill"])
        return fills_only

def generate_all_clues(puzzle):
    clues = {}
    words = expand_grammar(Grammar.GRAMMAR)
    print(words)
    for word in words:
        clue_type = list(word["hint"].keys())[0]
        if clue_type not in clues:
            clues[clue_type] = []
        fills = ext_fill_in_word(word, puzzle.categories)
        clues[clue_type].extend(fills)
    return clues

def generate_nonredundant_clues__is(categories):
    num_cats = len(categories)
    if num_cats < 2:
        return []
    clues = []
    for i in range(0, num_cats - 1):
        cat1 = categories[i]
        for j in range(i+1, num_cats):
            # A = B is the same as B = A
            cat2 = categories[j]
            for ent1 in cat1.entities:
                for ent2 in cat2.entities:
                    clues.append({"is": [cat1, ent1, cat2, ent2]})
    return clues

def generate_nonredundant_clues__not(is_clues):
    clues = []
    for clue in is_clues:
        clues.append({"not": [clue]})
    return clues

def generate_nonredundant_two_three_term_lists(categories):
    num_cats = len(categories)
    if num_cats < 2:
        return []
    num_ents = len(categories[0].entities)
    if num_ents < 2:
        return []
    term_sets = []
    for i in range(0, num_cats):
        cat1 = categories[i]
        for j in range(i, num_cats):
            cat2 = categories[j]
            for k in range(0, num_cats):
                if k == i or k == j:
                    continue
                cat3 = categories[k]

                last_m = num_ents
                if i == j:
                    last_m = num_ents - 1
                for m in range(0, last_m):
                    ent1 = cat1.entities[m]
                    first_n = 0
                    if i == j:
                        first_n = m + 1
                    for n in range(first_n, num_ents):
                        ent2 = cat2.entities[n]
                        term_sets.append([cat1, ent1, cat2, ent2, cat3])
    return term_sets

def generate_nonredundant_clues__before(two_three_term_lists):
    clues = []
    for terms in two_three_term_lists:
        cat3 = terms[-1]
        if cat3.is_numeric:
            clues.append({"before": terms})
            for i in range(1, len(cat3.entities) - 1):
                alt_terms = deepcopy(terms)
                alt_terms.append(i)
                clues.append({"before": alt_terms})
    return clues

def generate_nonredundant_clues__simple_or(two_three_term_lists):
    clues = []
    for terms in two_three_term_lists:
        cat3 = terms[-1]
        for ent3 in cat3.entities:
            terms.append(ent3)
            clues.append({"simple_or": terms})
    return clues


def generate_nonredundant_clues__compound_or(is_clues):
    clues = []
    num_is = len(is_clues)
    for i in range(0, num_is - 1):
        is1 = is_clues[i]
        for j in range(i+1, num_is):
            # a or b is the same as b or a
            is2 = is_clues[j]
            clues.append({"compound_or": [is1, is2]})
    return clues

def generate_nonredundant_clues(puzzle):
    clues = {}
    clues["is"] = generate_nonredundant_clues__is(puzzle.categories)
    clues["not"] = generate_nonredundant_clues__not(clues["is"])
    two_three_term_sets = generate_nonredundant_two_three_term_lists(puzzle.categories)
    clues["before"] = generate_nonredundant_clues__before(two_three_term_sets)
    clues["simple_or"] = generate_nonredundant_clues__simple_or(two_three_term_sets)
    clues["compound_or"] = generate_nonredundant_clues__compound_or(clues["is"])
    return clues

def generate_all_solutions(puzzle):
    solutions = []
    num_cats = len(puzzle.categories)
    if num_cats < 2:
        return []
    soln_perms = [{}]
    cat1 = puzzle.categories[0]
    for cat2 in puzzle.categories[1:]:
        cat_perms = permutations(cat2.entities, len(cat2.entities))
        duped_soln_perms = []
        for soln_perm in soln_perms:
            for cat_perm in cat_perms:
                duped_soln_perm = deepcopy(soln_perm)
                duped_soln_perm[cat2] = cat_perm
                duped_soln_perms.append(duped_soln_perm)
        soln_perms = duped_soln_perms
    
    for soln_perm in soln_perms:
        soln_puzzle = Puzzle(puzzle.categories)
        for cat2, cat_perm in soln_perm.items():
            for i in range(len(cat_perm)):
                ent1 = cat1.entities[i]
                ent2 = cat_perm[i]
                soln_puzzle.answer((cat1, cat2, ent1, ent2), "O")
        contradiction, _ = SOLVER.find_transitives(soln_puzzle, True)
        assert not contradiction
        contradiction, _ = SOLVER.apply_cross_out(soln_puzzle, True)
        assert not contradiction
        solutions.append(soln_puzzle)
    return solutions

def filter_clues_by_solution(clues_by_type, solution):
    filtered_clues = {}
    for clue_type, clues in clues_by_type.items():
        filtered_clues[clue_type] = []
        for clue in clues:
            contradiction, _ = SOLVER.apply_hint(solution, clue)
            if not contradiction:
                filtered_clues[clue_type].append(clue)
    return filtered_clues

def generate_solution_clues_dict(clues_by_type, solutions):
    soln_clues_dict = {}
    for soln in solutions:
        filtered_clues = filter_clues_by_solution(clues_by_type, soln)
        soln_clues_dict[soln.print_grid()] = filtered_clues
    return soln_clues_dict

def ext_gen_cluesets(puzzle, clues, idx_file, clues_file, valid_cluesets=[], max_depth=1000):
    queue = deque()
    N = len(clues)
    depth = 1
    for i in range(N):
        discard = False
        candidate_idx = [i]
        for valid_clueset_idx in valid_cluesets:
            if set(valid_clueset_idx) <= set(candidate_idx):
                # All the clues in the existing valid clueset are in the candidate;
                # the candidate contains redundant clues and should not be further explored.
                discard = True
                break
        if discard:
            continue
        candidate_clues = [clues[i]]
        post_clues, is_valid, _ = SOLVER.apply_hints(puzzle, candidate_clues)
        if not is_valid:
            # Discard invalid cluesets
            continue
        if post_clues.is_complete():
            print(f"complete set found of size {depth}")
            # Found a complete set; no need to explore this branch further.
            valid_cluesets.append(candidate_idx)
            idx_file.write(f"{jsons.dumps(candidate_idx)},")
            clues_file.write(f"{jsons.dumps(candidate_clues)},")
        queue.append((candidate_idx, post_clues))
    while depth <= max_depth and len(queue) > 0:
        candidate_idx, partial = queue.popleft()
        if len(candidate_idx) > depth:
            print(f"checked all cluesets sized {depth}")
            depth = len(candidate_idx)
        discard = False
        if len(valid_cluesets) > 0 and len(candidate_idx) < len(valid_cluesets[-1]):
            # We've already found all valid cluesets of this size.
            continue
        for valid_clueset_idx in valid_cluesets:
            if set(valid_clueset_idx) <= set(candidate_idx):
                # All the clues in the existing valid clueset are in the candidate;
                # the candidate contains redundant clues and should not be further explored.
                discard = True
                break
        if discard:
            continue
        # Convert clue indices back to the actual clues so we can 
        candidate_clues = []
        for idx in candidate_idx:
            candidate_clues.append(clues[idx])
        post_clues, is_valid, _ = SOLVER.apply_hints(partial, [candidate_clues[-1]])
        if not is_valid:
            # Discard invalid cluesets
            continue
        if post_clues.is_complete():
            print(f"complete set found of size {depth}")
            # Found a complete set; no need to explore this branch further.
            valid_cluesets.append(candidate_idx)
            idx_file.write(f"{json.dumps((candidate_idx))},")
            clues_file.write(f"{json.dumps((candidate_clues))},")
        else:
            # Add children to the end of the queue.
            # Only create children from clues after the final clue in the list,
            # because we want combinations, not permutations.
            i = candidate_idx[-1]
            for j in range (i+1, N):
                child = deepcopy(candidate_idx)
                child.append(j)
                queue.append((child, post_clues))


if __name__ == "__main__":
    # time = Category("time", ["1:00", "2:00", "3:00", "4:00", "5:00", "6:00"], True)
    time = Category("time", ["1:00", "2:00", "3:00", "4:00"], True)
    # suspect = Category(
    #     "suspect",
    #     [
    #         "Scarlet",
    #         "Plum",
    #         "White",
    #         "Mustard",
    #         "Peacock",
    #         "Green",
    #     ],
    # )
    suspect = Category(
        "suspect",
        [
            "Scarlet",
            "Plum",
            "Peacock",
            "Green",
        ],
    )
    # weapon = Category(
    #     "weapon", ["candlestick", "rope", "lead pipe", "revolver", "poison", "polearm"]
    # )
    weapon = Category(
        "weapon", ["candlestick", "rope", "lead pipe", "revolver"]
    )
    # room = Category(
    #     "room", ["Greenhouse", "Library", "Salon", "Dining Room", "Kitchen", "Bedroom"]
    # )
    room = Category(
        "room", ["Greenhouse", "Library", "Salon", "Dining Room"]
    )
    categories = [time, suspect, weapon]
    puzzle = Puzzle(categories)
    clues_by_type = generate_nonredundant_clues(puzzle)
    for clue_type, clues in clues_by_type.items():
        print(f"{clue_type}: {len(clues)} clues found for {len(categories)} x {len(categories[0].entities)} puzzle")
    solutions = generate_all_solutions(puzzle)
    # for soln in solutions:
    #     print(soln.print_grid())
    print(f"{len(solutions)} solutions found for {len(categories)} x {len(categories[0].entities)} puzzle")
    soln_clues_dict = generate_solution_clues_dict(clues_by_type, solutions)
    # print(soln_clues_dict)
    # for i, clues_by_type in enumerate(soln_clues_dict.values()):
    #     for clue_type, clues in clues_by_type.items():
    #         print(f"{len(clues)} {clue_type} clues found for solution {i}")
    print("Per solution: ")
    all_clues = []
    soln_clues_by_type = list(soln_clues_dict.values())[0]
    for clue_type, clues in soln_clues_by_type.items():
        print(f"   {len(clues)} {clue_type} clues")
        if clue_type != "compound_or":
            # compound or doubles the number of clues, which is significant in an exponential operation
            all_clues.extend(clues)
        
    idx_filepath = f"ExhaustiveGeneration/idx.txt"
    clues_filepath = f"ExhaustiveGeneration/clues.txt"
    with open(idx_filepath, "w") as idx_file:
        idx_file.write("[")
        with open(clues_filepath, "w") as clues_file:
            clues_file.write("[")
            clues_file.write(f"{jsons.dumps(all_clues[0])}")
            # ext_gen_cluesets(puzzle, all_clues, idx_file, clues_file)