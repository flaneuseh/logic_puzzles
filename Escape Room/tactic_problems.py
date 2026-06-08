import ultraimport

from puzzle_defs import PUZZLE_DEFS

ultraimport("__dir__/../LogicPuzzles.py", package="main")
from main.LogicPuzzles import Solver, Insight

ultraimport("__dir__/../Insights/SolutionMapEliteGeneration.py", package="insights")
from insights.SolutionMapEliteGeneration import map_elite_generate
from insights.SolutionMapElitesVisualization import (
    write_hint_files,
    heat_map,
    get_agg_children_grids,
    get_agg_hint_grids,
    write_summary_json_files,
)

SOLVER = Solver(set(), True)

if __name__ == "__main__":
    puzzle_ids = [
        "spoke_pasta",
        "spoke_sunlight",
        "spoke_water",
        "spoke_protein",
        "hub_soup",
    ]

    PUZZLE_DEFS["spoke_pasta"]["required"] = {
        Insight.APPLY_IS,
        Insight.CROSS_OUT,
        Insight.OPENING,
        Insight.APPLY_OR,
    }
    PUZZLE_DEFS["spoke_pasta"]["also_allowed"] = set()
    PUZZLE_DEFS["spoke_protein"]["required"] = {
        Insight.APPLY_IS,
        Insight.CROSS_OUT,
        Insight.OPENING,
        Insight.APPLY_BEFORE_ONE_SPOT,
    }
    PUZZLE_DEFS["spoke_protein"]["also_allowed"] = set()

    PUZZLE_DEFS["spoke_sunlight"]["required"] = {Insight.SIMPLE_OR_SAME_CAT}
    PUZZLE_DEFS["spoke_sunlight"]["also_allowed"] = {Insight.APPLY_OR}
    PUZZLE_DEFS["spoke_water"]["required"] = {Insight.BEFORE_NOINFO}
    PUZZLE_DEFS["spoke_water"]["also_allowed"] = {Insight.APPLY_BEFORE_ONE_SPOT}

    PUZZLE_DEFS["hub_soup"]["required"] = {
        Insight.BEFORE_NOINFO,
        Insight.SIMPLE_OR_SAME_CAT,
    }
    PUZZLE_DEFS["hub_soup"]["also_allowed"] = {
        Insight.APPLY_OR, Insight.APPLY_BEFORE_ONE_SPOT, Insight.TRANS_ABC_TRUE
    }

    always_allowed = {
        Insight.APPLY_IS,
        Insight.CROSS_OUT,
        Insight.OPENING,
        Insight.APPLY_NOT,
    }
    always_forbidden = {
        Insight.TRANS_SETS,
        Insight.BEFORE_N_SPOTS_SHIFT,
        Insight.BEFORE_N_SPOTS_CROSSCHECK,
        Insight.TRANS_ABC_FALSE,
        Insight.SIMPLE_OR_DIFF_CAT,
        Insight.BEFORE_DIFF_CAT,
    }

    puzzle_ids = ["hub_soup"]
    for puzzle_id in puzzle_ids:
        puzzle_info = PUZZLE_DEFS[puzzle_id]
        solution, _, _ = SOLVER.apply_hints(puzzle_info["puzzle"], puzzle_info["hints"])
        puzzle_info["solution"] = solution
        curr_unmissable_insights = SOLVER.unmissable_insights(
            puzzle_info["puzzle"], puzzle_info["hints"]
        )
        print(
            f"Current unmissable insights for {puzzle_id}: {curr_unmissable_insights}"
        )

        puzzle_info["forbidden"] = (
            Insight.ALL_INSIGHTS - puzzle_info["required"] - always_allowed
        )
        puzzle_info = PUZZLE_DEFS[puzzle_id]

        print(
            f"Generate new puzzles for {puzzle_id} with required insights {puzzle_info['required']} and forbidden {puzzle_info['forbidden']}"
        )
        folder = f"GenTacticsProblems/{puzzle_id}"

        starting = 0
        num_trials = 1
        gen_len = 100
        pop_size = 1000
        cell_capacity = 10
        mut_rate = 0.8
        x_rate = 0.6
        add_rate = 0.5
        elits = 100

        grid = map_elite_generate(
            puzzle_info["puzzle"],
            puzzle_info["solution"].print_grid(),
            folder,
            starting,
            num_trials,
            gen_len,
            pop_size,
            mut_rate,
            x_rate,
            add_rate,
            elits,
            required_insights=puzzle_info["required"],
            forbidden_insights= (always_forbidden - puzzle_info["also_allowed"]) | puzzle_info["forbidden"],
        )

        write_hint_files(folder, num_trials)
        agg_grid = get_agg_hint_grids(folder, num_trials)
        heat_map(
            agg_grid,
            True,
            title="Average Hint Size by Cell",
            ylabel="Gini Coefficent",
            xlabel="Solver loops",
            colorbar_label="Average Hint Size",
            vmin=3,
            savefile=f"{folder}/hintsize_heatmap.png",
        )

        agg_total_grid = get_agg_children_grids(folder, num_trials)
        heat_map(
            agg_total_grid,
            False,
            title="Average Children Produced by Cell",
            ylabel="Gini Coefficent",
            xlabel="Solver loops",
            colorbar_label="Average Children Produced",
            savefile=f"{folder}/children_heatmap.png",
        )

        write_summary_json_files(folder, num_trials)
        print(f"finished generating and saving puzzles for {puzzle_id}")
