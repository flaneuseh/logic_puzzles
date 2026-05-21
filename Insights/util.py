import ultraimport
ultraimport("__dir__/../LogicPuzzles.py", package="main")
from main.LogicPuzzles import Puzzle, Category

def get_puzzle_for_dimensions(categories, cat_cnt, ent_cnt, num_cnt):
    alp_cats = []
    num_cats = []
    for cat in categories:
        if cat.is_numeric:
            num_cats.append(cat)
        else:
            alp_cats.append(cat)

    cats = num_cats[:num_cnt]
    alp_cnt = cat_cnt - num_cnt
    cats.extend(alp_cats[:alp_cnt])
    trunc_cats = []
    for cat in cats:
        trunc_cats.append(Category(cat.title, cat.entities[:ent_cnt], cat.is_numeric))
    print(trunc_cats)
    return Puzzle(trunc_cats)