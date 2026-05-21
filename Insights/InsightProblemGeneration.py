import ultraimport
import random
from pathlib import Path
from copy import deepcopy

ultraimport("__dir__/../LogicPuzzles.py", package="main")
from main.LogicPuzzles import Puzzle, Category, Insight, Solver
from SolutionMapEliteGeneration import map_elite_generate
from SolutionMapElitesVisualization import write_hint_files
from main.InsightProblems import get_insight_problem
from main.HintToEnglish import hint_to_english
from random import shuffle


def generate_insight_candidates(insight, categories, folder):
    shuffle(categories)
    num_categories = []
    non_num_categories = []
    for cat in categories:
        if cat.is_numeric:
            num_categories.append(deepcopy(cat))
        else:
            non_num_categories.append(deepcopy(cat))
    insight_cats = []
    if insight.requirements["numeric"]:
        insight_cats.append(num_categories.pop())
    while len(insight_cats) < insight.requirements["num_cats"]:
        if len(non_num_categories) > 0:
            insight_cats.append(non_num_categories.pop())
        else:
            insight_cats.append(num_categories.pop())

    for cat in insight_cats:
        ents = cat.entities
        if not cat.is_numeric:
            shuffle(ents)
        cat.entities = ents[: insight.requirements["num_ents"]]

    num_ents = len(insight_cats[0].entities)
    for cat in insight_cats:
        assert len(cat.entities) == num_ents

    puzzle = Puzzle(insight_cats)
    starting = 0
    num_trials = 1
    gen_len = 10000
    pop_size = 1000
    mut_rate = 0.8
    x_rate = 0.6
    add_rate = 0.5
    elits = 100

    forbidden = insight.sub_dag() - {insight}
    for super in insight.requirements["superceded_by"]:
        forbidden |= super.sub_dag()
    children = []
    for child in forbidden:
        children.append(child.name)
    print(f"generating insight candidates for {insight.name} - forbidding {children}")

    grid = map_elite_generate(
        puzzle,
        folder,
        starting,
        num_trials,
        gen_len,
        pop_size,
        mut_rate,
        x_rate,
        add_rate,
        elits,
        required_insights={insight},
        forbidden_insights=forbidden,
    )
    write_hint_files(folder, num_trials)
    return grid


if __name__ == "__main__":
    time = Category("time", ["1", "2", "3", "4", "5", "6"], True)
    suspect = Category(
        "suspect",
        [
            "Scarlet",
            "Plum",
            "White",
            "Mustard",
            "Peacock",
            "Green",
        ],
    )
    weapon = Category(
        "weapon", ["candlestick", "rope", "lead pipe", "revolver", "poison", "polearm"]
    )
    room = Category(
        "room", ["Greenhouse", "Library", "Salon", "Dining Room", "Kitchen", "Bedroom"]
    )

    base = "GeneratedInsightProblems"

    # Check manually authored "APPLY_NOT" puzzle
    # catABC = Category("ABC", ["A", "B", "C"])
    # cat123 = Category("123", ["1", "2", "3"])
    # hints = [
    #     {"is": [catABC, "B", cat123, "1"]},
    #     {"not": [{"is": [catABC, "A", cat123, "2"]}]},
    # ]
    # puzzle = Puzzle([catABC, cat123])
    # insight_puzzle, move, err_msg = get_insight_problem(
    #     puzzle, hints, Insight.APPLY_NOT
    # )
    # if err_msg != "":
    #     print(err_msg)
    # assert err_msg == ""
    # print(insight_puzzle.print_grid())

    # # Check manually authored "BEFORE_DIFF_CAT" puzzle
    # catABC = Category("ABC", ["A", "B", "C"])
    # catxyz = Category("xyz", ["x", "y", "z"])
    # cat123 = Category("123", ["1", "2", "3"])
    # hints = [
    #     {"is": [catxyz, "y", catABC, "B"]},
    #     {"is": [catxyz, "y", cat123, "2"]},
    #     {"before": [catxyz, "x", catABC,"A", cat123]},
    # ]
    # puzzle = Puzzle([catABC, cat123, catxyz])
    # insight_puzzle, move, err_msg = get_insight_problem(
    #     puzzle, hints, Insight.BEFORE_DIFF_CAT
    # )
    # if err_msg != "":
    #     print(err_msg)
    # assert err_msg == ""
    # print(insight_puzzle.print_grid())

    insights = Insight.ALL_INSIGHTS

    # TODO: Try other tree structures e.g is -> crossout -> opening
    # TODO: Try other games
    for insight in insights:
        folder = f"{base}/{insight.name}"
        Path(folder).mkdir(parents=True, exist_ok=True)
        grid = generate_insight_candidates(
            insight, [time, suspect, weapon, room], folder
        )
        file = open(f"{folder}/insight_problems.txt", "w")
        num_problems = 0
        err_reasons = {}
        for row in range(grid.height):
            for col in range(grid.width):
                child_cell = grid.grid[row][col]
                if not child_cell is None:
                    child = child_cell[1]

                    child = child_cell[1]
                    solver = Solver()
                    assert solver.can_solve_without_forbidden(
                        child.puzzle, child.hints
                    ), "can't solve with all insights available"
                    required_insights = {insight}
                    forbidden_insights = insight.sub_dag() - {insight}
                    solver = Solver(required_insights | forbidden_insights)
                    assert not solver.can_solve_without_forbidden(
                        child.puzzle, child.hints
                    ), "can solve without required insight: {}".format(
                        required_insights
                    )
                    solver = Solver(forbidden_insights)
                    assert solver.can_solve_without_forbidden(
                        child.puzzle, child.hints
                    ), "can't solve without forbidden insights {}".format(
                        forbidden_insights
                    )

                    insight_puzzle, move, err_msg = get_insight_problem(
                        child.puzzle, child.hints, insight
                    )
                    if err_msg != "":
                        if err_msg not in err_reasons:
                            err_reasons[err_msg] = 0
                        err_reasons[err_msg] += 1
                    if insight_puzzle != None and move != None:
                        num_problems += 1
                        file.write(insight_puzzle.print_grid())
                        file.write(f"{move['insight'].name}\n")
                        for i, hint in enumerate(child.hints):
                            english_hint = hint_to_english(hint)
                            pre = ""
                            if (
                                "indexed_hint" in move
                                and i == move["indexed_hint"]["idx"]
                            ):
                                pre = "*"
                            file.write(f"{pre}{i}. {english_hint}\n")
        print(
            f"Found {num_problems} insight problems of {grid.pop_size} candidates for {insight}.\n"
        )
        print(f"Reasons for failed candidates: {err_reasons}")
    print("Done generating insight problems.")
