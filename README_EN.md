# Overview
This project works as an example to customize one's [FGO-py](https://github.com/hgjazhgj/FGO-py) script so that it (1) either finishes a battle more efficiently (2) or applies a certain set of strategies to cast skills and select cards, or even decides the actions according to the cards.

# What it can do...
1. Finishing 90++ levels of events with a certain set of strategies, i.e., a master specifies explicitly which skills to cast and which cards to select at each stage;
2. Finishing some easy battles more efficiently (like Fuyuki);
3. Loop on a certain event quest (e.g., 90++) iteratively: clear the AP gauge, wait until you have 40 AP, and then continue to the next battle (This function is by default enabled).

# What it cannot do...
1. Finishing a battle that even the master does not how to deal with.

# Install
## Windows
1. Change `FGO-py.bat` as follows (note we launch `install.py`, where the `-f` option can be followed by multiple files for customization. Please put these files under the `FGOPYCustomization` directory. Each of these files will be handled like a python class if it ends with `.py`; otherwise it should follow the conventions in section "Script Translator"). Also note you need to amend this bat file every time you write a new customization file. (Please back up `FGO-py.bat` before you change it):
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
cd "%~dp0"
git clone https://github.com/suchandler96/FGOPYCustomization.git
cd "%~dp0%FGOPYCustomization"
git pull
python install.py --fgo-py-root-dir "%_root%FGO-py" -f "%_root%FGO-py\FGO-py\customTurn.py"
cd "%_root%FGO-py\FGO-py"
python fgo.py
```
2. When you run the modified `FGO-py.bat`, it will automatically create a directory `FGOPYCustomization` under `FGO-py.portable`, as the hierarchy shown below:
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
3. Afterwards, double-click the modified `FGO-py.bat` to run FGO-py as usual.
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
2. Install the patch files and user-customized Turns into FGO-py: `cd FGOPYCustomization/ && python3 install.py -f ../FGO-py/FGO-py/customTurn.py`. If you refer to the "Script Translator" Section, you will find `-f` can also be followed with `.txt` files that contain the simplified representation for customized logic. If `install.py` isn't followed by the `-f` option, only the patch files will be installed, and no customized Turns will be installed. You need to run this command every time you change `customTurn.py` or change the customization files.
3. Run FGO-py in GUI or CLI mode as usual.

# Detailed usage if you want to customize your own Turn classes
1. Inherit a class from `class Turn` or `class CustomTurn`(added in the patch file) and implement it with your own strategy (`NoHouguNoSkillTurn` and `Summer890PPTurn` in this repo are two examples). Give your customized Turn class a different name and put it in `FGO-py/FGO-py/customTurn.py` (create a new file);
2. For linux users, please run `install.py` every time you change `customTurn.py` for the changes to take effect. On Windows, the modified `FGO-py.bat` has already done this for you.
3. No matter on Windows or Linux platforms, the FGO-py repo will be automatically `git reset --hard` in `install.py`, after which a patch file and the customized Turn will be installed. So please do backup your files if necessary;
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


# Script Translator
## Design Intention
The script translator is designed to simplify the programming of customized `Turn` class: several symbols would now suffice to represent a skill cast or card selection. Users now only need to write a simple sequence of such actions, and the customized `Turn` class will be generated by the script.

## Fitted Scenario and Usages
This feature is only supported when running FGO-py in command line interface (CLI) mode. As FGO-py by default runs in GUI on Windows, here we only show the usages on Linux. The sequence of actions needs to be placed in a separate file, e.g., `SampleTurnSeq.txt`, `WhitePaper90SS.txt` provided in the repo. If passed to `install.py` with the `-f` option, the script will automatically translate the file into python class and install it to `fgoKernel.py`. The `-f` option can be followed by 0 to multiple files for customization. At runtime, extra parameters can be added to the `main` or `battle` command to choose which logic to use.

Usually the user would run FGO-py in CLI mode as follows:
```
$ python fgo.py cli
> connnect 127.0.0.1:5555
> 169 invoke
> main 10 copper -s 10
```
If the script translator is to be used, slightly amending the `main` command would suffice:
```
> main 10 copper -s 10 -t <CustomTurnName>
```
where `<CustomTurnName>` is the prefix of the txt files that the user provides, e.g., `SampleTurnSeq` and `WhitePaper90SS`. For convenience, users can provide only several leading characters (e.g., `-f Sam`, or `-f Wh`) if there is no ambiguity. If there are multiple matches, the files won't be installed.

## Grammar
It roughly follows python-style if-else sequence and indent rules, in-line if-else branches (and even nested branches), and supports `#`-style comments. Loops are not supported as they are not needed.

### Numbering Conventions
All numbers start from 0. For instance, servants are numbered 0, 1, 2; skills are numbered 0, 1, 2. Master skills should start with `m`.

### Operators
1. `.`: Similar to `.` in python that connects an object and a class member, here it means **of**. Typical usages: skill 0 of servant 0 (`0.0`), skill 2 of master (`m.2`), green (quick) cards of servant 0 (`0.g`).
2. `*`: Any. Expected in specifying card types: `*.r` means red (buster) cards of any servant; `0.*` means any card of servant 0.
3. `>`: When used in `if` statements, it means **larger than**; when used in skill casting descriptions, it means **set the target of skills**: `0.1>2` means to cast skill 1 of servant 0, with servant 2 as the target. When multiple targets are involved, use brackets to include them. E.g., `m.2>(0,5)` means to set servant 0 and 5 as the targets of master skill 2, a typical scenario when exchanging servants.

### Keywords
1. `if...(elif)...else`: The same meaning as python condition statements. In conditional statements, logic operators (and, or, not, >, <, ==, >=, <=, !=) and brackets are supported just like normal python.
2. `r`, `g`, `b`: color of cards. Red (Buster), green (Quick), blue (Arts).
3. `exists()`: Used in `if` and `elif` conditions, to indicate whether certain types of cards exist.
4. `x`: Used inside `exists()` to indicate whether there are at least a specified number of a certain type of cards.
5. `np`: Used in a condition statement to indicate NP of a servant. `0.np` means the NP of the leftmost servant.
6. `target`: Specify which enemy to beat.
7. `hougu`: Specify the servant IDs that will use hougu this turn. Connect with `,` if multiple hougu are to be used.
8. `pre` & `post`: Specify the expected sequences of cards before (pre) and after (post) releasing hougu, from the highest priority to the lowest.
9. `sX`, `sXstY` (X & Y are numbers, and can be changed as you wish): Indicate that the following actions and configs are for stage X stageTurn Y.

### Examples:
1. `exists(2.b)`: There is an Arts card of the rightmost servant.
2. `exists(2 x 0.b)`: There are two Arts cards of the leftmost servant.
3. A larger code snippet:
```
s1:
if exists(2x0.r) and 0.np>=49:
    0.2>2, 0.0, 0.1>2, M.2>(0,5)
else: selectCard
target:2
hougu:2
post:(2.g,2.b),(2.g,2.*),(2.b, 2.*),(2.b, *)
```
This snippet specifies the behavior at stage 1. The `if...else` statement enables the user to act differently deciding upon whether the condition is met or not. The condition is "when there exists two buster cards of servant 0 and the NP of servant 0 no less than 49". When it is met, several servant and master skills are cast. Otherwise, the default `selectCard` function is called and the turn ends, so in the generated code, a `return` is inserted right after `selectCard`. Then we continue to set the actions for the case where the condition is met. The `target`, `hougu`, `post` fields set the behaviors of selecting cards. Here it sets the target to be enemy 2 (the rightmost enemy), and uses the hougu of servant 2 (the rightmost servant). The Sequence of brackets in `post` specifies the preferred cards to select after the hougu card, from the highest priority to the lowest. For example, here the most preferred combination is the *quick card of the rightmost servant, followed by the arts card of that servant*. Combinations that don't match any in the provided sequence have the same (lowest) priority.
4. For more examples, please check `SampleTurnSeq.txt` and `WhitePaper90SS.txt` in this repo.

# Some tips
1. Customization is in fact against the design principle of FGO-py. So please be cautious when you want to send an issue or pull request to the FGO-py project.
2. Salute to FGO-py project!
