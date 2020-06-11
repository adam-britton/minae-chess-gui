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

from PySide2.QtCore import QPointF, Qt, QThread, Signal, Slot
from PySide2.QtSvg import QGraphicsSvgItem
from PySide2.QtWidgets import (QAction, QApplication, QDockWidget,
                               QGraphicsScene, QGraphicsSimpleTextItem,
                               QGraphicsView, QMainWindow, QMenuBar,
                               QStatusBar)


class BoardScene(QGraphicsScene):
    """A chess board scene."""

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
        QGraphicsScene.__init__(self)
        self.__add_squares()
        self.piece_items = []
        self.highlighted_square_items = []
        self.legal_moves = {}
        self.selected_pos = None

    def __add_squares(self):
        """Adds initial squares to the board view."""
        for file in 'abcdefgh':
            for rank in '12345678':
                (x, y) = self.__pos_to_x_y(file + rank)
                square = QGraphicsSvgItem(
                    self.IMAGES['l'] if self.__is_light_square(file + rank)
                    else self.IMAGES['d'])
                square.setPos(x, y)
                self.addItem(square)

    def __is_light_square(self, pos):
        """
        Determines if a square position is light or dark.

        This method should only be called on a valid position.

        :param pos: Square position in algebraic notation, e.g. 'e2'
        :return: True of square is light, false if square is dark
        """
        pos_match = re.compile(r'([a-h])([1-8])').match(pos)
        if not pos_match or pos_match.group() != pos:
            raise ValueError

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
        if not pos_match or pos_match.group() != pos:
            raise ValueError

        x = self.SQUARE_WIDTH * (ord(pos_match.group(1)) - ord('a'))
        y = self.BOARD_WIDTH \
            - self.SQUARE_WIDTH \
            * int(pos_match.group(2))

        return (x, y)

    def __x_y_to_pos(self, x, y):
        """
        Converts a scene coordinate position to a chess position.

        :param x: x coordinate (float)
        :param y: y coordinate (float)
        :return: String of chess position
        """
        file = chr(ord('a') + (int(x) // self.SQUARE_WIDTH))
        rank = chr(ord('8') - (int(y) // self.SQUARE_WIDTH))
        return file + rank

    def set_position(self, populated_squares):
        """See BoardView.set_position()."""
        for item in self.highlighted_square_items:
            self.removeItem(item)
        self.highlighted_square_items = []

        for item in self.piece_items:
            self.removeItem(item)
        self.piece_items = []

        for pos in populated_squares:
            (x, y) = self.__pos_to_x_y(pos)
            piece = QGraphicsSvgItem(self.IMAGES[populated_squares[pos]])
            piece.setPos(x, y)
            self.addItem(piece)
            self.piece_items += [piece]

    def set_legal_moves(self, legal_moves):
        """See BoardView.set_legal_moves()."""
        self.legal_moves = legal_moves

    def highlight_squares(self, squares):
        """
        Highlighted a list of squares on the board.

        :param squares: List of squares to highlight.
        """
        for item in self.highlighted_square_items:
            self.removeItem(item)
        self.highlighted_square_items = []

        for pos in squares:
            (x, y) = self.__pos_to_x_y(pos)
            highlighted_square_item = QGraphicsSvgItem(self.IMAGES['h'])
            highlighted_square_item.setPos(x, y)
            self.addItem(highlighted_square_item)
            self.highlighted_square_items += [highlighted_square_item]

    def mousePressEvent(self, event):
        """
        Handles a mouse press event on the scene.

        :param event: QGraphicsSceneMouseEvent
        """
        pos = self.__x_y_to_pos(event.scenePos().x(), event.scenePos().y())

        if self.selected_pos is not None:
            if pos == self.selected_pos:
                self.selected_pos = None
                self.highlight_squares([])
            elif pos in self.legal_moves[self.selected_pos]:
                print(f'Moved from {self.selected_pos} to {pos}')
                self.selected_pos = None
                self.legal_moves = {}
                self.highlight_squares([])
            elif pos in self.legal_moves:
                self.selected_pos = pos
                self.highlight_squares(list(self.legal_moves[pos]) + [pos])
            else:
                self.selected_pos = None
                self.highlight_squares([])

        elif pos in self.legal_moves:
            self.selected_pos = pos
            self.highlight_squares(list(self.legal_moves[pos]) + [pos])


class BoardView(QGraphicsView):
    """A widget representing a graphical view of a chess board."""

    def __init__(self, parent):
        QGraphicsView.__init__(self, parent)
        self.setMinimumSize(BoardScene.BOARD_WIDTH, BoardScene.BOARD_WIDTH)
        self.setMaximumSize(BoardScene.BOARD_WIDTH, BoardScene.BOARD_WIDTH)
        self.scene = BoardScene()
        self.setScene(self.scene)
        self.show()

    def set_position(self, populated_squares):
        """
        Sets the board view to a new position. Discards any square highlights.

        :param populated_squares: Dictionary of non-empty squares, in format
                                  {pos:piece}, e.g. {'e2':'P', ...}
        """
        self.scene.set_position(populated_squares)

    def set_legal_moves(self, legal_moves):
        """
        Sets the legals moves for the board position. This will determine
        which squares get highlighted as a result of mouse clicks.

        :param legal_moves: Dictionary with entries in form
                            {src0:[target0, target1, ...], src1[target0, ...],}
        """
        self.scene.set_legal_moves(legal_moves)


class GameStateView(QGraphicsView):
    """A widget displaying a view of the chess game state."""

    def __init__(self, parent):
        QGraphicsView.__init__(self, parent)
        self.setMinimumSize(180, 115)
        self.setMaximumSize(180, 115)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.text_item = QGraphicsSimpleTextItem()
        self.scene.addItem(self.text_item)
        self.show()

    def set_game_state(self, game_state):
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

    def __init__(self, parent):
        QGraphicsView.__init__(self, parent)
        self.setMinimumWidth(180)
        self.setMaximumWidth(180)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.text_item = QGraphicsSimpleTextItem()
        self.scene.addItem(self.text_item)
        self.show()

    def set_move_history(self, move_history):
        """
        Sets the move history according to a list of moves.

        :param move_history: List of half moves
        """
        text = ''
        half_move_number = 1
        full_move_number = 1
        for half_move in move_history:
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
    set_legal_moves_signal = Signal(dict)
    set_game_state_signal = Signal(dict)
    set_move_history_signal = Signal(list)
    quit_app_signal = Signal()

    def __init__(self):
        QThread.__init__(self)
        self.fen_parser = re.compile(self.FEN_REGEX)
        self.move_history = []

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
            console_in = input('minae-chess-gui$ ')
            try:
                cmds = json.loads(console_in)
            except json.JSONDecodeError as err:
                print(err)
                continue

            for cmd, val in cmds.items():

                if cmd == 'set fen':
                    fen_match = self.fen_parser.match(val)
                    if fen_match \
                            and fen_match.group() == val \
                            and self.__is_minimally_valid_fen(fen_match):
                        populated_squares = \
                            self.__fen_to_populated_squares(fen_match)
                        self.set_position_signal.emit(populated_squares)
                        self.set_game_state_signal.emit({
                            'Turn': fen_match.group(9),
                            'Castling availability': fen_match.group(10),
                            'En-passant target': fen_match.group(11),
                            'Half move clock': fen_match.group(14),
                            'Full move number': fen_match.group(15),
                        })

                elif cmd == 'append history':
                    self.move_history += val
                    self.set_move_history_signal.emit(self.move_history)

                elif cmd == 'undo history':
                    if len(self.move_history) > 0:
                        self.move_history.pop()
                        self.set_move_history_signal.emit(self.move_history)

                elif cmd == 'set history':
                    self.move_history = val
                    self.set_move_history_signal.emit(self.move_history)

                elif cmd == 'set legal moves':
                    legal_moves = {}
                    for move in val:
                        move_match = re.compile(
                            r'([a-h][1-8])([a-h][1-8])').match(move)
                        if not move_match or move_match.group() != move:
                            print(f'Unrecognized move: {move}')
                            continue
                        if move_match.group(1) in legal_moves:
                            legal_moves[move_match.group(1)] \
                                .add(move_match.group(2))
                        else:
                            legal_moves[move_match.group(1)] \
                                = {move_match.group(2)}
                    self.set_legal_moves_signal.emit(legal_moves)

                elif cmd == 'quit':
                    self.quit_app_signal.emit()
                    return

                else:
                    print('Error: Unrecognized command')



class MainWindow(QMainWindow):

    """Main window for the application."""
    def __init__(self):
        QMainWindow.__init__(self)

        # First initialize the underlying views
        self.board_view = BoardView(self)
        self.game_state_view = GameStateView(self)
        self.move_history_view = MoveHistoryView(self)

        # Next initialize the docks
        self.game_state_dock = self.add_dock(
            'GameState',
            self.game_state_view,
            hidden=True
        )
        self.move_history_dock = self.add_dock(
            'Move History',
            self.move_history_view,
            hidden=True
        )

        # Next initialize the menu and status bars
        self.undo_action = QAction('Undo', self)
        self.undo_action.setDisabled(True)
        self.menu_bar = self.add_menu_bar({
            'Minae': [
                self.game_state_dock.toggleViewAction(),
                self.move_history_dock.toggleViewAction(),
                self.undo_action,
            ],
        })
        self.status_bar = QStatusBar(self)

        # Finally tie it all together
        self.setCentralWidget(self.board_view)
        self.addDockWidget(Qt.RightDockWidgetArea, self.game_state_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.move_history_dock)
        self.setMenuBar(self.menu_bar)
        self.setStatusBar(self.status_bar)
        self.show()

    def closeEvent(self, event):
        """Handle closing of the main window."""
        event.accept()

    @Slot(dict)
    def set_position(self, populated_squares):
        """
        Sets to a new chess position.

        :param populated_squares: Dictionary of non-empty squares, in format
                                  {pos:piece}, e.g. {'e2':'P', ...}
        """
        self.board_view.set_position(populated_squares)

    @Slot(dict)
    def set_legal_moves(self, legal_moves):
        """
        Sets the legals moves.

        :param legal_moves: Dictionary with entries in form
            {src0:[target0, target1, ...], src1:[target0, ...],}
        """
        self.board_view.set_legal_moves(legal_moves)

    @Slot(dict)
    def set_game_state(self, game_state):
        """
        Sets the game state.

        :param game_state: Dictionary containing {topic:value} pairs
        """
        self.game_state_view.set_game_state(game_state)

    @Slot(list)
    def set_move_history(self, move_history):
        """
        Sets the move history.

        :param move_history: List of half moves
        """
        self.move_history_view.set_move_history(move_history)

    def add_dock(self, title, widget, hidden=True):
        """Adds the move history dock to the main window."""
        dock = QDockWidget(title, self)
        dock.setWidget(widget)
        if hidden:
            dock.hide()
        return dock

    def add_menu_bar(self, menus):
        """Adds the menu bar to the main window."""
        menu_bar = QMenuBar(self)
        for menu, actions in menus.items():
            menu = menu_bar.addMenu(menu)
            for action in actions:
                menu.addAction(action)
        return menu_bar


class Minae:

    def __init__(self):
        self.app = QApplication()
        self.main_window = MainWindow()
        self.io_thread = IOThread()

        self.io_thread.set_position_signal.connect(
            self.main_window.set_position)
        self.io_thread.set_legal_moves_signal.connect(
            self.main_window.set_legal_moves)
        self.io_thread.set_game_state_signal.connect(
            self.main_window.set_game_state)
        self.io_thread.set_move_history_signal.connect(
            self.main_window.set_move_history)
        self.io_thread.quit_app_signal.connect(
            self.app.quit, Qt.QueuedConnection)

    def start(self):
        self.io_thread.start()
        self.app.exec_()


def main(argv):

    minae = Minae()
    minae.start()


if __name__ == "__main__":

    main(sys.argv)
