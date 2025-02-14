# 天国拯救骰子游戏

## 一、简介

这是一款模拟天国拯救系列玩法的骰子游戏，支持本地对战、与电脑玩家对战两种模式。游戏中玩家通过投掷骰子，选择有效计分的骰子来积累分数，率先达到目标分数的玩家获胜。本程序由豆包编程助手编写，将趣味性和策略性相结合，为玩家带来愉快的游戏体验。

## 二、功能特性

### 1. 多种对战模式
提供本地对战和与电脑玩家对战两种模式，满足不同玩家的需求。

### 2. AI 智能决策
电脑玩家（AI）会根据场上情况，如剩余分数、剩余骰子数量等，运用权重策略进行智能决策，选择激进或保守的游戏路径。

### 3. 操作记录台
详细记录双方玩家每一轮的操作，包括选取的骰子点数、得分情况以及决策（继续投掷或结束本轮），方便玩家回顾游戏过程。

### 4. 实时计分
游戏过程中实时显示当前玩家、总得分、本轮得分以及选中骰子组合的得分，让玩家清晰了解游戏状态。

## 三、安装与运行

### 安装依赖
本程序使用 Python 编写，需要安装以下依赖库：
- `tkinter`：Python 内置的 GUI 库，无需额外安装。
- `Pillow`：用于处理图片，可使用以下命令安装：
```bash
pip install pillow
```

### 运行程序
1. 将代码保存为一个 Python 文件，例如 `dice_game.py`。
2. 确保 `StartUI.png` 文件与 Python 代码文件在同一目录下，该文件为游戏启动界面的背景图片。
3. 在终端中运行以下命令启动游戏：
```bash
python dice_game.py
```

## 四、游戏规则

### 1. 底注选择
游戏开始时，玩家需要选择底注，底注分为“乞丐(1000 分)”、“农民(2000 分)”、“骑士(4000 分)”、“国王(8000 分)”四种，底注分数即为游戏的目标分数。

### 2. 回合流程
- 玩家轮流投掷 6 个骰子。
- 检查投掷结果是否有有效计分的骰子（如单个 1 或 5、三个相同点数等），若没有则失去本轮所有分数，结束本轮。
- 若有有效计分的骰子，玩家可以选择保留部分或全部计分骰子，并获得相应分数。
- 玩家可以选择继续投掷剩余骰子以获取更多分数，也可以选择结束本轮，将本轮得分累加到总得分中。

### 3. 获胜条件
率先达到目标分数的玩家获胜。

## 五、代码结构

### 主要类
1. **`StartUI` 类**：负责游戏启动界面的显示，包括开始游戏、关于、退出游戏等按钮，以及底注和对战模式的选择。
2. **`DiceGame` 类**：游戏的核心类，处理游戏的主要逻辑，包括骰子投掷、计分计算、玩家操作处理、AI 决策等。

### 主要函数
- `is_die_scoring`：检查单个骰子是否有效计分。
- `calculate_score`：计算一次投掷中选中骰子的得分。
- `has_scoring_opportunity`：检查投掷结果是否有得分机会。
- `all_dice_scoring`：检查选中的骰子是否全部有效计分。

## 六、贡献与反馈

如果你对本项目感兴趣，欢迎进行以下操作：
- **提出问题**：如果你在使用过程中遇到任何问题或发现 BUG，可以在项目的 Issues 板块提交问题。
- **贡献代码**：如果你有改进的想法或功能建议，可以提交 Pull Request，我会及时查看并处理。

## 七、版权信息

本项目采用[MIT]开源，你可以自由使用、修改和分发本代码。

作者：豆包编程助手

日期：2024 年 7 月 11 日 
