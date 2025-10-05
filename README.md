# 项目概览
本项目为魔改[FGO-py](https://github.com/hgjazhgj/FGO-py)提供了一套框架。我们知道FGO-py使用一套通用逻辑应对所有副本，但在某些场景中可以进一步优化，包括柱子战和容易暴毙的90++副本。而优化的手段则是用户手动指定一套出牌放技能策略，可以是成品作业，在配置不足时也可以模仿玩家自身逻辑选卡补刀、补NP等，从而形成作业和xjbd的结合。

尽管已经提供了简单明了的安装指导和函数说明，本项目仍需要少量Python基础。

# 本项目可以做到...
1. 以特定策略完成活动90++副本，即玩家显式指定每面的出卡放技能策略，并在1回合清不掉最后一面时继续补刀；
2. 提升异常简单的副本的通关效率（如冬木）；
3. 循环刷某个副本（如活动90++）: 清空AP，自回体到40AP后继续下一场（本功能默认启用，且暂不提供接口关闭）。

# 本项目不能...
1. 完成玩家都不知如何应对的副本。

# 安装
## Windows
1. 按照以下目录结构组织文件：
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
2. 按下修改`FGO-py.bat`（注意调用了`install.py`），并请在修改前备份原文件：
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
1. 按照以下目录结构组织文件：
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

# 定制策略的详细说明
1. 继承`class Turn`或`class CustomTurn`（安装后可以在`fgoKernel.py`中看到）实现自己的类，参考本项目中的`NoHouguNoSkillTurn`和`Summer890PPTurn`。核心代码可以直接从`class Turn`复制然后魔改。给这个类起个新名字，并放在`FGO-py/FGO-py/customTurn.py`中（要创建新文件）；
2. Linux用户请在每次更改`customTurn.py`后执行`python3 install.py`。Windows上这步已经涵盖在更改后的`FGO-py.bat`中了，无需额外操作；
3. 注意FGO-py仓库会在执行`install.py`时强制被`git reset --hard`。
4. 完成上述步骤后，FGO-py运行时会自动调用你实现的类，而非原本的`Turn`类。若想用回原本的`Turn`，请将`customTurn.py`重命名或删除。
5. `class CustomTurn`中实现了些便利的接口供参考：
   - `selectCard_for_np(self,servant_id)`：选择能使指定从者获得最多NP的卡。`servant_id`从0开始计数；
   - `castSingleOrNoTargetServantSkill(self,pos,skill,target)`：使用从者技能。若涉及单个目标，则`target`为0/1/2，对应场上三名从者；若不需选择目标，则`target`要设为-1。`pos`和`skill`也从0开始计数；
   - `castMasterSkill(self, skill, targets)`：使用御主技能。不论有几个目标，`targets`均应为整数列表。如换人服交换1号和4号位，则`targets = [0, 3]`；
   - `getNP(self)`：返回一个包含3个整数的列表；
   - `getServantHP(self)`：返回一个包含3个整数的列表。

# 卸载
## Windows
1. 按下恢复`FGO-py.bat`：
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
2. 删除`FGOPYCustomization`目录。
## Linux
1. `cd FGO-py/FGO-py && rm -rf fgoImage/slash.png && git reset --hard origin/master`
2. 删除`FGOPYCustomization`目录。

# `FGO-py/FGO-py/fgoKernel.py`中部分变量的个人理解
1. class Turn -> self.servant: `list[int]`，每个元素对应从者ID，如玛修=1； 
2. class Turn -> color: `list[int]`，每个元素对应指令卡颜色。0：Arts，1：Quick，2：Buster；
3. class Turn -> group: `list[int]`，每个元素对应场上8张指令卡（5发牌+3宝具）的所属从者站位。它必定由0、1、2组成且长度固定为8。

# 附注
1. 定制化与FGO-py的项目宗旨存在冲突，本项目仅为个人魔改，所以向FGO-py提交issue和PR前请三思。
2. 向FGO-py项目致敬！
