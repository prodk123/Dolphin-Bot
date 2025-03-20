from board import Board
from dragger import Dragger
from const import *
import pygame

class Game:
    def __init__(self):
        self.board = Board()
        self.dragger = Dragger()
        self.next_player = 'white'
        self.hovered_sqr = None

    def show_moves(self, surface):
        """Show valid moves for the currently dragged piece."""
        if self.dragger.dragging:
            piece = self.dragger.piece
            
            # Loop through valid moves
            for move in piece.moves:
                # Color
                color = (180, 180, 180)
                # Circle center position
                center = (move.final.col * SQUARE_SIZE + SQUARE_SIZE // 2, 
                         move.final.row * SQUARE_SIZE + SQUARE_SIZE // 2)
                # Draw circle
                pygame.draw.circle(surface, color, center, 15)

    def show_bg(self, surface):
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                color = (234, 235, 200) if (row + col) % 2 == 0 else (119, 154, 88)
                rect = (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                pygame.draw.rect(surface, color, rect)

    def show_pieces(self, surface):
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                if self.board.squares[row][col].has_piece():
                    piece = self.board.squares[row][col].piece
                    if piece is not self.dragger.piece:
                        img = pygame.image.load(piece.texture)
                        img_center = (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2)
                        piece.texture_rect = img.get_rect(center=img_center)
                        surface.blit(img, piece.texture_rect)

    def show_last_move(self, surface):
        if self.board.last_move:
            initial = self.board.last_move.initial
            final = self.board.last_move.final
            color = (180, 180, 180)
            rect_initial = (initial.col * SQUARE_SIZE, initial.row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            rect_final = (final.col * SQUARE_SIZE, final.row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(surface, color, rect_initial)
            pygame.draw.rect(surface, color, rect_final)

    def show_hover(self, surface):
        if self.hovered_sqr:
            color = (180, 180, 180)
            rect = (self.hovered_sqr.col * SQUARE_SIZE, self.hovered_sqr.row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(surface, color, rect, width=3)

    def next_turn(self):
        """Handle the transition to the next turn and check for game end conditions."""
        self.next_player = 'black' if self.next_player == 'white' else 'white'
        
        # Check for check
        if self.board.is_in_check(self.next_player):
            if self.board.is_checkmate(self.next_player):
                print(f"Checkmate! {self.next_player} loses!")
                return True
            print(f"{self.next_player} is in check!")
        
        # Check for stalemate
        elif self.board.is_stalemate(self.next_player):
            print("Stalemate! Game is a draw.")
            return True
        
        return False

    def set_hover(self, row, col):
        if 0 <= row < BOARD_HEIGHT and 0 <= col < BOARD_WIDTH:
            self.hovered_sqr = self.board.squares[row][col]
        else:
            self.hovered_sqr = None

    def reset(self):
        """Reset the game to initial state."""
        self.board = Board()  # This will create a fresh board with reset scores
        self.dragger = Dragger()
        self.next_player = 'white'
        self.hovered_sqr = None

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
