from board import Board
from const import *

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

    def play_sound(self, captured=False):
        sound = pygame.mixer.Sound('assets/capture.wav' if captured else 'assets/move.wav')
        sound.play()

    def show_scores(self, surface):
        font = pygame.font.SysFont('Arial', 24, bold=True)
        panel_x = SCREEN_WIDTH - 200
        
        # Draw panel background
        pygame.draw.rect(surface, (40, 40, 40), (panel_x, 0, 200, SCREEN_HEIGHT))
        
        # Show scores
        white_score = self.board.white_score
        black_score = self.board.black_score
        
        white_text = font.render(f"White: {white_score}", True, (255, 255, 255))
        black_text = font.render(f"Black: {black_score}", True, (200, 200, 200))
        surface.blit(white_text, (panel_x + 20, 20))
        surface.blit(black_text, (panel_x + 20, SCREEN_HEIGHT - 40))

        # Show captured pieces headers
        font = pygame.font.SysFont('Arial', 20, bold=True)
        white_captured = font.render("White Captures:", True, (255, 255, 255))
        black_captured = font.render("Black Captures:", True, (200, 200, 200))
        surface.blit(white_captured, (panel_x + 20, 60))
        surface.blit(black_captured, (panel_x + 20, SCREEN_HEIGHT - 180))

        # Display captured pieces
        piece_size = 35
        spacing = 40
        max_pieces_per_row = 4
        
        # White's captured pieces (black pieces captured by white)
        for i, piece_type in enumerate(self.board.captured_pieces["white"]):
            row = i // max_pieces_per_row
            col = i % max_pieces_per_row
            x = panel_x + 20 + col * spacing
            y = 100 + row * spacing
            
            try:
                piece_path = f'assets/{piece_type}_b.png'  # black pieces captured by white
                img = pygame.image.load(piece_path)
                img = pygame.transform.scale(img, (piece_size, piece_size))
                surface.blit(img, (x, y))
            except Exception as e:
                print(f"Error loading piece texture: {e}")

        # Black's captured pieces (white pieces captured by black)
        for i, piece_type in enumerate(self.board.captured_pieces["black"]):
            row = i // max_pieces_per_row
            col = i % max_pieces_per_row
            x = panel_x + 20 + col * spacing
            y = SCREEN_HEIGHT - 140 + row * spacing
            
            try:
                piece_path = f'assets/{piece_type}_w.png'  # white pieces captured by black
                img = pygame.image.load(piece_path)
                img = pygame.transform.scale(img, (piece_size, piece_size))
                surface.blit(img, (x, y))
            except Exception as e:
                print(f"Error loading piece texture: {e}")
