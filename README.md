# 项目概览
本项目为魔改[FGO-py](https://github.com/hgjazhgj/FGO-py)提供了一套框架。我们知道FGO-py使用一套通用逻辑应对所有副本，但在某些场景中可以进一步优化，包括柱子战和容易暴毙的90++副本。而优化的手段则是用户手动指定一套出牌放技能策略，可以是成品作业，在配置不足时也可以模仿玩家自身逻辑选卡补刀、补NP等，或是视指令卡情况决定策略，从而形成作业和xjbd的结合。

尽管已经提供了简单明了的安装指导和函数说明，本项目仍需要少量Python基础。

# 本项目可以做到...
1. 以特定策略完成活动90++副本，即玩家显式指定每面的出卡放技能策略，并在1回合清不掉最后一面时继续补刀；
2. 提升异常简单的副本的通关效率（如冬木）；
3. 循环刷某个副本（如活动90++）: 清空AP，如果AP不够进行下一场则在结算界面等待，直到AP恢复到足够之后再继续下一场（本功能在以图形界面启动FGO-py时默认启用，且暂不提供方法关闭；在以CLI运行FGO-py时，仅在运行`main`时附加`--wait-for-ap`命令时会启用该功能）。

# 本项目不能...
1. 完成玩家都不知如何应对的副本。

# 安装
## Windows
1. 按下修改`FGO-py.bat`（注意调用了`install.py`），并请在修改前备份原文件：
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
2. 首次双击运行修改后的`FGO-py.bat`启动FGO-py时会自动在`FGO-py.portable`目录下创建`FGOPYCustomization`目录，如下所示：
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
3. 往后每次运行都照常双击`FGO-py.bat`即可。

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
2. 将本项目提供的补丁和定制策略安装到FGO-py项目中：`cd FGOPYCustomization/ && python3 install.py -f ../FGO-py/FGO-py/customTurn.py`。若参考“脚本翻译器”一节，`-f`后也可以是写有定制策略信息的`.txt`文件。若运行`install.py`时不指定`-f`参数，则不安装定制策略，仅打补丁。每次修改`customTurn.py`、或更换定制策略的文件后都需要重新运行此命令。
3. 按照自身习惯运行FGO-py的图形界面或CLI。

# 定制策略的详细说明
1. 继承`class Turn`或`class CustomTurn`（安装后可以在`fgoKernel.py`中看到）实现自己的类，参考本项目中的`NoHouguNoSkillTurn`和`Summer890PPTurn`。核心代码可以直接从`class Turn`复制然后魔改。给这个类起个新名字，并放在`FGO-py/FGO-py/customTurn.py`中（要创建新文件）；
2. Linux用户请在每次更改`customTurn.py`后执行`python3 install.py -f ../FGO-py/FGO-py/customTurn.py`。Windows上这步已经涵盖在更改后的`FGO-py.bat`中了，无需额外操作；
3. 不论在Windows还是Linux平台上执行`install.py`时，FGO-py仓库都会先强制被`git reset --hard`重置，而后再安装补丁和定制的行动逻辑。所以如有修改，请在执行前做好备份。
4. 完成上述步骤后，FGO-py运行时会自动调用你实现的类，而非原本的`Turn`类。若想用回原本的`Turn`，请将`customTurn.py`删除或将其内容清空。
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

# 脚本翻译器
## 设计目的
脚本翻译器旨在简化定制`Turn`类时的编程过程：仅使用几个字符即可表示技能释放或选卡操作。用户只需编写一段简单的行动代码，脚本即可自动生成定制的`Turn`类。

## 适用范围与使用方法
目前只支持在命令行界面（CLI）模式下运行FGO-py时使用该功能。由于Windows上的FGO-py默认以图形界面运行，此处使用Linux运行。这串行动代码需要放在单独的文件中，例如本仓库提供的`SampleTurnSeq.txt`和`WhitePaper90SS.txt`。如果将该文件作为`-f`的参数传给`install.py`，它会自动将其翻译成Python的类并复制到`fgoKernel.py`中。`-f`后可以加0至多个定制逻辑的描述文件，在运行时可以在`main`或`battle`命令后加额外参数选择用哪个逻辑打当前副本。

一般运行FGO-py的CLI是这样操作的：
```
$ python fgo.py cli
> connnect 127.0.0.1:5555
> 169 invoke
> main 10 copper -s 10
```
若想用脚本翻译器生成的定制逻辑打副本，少许修改`main`命令即可：
```
> main 10 copper -s 10 -t <CustomTurnName>
```
其中`<CustomTurnName>`是用户提供的txt文件名的前缀，例如`SampleTurnSeq`或`WhitePaper90SS`。但为了方便起见，用户也可以在不引起歧义时只提供开头几个字符，如`-f Sam`或`-f Wh`。如果发现有多个匹配项则会不予安装。

## 语法
它大致遵循Python风格的if-else语句和缩进规则（甚至允许嵌套），支持行内if-else分支，以及可以用`#`注释。但不支持循环，因为不需要。

### 计数约定
所有数均从0开始计数。例如，从者编号为0、1、2；技能编号为0、1、2。御主技能需以`m`开头。

### 操作符
1. `.`：与Python中连接对象和类的成员的`.`相似，这里它也表示**的**。典型用例：从者0的技能0（`0.0`），御主的技能2（`m.2`），从者0的绿卡（`0.g`）。
2. `*`：通配符，在指定指令卡类型时使用：`*.r` 表示任意从者的红卡；`0.*`表示从者0的任意卡。
3. `>`：当在`if`的条件语句中使用时，它就是大于号；但在使用技能的字符串里，它表示**使用技能的目标**：`0.1>2` 表示使用0从者的1技能，并以2号从者（最右侧从者）为目标。当涉及多目标时，需要用括号将目标包起来，例如换人：`m.2>(0,5)`表示使用御主2技能（最右侧技能），目标是0和5号从者。

### 关键字
1. `if...(elif)...else`：与python条件语句含义相同。在条件语句中，逻辑运算符（and、or、not、>、<、==、>=、<=、!=）和括号均与普通python相同。
2. `r`, `g`, `b`: 指令卡颜色。红卡（red, Buster），绿卡（green, Quick），蓝卡（blue, Arts）。
3. `exists()`：仅限`if`和`elif`的条件中使用，用以表示**特定种类的卡是否存在**。
4. `x`: 仅限在`exists()`的括号内使用，用以表示**是否存在特定张数的某种卡**。
5. `np`：仅限在条件语句中表示从者的NP。`0.np`表示最左侧从者的NP。
6. `target`：指定指令卡的目标。
7. `hougu`：指定本回合要使用宝具的从者ID。若有多名从者要放宝具，他们的ID之间用逗号连接。
8. `pre` & `post`：指定在使用宝具之前和之后要选取的指令卡。用户可以输入多种期望选取的指令卡组合，组合与组合之间用逗号连接，优先级从高到低。
9. `sX`, `sXstY`（X & Y是数字，用户可自行更改）：表示从这里往下的行动和配置信息都是针对第X面（stage）、该面的第Y回合（stageTurn）的。

### 示例
1. `exists(2.b)`: 存在2号（最右侧）从者的蓝卡。
2. `exists(2 x 0.b)`：存在2张0号（最左侧）从者的蓝卡。
3. 下面看一个更复杂的例子：
```
s1:
if exists(2x0.r) and 0.np>=49:
    0.2>2, 0.0, 0.1>2, M.2>(0,5)
else: selectCard
target:2
hougu:2
post:(2.g,2.b),(2.g,2.*),(2.b, 2.*),(2.b, *)
```
这段代码定义了第1面（s1）的行为。`if...else`语句允许用户根据条件是否满足采取不同行动。这里的条件则是“存在2张0号从者的红卡，且0号从者的NP至少为49”。当条件满足时，则会释放一系列从者和御主技能。否则，此例调用了默认的`selectCard`函数。由于选好卡之后这个Turn就结束了，于是在生成的代码中会紧随`selectCard`插入`return`。如果`else`语句后也是放技能序列，而不包括出卡的函数，则不会插入`return`。在`else`语句结束后，示例代码继续为条件被满足的情况设置出卡信息，即此处的`target`，`hougu`，`post`这三行。这里目标设为了2号敌人（3个怪的最右侧敌人），2号（最右侧）从者要放宝具。`post`这行的一系列括号则表示用户给的若干种宝具后的候选出牌方法，优先级从左至右为从高到低。由于这里只有1个从者放宝具，宝具前不出卡，所以宝具后要选2张卡。为了表示2张卡的组合，就需要打上括号。例如这里优先级最高的出卡方法是2号从者的绿卡、2号的蓝卡。如果没有这种组合，则次优先的是2号的绿卡和2号的任意卡。最后一种`(2.b, *)`表示只要有2号从者的蓝卡，另一张卡可以是任意卡。当所有组合都不匹配时，则会随机出卡。
4. 更多例子请参考仓库中的`SampleTurnSeq.txt`和`WhitePaper90SS.txt`。

# 附注
1. 定制化与FGO-py的项目宗旨存在冲突，本项目仅为个人魔改，所以向FGO-py提交issue和PR前请三思。
2. 向FGO-py项目致敬！
