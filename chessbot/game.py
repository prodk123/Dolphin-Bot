from chessbot.board import Board
from chessbot.const import *

class Game:
    def __init__(self):
        self.board = Board()
        self.next_player = 'white'
        self.hovered_sqr = None
        self.game_over = False

    def next_turn(self):
        """Handle the transition to the next turn and check for game end conditions."""
        self.next_player = 'black' if self.next_player == 'white' else 'white'
        
        # Check for checkmate first
        if self.board.is_checkmate(self.next_player):
            winner = 'black' if self.next_player == 'white' else 'white'
            print(f"Checkmate! {winner} wins!")
            # Set game state to ended
            self.game_over = True
            return True
        
        # Check for check
        if self.board.is_in_check(self.next_player):
            print(f"{self.next_player} is in check!")
        
        # Check for stalemate
        elif self.board.is_stalemate(self.next_player):
            print("Stalemate! Game is a draw.")
            self.game_over = True
            return True
        
        return False

    def set_hover(self, row, col):
        if 0 <= row < BOARD_HEIGHT and 0 <= col < BOARD_WIDTH:
            self.hovered_sqr = self.board.squares[row][col]
        else:
            self.hovered_sqr = None

    def reset(self):
        """Reset the game to initial state."""
        self.board = Board()  # Create a fresh board
        self.board.reset_scores()  # Explicitly reset scores
        self.next_player = 'white'
        self.hovered_sqr = None
        self.game_over = False
        # Clear move history
        self.board.move_history = []
        self.board.last_move = None
