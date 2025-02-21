import tkinter as tk
from tkinter import messagebox, font
from tkinter import ttk
from PIL import Image, ImageTk, ImageFont
import random
import sys
import time
from itertools import combinations
import socket
import threading

# 骰子表情符号映射
DICE_EMOJI = {
    1: "⚀",
    2: "⚁",
    3: "⚂",
    4: "⚃",
    5: "⚄",
    6: "⚅"
}

# 检查单个骰子是否有效计分
def is_die_scoring(die, counts):
    if die == 1 or die == 5:
        return True
    if counts[die] >= 3:
        return True
    # 检查顺子情况比较复杂，这里简化处理，暂不考虑部分顺子组成情况
    return False

# 计算一次投掷的得分
def calculate_score(dice):
    score = 0
    counts = [0] * 7  # 用于记录每个点数出现的次数
    for die in dice:
        counts[die] += 1

    # 计算单个 1 和 5 的得分
    score += counts[1] * 100
    score += counts[5] * 50

    # 处理三个相同点数及以上的情况
    for i in range(1, 7):
        if counts[i] >= 3:
            if i == 1:
                base_score = 1000
            else:
                base_score = i * 100
            multiplier = 2 ** (counts[i] - 3)
            score += base_score * multiplier
            if i == 1:
                score -= counts[1] * 100  # 减去之前单独计算的 1 的得分
            if i == 5:
                score -= counts[5] * 50  # 减去之前单独计算的 5 的得分

    # 检查顺子
    if all(counts[1:7]):
        score = 1500
    elif counts[1] and counts[2] and counts[3] and counts[4] and counts[5]:
        score = 500

    return score

# 检查是否有得分机会
def has_scoring_opportunity(dice):
    return calculate_score(dice) > 0

# 检查选中的骰子是否全部有效计分
def all_dice_scoring(kept_dice, all_dice):
    counts = [0] * 7
    for die in all_dice:
        counts[die] += 1
    for die in kept_dice:
        if not is_die_scoring(die, counts):
            return False
    return True

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
        self.widget.bind("<Motion>", self.update_tooltip_position)

    def show_tooltip(self, event):
        if self.tooltip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tooltip(self, event):
        tw = self.tooltip_window
        self.tooltip_window = None
        if tw:
            tw.destroy()

    def update_tooltip_position(self, event):
        if self.tooltip_window:
            x, y = event.x_root + 25, event.y_root + 25
            self.tooltip_window.wm_geometry(f"+{x}+{y}")

class DiceGame:
    def __init__(self, root, target_score, is_ai_mode=False):
        self.root = root
        self.root.title("天国拯救骰子游戏")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        self.player1_score = 0
        self.player2_score = 0
        self.current_player = 1
        self.round_score = 0
        self.remaining_dice = 6
        self.dice = []
        self.kept_dice = []
        self.target_score = target_score
        self.has_rolled = False  # 标记是否已经投掷过骰子
        self.is_ai_mode = is_ai_mode  # 是否为 AI 对战模式
        self.round_num = 1
        self.animation_duration = 1000  # 动画总时长（毫秒）
        self.animation_steps = 20  # 动画步数
        self.animation_interval = self.animation_duration // self.animation_steps  # 每步间隔时间
        self.animation_running = False  # 动画是否正在运行

        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 显示当前操作玩家
        self.player_label = tk.Label(root, text=f"当前轮到: 玩家 {self.current_player}",font=("Huiwen-mincho", 16), bd=2, relief=tk.RIDGE)
        self.player_label.place(x=10, y=10)

        # 显示玩家1得分
        self.player1_total_score_label = tk.Label(root, text=f"玩家 1 总得分: {self.player1_score}",font=("Huiwen-mincho", 16))
        self.player1_total_score_label.place(x=10, y=60)

        # 显示玩家2得分
        self.player2_total_score_label = tk.Label(root, text=f"玩家 2 总得分: {self.player2_score}",font=("Huiwen-mincho", 16))
        self.player2_total_score_label.place(x=10, y=100)

        # 显示目标得分
        self.target_score_label = tk.Label(root, text=f"目标得分:{self.target_score}",font=("Huiwen-mincho", 16))
        self.target_score_label.place(x=5, y=480)

        # 显示本轮得分
        self.round_score_label = tk.Label(root, text=f"本轮: {self.round_score}",font=("Huiwen-mincho", 16))
        self.round_score_label.place(x=5, y=510)

        # 实时计分器
        self.selected_score_label = tk.Label(root, text="选中: 0",font=("Huiwen-mincho", 16))
        self.selected_score_label.place(x=5, y=540)

        # 骰子按钮
        self.dice_buttons = []
        default_font_size = 10  # 假设默认字体大小为 10
        enlarged_font_size = default_font_size * 8  # 放大 5 倍
        enlarged_font = ("Arial", enlarged_font_size)
        zeroX = 10
        button1 = tk.Button(root, text="", font=enlarged_font, command=lambda: self.toggle_keep_dice(0))
        button1.place(x=180, y=180, width=80, height=80)
        self.dice_buttons.append(button1)
        Tooltip(button1, "普通骰子")

        button2 = tk.Button(root, text="", font=enlarged_font, command=lambda: self.toggle_keep_dice(1))
        button2.place(x=330, y=180, width=80, height=80)
        self.dice_buttons.append(button2)
        Tooltip(button2, "普通骰子")

        button3 = tk.Button(root, text="", font=enlarged_font, command=lambda: self.toggle_keep_dice(2))
        button3.place(x=480, y=180, width=80, height=80)
        self.dice_buttons.append(button3)
        Tooltip(button3, "普通骰子")

        button4 = tk.Button(root, text="", font=enlarged_font, command=lambda: self.toggle_keep_dice(3))
        button4.place(x=180, y=330, width=80, height=80)
        self.dice_buttons.append(button4)
        Tooltip(button4, "普通骰子")

        button5 = tk.Button(root, text="", font=enlarged_font, command=lambda: self.toggle_keep_dice(4))
        button5.place(x=330, y=330, width=80, height=80)
        self.dice_buttons.append(button5)
        Tooltip(button5, "普通骰子")

        button6 = tk.Button(root, text="", font=enlarged_font, command=lambda: self.toggle_keep_dice(5))
        button6.place(x=480, y=330, width=80, height=80)
        self.dice_buttons.append(button6)
        Tooltip(button6, "普通骰子")

        # 投掷按钮
        self.roll_button = tk.Button(root, text="投掷骰子",font=("Huiwen-mincho", 16),command=self.roll_dice)
        self.roll_button.place(x=690, y=420)

        # 继续/结束按钮
        self.continue_button = tk.Button(root, text="继续投掷", font=("Huiwen-mincho", 16),command=self.continue_turn, state=tk.DISABLED)
        self.continue_button.place(x=690, y=480)
        self.end_turn_button = tk.Button(root, text="结束本轮", font=("Huiwen-mincho", 16),command=self.end_turn, state=tk.DISABLED)
        self.end_turn_button.place(x=690, y=540)

        # 操作日志
        self.record_text = tk.Text(root, height=6, width=68,font=("微软雅黑", 10),bd=2, relief=tk.RIDGE)
        self.record_text.place(x=225, y=10)

        if self.is_ai_mode and self.current_player == 2:
            self.root.after(self._get_random_delay(), self.ai_turn)

    # 在DiceGame类中添加一个方法用于插入日志并滚动到最底部
    def insert_log(self, action):
        self.record_text.insert(tk.END, action)
        self.record_text.see(tk.END)

    def on_closing(self):
        self.root.destroy()
        sys.exit()

    def roll_dice(self):
        self.roll_button.config(state=tk.DISABLED)
        if self.has_rolled or self.animation_running:
            return  # 如果已经投掷过或动画正在运行，不进行任何操作
        self.kept_dice = []
        self.animation_running = True
        self.animate_dice(0)

    # 骰子动画
    def animate_dice(self, step):
        if step < self.animation_steps:
            for i, button in enumerate(self.dice_buttons):
                if i < self.remaining_dice:
                    button.config(state=tk.NORMAL, bg="SystemButtonFace", relief=tk.RAISED)
                    button.config(text=DICE_EMOJI[random.randint(1, 6)])
                else:
                    button.config(text="", state=tk.DISABLED, bg="SystemButtonFace", relief=tk.RAISED)
            self.root.after(self.animation_interval, self.animate_dice, step + 1)
        else:
            self.animation_running = False
            self.finalize_roll()

    # 摇骰子结束后的处理
    def finalize_roll(self):
        self.dice = [random.randint(1, 6) for _ in range(self.remaining_dice)] #生成随机骰子点数
        for i, die in enumerate(self.dice):
            self.dice_buttons[i].config(text=DICE_EMOJI[die])  # 更新按钮骰子点数显示

        if not has_scoring_opportunity(self.dice):
            action = f"[回合{self.round_num}][{'AI' if self.current_player == 2 and self.is_ai_mode else '玩家'}]投掷骰子无得分机会，回合结束，回合得分为0。\n"
            self.insert_log(action)
            self.round_score = 0
            self.end_turn()
            return
        else:
            self.continue_button.config(state=tk.DISABLED)  # 初始时继续投掷按钮不可用
            self.end_turn_button.config(state=tk.DISABLED)  # 初始时结束按钮不可用
            self.has_rolled = True
            self.update_continue_button_state()
            self.update_selected_score()
        self.roll_button.config(state=tk.DISABLED)  # 投掷后禁用投掷按钮

        # 如果是AI模式且当前玩家是AI，自动选择骰子
        if self.is_ai_mode and self.current_player == 2:
            # 禁用玩家操作按钮
            for button in self.dice_buttons:
                button.config(state=tk.DISABLED, disabledforeground=button.cget("foreground"))
            self.roll_button.config(state=tk.DISABLED)
            self.continue_button.config(state=tk.DISABLED)
            self.end_turn_button.config(state=tk.DISABLED)
            self.root.after(self._get_random_delay(), self.ai_choose_dice) # AI选择骰子
        else:
            # 启用玩家操作按钮
            for button in self.dice_buttons:
                button.config(state=tk.NORMAL)
            self.roll_button.config(state=tk.DISABLED)
            self.continue_button.config(state=tk.DISABLED)
            self.end_turn_button.config(state=tk.DISABLED)

    def toggle_keep_dice(self, index):
        if index < len(self.dice):
            if index in self.kept_dice:
                self.kept_dice.remove(index)
                self.dice_buttons[index].config(bg="SystemButtonFace", relief=tk.RAISED)
            else:
                self.kept_dice.append(index)
                self.dice_buttons[index].config(bg="green", relief=tk.SUNKEN)
            self.update_continue_button_state()
            self.update_selected_score()

    def update_continue_button_state(self):
        if self.is_ai_mode and self.current_player == 2:
            return  # 如果是AI操作，不改变按钮状态
        kept_values = [self.dice[i] for i in self.kept_dice]
        if len(self.kept_dice) > 0 and all_dice_scoring(kept_values, self.dice):
            self.continue_button.config(state=tk.NORMAL)
            self.end_turn_button.config(state=tk.NORMAL)  # 启用结束按钮
        else:
            self.continue_button.config(state=tk.DISABLED)
            self.end_turn_button.config(state=tk.DISABLED)  # 禁用结束按钮

    def update_selected_score(self):
        kept_values = [self.dice[i] for i in self.kept_dice]
        if all_dice_scoring(kept_values, self.dice):
            score = calculate_score(kept_values)
        else:
            score = 0
        self.selected_score_label.config(text=f"选中: {score}")

    def continue_turn(self):
        kept_values = [self.dice[i] for i in self.kept_dice]
        score = calculate_score(kept_values)
        self.round_score += score
        self.round_score_label.config(text=f"本轮: {self.round_score}")  # 更新本轮得分显示
        action = f"[回合{self.round_num}][{'AI' if self.current_player == 2 and self.is_ai_mode else '玩家'}]选取骰子点数为: {' '.join(map(str, kept_values))},获取得分{score},回合得分为{self.round_score},[选择]继续投掷\n"
        self.insert_log(action)
        remaining = []
        remaining_buttons = []
        for i, die in enumerate(self.dice):
            if i not in self.kept_dice:
                remaining.append(die)
                remaining_buttons.append(i)
        self.remaining_dice = len(remaining)
        if self.remaining_dice == 0:
            self.remaining_dice = 6
        self.dice = remaining
        for i in range(6):
            if i in remaining_buttons:
                self.dice_buttons[i].config(state=tk.NORMAL)
            else:
                self.dice_buttons[i].config(text="", state=tk.DISABLED, bg="SystemButtonFace", relief=tk.RAISED)
        self.has_rolled = False  # 重置投掷标记
        self.roll_button.config(state=tk.NORMAL)  # 启用投掷按钮
        self.continue_button.config(state=tk.DISABLED)  # 继续投掷按钮初始不可用
        self.roll_dice()

    def end_turn(self):
        kept_values = [self.dice[i] for i in self.kept_dice]
        score = calculate_score(kept_values)
        self.round_score += score
        action = f"[回合{self.round_num}][{'AI' if self.current_player == 2 and self.is_ai_mode else '玩家'}]选取骰子点数为: {' '.join(map(str, kept_values))},获取得分{score},回合得分为{self.round_score},[选择]结束本轮\n"
        self.record_text.insert(tk.END, action)
        if self.current_player == 1:
            self.player1_score += self.round_score
            self.current_player = 2
        else:
            self.player2_score += self.round_score
            self.current_player = 1
            self.round_num += 1

        self.player1_total_score_label.config(text=f"玩家 1 总得分: {self.player1_score}")
        self.player2_total_score_label.config(text=f"玩家 2 总得分: {self.player2_score}")
        self.round_score = 0
        self.round_score_label.config(text=f"本轮: {self.round_score}")
        self.remaining_dice = 6
        self.player_label.config(text=f"当前玩家: 玩家 {self.current_player}")

        for button in self.dice_buttons:
            button.config(text="", bg="SystemButtonFace", state=tk.DISABLED, relief=tk.RAISED)
        self.continue_button.config(state=tk.DISABLED)
        self.end_turn_button.config(state=tk.DISABLED)
        self.selected_score_label.config(text="选中: 0")
        self.has_rolled = False  # 重置投掷标记
        self.roll_button.config(state=tk.NORMAL)  # 启用投掷按钮

        if self.player1_score >= self.target_score:
            messagebox.showinfo("游戏结束", "玩家 1 获胜！")
            self.root.destroy()
            sys.exit()
        elif self.player2_score >= self.target_score:
            messagebox.showinfo("游戏结束", "玩家 2 获胜！")
            self.root.destroy()
            sys.exit()

        if self.is_ai_mode and self.current_player == 2:
            # 禁用玩家操作按钮
            for button in self.dice_buttons:
                button.config(state=tk.DISABLED)
            self.roll_button.config(state=tk.DISABLED)
            self.continue_button.config(state=tk.DISABLED)
            self.end_turn_button.config(state=tk.DISABLED)
            self.root.after(self._get_random_delay(), self.ai_turn)
        else:
            # 启用玩家操作按钮
            for button in self.dice_buttons:
                button.config(state=tk.NORMAL)
            self.roll_button.config(state=tk.NORMAL)
            self.continue_button.config(state=tk.DISABLED)
            self.end_turn_button.config(state=tk.DISABLED)

    def ai_turn(self):
        self.root.after(self._get_random_delay(), self.roll_dice)

    def ai_choose_dice(self):
        all_combinations = []  # 存储所有可能的骰子组合
        for r in range(1, len(self.dice) + 1):
            for comb in combinations(range(len(self.dice)), r):
                kept_values = [self.dice[i] for i in comb]
                if all_dice_scoring(kept_values, self.dice):
                    all_combinations.append(comb)

        if not all_combinations:
            # 没有有效计分的骰子组合，直接结束回合
            action = f"[回合{self.round_num}][AI]无有效计分骰子，回合得分为0，[选择]结束本轮\n"
            self.insert_log(action)
            self.root.after(self._get_random_delay(), self.end_turn)
            return

        scores = [calculate_score([self.dice[i] for i in comb]) for comb in all_combinations]  # 计算所有组合的得分
        max_score_comb = all_combinations[scores.index(max(scores))]  # 获取最大得分的骰子组合
        print(max_score_comb)

        # 计算选取完后的剩余骰子数量
        remaining_dice_after_selection = len(self.dice) - len(max_score_comb)
        print(remaining_dice_after_selection)
        if remaining_dice_after_selection == 0:
            remaining_dice_after_selection = 6  # 如果选取完后剩余0个骰子，根据规则重新投掷6个骰子

        # 根据场上情况决定策略
        remaining_score_to_win = self.target_score - self.player2_score if self.is_ai_mode else self.target_score - self.player1_score
        current_round_score = self.round_score

        aggressive_weight = 0
        conservative_weight = 0

        if remaining_score_to_win > 2 * max(scores):
            # 距离胜利还远，更倾向于激进策略
            aggressive_weight = 70
            conservative_weight = 30
        elif remaining_score_to_win <= max(scores):
            # 可以一轮获胜，保守结束回合
            aggressive_weight = 20
            conservative_weight = 80
        elif remaining_dice_after_selection < 3:
            # 剩余骰子少，保守策略
            aggressive_weight = 30
            conservative_weight = 70
        else:
            # 其他情况，激进和保守策略权重相当
            aggressive_weight = 50
            conservative_weight = 50

        strategy_choice = random.choices(['aggressive', 'conservative'], weights=[aggressive_weight, conservative_weight])[0]

        if strategy_choice == 'aggressive':
            self.kept_dice = list(max_score_comb)
        else:
            if current_round_score == 0 and remaining_dice_after_selection == 6 and max(scores) < 200:
                # 第一回合得分低时，只选一个骰子
                single_comb = random.choice([comb for comb in all_combinations if len(comb) == 1])
                self.kept_dice = list(single_comb)
            else:
                self.kept_dice = list(max_score_comb)

        def select_next_dice(index_list, idx=0):
            if idx < len(index_list):
                index = index_list[idx]
                self.kept_dice = [index_list[i] for i in range(idx + 1)]
                self.dice_buttons[index].config(bg="green", relief=tk.SUNKEN)
                self.update_continue_button_state()
                self.update_selected_score()
                self.root.after(self._get_random_delay(), lambda: select_next_dice(index_list, idx + 1))
            else:
                # 所有骰子选择完成后，根据策略决定下一步操作
                if strategy_choice == 'aggressive' or remaining_dice_after_selection == 6:
                    self.root.after(self._get_random_delay(), self.continue_turn)
                else:
                    self.root.after(self._get_random_delay(), self.end_turn)

        select_next_dice(self.kept_dice)

    def _get_random_delay(self):
        return int(random.uniform(800, 1500))

class StartUI:
    def __init__(self, root):
        self.root = root
        self.root.title("游戏启动界面")

        # 加载背景图片
        self.load_background_image()

        # 创建按钮
        start_button = tk.Button(root, text="开始游戏", command=self.start_game)
        start_button.pack(pady=20)

        about_button = tk.Button(root, text="关于", command=self.show_about)
        about_button.pack(pady=20)

        exit_button = tk.Button(root, text="退出游戏", command=root.destroy)
        exit_button.pack(pady=20)

    def load_background_image(self):
        try:
            self.bg_image = Image.open("StartUI.png")
            self.bg_photo = ImageTk.PhotoImage(self.bg_image)
            self.bg_label = tk.Label(self.root, image=self.bg_photo)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print(f"加载背景图片时出错: {e}")

    def start_game(self):
        self.root.withdraw()
        self.bet_window = tk.Toplevel()
        self.bet_window.title("选择底注")

        bet_labels = ["乞丐(1000分)", "农民(2000分)", "骑士(4000分)", "国王(8000分)"]
        bet_values = [1000, 2000, 4000, 8000]

        for i, label in enumerate(bet_labels):
            tk.Button(self.bet_window, text=label, command=lambda v=bet_values[i]: self.select_bet(v)).pack(pady=10)

    def select_bet(self, bet):
        self.bet = bet  # 保存底注信息
        self.bet_window.withdraw()
        self.create_mode_window(bet)

    def create_mode_window(self, bet):
        self.mode_window = tk.Toplevel()
        self.mode_window.title("选择对战模式")

        local_button = tk.Button(self.mode_window, text="本地对战", command=lambda: self.start_local_game(bet))
        local_button.pack(pady=20)

        ai_button = tk.Button(self.mode_window, text="和电脑玩家对战", command=lambda: self.start_ai_game(bet))
        ai_button.pack(pady=20)

        online_button = tk.Button(self.mode_window, text="网络对战", command=self.show_online_lobby)
        online_button.pack(pady=20)

    def start_local_game(self, bet):
        self.mode_window.destroy()
        game_root = tk.Tk()
        game = DiceGame(game_root, bet)
        game_root.mainloop()

    def start_ai_game(self, bet):
        self.mode_window.destroy()
        game_root = tk.Tk()
        game = DiceGame(game_root, bet, is_ai_mode=True)
        game_root.mainloop()

    def show_about(self):
        messagebox.showinfo("关于", "游戏是在豆包AI和GitHub Copilot合作下完成的，游戏玩法参考了天国拯救系列。")

    def show_online_lobby(self):
        self.mode_window.withdraw()
        self.lobby_window = tk.Toplevel()
        self.lobby_window.title("房间列表")

        # 获取本机IP
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        self.local_ip = local_ip  # 保存本机IP
        self.local_name = hostname  # 保存本机名称
        ip_label = tk.Label(self.lobby_window, text=f"本机IP: {local_ip}")
        ip_label.pack(pady=10)

        # 房间列表
        columns = ("name", "host_ip", "status", "password")
        self.room_treeview = ttk.Treeview(self.lobby_window, columns=columns, show="headings")
        self.room_treeview.heading("name", text="房间名")
        self.room_treeview.heading("host_ip", text="房主IP")
        self.room_treeview.heading("status", text="状态")
        self.room_treeview.heading("password", text="密码")
        self.room_treeview.pack(pady=10)

        # 搜索房间中标签
        self.searching_label = tk.Label(self.lobby_window, text="搜索房间中...", font=("Arial", 12))
        self.searching_label.pack(pady=10)

        # 刷新房间列表
        self.refresh_room_list()

        # 创建房间按钮
        create_room_button = tk.Button(self.lobby_window, text="创建房间", command=self.create_room)
        create_room_button.pack(side=tk.LEFT, padx=10, pady=10)

        # 加入房间按钮
        join_room_button = tk.Button(self.lobby_window, text="加入房间", command=self.join_room)
        join_room_button.pack(side=tk.LEFT, padx=10, pady=10)

        # 刷新按钮
        refresh_button = tk.Button(self.lobby_window, text="刷新", command=self.refresh_room_list)
        refresh_button.pack(side=tk.LEFT, padx=10, pady=10)

    def refresh_room_list(self):
        # 清空列表
        for item in self.room_treeview.get_children():
            self.room_treeview.delete(item)

        # 搜索房间信息
        self.search_rooms()

    def search_rooms(self):
        self.search_attempts = 0
        self.found_rooms = set()

        def listen_for_broadcast():
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            udp_socket.bind(("", 12345))

            while True:
                try:
                    data, addr = udp_socket.recvfrom(1024)
                    print(f"接收到广播数据: {data} 来自: {addr}")  # 调试信息
                    room_info = eval(data.decode('utf-8'))
                    if addr[0] not in self.found_rooms:
                        self.found_rooms.add(addr[0])
                        self.room_treeview.insert("", tk.END, values=(room_info["name"], room_info["host_ip"], room_info["status"], room_info["password"]))
                        self.searching_label.config(text="")
                        self.search_attempts = 0  # 重置搜索尝试次数
                except Exception as e:
                    print(f"接收广播数据时出错: {e}")  # 调试信息

        def search():
            if self.search_attempts < 5:
                self.search_attempts += 1
                self.searching_label.config(text=f"搜索房间中...（尝试 {self.search_attempts}/5）")
                threading.Thread(target=listen_for_broadcast, daemon=True).start()
                if not self.found_rooms:
                    self.lobby_window.after(10000, search)
            else:
                self.searching_label.config(text="未找到房间")

        # 打开大厅后立即搜索一次
        search()
        # 三秒后再搜索一次
        self.lobby_window.after(3000, search)

    def create_room(self):
        self.create_room_window = tk.Toplevel()
        self.create_room_window.title("创建房间")

        # 获取本机IP
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)

        # 房间名默认值
        default_room_name = f"{hostname}的房间"

        # IP输入框
        tk.Label(self.create_room_window, text="IP:").pack(pady=5)
        ip_entry = tk.Entry(self.create_room_window)
        ip_entry.insert(0, local_ip)
        ip_entry.config(state='readonly')
        ip_entry.pack(pady=5)

        # 房间名输入框
        tk.Label(self.create_room_window, text="房间名:").pack(pady=5)
        room_name_entry = tk.Entry(self.create_room_window)
        room_name_entry.insert(0, default_room_name)
        room_name_entry.pack(pady=5)

        # 密码复选框和输入框
        password_var = tk.BooleanVar()
        password_check = tk.Checkbutton(self.create_room_window, text="需要密码", variable=password_var, command=lambda: password_entry.config(state='normal' if password_var.get() else 'disabled'))
        password_check.pack(pady=5)
        password_entry = tk.Entry(self.create_room_window, show="*")
        password_entry.config(state='disabled')
        password_entry.pack(pady=5)

        # 确认创建按钮
        confirm_button = tk.Button(self.create_room_window, text="确认创建", command=lambda: self.confirm_create_room(local_ip, room_name_entry.get(), password_var.get(), password_entry.get()))
        confirm_button.pack(pady=10)

        # 取消按钮
        cancel_button = tk.Button(self.create_room_window, text="取消", command=self.create_room_window.destroy)
        cancel_button.pack(pady=10)

    def confirm_create_room(self, ip, room_name, need_password, password):
        self.password = password  # 保存密码信息
        self.host_ip = ip  # 保存主机IP
        self.host_name = self.local_name  # 保存主机名称
        self.create_room_window.destroy()
        self.lobby_window.destroy()
        self.show_room_window(ip, room_name, need_password, password, is_host=True)
        self.broadcast_room_info(ip, room_name, need_password, password)

    def broadcast_room_info(self, ip, room_name, need_password, password):
        def broadcast():
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            room_info = {
                "name": room_name,
                "host_ip": ip,
                "status": "等待中",
                "password": "是" if need_password else "否",
                "bet": self.bet
            }
            while True:
                udp_socket.sendto(str(room_info).encode('utf-8'), ('<broadcast>', 12345))
                print(f"广播房间信息: {room_info}")  # 调试信息
                time.sleep(3)

        threading.Thread(target=broadcast, daemon=True).start()

    def show_room_window(self, ip, room_name, need_password, password, is_host=False):
        self.room_window = tk.Toplevel()
        if is_host:
            self.room_window.title("房主")
        else:
            self.room_window.title("客户端")

        # 左侧显示本机电脑名或主机信息
        if is_host:
            tk.Label(self.room_window, text=f"主机: {self.local_name} ({ip})").pack(pady=10)
        else:
            tk.Label(self.room_window, text=f"主机: {self.host_name} ({self.host_ip})").pack(pady=10)

        # 中间显示当前对局的底注大小
        self.bet_label = tk.Label(self.room_window, text=f"底注: {self.bet}")
        self.bet_label.pack(pady=10)

        # 右侧显示其他玩家信息或虚位以待
        self.player_label = tk.Label(self.room_window, text="虚位以待")
        self.player_label.pack(pady=10)

        # 单选框指示用户准备状态
        self.ready_var = tk.BooleanVar()
        self.ready_check = tk.Checkbutton(self.room_window, text="准备", variable=self.ready_var, state=tk.DISABLED if is_host else tk.NORMAL)
        self.ready_check.pack(pady=10)

        if is_host:
            self.start_broadcasting(ip, room_name, need_password, password)
            self.wait_for_connection()

    def start_broadcasting(self, ip, room_name, need_password, password):
        def broadcast():
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            room_info = {
                "name": room_name,
                "host_ip": ip,
                "status": "等待中",
                "password": "是" if need_password else "否",
                "bet": self.bet
            }
            while True:
                udp_socket.sendto(str(room_info).encode('utf-8'), ('<broadcast>', 12345))
                print(f"广播房间信息: {room_info}")  # 调试信息
                time.sleep(3)

        threading.Thread(target=broadcast, daemon=True).start()

    def wait_for_connection(self):
        def listen_for_connection():
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.bind(("", 12345))
            tcp_socket.listen(1)

            while True:
                conn, addr = tcp_socket.accept()
                data = conn.recv(1024).decode('utf-8')
                print(f"接收到连接请求: {data} 来自: {addr}")  # 调试信息
                request_info = eval(data)
                if request_info["password"] == self.password:
                    response_info = {
                        "status": "确认连接",
                        "host_ip": self.host_ip,
                        "host_name": self.host_name,
                        "bet": self.bet,
                        "client_name": request_info["name"]
                    }
                    conn.send(str(response_info).encode('utf-8'))
                    self.player_label.config(text=f"玩家: {request_info['name']} ({request_info['ip']})")
                else:
                    response_info = {
                        "status": "密码错误"
                    }
                    conn.send(str(response_info).encode('utf-8'))
                conn.close()

        threading.Thread(target=listen_for_connection, daemon=True).start()

    def join_room(self):
        selected_item = self.room_treeview.selection()
        if selected_item:
            room_info = self.room_treeview.item(selected_item, "values")
            self.host_ip = room_info[1]
            self.host_name = room_info[0]
            self.bet = room_info[2]
            self.password_required = room_info[3] == "是"

            if self.password_required:
                self.ask_password()
            else:
                self.send_connection_request("")

    def ask_password(self):
        self.password_window = tk.Toplevel()
        self.password_window.title("输入密码")

        tk.Label(self.password_window, text="密码:").pack(pady=5)
        self.password_entry = tk.Entry(self.password_window, show="*")
        self.password_entry.pack(pady=5)

        confirm_button = tk.Button(self.password_window, text="确认", command=lambda: self.send_connection_request(self.password_entry.get()))
        confirm_button.pack(pady=10)

    def send_connection_request(self, password):
        if hasattr(self, 'password_window'):
            self.password_window.destroy()
        self.lobby_window.destroy()
        self.show_room_window(self.host_ip, self.host_name, self.password_required, password, is_host=False)

        def connect():
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.connect((self.host_ip, 12345))
            request_info = {
                "ip": self.local_ip,
                "name": self.local_name,
                "password": password
            }
            tcp_socket.send(str(request_info).encode('utf-8'))

            data = tcp_socket.recv(1024).decode('utf-8')
            response_info = eval(data)
            if response_info["status"] == "确认连接":
                self.player_label.config(text=f"玩家: {response_info['host_name']} ({response_info['host_ip']})")
                self.bet_label.config(text=f"底注: {response_info['bet']}")
            elif response_info["status"] == "密码错误":
                messagebox.showerror("错误", "密码错误")
                self.room_window.destroy()
                self.show_online_lobby()
            else:
                messagebox.showerror("错误", "连接失败")
                self.room_window.destroy()
                self.show_online_lobby()

        threading.Thread(target=connect, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    start_ui = StartUI(root)
    root.mainloop()