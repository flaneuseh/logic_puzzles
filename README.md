# logic_puzzles

Version Control: (from https://github.com/mwouts/jupytext)

1. Install Jupytext using either ```pip install jupytext``` or ```conda install jupytext -c conda-forge```
2. Edit LogicPuzzles.py, and update the notebook with ```jupytext --sync LogicPuzzles.py```
3. Create/update py file based on notebook: ```jupytext --set-formats ipynb,py:percent notebook.ipynb```


JupyterLab using Conda (can also use pip for universal environments)
1. Install JupyterLab ```conda install jupyterlab -c conda-forge```
2. Install Jupytext ```conda install jupytext -c conda-forge```
3. ```jupyter lab``` to open the notebook/py editor
4. Edit the notebook using JupyterLab, and LogicPuzzles.py will auto-update (and vice versa, though be sure to keep only ONE open in Jupyter Lab at a time) At least in theory. .
5. Happy Coding!