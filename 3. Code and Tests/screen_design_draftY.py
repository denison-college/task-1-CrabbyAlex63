import tkinter as tk
from tkinter import messagebox, simpledialog
import random
import time
import json
import os
# Saves Highscores
highscore_file = "minesweeper_highscores.json"


# Difficulies 
Difficulties = {
        "Easy": {"rows": *, "cols": 8, "mines": 10},
        "Medium": {"rows": 10, "cols": 10, "mines": 15},
        "Hard": {"rows": 12, "cols": 12, "mines": 25},
}
# Cell being a bomb or not a bomb
class Cell:
    def __init__(self):
        self.is_mine = False
        self.is_revealed = False
        self.is_flagged = False
        self.adjacent_mines = 0


# Setting up the actual game
class Minesweeper:
    def __init__(self, root):
        self.root = root
        self.root.title("Explosive Day - Minesweeper")


# Reseting all of the thingy things (variables)
        self.player_name = None
        self.difficulty = "Easy"
        self.rows = 0
        self.cols = 0
        self.mine_count = 0
        self.board = []
        self.buttons = []

        self.first_click = True
        self.game_over = False
        self.start_time = None
        self.elapsed_time = 0
        self.score = 100
        self.hint_used = False


# Creates the top section showing info
        self.top_frame = tk.Frame(root)
        self.top_frame.pack(pady=5)

        self.info_label = tk.Label(self.top_frame, text="Welcome to Explosive Day!", font=("Arial", 12, "bold"))
        self.info_label.grid(row=0, column=0, columnspan=6, pady=5)

        self.timer_label = tk.Label(self.top_frame, text="Time: 0", width=12)
        self.timer_label.grid(row=1, column=0)

        self.score_label = tk.Label(self.top_frame, text="Score: 100", width=12)
        self.score_label.grid(row=1, column=1)


# changes difficulty/start game.
        self.difficulty_var = tk.StringVar(value="Easy")
        self.difficulty_menu = tk.OptionMenu(self.top_frame, self.difficulty_var, *DIFFICULTIES.keys())
        self.difficulty_menu.grid(row=1, column=2)

        self.new_game_btn = tk.Button(self.top_frame, text="New Game", command=self.new_game)
        self.new_game_btn.grid(row=1, column=3, padx=5)

# Hints
        self.hint_btn = tk.Button(self.top_frame, text="Hint", command=self.use_hint)
        self.hint_btn.grid(row=1, column=4, padx=5)

        self.highscore_btn = tk.Button(self.top_frame, text="Highscores", command=self.show_highscores)
        self.highscore_btn.grid(row=1, column=5, padx=5)

# Actual grid of the game
        self.board_frame = tk.Frame(root)
        self.board_frame.pack(pady=10)

# Gets the players name
        self.player_name = simpledialog.askstring("Player Name", "Enter your name:")
        if not self.player_name:
            self.player_name = "Player"

# Actually starts the game.
        self.new_game()



        "Knowledge means survival.
        "The difficulty you choose will dictate how hard and more bomb-packed the game is. Your goal is to strategically locate and mark all the bombs without setting one off.
        "Upon your mission, you will come across ‘powers’ which may be beneficial or negative towards your mission.
        "To win the game, all tiles must be correctly marked or cleared.
        "To mark a tile of a bomb, you are to type the coordinates of the chosen tile, then when given the selection prompt, you choose ‘Mark’. This will change the tile into a ‘p’, this represents a flag.
        "To reveal a tile, you are to type the coordinates of the chosen tile, then when given the selection prompt, you choose ‘Reveal’. This will change the tile to one of the following 2: 0, which represents a clear tile, or an ?, which represents a bomb.
        "Upon discovering a bomb you will lose the game.