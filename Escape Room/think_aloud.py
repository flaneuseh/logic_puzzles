from copy import deepcopy
import json
import ultraimport

from insight_recovery import load_online_puzzles
from puzzle_defs import PUZZLE_DEFS
ultraimport("__dir__/../LogicPuzzles.py", package="main")
from main.LogicPuzzles import Solver, Insight
from main.HintToEnglish import hint_to_english

SOLVER = Solver(set(), True)

def is_solved(puzzle, solution):
    contradiction, _ = SOLVER.repair(puzzle, solution, False)
    if contradiction:
        return False
    if puzzle.is_complete():
        return True
    return False

def think_aloud(puzzle_id, puzzle_info):
    puzzle = puzzle_info["puzzle"]
    hints = puzzle_info["hints"]
    solution = puzzle_info["solution"]
    trace = []
    curr_state = deepcopy(puzzle)
    i = 0
    print("----------------------")
    print("----------------------")
    print(f"PUZZLE {puzzle_id}")
    while not is_solved(curr_state, solution):
        for cat in puzzle.categories:
            print(f"{cat.title}: {cat.entities}")
        print(curr_state.print_grid())
        for i, hint in enumerate(hints):
            print(f"{i}. {hint_to_english(hint)}")
        success = False
        while success == False:
            temp_state = deepcopy(curr_state)
            try:
                move = input("Enter your move (cat1, cat2, ent1, ent2, sy, reasoning, hint_idx): ")
                if move == "NEXT":
                    return []
                if move == "EXIT":
                    return None
            
                cat1_title, cat2_title, ent1, ent2, sy, insight, hint_idx = move.split(", ")
                cat1 = None
                cat2 = None
                for cat in puzzle.categories:
                    if cat.title == cat1_title:
                        cat1 = cat
                    if cat.title == cat2_title:
                        cat2 = cat
                temp_state.answer((cat1, cat2, ent1, ent2), sy)
                trace.append({
                    "insight_str": insight,
                    "move_str": ((cat1_title, cat2_title, ent1, ent2), sy),
                    "repair": False,
                    "hint_idx": int(hint_idx),
                })
                success = True
            except:
                print("Invalid input.")
        curr_state = temp_state
        i += 1
    
    return trace

if __name__ == "__main__":
    online_dir = "user_data/online_puzzle_study"
    expert_dir = "expert_data/e1_kf"
    puzzles = PUZZLE_DEFS | load_online_puzzles(online_dir)
    puzzle_ids = puzzles.keys()
    for puzzle_id, puzzle_info in puzzles.items():
        solution, _, _ = SOLVER.apply_hints(puzzle_info["puzzle"], puzzle_info["hints"])
        puzzles[puzzle_id]["solution"] = solution
    for puzzle_id, puzzle_info in puzzles.items():
        if puzzle_id not in puzzle_ids:
            continue
        trace = None
        trace = think_aloud(puzzle_id, puzzle_info)
        if trace != None and len(trace) > 0:
            with open(f"{expert_dir}/{puzzle_id}_ground.json", "w") as f:
                json.dump(trace, f)
        proceed = input(f"Check trace for {puzzle_id}? ")
        if proceed not in ["y", "Y", "yes", "Yes", "YES"]:
            continue
        with open(f"{expert_dir}/{puzzle_id}_ground.json", "r") as f:
            trace = json.load(f)

        curr_state = deepcopy(puzzle_info["puzzle"])
        clean_trace = []
        for entry in trace:
            move_str = entry["move_str"]
            insight_str = entry["insight_str"]
            hint_idx = entry["hint_idx"]
            (cat1_title, cat2_title, ent1, ent2), sy = move_str
            cat1 = None
            cat2 = None
            for cat in curr_state.categories:
                if cat.title == cat1_title:
                    cat1 = cat
                if cat.title == cat2_title: 
                    cat2 = cat
            curr_state.answer((cat1, cat2, ent1, ent2), sy)
            for cat in curr_state.categories:
                print(f"{cat.title}: {cat.entities}")
            print(curr_state.print_grid())
                
            for i, hint in enumerate(puzzle_info["hints"]):
                print(f"{i}. {hint_to_english(hint)}")
            insight = None
            for ins in Insight.ALL_INSIGHTS:
                if ins.name == insight_str:
                    insight = ins
            
            while insight == None:
                new_insight_str = input(f"Enter a valid insight (given: {insight_str}): ")
                if new_insight_str == "SKIP":
                    break
                for ins in Insight.ALL_INSIGHTS:
                    if ins.name == new_insight_str:
                        insight = ins
            if insight == None:
                continue
            
            if insight == Insight.OPENING:
                hint_idx = -3
            elif insight == Insight.CROSS_OUT:
                hint_idx = -2
            elif insight == Insight.TRANS_ABC_TRUE or insight == Insight.TRANS_ABC_FALSE or insight == Insight.TRANS_SETS:
                hint_idx = -1

            ok = input(f"{insight.name}: hint {hint_idx} - ok? ")
            if ok not in ["y", "Y", "yes", "Yes", "YES"]:
                insight = None
                while insight == None:
                    insight_str = input(f"Enter new insight: ")
                    if insight_str == "SKIP":
                        break
                    for ins in Insight.ALL_INSIGHTS:
                        if ins.name == new_insight_str:
                            insight = ins
                if insight == None:
                    continue
                
                hint_idx = input(f"Enter new hint idx: ")

            entry["insight_str"] = insight.name
            entry["move_str"] = move_str
            entry["hint_idx"] = hint_idx
            if insight == Insight.USER_INSIGHT:                                                       
                entry["user_expl"] = insight_str
            clean_trace.append(entry)

        with open(f"{expert_dir}/{puzzle_id}_ground.json", "w") as f:
            json.dump(clean_trace, f)

        


                



         


    
    