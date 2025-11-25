"""
Core game logic for Minesweeper.

This module contains pure domain logic without any pygame or pixel-level
concerns. It defines:
- CellState: the state of a single cell
- Cell: a cell positioned by (col,row) with an attached CellState
- Board: grid management, mine placement, adjacency computation, reveal/flag

The Board exposes imperative methods that the presentation layer (run.py)
can call in response to user inputs, and does not know anything about
rendering, timing, or input devices.
"""

import random
from typing import List, Tuple


class CellState:
    """Mutable state of a single cell.

    Attributes:
        is_mine: Whether this cell contains a mine.
        is_revealed: Whether the cell has been revealed to the player.
        is_flagged: Whether the player flagged this cell as a mine.
        adjacent: Number of adjacent mines in the 8 neighboring cells.
    """

    def __init__(self, is_mine: bool = False, is_revealed: bool = False, is_flagged: bool = False, adjacent: int = 0):
        self.is_mine = is_mine
        self.is_revealed = is_revealed
        self.is_flagged = is_flagged
        self.adjacent = adjacent


class Cell:
    """Logical cell positioned on the board by column and row."""

    def __init__(self, col: int, row: int):
        self.col = col
        self.row = row
        self.state = CellState()


class Board:
    """Minesweeper board state and rules.

    Responsibilities:
    - Generate and place mines with first-click safety
    - Compute adjacency counts for every cell
    - Reveal cells (iterative flood fill when adjacent == 0)
    - Toggle flags, check win/lose conditions
    """

    def __init__(self, cols: int, rows: int, mines: int):
        self.cols = cols
        self.rows = rows
        self.num_mines = mines
        self.cells: List[Cell] = [Cell(c, r) for r in range(rows) for c in range(cols)]
        self._mines_placed = False
        self.revealed_count = 0
        self.game_over = False
        self.win = False

    def index(self, col: int, row: int) -> int:
        """Return the flat list index for (col,row)."""
        return row * self.cols + col

    def is_inbounds(self, col: int, row: int) -> bool:
        return 0 <= col < self.cols and 0 <= row < self.rows
    
    def neighbors(self, col: int, row: int) -> List[Tuple[int, int]]:
        deltas = [
            (-1, -1), (0, -1), (1, -1),
            (-1, 0),           (1, 0),
            (-1, 1),  (0, 1),  (1, 1),
        ]
        result = []

        for dx, dy in deltas:
            nc, nr = col + dx, row + dy
            if self.is_inbounds(nc, nr):
                result.append((nc, nr))

        return result

    def place_mines(self, safe_col: int, safe_row: int) -> None:
        forbidden = set()
        forbidden.add((safe_col, safe_row))
        for nc, nr in self.neighbors(safe_col, safe_row):
            forbidden.add((nc, nr))

        candidates = []
        for r in range(self.rows):
            for c in range(self.cols):
                if (c, r) not in forbidden:
                    candidates.append((c, r))

        count = min(self.num_mines, len(candidates))
        mine_positions = random.sample(candidates, count)

        for mc, mr in mine_positions:
            idx = self.index(mc, mr)
            self.cells[idx].state.is_mine = True

        for cell in self.cells:
            mine_count = 0
            for nc, nr in self.neighbors(cell.col, cell.row):
                n_idx = self.index(nc, nr)
                if self.cells[n_idx].state.is_mine:
                    mine_count += 1
            cell.state.adjacent = mine_count

        self.mines_placed = True


    def reveal(self, col: int, row: int) -> None:
        if not self.is_inbounds(col, row):
            return
        
        idx = self.index(col, row)
        cell = self.cells[idx]

        if cell.state.is_revealed or cell.state.is_flagged:
            return
        
        if not self._mines_placed:
            self.place_mines(col, row)

        cell.state.is_revealed = True
        self.revealed_count += 1

        if cell.state.is_mine:
            self.game_over = True
            self._reveal_all_mines()
            return
        
        if cell.state.adjacent == 0:
            for nc, nr in self.neighbors(col, row):
                self.reveal(nc, nr)

        self._check_win()

    def toggle_flag(self, col: int, row: int) -> None:
        if not self.is_inbounds(col, row):
            return
        
        idx = self.index(col, row)
        cell = self.cells[idx]

        if not cell.state.is_revealed:
            cell.state.is_flagged = not cell.state.is_flagged

    def flagged_count(self) -> int:
        count = 0
        for cell in self.cells:
            if cell.state.is_flagged:
                count += 1
        return count

    def _reveal_all_mines(self) -> None:
        """Reveal all mines; called on game over."""
        for cell in self.cells:
            if cell.state.is_mine:
                cell.state.is_revealed = True

    def _check_win(self) -> None:
        """Set win=True when all non-mine cells have been revealed."""
        total_cells = self.cols * self.rows
        if self.revealed_count == total_cells - self.num_mines and not self.game_over:
            self.win = True
            for cell in self.cells:
                if not cell.state.is_revealed and not cell.state.is_mine:
                    cell.state.is_revealed = True
