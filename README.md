# logic_puzzles
This is a project for generating new logic grid puzzle. It uses a FI-2Pop genetic algorithm to generate puzzles that are both solvable and challenging. Solvable puzzles with complete and valid solution. Challenging puzzles are ones that require many round to complete. 


## Hosting on a VM 

* Step 1: SSH into vm 
* step 2: cd into logic_puzzle
* step 3: pull latest code 
* step 4: reload systemctl 

```sudo systemctl daemon-reload```

* step 5: re-start the gunicorn service 

```sudo systemctl restart logic_puzzle_app.service``` 

If there is an error you can check with 

```sudo systemctl status logic_puzzle_app.service``` 

Or for more detail logs, check the journal with (where 200 is the number of lines to print): 

```sudo journalctl -u logic_puzzle_app.service -n 200```


You can find/modify the Gunicorn configuration with: 

```sudo nano /etc/systemd/system/logic_puzzle_app.service```

You can reference this tutorial: https://medium.com/@adityaarya1/deploy-a-flask-application-to-azure-vm-with-a-ssl-certificate-d2960c50783d 

## Quick Start 

### Playing generated puzzles 
The generated puzzles are located in the Difficulty-Only and Hints-And-Difficulty folders. The Hints-and-Difficulty contains puzzles that were optimized both for difficulty and for small hint sizes, where the Difficulty-Only contians puzzles that were optimized for difficulty only. Each folder contains a hint.txt that contains the hints for each puzzle. For the puzzles you can use the BlankPuzzle.png to mark the your answers. You can check your solutions agains't the solutions in the solutions.txt file that is each both folders. 

### Looking at Experiment data 
Each experiment folder also contains several visualizations about the generated puzzles and the generation process. The "data.txt" file also contains key information from the experiment. Each "pop_<i>.p" file contains a pickled version of the feasible and infeasible population of the last generation for that trial, along with a history object, which tracks fitness over generations. 

### Running a new experiement 
New experiements can be run by modifying the "Experiments.py" file. At the top, several contains are defined. Most important is the "folder" which tells the program where to put experiement data. We recommend created a new folder for each experiement run. You can also modify the puzzle to generate puzzles with different themes. Note that currenlty puzzles are required to have at least one numeric category. 

After the experiement finishes running, you will need to run the "DataVisualisation.py" file, with the updated folder. This will produce "hint.txt" and "solutions.txt" files, of which you can look at and play your generated puzzles. 

## Important Files 

### LogicPuzzle.py 
This file defines the objects and logics for logic puzzles. 

#### Category 
A category object is a set of entities, that is either numerical or categorical. To create a new category, you need to provide a title for the category, list of string names for the entities, and whether the category is numerical or categorical.

```
suspects = Category("suspect", ["Ms. carlet", "Mrs. White", "Col. Mustard", "Prof. Plum"], False) 
```

#### Puzzle 
One you haves a set of categories, you can create an empty puzzle. 

```
puzzle = Puzzle([suspects, weapons, rooms, time]) 
```

These puzzles can be updated using the " answer(self, cat1, cat2, ent1, ent2, new_symbol)" method. This will put the string "new_symbol" in the cell location of ent1 in cat1 and ent2 in cat2. 

Given a partially or completelty solved puzzle, there are several methods that are use full. 

* print_grid: return a string of the grid 
* is_valid: returns true if there are no logical contradictions in the puzzle 
* is_complete: returns true if the puzzle is valid and all cells are filled 

#### Hint Grammar 
The hint grammar is defined as a nested dictionary. You can generated a random hint for a given puzzle using the "generate_hint(puzzle)" function. This hint will be returned as a dictionary, but can be translated to a string in English using "hint_to_english" function in "HintToEnglish.py" 

#### Apply Hint 
The "apply_hint(hint, puzzle)" will take a hint dictionary and apply any logic to the current game state. It will return three booleans 
* applied: whether the hint changed the state 
* is_valid: whether there was a contradiction in the state 
* complete: true if the hint cannot change state anymore 



### Evolution.py 

#### apply_hints(puzzle, hints)
This is the main solver for logic puzzles. This functions takes in a puzzle and and list of hints, and attempts to solve the puzzle using the hints. It will create a copy of the puzzle and update it with any logic contained in the hints. If this puzzle copy has empty space that means the puzzle was unsolvable. Note the returned puzzle may still not be valid. 

#### Hint Set 
This class the indivuals for evolution. There are three important attributes in hint set: 
* hints: a list of hints (given at intialization)
* puzzle: an empty puzzle state (given at initalization)
* completed_puzzle: a puzzle state which was attempted to be solved with hints 

There are also several important methods in hint set. 

##### mutate(add_rate)
Returns a new hint set that is mutated once. There are two types of mutation that can occur 

* addition: a new random hint is added 
* deletion: a random hint is removed 

The probability of the mutation being addition is specified with the add_rate parameter. However, if there are over 20 hints only deletion will be chosen. 

##### cross_over(other) 
Crossover combines the hint lists of two puzzle and randomly shuffles them between two children. Each child gets an equal number of hints (except if there is an odd number). 

##### is_valid()
Returns true if this hint set represents a solvable puzzle. 

##### feasiblity()
This is the fitness function for infeasible (unsolvable) puzzles. It will return a number between 0 and 1, where 1 represents a solvable puzzle. There are three components to this fitness function: 

* completion: percentage of filled-in cells 
* validity: percentages of rows with exactly one "O" 
* violaitons: number of transitive violations (lower numbers are rewarded)

##### optimize_fun()
This is the fitness function for feasible (solvable) puzzles. This deines the optimization criteria for the puzzle. Several fitness functions are present, and can be uncommented out to change. 

#### evolve(puzzle, generations, pop_size, x_rate, mut_rate, add_rate, elits)
This is the function for the FI-2Pop genetic algorithm that generated new puzzles. 

Parameters: 
* puzzle: a blank puzzle to generate hints for 
* generations: number of generations to run for 
* pop_size: the size of population (this will be the sum of the feasible and infeasible populations)
* x_rate: rate of cross over 
* mut_rate: ratio of children to mutate 
* add_rate: ratio of mutations that should be addition 
* elits: number of elites to keep in each population 

Returns: 
* feasible: the feasible population at the last generation
* infeasible: the infeasible popuation at the last generation 
* history: a history object that tracks fitness over time 

Note: the feasible and infeasible populations are returned as list of tuples where the first item in the tuple is the fitness and the second item is the HintSet 



### MapElites.py

#### EliteGrid 

Data structure for representing the map elite grid. Some important parameters and methods are: 

* grid: a list of lists representing the grid. Each cell either contains ``None'' or a hintSet object 

* addChild: Children are added to the grid with the addChild method. To add a child a row (based on solution) and column (based on solver loops) are determined. The child is added if this cell is empty or the new child is at least as small in terms of hint size. 

* select: returns a random child in the grid 

* getFitnessGrid: return the fitness (hint size) of children in the grid (or -1 if cell is empty)

 #### History 
 This object tracks various values throughout evolution history 

 #### evolve 

 Runs contrained map-elites evolition 

 *inputs* 

 * puzzle: the puzzle being generated 
 *  generations: number of generations to run 
 *  pop_size: opulation size
 *  x_rate: cross over rate 
 *  mut_rate: mutation rate 
 *  add_rate: ratio of add mutations 
 *  elits: number elites (for infeasible pop)

 *outputs* 

 * feasibleGrid: the mapElites grid of all feasible children in last generation 
 * infeasiblePopulation: list of infeasible children in last generation 
* history: history object across evolution 

## Aiide-24 Files 

The trials presented in the AIIDE-24 paper are provided in the school3 folder, including the graphs generated. The code used for anayalsis and visualization is given in the MapElitesVisualation.py file. 