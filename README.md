# logic_puzzles
This project is to host a backend generator server for logic puzzles. The generator using a constrained quality diversity algorithm to create puzzles that are valid and vary in terms of solution and difficulty. This server can be run locally or on a virtual machine. 


## Run the backend locally 

### Step 1: Install Python 
Install python onto your computer. This project was based on python version 3.10.12 

https://www.python.org/ 

### Step 2: Install MongoDB 

Following the instructions to install Mongo on your computer. 

https://www.mongodb.com/docs/manual/installation/ 

Make sure a MongoDB instance is running before starting 

### Step 3: Download Code and Install Packages 
Install code onto your computer and go to that directory in your terminal. 

Start a python virtual environment with the following code: 

```
python3 -m venv
```

Run the environment with the following command 

```
source venv/bin/activate 
```

Install all the necessary packages: 

```
pip install flask==3.1.0
pip install flask_cors==5.0.0
pip install jsonpickle==3.0.2
pip install pymongo==4.11.1
```

### Load data 
If you want to add a user, add the data.json file to the main code directory. Then run the following code (with the virtual environment active): 

```
python LoadData.py
```

### Run main.py 
In the code directory run the code to launch the database: 

```
python main.py
```

The flask server should now be running on localhost:3000 

## Hosting on a VM 

### Setting up VM  
We mostly followed this tutorial: https://medium.com/@adityaarya1/deploy-a-flask-application-to-azure-vm-with-a-ssl-certificate-d2960c50783d 

The main steps are: 

1. Create a VM 
2. Set up the code as you would locally 
3. Set up a Gunicorn instance to run the falsk server
4. Set up a Nginx server 
5. User certbox to run on https 



### Updating VM once set up 

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



## Major API end points 


### /iterate_map_evolve
Conduct a cycle of generation. 
Parameters: 
* user: password for user 
* id: id of mapElites grid to generate. If not included, a new grid will be create and the id will be returned 
* puzzle: base puzzle (categories, entities, scenario) to evolve hints for 

Optional Evolution parameters: 
* gens: number of generations to run 
* pop_size: number of children to create per generation 
* x_rate: cross over rate 
* mut_rate: mutation rate 
* add_rate: ratio of how often to add hint in mutation 
* elites: number of elites in the infeasible population 

### /add_account 
admin accounts can add users. 

Parameters: 
* user: admin password
* privateKey: password of new account 
* publicKey: username of new user
* mode: interface type out of [casual, serious, mixed, admin]

### /like_puzzle
Add puzzle to users liked puzzles. 

Parameters: 
* username: password of user 
* puzzle: json representation of puzzle 
### /remove_puzzle 
Remove puzzle from users liked puzzles.

Parameters: 
* username: password of user
* key: unique index of puzzle to remove

### /update_puzzle 
Replace liked puzzles with new version. 

Parameters: 
* username: password of user
* key: unique index of puzzle to update
* puzzle: json representation of updated puzzle 

### /get_liked_puzzles 
Returns a list of all liked puzzles for user.

Parameters: 
* username: password of user

### /add_scenario 
Adds a new scenario for user to access later. 

Parameters: 
* user: password of user, if admin scenario will be added to sample  
* name: name of scenario
* scenario: text explanation of scenario 
* categories: list of categories within scenario 

### /update_scenario 
Updates an existing scenario with new data 

Parameters: 
* user: password of user, if admin scenario will be added to sample  
* name: name of scenario
* scenario: text explanation of scenario 
* categories: list of categories within scenario 

### /delete_scenario 
Remove a scenario 

Parameters: 
* user: password of user
* name: name of scenario

### /get_scenarios 
Get the scenarios for a user 

Parameters: 
* user: password of user 

### /get_unused_grammar 
Returns the list of hints that will have the default grammar

Parameters: 
* username: password of user 
* cats: list of categories to test for 

### /add_grammar_rule
Add a new grammar template for a hint. 

Parameters: 
* user: password of user, if admin grammar will be added to sample 
* type: type of hint from [is, not, before, or]
* all hint parameters: all categories for hint type from: cat1, cat2, is_cat, num_cat 
* template [times and untimed for before]: String template for hint. Parameters should be surrounded by curly braces. For example "{ent1} is {ent2}" 

### /get_template 

Get the template of a hint for a user 

parameters: 
* user: password of user 
* type: type of hint 
* all hint parameters: all categories for hint type from: cat1, cat2, is_cat, num_cat

### /get_brainstorm 
Gets all the narrative brainstorms of a hint for a user 

parameters: 
* user: password of user 
* type: type of hint 
* all hint parameters: all categories for hint type from: cat1, cat2, is_cat, num_cat 

### /add_brainstorm 
Add a narrative brainstorm for a hint 

Parameters: 
* user: password of user, if admin grammar will be added to sample 
* type: type of hint from [is, not, before, or]
* all hint parameters: all categories for hint type from: cat1, cat2, is_cat, num_cat 
* template [times and untimed for before]: String template for hint. Parameters should be surrounded by curly braces. For example "{ent1} is {ent2}" 

### /get_public_key
Gets the username and mode of a user 

Parameters: 
* user: password of user 

### /get_posted_puzzles
Returns all puzzles in community of user 

Parameter: 
* user: password of user 
 


### /post_puzzle 
Post a puzzle to the community 

Parameters: 
* username: password of user 
* puzzle : json representation of puzzle 
* title: title of post 
* body: body of post 
* time: time of post as string 

### /add_comment
Add a comment to a posted puzzle 

Parameters: 
* username: password of user 
* comment: text of comment 
* puzzleId: Id of post 
* time: time of comment as string 


### /get_user_data
Get all data associated with a user

Parameters: 
* user: password of user 


## Important Files 

### Database.py 
Functions to manage the MonogDB database 

### main.py 
End points for the flask API. 

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

