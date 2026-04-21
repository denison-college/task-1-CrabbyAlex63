import tkinter as tk
from tkinter import messagebox, simpledialog
import random
import time
import json
import os

# Saves Highscores
highscore_file = "minesweeper_highscores.json"

# Difficulies
DIFFICULTIES = {
    "Easy": {"rows": 8, "cols": 8, "mines": 10},
    "Medium": {"rows": 10, "cols": 10, "mines": 15},
    "Hard": {"rows": 12, "cols": 12, "mines": 25},
    }

# Changing number colours
NUMBER_COLOURS = {
    1: "blue", 2: "green", 3: "red", 4: "darkblue",
    5: "brown", 6: "cyan", 7: "black", 8: "gray"
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

# clears the board and creates a fresh grid of buttons
    def new_game(self):

 # Load difficulty settings
        self.difficulty = self.difficulty_var.get()
        settings = DIFFICULTIES[self.difficulty]
        self.rows = settings["rows"]
        self.cols = settings["cols"]
        self.mine_count = settings["mines"]

 # Reset game variables
        self.first_click = True
        self.game_over = False
        self.start_time = None
        self.elapsed_time = 0
        self.score = 100
        self.hint_used = False

# Reset UI labels
        self.timer_label.config(text="Time: 0")
        self.score_label.config(text="Score: 100")
        self.info_label.config(
            text=f"{self.player_name} | {self.difficulty} | Left click = Reveal, Right click = Flag"
        )

# Clear previous board
        for widget in self.board_frame.winfo_children():
            widget.destroy()

# New board info
        self.board = [[Cell() for _ in range(self.cols)] for _ in range(self.rows)]
        self.buttons = [[None for _ in range(self.cols)] for _ in range(self.rows)]

# Makes the buttons clickable and grids them out
        for r in range(self.rows):
            for c in range(self.cols):
                btn = tk.Button(
                    self.board_frame,
                    width=3,
                    height=1,
                    font=("Arial", 12, "bold"),
                    bg="lightgray",
                    command=lambda row=r, col=c: self.on_left_click(row, col)
                )
                btn.grid(row=r, column=c)
                btn.bind("<Button-3>", lambda event, row=r, col=c: self.on_right_click(row, col))
                self.buttons[r][c] = btn

# randomly places mines and first click is safe always
    def place_mines(self, safe_row, safe_col):
        placed = 0
        while placed < self.mine_count:
            r = random.randint(0, self.rows - 1)
            c = random.randint(0, self.cols - 1)

# skip if a mine or first clicked cell
            if self.board[r][c].is_mine:
                continue
            if r == safe_row and c == safe_col:
                continue

            self.board[r][c].is_mine = True
            placed += 1

# number of mines around each already placed mine
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.board[r][c].is_mine:
                    self.board[r][c].adjacent_mines = self.count_adjacent_mines(r, c)

# counts how many mines are around each cell
    def count_adjacent_mines(self, row, col):
        count = 0
        for r in range(max(0, row - 1), min(self.rows, row + 2)):
            for c in range(max(0, col - 1), min(self.cols, col + 2)):
                if self.board[r][c].is_mine:
                    count += 1
        return count

# revealing cells, starting the game, and checking win or lost
    def on_left_click(self, row, col):

# if the game has eneded nothing will happen
        if self.game_over:
            return

        cell = self.board[row][col]

 # Prevent revealing flagged or already revealed cells
        if cell.is_flagged or cell.is_revealed:
            return

# makes sure the first click is safe and then starts a timer
        if self.first_click:
            self.place_mines(row, col)
            self.first_click = False
            self.start_time = time.time()
            self.update_timer()

# reveal the cell
        self.reveal_cell(row, col)

# Boom
        if cell.is_mine:
            self.end_game(False)
            return

# checks if the player has won
        if self.check_win():
            self.end_game(True)

# lets the player add or remove flags
    def on_right_click(self, row, col):

# cant flag before first click
        if self.game_over or self.first_click:
            return

        cell = self.board[row][col]
        btn = self.buttons[row][col]

# cant flag already revelaed cells
        if cell.is_revealed:
            return
        cell.is_flagged = not cell.is_flagged

        if cell.is_flagged:
            btn.config(text="⚑", fg="orange", bg="lightgray")
        else:
            btn.config(text="", bg="lightgray")

# Reveals a cell, updates its appearance, and spreads to nearby cells if empty
    def reveal_cell(self, row, col):
        cell = self.board[row][col]
        btn = self.buttons[row][col]

# Prevent revealing flagged or already revealed cells
        if cell.is_revealed or cell.is_flagged:
            return

# Mark cell as revealed and update button appearance
        cell.is_revealed = True
        btn.config(relief=tk.SUNKEN, state="disabled", bg="white")

# display explosion
        if cell.is_mine:
            btn.config(text="✹", bg="red", fg="black")
            return
# If adjacent mines then show number
        if cell.adjacent_mines > 0:
            btn.config(
                text=str(cell.adjacent_mines),
                fg=NUMBER_COLOURS.get(cell.adjacent_mines, "black")
            )
        else:
# If empty → recursively reveal surrounding cells
            btn.config(text="")
            for r in range(max(0, row - 1), min(self.rows, row + 2)):
                for c in range(max(0, col - 1), min(self.cols, col + 2)):
                    if not self.board[r][c].is_revealed:
                        self.reveal_cell(r, c)

# Updates the game timer and dynamically adjusts score over time
    def update_timer(self):
        if self.game_over or self.first_click:
            return

        self.elapsed_time = int(time.time() - self.start_time)
        current_score = max(0, 100 - self.elapsed_time)

        self.timer_label.config(text=f"Time: {self.elapsed_time}")
        self.score_label.config(text=f"Score: {current_score}")

        self.root.after(1000, self.update_timer)

# Checks if all non-mine cells have been revealed
    def check_win(self):
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.board[r][c]
                if not cell.is_mine and not cell.is_revealed:
                    return False
        return True

# Calculates final score and applies penalties for incorrect flags
    def calculate_final_score(self):
        base_score = max(0, 100 - self.elapsed_time)
        wrong_flags = 0

        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.board[r][c]
                if cell.is_flagged and not cell.is_mine:
                    wrong_flags += 1

        final_score = max(0, base_score - (wrong_flags * 5))
        return final_score, wrong_flags

# Displays all mines and highlights correct/incorrect flags
    def reveal_all_mines(self):
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.board[r][c]
                btn = self.buttons[r][c]

                if cell.is_mine:
                    if cell.is_flagged:
                        btn.config(text="⚑", bg="yellow", fg="orange")
                    else:
                        btn.config(text="✹", bg="red", fg="black")
                elif cell.is_flagged and not cell.is_mine:
                    btn.config(text="X", bg="pink", fg="black")

    # Handles win/loss, calculates score, and displays results
    def end_game(self, won):
        self.game_over = True
        self.elapsed_time = int(time.time() - self.start_time) if self.start_time else 0
        final_score, wrong_flags = self.calculate_final_score()
        self.score = final_score

        self.reveal_all_mines()

        if won:
            self.save_highscore(self.player_name, self.difficulty, final_score)
            messagebox.showinfo(
                "You Win!",
                f"Congratulations, {self.player_name}!\n\n"
                f"Time: {self.elapsed_time} seconds\n"
                f"Wrong flags: {wrong_flags}\n"
                f"Final Score: {final_score}"
            )
        else:
            messagebox.showinfo(
                "Game Over",
                f"You hit a mine!\n\n"
                f"Time: {self.elapsed_time} seconds\n"
                f"Final Score: 0"
            )

        self.timer_label.config(text=f"Time: {self.elapsed_time}")
        self.score_label.config(text=f"Score: {0 if not won else final_score}")

# Reveals one safe cell automatically
    def use_hint(self):
        if self.game_over:
            return

        if self.hint_used:
            messagebox.showinfo("Hint", "You already used your one hint this game.")
            return

        if self.first_click:
            messagebox.showinfo("Hint", "Make your first move before using a hint.")
            return

        safe_cells = []
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.board[r][c]
                if not cell.is_mine and not cell.is_revealed and not cell.is_flagged:
                    safe_cells.append((r, c))

        if not safe_cells:
            messagebox.showinfo("Hint", "No safe cells available.")
            return

        row, col = random.choice(safe_cells)
        self.reveal_cell(row, col)
        self.hint_used = True

        if self.check_win():
            self.end_game(True)

# Loads saved highscores from file
    def load_highscores(self):
        if not os.path.exists(highscore_file):
            return {"Easy": [], "Medium": [], "Hard": []}

        try:
            with open(highscore_file, "r") as f:
                return json.load(f)
        except:
            return {"Easy": [], "Medium": [], "Hard": []}

# Saves new highscore and keeps top 5
    def save_highscore(self, name, difficulty, score):
        highscores = self.load_highscores()
        highscores[difficulty].append({"name": name, "score": score})
        highscores[difficulty] = sorted(highscores[difficulty], key=lambda x: x["score"], reverse=True)[:5]

        with open(highscore_file, "w") as f:
            json.dump(highscores, f, indent=4)

# Displays highscores in a popup window
    def show_highscores(self):
        highscores = self.load_highscores()

        text = ""
        for difficulty in ["Easy", "Medium", "Hard"]:
            text += f"{difficulty}:\n"
            if highscores.get(difficulty):
                for i, entry in enumerate(highscores[difficulty], start=1):
                    text += f"{i}. {entry['name']} - {entry['score']}\n"
            else:
                text += "No scores yet\n"
            text += "\n"

        messagebox.showinfo("Highscores", text)

# Game starter
if __name__ == "__main__":
    root = tk.Tk()
    game = Minesweeper(root)
    root.mainloop()
