#!/usr/bin/env python3
#
# Copyright 2020 Adam Britton
#
# This file is part of Minae Chess GUI.
#
# Minae Chess GUI is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Minae Chess GUI is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Minae Chess GUI.  If not, see <https://www.gnu.org/licenses/>.

import json
import re
import sys

from PySide2.QtCore import Qt, QThread, Signal, Slot
from PySide2.QtSvg import QGraphicsSvgItem
from PySide2.QtWidgets import (QApplication, QDockWidget,
                               QGraphicsScene, QGraphicsSimpleTextItem,
                               QGraphicsView, QMainWindow)


class BoardView(QGraphicsView):
    """A widget representing a graphical view of a chess board."""

    SQUARE_WIDTH = 45
    BOARD_WIDTH = SQUARE_WIDTH * 8

    IMAGES = {
        'P': 'graphics/white-pawn.svg',
        'R': 'graphics/white-rook.svg',
        'N': 'graphics/white-knight.svg',
        'B': 'graphics/white-bishop.svg',
        'Q': 'graphics/white-queen.svg',
        'K': 'graphics/white-king.svg',
        'p': 'graphics/black-pawn.svg',
        'r': 'graphics/black-rook.svg',
        'n': 'graphics/black-knight.svg',
        'b': 'graphics/black-bishop.svg',
        'q': 'graphics/black-queen.svg',
        'k': 'graphics/black-king.svg',
        'l': 'graphics/light.svg',
        'd': 'graphics/dark.svg',
        'h': 'graphics/highlight.svg',
    }

    def __init__(self):
        QGraphicsView.__init__(self)
        self.setMinimumSize(self.BOARD_WIDTH, self.BOARD_WIDTH)
        self.setMaximumSize(self.BOARD_WIDTH, self.BOARD_WIDTH)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.__add_squares()
        self.show()
        self.piece_items = []
        self.highlighted_square_items = []

    def __add_squares(self):
        """Adds initial squares to the board view."""
        for file in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']:
            for rank in ['1', '2', '3', '4', '5', '6', '7', '8']:
                (x, y) = self.__pos_to_x_y(file + rank)
                square = QGraphicsSvgItem(
                    self.IMAGES['l'] if self.__is_light_square(file + rank)
                    else self.IMAGES['d'])
                square.setPos(x, y)
                self.scene.addItem(square)

    def __is_light_square(self, pos):
        """
        Determines if a square position is light or dark.

        This method should only be called on a valid position.

        :param pos: Square position in algebraic notation, e.g. 'e2'
        :return: True of square is light, false if square is dark
        """
        pos_match = re.compile(r'([a-h])([1-8])').match(pos)
        assert(pos_match)
        assert(pos_match.group() == pos)

        if pos_match.group(1) in 'aceg':
            return int(pos_match.group(2)) % 2 == 0
        else:
            return int(pos_match.group(2)) % 2 == 1

    def __pos_to_x_y(self, pos):
        """
        Converts a square position in algebraic notation to a scene
        coordinate position.

        This method should only be called on a valid position.

        :param pos: Square position in algebraic notation (e.g. 'e2')
        :return: Tuple containing (x, y) coordinates for the position
        """
        pos_match = re.compile(r'([a-h])([1-8])').match(pos)
        assert(pos_match)
        assert(pos_match.group() == pos)

        x = self.SQUARE_WIDTH * (ord(pos_match.group(1)) - ord('a'))
        y = self.BOARD_WIDTH \
            - self.SQUARE_WIDTH \
            * int(pos_match.group(2))

        return (x, y)

    @Slot(dict)
    def set_position(self, populated_squares):
        """
        Sets the board view to a new position. Discards any square highlights.

        :param populated_squares: Dictionary of non-empty squares, in format
                                  {pos:piece}, e.g. {'e2':'P', ...}
        """
        for item in self.highlighted_square_items:
            self.scene.removeItem(item)
        self.highlighted_square_items = []

        for item in self.piece_items:
            self.scene.removeItem(item)
        self.piece_items = []

        for pos in populated_squares:
            (x, y) = self.__pos_to_x_y(pos)
            piece = QGraphicsSvgItem(self.IMAGES[populated_squares[pos]])
            piece.setPos(x, y)
            self.scene.addItem(piece)
            self.piece_items += [piece]

    @Slot(list)
    def set_highlighted_squares(self, highlighted_squares):
        """
        Sets the highlighted squares on the board.

        :param highlighted_squares: List of highlighted squares
        """
        for item in self.highlighted_square_items:
            self.scene.removeItem(item)
        self.highlighted_square_items = []

        for pos in highlighted_squares:
            (x, y) = self.__pos_to_x_y(pos)
            square = QGraphicsSvgItem(self.IMAGES['h'])
            square.setPos(x, y)
            self.scene.addItem(square)
            self.highlighted_square_items += [square]


class GameStateView(QGraphicsView):
    """A widget displaying a view of the chess game state."""

    def __init__(self):
        QGraphicsView.__init__(self)
        self.setMinimumSize(180, 115)
        self.setMaximumSize(180, 115)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.text_item = QGraphicsSimpleTextItem()
        self.scene.addItem(self.text_item)
        self.show()

    @Slot(dict)
    def update(self, game_state):
        """
        Updates the game state view with the provided values.

        :param game_state: Dictionary containing {topic:value} pairs
        """
        text = ''
        for topic in game_state:
            text += topic + ': ' + game_state[topic] + '\n'

        self.text_item.setText(text)


class MoveHistoryView(QGraphicsView):
    """A widget containing a view of the move history."""

    def __init__(self):
        QGraphicsView.__init__(self)
        self.setMinimumWidth(180)
        self.setMaximumWidth(180)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.text_item = QGraphicsSimpleTextItem()
        self.scene.addItem(self.text_item)
        self.show()
        self.move_history = []

    @Slot(str)
    def add_half_move(self, half_move):
        """
        Adds a half move to the move history.

        :param half_move: String of the half move
        """
        self.move_history += [half_move]
        self.update()

    @Slot()
    def remove_half_move(self):
        """Removes the most recent half move from the move history."""
        if len(self.move_history) > 0:
            self.move_history.pop()
            self.update()

    @Slot(list)
    def set_history(self, history):
        """
        Sets the move history according to a list of moves.

        :param history: List of half moves
        """
        self.move_history = history
        self.update()

    def update(self):
        """Updates the view with the move history."""
        text = ''
        half_move_number = 1
        full_move_number = 1
        for half_move in self.move_history:
            if half_move_number % 2 == 1:
                text += str(full_move_number) + '. ' + half_move
                half_move_number += 1
            else:
                text += ' ' + half_move + '\n'
                half_move_number += 1
                full_move_number += 1

        self.text_item.setText(text)


class IOThread(QThread):
    """Collects and validates input data, and updates views."""

    FEN_REGEX = (
        r'([PRNBQKprnbqk1-8]{1,8})/'  # Group 1:  Rank 8
        r'([PRNBQKprnbqk1-8]{1,8})/'  # Group 2:  Rank 7
        r'([PRNBQKprnbqk1-8]{1,8})/'  # Group 3:  Rank 6
        r'([PRNBQKprnbqk1-8]{1,8})/'  # Group 4:  Rank 5
        r'([PRNBQKprnbqk1-8]{1,8})/'  # Group 5:  Rank 4
        r'([PRNBQKprnbqk1-8]{1,8})/'  # Group 6:  Rank 3
        r'([PRNBQKprnbqk1-8]{1,8})/'  # Group 7:  Rank 2
        r'([PRNBQKprnbqk1-8]{1,8}) '  # Group 8:  Rank 1
        r'([wb]) '                    # Group 9:  Active color
        r'(-|K?Q?k?q?) '              # Group 10: Castling availability
        r'(-|([a-h])([1-8])) '        # Group 11: En passant target
                                      # Group 12: En passant target, file
                                      # Group 13: En passant target, rank
        r'(0|[1-9][0-9]*) '           # Group 14: Half move clock (for draws)
        r'([1-9][0-9]*)'              # Group 15: Full move number
    )

    set_position_signal = Signal(dict)
    set_highlighted_squares_signal = Signal(list)
    update_game_state_signal = Signal(dict)
    add_half_move_signal = Signal(str)
    remove_half_move_signal = Signal()
    set_history_signal = Signal(list)
    close_app_signal = Signal()

    def __init__(self, set_position_slot, set_highlighted_squares_slot,
                 update_game_state_slot, add_half_move_slot,
                 remove_half_move_slot, set_history_slot, close_app_slot):
        QThread.__init__(self)
        self.fen_parser = re.compile(self.FEN_REGEX)
        self.set_position_signal.connect(set_position_slot)
        self.set_highlighted_squares_signal.connect(
            set_highlighted_squares_slot)
        self.update_game_state_signal.connect(update_game_state_slot)
        self.add_half_move_signal.connect(add_half_move_slot)
        self.remove_half_move_signal.connect(remove_half_move_slot)
        self.set_history_signal.connect(set_history_slot)
        self.close_app_signal.connect(close_app_slot, Qt.QueuedConnection)

    def __is_minimally_valid_fen(self, fen_match):
        """
        Checks if a FEN is minimally valid, that is, valid enough to display.

        This method does not necessarily determine whether the position is
        fully legal.

        :param fen_match Match object for the FEN
        """
        # For the ranks (groups 1-8), validate that:
        # - There are never two numbers consecutively
        # - The sum of pieces and empty squares adds to 8
        for g in range(1, 9):
            prev_was_number = False
            sum_for_rank = 0
            for c in fen_match.group(g):
                if '1' <= c <= '8':
                    # Number denotes empty square(s)
                    if prev_was_number:
                        return False
                    sum_for_rank += int(c)
                    prev_was_number = True
                else:
                    # Letter denotes a piece
                    sum_for_rank += 1
                    prev_was_number = False
            if sum_for_rank != 8:
                return False

        # For the active color (group 9), no validation is
        # needed beyond matching the regex.

        # For castling availability (group 10), validate that it is not an
        # empty string. The regex validates everything else.
        if fen_match.group(10) == '':
            return False

        # For en passant target square (group 11, with file and rank
        # separately as group 12 and 13), no validation is needed beyond
        # matching the regex. The engine must make sure it is valid
        # otherwise.

        # For half move clock (group 14), no additional validation is needed
        # beyond matching the regex.

        # For the full move number (group 15), no additional validation is
        # needed beyond matching the regex.

        return True

    def __fen_to_populated_squares(self, fen_match):
        """
        Given a FEN Match object, returns a dictionary of populated squares.

        :param fen_match Match object for the FEN
        :return: Dictionary in format {pos:piece}, e.g. {'e2':'P'}
        """
        populated_squares = {}
        for g in range(1, 9):
            file = 'a'
            rank = chr(ord('9') - g)
            for c in fen_match.group(g):
                if '1' <= c <= '8':
                    # Empty square(s), so just increment the file
                    file = chr(ord(file) + int(c))
                else:
                    # Populated square, so add the piece
                    populated_squares[file + rank] = c
                    file = chr(ord(file) + 1)
        return populated_squares

    def run(self):
        """Executes the IO thread."""
        while True:
            console_in = input('chess$ ')
            try:
                cmds = json.loads(console_in)
            except json.JSONDecodeError as err:
                print(err)
                continue

            for cmd in cmds:
                if cmd == 'set fen':
                    fen_match = self.fen_parser.match(cmds[cmd])
                    if fen_match \
                            and fen_match.group() == cmds[cmd] \
                            and self.__is_minimally_valid_fen(fen_match):
                        populated_squares = \
                            self.__fen_to_populated_squares(fen_match)
                        self.set_position_signal.emit(populated_squares)
                        self.update_game_state_signal.emit({
                            'Turn': fen_match.group(9),
                            'Castling availability': fen_match.group(10),
                            'En-passant target': fen_match.group(11),
                            'Half move clock': fen_match.group(14),
                            'Full move number': fen_match.group(15),
                        })
                elif cmd == 'append history':
                    for half_move in cmds[cmd]:
                        self.add_half_move_signal.emit(half_move)
                elif cmd == 'undo history':
                    self.remove_half_move_signal.emit()
                elif cmd == 'set history':
                    self.set_history_signal.emit(cmds[cmd])
                elif cmd == 'set legal moves':
                    pass
                elif cmd == 'quit':
                    self.close_app_signal.emit()
                    return
                else:
                    print('Error: Unrecognized command')


def main(argv):

    print("Let's play chess!")
    app = QApplication()
    main_window = QMainWindow()
    board_view = BoardView()
    game_state_view = GameStateView()
    move_history_view = MoveHistoryView()
    main_window.setCentralWidget(board_view)
    game_state_dock = QDockWidget('Game State')
    game_state_dock.setWidget(game_state_view)
    move_history_dock = QDockWidget('Move History')
    move_history_dock.setWidget(move_history_view)
    main_window.addDockWidget(Qt.RightDockWidgetArea, game_state_dock)
    main_window.addDockWidget(Qt.RightDockWidgetArea, move_history_dock)
    main_window.show()
    iothread = IOThread(
        board_view.set_position,
        board_view.set_highlighted_squares,
        game_state_view.update,
        move_history_view.add_half_move,
        move_history_view.remove_half_move,
        move_history_view.set_history,
        app.quit
    )
    iothread.start()
    app.exec_()


if __name__ == "__main__":

    main(sys.argv)
