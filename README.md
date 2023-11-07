# logic_puzzles

Version Control: (from https://github.com/mwouts/jupytext)

1. Install Jupytext using either ```pip install jupytext``` or ```conda install jupytext -c conda-forge```
2. Edit LogicPuzzles.py, and update the notebook with ```jupytext --sync LogicPuzzles.py```
3. Don't directly edit the notebook, unless you're using JupyterLab


JupyterLab using Conda (can also use pip for universal environments)
1. Install JupyterLab ```conda install jupyterlab -c conda-forge```
2. Install Jupytext ```conda install jupytext -c conda-forge```
3. ```jupyter lab```
4. Pair the notebook to the text file / create text file if it does not exist: ```jupytext --set-formats ipynb,py:percent notebook.ipynb```
5. Edit the notebook using JupyterLab, and LogicPuzzles.py will auto-update (and vice versa, though be sure to keep only ONE open in Jupyter Lab at a time).
6. Happy Coding!