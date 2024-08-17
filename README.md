# Overview
This project works as an example to customize one's FGO-py script so that it (1) either finishes a battle more efficiently (2) or applies a certain set of strategies to cast skills and select cards.

# What it can do...
1. Finishing 90++ levels of events with a certain set of strategies, i.e., a master specifies explicitly which skills to cast and which cards to select at each stage;
2. Finishing some easy battles more efficiently (like Fuyuki);
3. ...

# What it cannot do...
1. Finishing a battle that even the master does not how to deal with.

# Usage
1. Inherit a class from `class Turn` in FGO-py/FGO-py/fgoKernel.py and implement it with your own strategy (`NoHouguNoSkillTurn` and `Summer890PPTurn` in this repo are two examples);
2. Set the default class of turn in `class Battle` to the subclass of Turn that you have just implemented;
3. For Windows users, please comment out the lines of codes related to updating in `FGO-py.bat`, so that your modification will not get erased by `git reset --hard`.

# Some personal understanding of some variables in `FGO-py/FGO-py/fgoKernel.py`
1. class Turn -> self.servant: `list[int]`, each element corresponds to the ID of the servant. E.g., Mash Kyrielight = 1
2. class Turn -> color: `list[int]`, each element corresponds to the color of the card. 0: Arts, 1: Quick, 2: Buster;
3. class Turn -> group: `list[int]`, each element corresponds to the servant position ID of each of the 8 cards (5 regular + 3 Hougu), i.e., it must be a list consisting of 0,1,2 and a fixed length 8.

# Some tips
1. Customization is in fact against the design principle of FGO-py. So please be cautious when you want to send an issue or pull request to the FGO-py project.
2. Salute to FGO-py project!
