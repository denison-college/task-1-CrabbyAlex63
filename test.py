import io
import json
import os
import sys
import types
from unittest.mock import mock_open

import pytest

import script.py


class DummyWidget:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.config_calls = []
        self.grid_calls = []
        self.bind_calls = []
        self.destroyed = False
        self.text = kwargs.get("text", "")
        self.children = []

    def pack(self, *args, **kwargs):
        return None

    def grid(self, *args, **kwargs):
        self.grid_calls.append((args, kwargs))
        return None

    def bind(self, *args, **kwargs):
        self.bind_calls.append((args, kwargs))
        return None

    def config(self, **kwargs):
        self.config_calls.append(kwargs)
        for key, value in kwargs.items():
            setattr(self, key, value)

    def destroy(self):
        self.destroyed = True

    def winfo_children(self):
        return self.children


class DummyRoot:
    def __init__(self):
        self.title_value = None
        self.after_calls = []

    def title(self, value):
        self.title_value = value

    def after(self, delay, callback):
        self.after_calls.append((delay, callback))


class DummyStringVar:
    def __init__(self, value=None):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class DummyButton(DummyWidget):
    pass


class DummyLabel(DummyWidget):
    pass


class DummyFrame(DummyWidget):
    pass


class DummyOptionMenu(DummyWidget):
    pass


@pytest.fixture
def patched_tk(monkeypatch):
    monkeypatch.setattr(script.tk, "Frame", DummyFrame)
    monkeypatch.setattr(script.tk, "Label", DummyLabel)
    monkeypatch.setattr(script.tk, "Button", DummyButton)
    monkeypatch.setattr(script.tk, "OptionMenu", DummyOptionMenu)
    monkeypatch.setattr(script.tk, "StringVar", DummyStringVar)
    monkeypatch.setattr(script.tk, "SUNKEN", "sunken")
    return monkeypatch


@pytest.fixture
def fake_game(patched_tk, monkeypatch):
    monkeypatch.setattr(script.simpledialog, "askstring", lambda *args, **kwargs: "Tester")
    monkeypatch.setattr(script.messagebox, "showinfo", lambda *args, **kwargs: None)

    root = DummyRoot()
    game = script.Minesweeper(root)
    return game


def make_board(game, rows, cols, mines=None):
    game.rows = rows
    game.cols = cols
    game.board = [[script.Cell() for _ in range(cols)] for _ in range(rows)]
    game.buttons = [[DummyButton() for _ in range(cols)] for _ in range(rows)]
    if mines:
        for r, c in mines:
            game.board[r][c].is_mine = True


def test_cell_defaults():
    cell = script.Cell()
    assert cell.is_mine is False
    assert cell.is_revealed is False
    assert cell.is_flagged is False
    assert cell.adjacent_mines == 0


def test_new_game_initializes_board_and_resets_state(fake_game):
    game = fake_game
    game.difficulty_var.set("Medium")
    game.board_frame.children = [DummyWidget(), DummyWidget()]

    game.new_game()

    assert game.difficulty == "Medium"
    assert game.rows == 10
    assert game.cols == 10
    assert game.mine_count == 15
    assert game.first_click is True
    assert game.game_over is False
    assert game.start_time is None
    assert game.elapsed_time == 0
    assert game.score == 100
    assert game.hint_used is False
    assert len(game.board) == 10
    assert len(game.buttons) == 10
    assert len(game.buttons[0]) == 10
    assert game.info_label.text == "Tester | Medium | Left click = Reveal, Right click = Flag"
    assert game.timer_label.text == "Time: 0"
    assert game.score_label.text == "Score: 100"


def test_place_mines_skips_safe_cell_and_computes_adjacent_counts(fake_game, monkeypatch):
    game = fake_game
    make_board(game, 3, 3)
    game.mine_count = 2

    positions = iter([(0, 0), (1, 1), (2, 2)])
    monkeypatch.setattr(script.random, "randint", lambda a, b: next(positions))

    game.place_mines(0, 0)

    assert game.board[0][0].is_mine is False
    assert game.board[1][1].is_mine is True
    assert game.board[2][2].is_mine is True
    assert game.board[0][1].adjacent_mines == 1
    assert game.board[1][0].adjacent_mines == 1
    assert game.board[1][2].adjacent_mines == 2


def test_count_adjacent_mines_counts_only_neighbors(fake_game):
    game = fake_game
    make_board(game, 3, 3, mines=[(0, 0), (1, 1), (2, 2)])
    assert game.count_adjacent_mines(1, 0) == 2
    assert game.count_adjacent_mines(0, 2) == 1


def test_on_left_click_first_click_places_mines_starts_timer_and_reveals(fake_game, monkeypatch):
    game = fake_game
    make_board(game, 2, 2)
    game.mine_count = 1
    game.first_click = True
    game.start_time = None

    calls = {"placed": False, "update": 0, "reveal": [], "win": 0, "end": []}

    def fake_place_mines(row, col):
        calls["placed"] = (row, col)

    def fake_update_timer():
        calls["update"] += 1

    def fake_reveal_cell(row, col):
        calls["reveal"].append((row, col))

    monkeypatch.setattr(game, "place_mines", fake_place_mines)
    monkeypatch.setattr(game, "update_timer", fake_update_timer)
    monkeypatch.setattr(game, "reveal_cell", fake_reveal_cell)
    monkeypatch.setattr(game, "check_win", lambda: False)

    monkeypatch.setattr(script.time, "time", lambda: 123.4)

    game.on_left_click(0, 1)

    assert calls["placed"] == (0, 1)
    assert game.first_click is False
    assert game.start_time == 123.4
    assert calls["update"] == 1
    assert calls["reveal"] == [(0, 1)]


def test_on_left_click_hits_mine_ends_game(fake_game, monkeypatch):
    game = fake_game
    make_board(game, 1, 1, mines=[(0, 0)])
    game.first_click = False

    ended = {"value": None}
    monkeypatch.setattr(game, "reveal_cell", lambda row, col: None)
    monkeypatch.setattr(game, "check_win", lambda: False)
    monkeypatch.setattr(game, "end_game", lambda won: ended.__setitem__("value", won))

    game.on_left_click(0, 0)

    assert ended["value"] is False


def test_on_left_click_win_ends_game(fake_game, monkeypatch):
    game = fake_game
    make_board(game, 1, 1)
    game.first_click = False

    ended = {"value": None}
    monkeypatch.setattr(game, "reveal_cell", lambda row, col: None)
    monkeypatch.setattr(game, "check_win", lambda: True)
    monkeypatch.setattr(game, "end_game", lambda won: ended.__setitem__("value", won))

    game.on_left_click(0, 0)

    assert ended["value"] is True


def test_on_right_click_toggles_flag(fake_game):
    game = fake_game
    make_board(game, 1, 1)
    game.first_click = False

    game.on_right_click(0, 0)
    assert game.board[0][0].is_flagged is True
    assert game.buttons[0][0].text == "⚑"
    assert game.buttons[0][0].fg == "orange"

    game.on_right_click(0, 0)
    assert game.board[0][0].is_flagged is False
    assert game.buttons[0][0].text == ""
    assert game.buttons[0][0].bg == "lightgray"


def test_reveal_cell_non_mine_with_number(fake_game):
    game = fake_game
    make_board(game, 1, 1)
    cell = game.board[0][0]
    cell.adjacent_mines = 3

    game.reveal_cell(0, 0)

    assert cell.is_revealed is True
    assert game.buttons[0][0].relief == "sunken"
    assert game.buttons[0][0].state == "disabled"
    assert game.buttons[0][0].text == "3"
    assert game.buttons[0][0].fg == "red"


def test_reveal_cell_empty_expands(fake_game):
    game = fake_game
    make_board(game, 2, 2)
    game.board[0][0].adjacent_mines = 0
    game.board[0][1].adjacent_mines = 1
    game.board[1][0].adjacent_mines = 1
    game.board[1][1].adjacent_mines = 1

    game.reveal_cell(0, 0)

    assert all(game.board[r][c].is_revealed for r in range(2) for c in range(2))


def test_update_timer_updates_labels_and_schedules(fake_game, monkeypatch):
    game = fake_game
    game.game_over = False
    game.first_click = False
    game.start_time = 10.0

    monkeypatch.setattr(script.time, "time", lambda: 15.7)

    game.update_timer()

    assert game.elapsed_time == 5
    assert game.timer_label.text == "Time: 5"
    assert game.score_label.text == "Score: 95"
    assert game.root.after_calls[0][0] == 1000


def test_update_timer_stops_when_game_over_or_first_click(fake_game):
    game = fake_game
    game.game_over = True
    game.first_click = False
    game.update_timer()
    assert game.root.after_calls == []


def test_check_win(fake_game):
    game = fake_game
    make_board(game, 2, 2, mines=[(0, 0)])
    game.board[0][0].is_revealed = False
    game.board[0][1].is_revealed = True
    game.board[1][0].is_revealed = True
    game.board[1][1].is_revealed = True
    assert game.check_win() is False

    game.board[0][0].is_revealed = True
    assert game.check_win() is True


def test_calculate_final_score_counts_wrong_flags(fake_game):
    game = fake_game
    make_board(game, 2, 2, mines=[(0, 0)])
    game.elapsed_time = 20
    game.board[0][1].is_flagged = True
    game.board[1][1].is_flagged = True
    game.board[1][1].is_mine = True

    score, wrong_flags = game.calculate_final_score()

    assert score == 75
    assert wrong_flags == 1


def test_reveal_all_mines_marks_mines_and_wrong_flags(fake_game):
    game = fake_game
    make_board(game, 2, 2, mines=[(0, 0), (1, 1)])
    game.board[0][1].is_flagged = True

    game.reveal_all_mines()

    assert game.buttons[0][0].text == "✹"
    assert game.buttons[0][0].bg == "red"
    assert game.buttons[1][1].text == "✹"
    assert game.buttons[0][1].text == "X"
    assert game.buttons[0][1].bg == "pink"


def test_end_game_win_saves_highscore_and_shows_message(fake_game, monkeypatch):
    game = fake_game
    make_board(game, 1, 1)
    game.start_time = 100.0
    game.player_name = "Tester"
    game.difficulty = "Easy"
    game.elapsed_time = 12

    monkeypatch.setattr(script.time, "time", lambda: 112.0)
    monkeypatch.setattr(game, "calculate_final_score", lambda: (88, 2))
    monkeypatch.setattr(game, "reveal_all_mines", lambda: None)

    saved = {}
    monkeypatch.setattr(game, "save_highscore", lambda name, difficulty, score: saved.update(
        {"name": name, "difficulty": difficulty, "score": score}
    ))

    messages = []
    monkeypatch.setattr(script.messagebox, "showinfo", lambda title, msg: messages.append((title, msg)))

    game.end_game(True)

    assert game.game_over is True
    assert game.score == 88
    assert saved == {"name": "Tester", "difficulty": "Easy", "score": 88}
    assert messages[0][0] == "You Win!"
    assert "Wrong flags: 2" in messages[0][1]
    assert game.score_label.text == "Score: 88"


def test_end_game_loss_shows_game_over(fake_game, monkeypatch):
    game = fake_game
    make_board(game, 1, 1)
    game.start_time = 100.0
    monkeypatch.setattr(script.time, "time", lambda: 110.0)
    monkeypatch.setattr(game, "calculate_final_score", lambda: (91, 0))
    monkeypatch.setattr(game, "reveal_all_mines", lambda: None)

    messages = []
    monkeypatch.setattr(script.messagebox, "showinfo", lambda title, msg: messages.append((title, msg)))

    game.end_game(False)

    assert game.game_over is True
    assert game.score == 91
    assert messages[0][0] == "Game Over"
    assert "Final Score: 0" in messages[0][1]
    assert game.score_label.text == "Score: 0"


def test_use_hint_conditions_and_success(fake_game, monkeypatch):
    game = fake_game
    make_board(game, 2, 2, mines=[(0, 0)])
    game.first_click = False

    messages = []
    monkeypatch.setattr(script.messagebox, "showinfo", lambda title, msg: messages.append((title, msg)))

    game.hint_used = True
    game.use_hint()
    assert messages[-1] == ("Hint", "You already used your one hint this game.")

    game.hint_used = False
    game.first_click = True
    game.use_hint()
    assert messages[-1] == ("Hint", "Make your first move before using a hint.")

    game.first_click = False
    game.board[0][1].is_revealed = True
    game.board[1][0].is_flagged = True

    monkeypatch.setattr(script.random, "choice", lambda seq: seq[0])
    ended = {"won": None}
    monkeypatch.setattr(game, "check_win", lambda: False)
    monkeypatch.setattr(game, "reveal_cell", lambda row, col: setattr(game.board[row][col], "is_revealed", True))
    monkeypatch.setattr(game, "end_game", lambda won: ended.__setitem__("won", won))

    game.use_hint()

    assert game.hint_used is True
    assert game.board[1][1].is_revealed is True
    assert ended["won"] is None


def test_use_hint_wins_game_when_last_safe_cell_revealed(fake_game, monkeypatch):
    game = fake_game
    make_board(game, 1, 2, mines=[(0, 0)])
    game.first_click = False
    game.hint_used = False
    game.board[0][0].is_mine = True

    monkeypatch.setattr(script.random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(game, "reveal_cell", lambda row, col: setattr(game.board[row][col], "is_revealed", True))

    ended = {"won": None}
    monkeypatch.setattr(game, "check_win", lambda: True)
    monkeypatch.setattr(game, "end_game", lambda won: ended.__setitem__("won", won))

    game.use_hint()

    assert ended["won"] is True


def test_load_highscores_missing_file_returns_defaults(fake_game, monkeypatch):
    game = fake_game
    monkeypatch.setattr(script.os.path, "exists", lambda path: False)
    assert game.load_highscores() == {"Easy": [], "Medium": [], "Hard": []}


def test_load_highscores_invalid_json_returns_defaults(fake_game, monkeypatch):
    game = fake_game
    monkeypatch.setattr(script.os.path, "exists", lambda path: True)
    monkeypatch.setattr("builtins.open", mock_open(read_data="not-json"))

    assert game.load_highscores() == {"Easy": [], "Medium": [], "Hard": []}


def test_save_highscore_keeps_top_five_sorted(fake_game, monkeypatch):
    game = fake_game
    monkeypatch.setattr(game, "load_highscores", lambda: {"Easy": [{"name": "A", "score": 10}], "Medium": [], "Hard": []})

    captured = {}

    def fake_open(*args, **kwargs):
        captured["path"] = args[0]
        return io.StringIO()

    monkeypatch.setattr("builtins.open", fake_open)
    dump_calls = []

    def fake_dump(obj, f, indent):
        dump_calls.append(obj)

    monkeypatch.setattr(script.json, "dump", fake_dump)

    game.save_highscore("B", "Easy", 99)

    assert captured["path"] == script.highscore_file
    assert dump_calls[0]["Easy"][0] == {"name": "B", "score": 99}


def test_show_highscores_formats_message(fake_game, monkeypatch):
    game = fake_game
    monkeypatch.setattr(
        game,
        "load_highscores",
        lambda: {
            "Easy": [{"name": "A", "score": 10}],
            "Medium": [],
            "Hard": [{"name": "C", "score": 30}, {"name": "D", "score": 20}],
        },
    )

    messages = []
    monkeypatch.setattr(script.messagebox, "showinfo", lambda title, msg: messages.append((title, msg)))

    game.show_highscores()

    assert messages[0][0] == "Highscores"
    assert "Easy:\n1. A - 10" in messages[0][1]
    assert "Medium:\nNo scores yet" in messages[0][1]
    assert "Hard:\n1. C - 30\n2. D - 20" in messages[0][1]