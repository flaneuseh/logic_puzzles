# logic_puzzles
This is a project for generating new logic grid puzzle. It uses a FI-2Pop genetic algorithm to generate puzzles that are both solvable and challenging. Solvable puzzles with complete and valid solution. Challenging puzzles are ones that require many round to complete. 

## Quick Start 

### Playing generated puzzles 
The generated puzzles are located in the [ENTER FOLDER HERE] and [ENTER FOLDER HERE] folders. The [ENTER FOLDER HERE] contains puzzles that were optimized both for difficulty and for small hint sizes, where the [ENTER FOLDER HERE] contians puzzles that were optimized for difficulty only. Each folder contains a hint.txt that contains the hints for each puzzle. For the puzzles you can use the [ENTER IMAGE HERE] to mark the your answers. You can check your solutions agains't the solutions in the solutions.txt file that is each both folders. 

### Looking at Experiment data 
Each experiment folder also contains several visualizations about the generated puzzles and the generation process. The "data.txt" file also contains key information from the experiment. Each "pop_<i>.p" file contains a pickled version of the feasible and infeasible population of the last generation for that trial, along with a history object, which tracks fitness over generations. 

### Running a new experiement 
New experiements can be run by modifying the "Experiments.py" file. At the top, several contains are defined. Most important is the "folder" which tells the program where to put experiement data. We recommend created a new folder for each experiement run. You can also modify the puzzle to generate puzzles with different themes. Note that currenlty puzzles are required to have at least one numeric category. 

After the experiement finishes running, you will need to run the "DataVisualisation.py" file, with the updated folder. This will produce "hint.txt" and "solutions.txt" files, of which you can look at and play your generated puzzles. 


### Version control for jupyter notebooks 
Version Control: (from https://github.com/mwouts/jupytext)

1. Install Jupytext using either ```pip install jupytext``` or ```conda install jupytext -c conda-forge```
2. Update the notebook based on the py file with ```jupytext --sync LogicPuzzles.py```
3. Create/update py file based on notebook: ```jupytext --set-formats ipynb,py:percent LogicPuzzles.ipynb```


JupyterLab using Conda (can also use pip for universal environments)
1. Install JupyterLab ```conda install jupyterlab -c conda-forge```
2. Install Jupytext ```conda install jupytext -c conda-forge```
3. ```jupyter lab``` to open the notebook/py editor
4. Edit the notebook using JupyterLab, and LogicPuzzles.py will auto-update (and vice versa, though be sure to keep only ONE open in Jupyter Lab at a time) At least in theory. Be sure to verify for yourself with a changing version number at the top of the notebook.
5. Happy Coding!