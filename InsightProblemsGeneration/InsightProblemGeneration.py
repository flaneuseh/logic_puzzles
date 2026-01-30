import ultraimport
ultraimport("__dir__/../LogicPuzzles.py", package="main")
from main.LogicPuzzles import (
    Puzzle,
    Category,
    Insight,
)
from main.MapEliteGeneration import map_elite_generate
from main.MapElitesVisualization import write_hint_files
from random import shuffle

def generate_insight_candidates(insight, categories):
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
        cat.entities = ents[:insight.requirements["num_ents"]]

    puzzle = Puzzle(insight_cats)
    folder = "GeneratedInsightProblems"
    starting = 0
    num_trials = 1
    gen_len = 501
    pop_size = 100
    mut_rate = 0.8
    x_rate = 0.6
    add_rate = 0.5
    elits = 10

    children = []
    for child in Insight.sub_dag(insight) - {insight}:
        children.append(child.name)
    print(f"generating insight candidates for {insight.name} - forbidding {children}")
    map_elite_generate(
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
        forbidden_insights=Insight.sub_dag(insight) - {insight},
    )
    write_hint_files(folder, num_trials)


if __name__ == "__main__":
    time = Category("time", ["1", "2", "3", "4"], True)
    suspect = Category(
        "suspect",
        [
            "Miss Scarlet",
            "Prof. Plum", 
            "Mrs. White",
            "Col. Mustard",
        ],
        False,
    )
    weapon = Category("weapon", ["candlestick", "rope", "lead pipe", "revolver"], False)

    generate_insight_candidates(Insight.APPLY_OR, [time, suspect, weapon])
