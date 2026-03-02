import ultraimport
import random
from pathlib import Path

ultraimport("__dir__/../LogicPuzzles.py", package="main")
from main.LogicPuzzles import (
    Puzzle,
    Category,
    Insight,
    Solver
)
from main.MapEliteGeneration import map_elite_generate
from main.MapElitesVisualization import write_hint_files
from main.InsightProblems import get_insight_problem
from main.HintToEnglish import hint_to_english
from random import shuffle


def generate_insight_candidates(insight, categories, folder):
    shuffle(categories)
    num_categories = []
    non_num_categories = []
    for cat in categories:
        if cat.is_numeric:
            num_categories.append(cat)
        else:
            non_num_categories.append(cat)
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

    puzzle = Puzzle(insight_cats)
    starting = 0
    num_trials = 1
    gen_len = 100000
    pop_size = 5000
    mut_rate = 0.8
    x_rate = 0.6
    add_rate = 0.5
    elits = 10

    children = []
    for child in insight.sub_dag() - {insight}:
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
        forbidden_insights=insight.sub_dag() - {insight},
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
        False,
    )
    weapon = Category("weapon", ["candlestick", "rope", "lead pipe", "revolver", "poison", "polearm"])
    room = Category("room", ["Greenhouse", "Library", "Salon", "Dining Room", "Kitchen", "Bedroom"])

    base = "GeneratedInsightProblems"
    
    # TODO: Try other tree structures e.g is -> crossout -> opening
    # TODO: Try other games
    for insight in Insight.ALL_INSIGHTS:
        folder = f"{base}/{insight.name}"
        Path(folder).mkdir(parents=True, exist_ok=True)
        grid = generate_insight_candidates(insight, [time, suspect, weapon, room], folder)
        file = open(f"{folder}/insight_problems.txt", "w") 
        num_problems = 0
        for row in range(grid.height):
            for col in range(grid.width):
                child_cell = grid.grid[row][col]
                if not child_cell is None:
                    child = child_cell[1]

                    child = child_cell[1]
                    solver = Solver()
                    assert solver.can_solve_without_forbidden(child.puzzle, child.hints), "can't solve with all insights available"
                    required_insights = {insight}
                    forbidden_insights = insight.sub_dag() - {insight}
                    solver = Solver(required_insights | forbidden_insights)
                    assert not solver.can_solve_without_forbidden(
                        child.puzzle, child.hints
                    ), "can solve without required insight: {}".format(required_insights)
                    solver = Solver(forbidden_insights)
                    assert solver.can_solve_without_forbidden(
                        child.puzzle, child.hints
                    ), "can't solve without forbidden insights {}".format(forbidden_insights)

                    insight_puzzle, move = get_insight_problem(
                        child.puzzle, child.hints, insight
                    )
                    if insight_puzzle != None and move != None:
                        num_problems += 1
                        file.write(insight_puzzle.print_grid())
                        for insight in move["insights"]:
                            file.write(f"{insight.name}\n")
                        for i, hint in enumerate(child.hints):
                            english_hint = hint_to_english(hint)
                            pre = ""
                            if "indexed_hint" in move and i == move["indexed_hint"]["idx"]:
                                pre = "*"
                            file.write(f"{pre}{i}. {english_hint}\n")
        print(f"Found {num_problems} insight problems of {grid.pop_size} candidates for {insight}.\n")
    print("Done generating insight problems.")
        
