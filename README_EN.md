# Overview
This project works as an example to customize one's [FGO-py](https://github.com/hgjazhgj/FGO-py) script so that it (1) either finishes a battle more efficiently (2) or applies a certain set of strategies to cast skills and select cards.

# What it can do...
1. Finishing 90++ levels of events with a certain set of strategies, i.e., a master specifies explicitly which skills to cast and which cards to select at each stage;
2. Finishing some easy battles more efficiently (like Fuyuki);
3. Loop on a certain event quest (e.g., 90++) iteratively: clear the AP gauge, wait until you have 40 AP, and then continue to the next battle (This function is by default enabled).

# What it cannot do...
1. Finishing a battle that even the master does not how to deal with.

# Install
## Windows
1. Organize your directories as follows:
```
|-- FGO-py.portable\
|   |-- FGO-py.bat
|   |-- Git\
|   |-- Python311\
|   |-- FGO-py\
|   |   |-- deploy\
|   |   |-- doc\
|   |   |-- FGO-py\
|   |   |-- ...
|   |-- FGOPYCustomization\
|   |   |-- install.py
|   |   |-- ...
```
2. Change `FGO-py.bat` as follows (note we launch `install.py`) (please back up `FGO-py.bat` before you change it):
```
@echo off
title FGO-py
set "_root=%~dp0"
set "PATH=%_root%Python311;%_root%Python311\Scripts;%_root%Git\mingw64\bin;%PATH%"
cd "%_root%FGO-py\FGO-py"
python ../../deploy/updater.py
if errorlevel 1 (
    echo "Update failed. See above."
    pause
    exit
)
cd "%~dp0%.."
git clone https://github.com/suchandler96/FGOPYCustomization.git
cd "%~dp0%..\FGOPYCustomization"
git pull
cd "%_root%FGO-py\FGO-py"
python "%~dp0%..\FGOPYCustomization\install.py"
python fgo.py
```
## Linux
1. Organize your directories as follows:
```
|-- FGO-py\
|   |-- deploy\
|   |-- doc\
|   |-- FGO-py\
|   |-- ...
|-- FGOPYCustomization\
|   |-- install.py
|   |-- ...
```
2. `cd FGO-py/FGO-py && python3 ../../FGOPYCustomization/install.py`

# Detailed usage if you want to customize your own Turn classes
1. Inherit a class from `class Turn` or `class CustomTurn`(added in the patch file) and implement it with your own strategy (`NoHouguNoSkillTurn` and `Summer890PPTurn` in this repo are two examples). Give your customized Turn class a different name and put it in `FGO-py/FGO-py/customTurn.py` (create a new file);
2. For linux users, please run `install.py` every time you change `customTurn.py` for the changes to take effect. On Windows, the modified `FGO-py.bat` has already done this for you.
3. Note the FGO-py repo will be automatically `git reset --hard` in `install.py`;
4. After these steps, when FGO-py runs, it will call your implementation instead of the original `Turn` class. If you want to use the default `Turn` class, you can delete or rename your `customTurn.py` so that `install.py` will not find it.
5. Some APIs provided in `class CustomTurn`:
   - `selectCard_for_np(self,servant_id)`: select cards such that the specified servant can gain the most NP. `servant_id` starts from 0;
   - `castSingleOrNoTargetServantSkill(self,pos,skill,target)`: cast a servant skill. If it needs one target, set `target` to 0/1/2, depending on the target position; If it does not involve a target, set `target` to -1. `pos` and `skill` also start from 0;
   - `castMasterSkill(self, skill, targets)`: cast a master skill. `targets` should be a list of integers, even if it only needs one target. For instance, swapping the positions of the first and the 4th servants would require `targets = [0, 3]`;
   - `getNP(self)`: return a list of 3 integers;
   - `getServantHP(self)`: return a list of 3 integers.

# Uninstall
## Windows
1. Recover `FGO-py.bat` as follows (below shows the original code in case you didn't do backup before changing):
```
@echo off
title FGO-py
set "_root=%~dp0"
set "PATH=%_root%Python311;%_root%Python311\Scripts;%_root%Git\mingw64\bin;%PATH%"
cd "%_root%FGO-py\FGO-py"
python ../../deploy/updater.py
if errorlevel 1 (
    echo "Update failed. See above."
    pause
    exit
)
python fgo.py
```
2. Delete the directory `FGOPYCustomization` if you wish.
## Linux
1. `cd FGO-py/FGO-py && rm -rf fgoImage/slash.png && git reset --hard origin/master`
2. Delete the directory `FGOPYCustomization` if you wish.

# Some personal understanding of some variables in `FGO-py/FGO-py/fgoKernel.py`
1. class Turn -> self.servant: `list[int]`, each element corresponds to the ID of the servant. E.g., Mash Kyrielight = 1
2. class Turn -> color: `list[int]`, each element corresponds to the color of the card. 0: Arts, 1: Quick, 2: Buster;
3. class Turn -> group: `list[int]`, each element corresponds to the servant position ID of each of the 8 cards (5 regular + 3 Hougu), i.e., it must be a list consisting of 0,1,2 and a fixed length 8.

# Some tips
1. Customization is in fact against the design principle of FGO-py. So please be cautious when you want to send an issue or pull request to the FGO-py project.
2. Salute to FGO-py project!
