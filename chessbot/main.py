import pygame
import sys
import threading
import time
from const import *
from game import Game
from square import Square
from move import Move
from chess_ai_bot import get_best_move
import os


class Main:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Chess')
        self.init_game()

    def init_game(self):
        self.game = Game()
        self.ai_thinking = False
        self.clock = pygame.time.Clock()
        self.FPS = 60
        self.game_over = False

    def ai_move(self, board, game):
        try:
            self.ai_thinking = True
            best_move = get_best_move(board, depth=2, player=game.next_player)
            
            # Check if game is still active before making the move
            if best_move and not self.game_over:
                piece = board.squares[best_move.initial.row][best_move.initial.col].piece
                if piece:  # Verify piece still exists
                    captured = board.squares[best_move.final.row][best_move.final.col].has_piece()
                    board.move(piece, best_move)
                    self.safe_play_sound(captured)
                    game.next_turn()
        except Exception as e:
            print(f"AI move error: {str(e)}")
        finally:
            self.ai_thinking = False

    def safe_play_sound(self, captured=False):
        try:
            sound_file = 'assets/capture.wav' if captured else 'assets/move.wav'
            if os.path.exists(sound_file):
                sound = pygame.mixer.Sound(sound_file)
                sound.play()
        except Exception as e:
            print(f"Sound error: {str(e)}")

    def update_screen(self, screen, game, dragger):
        try:
            game.show_bg(screen)
            game.show_last_move(screen)
            game.show_pieces(screen)
            game.show_scores(screen)
            game.show_hover(screen)
            game.show_moves(screen)
            
            if dragger.dragging:
                dragger.update_blit(screen)
            
            if self.game_over:
                self.show_game_over(screen, game.next_player)
            
            pygame.display.flip()
        except Exception as e:
            print(f"Screen update error: {str(e)}")

    def show_game_over(self, screen, winner):
        s = pygame.Surface((400, 200))
        s.set_alpha(200)  # More visible
        s.fill((0, 0, 0))  # Black background
        screen.blit(s, (WIDTH//2 - 200, HEIGHT//2 - 100))
        
        font = pygame.font.SysFont('arial', 36, bold=True)
        if winner == 'black':
            text = font.render("White Wins by Checkmate!", True, (255, 255, 255))
        else:
            text = font.render("Black Wins by Checkmate!", True, (255, 255, 255))
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - text.get_height()//2))
        
        font = pygame.font.SysFont('arial', 24)
        text = font.render("Press 'R' to restart", True, (255, 255, 255))
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 + 40))

    def mainloop(self):
        screen = self.screen
        game = self.game
        board = game.board
        dragger = game.dragger

        while True:
            self.clock.tick(self.FPS)
            self.update_screen(screen, game, dragger)

            # Check for checkmate at the start of each turn
            if not self.game_over:
                if board.is_checkmate(game.next_player):
                    self.game_over = True
                    continue
                elif board.is_stalemate(game.next_player):
                    self.game_over = True
                    continue

            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if not self.ai_thinking and game.next_player == 'white' and not self.game_over:
                        dragger.update_mouse(event.pos)
                        clicked_row = dragger.mouseY // SQSIZE
                        clicked_col = dragger.mouseX // SQSIZE

                        if 0 <= clicked_row < ROWS and 0 <= clicked_col < COLS:
                            square = board.squares[clicked_row][clicked_col]
                            if square.has_piece():
                                piece = square.piece
                                if piece.color == game.next_player:
                                    board.calc_moves(piece, clicked_row, clicked_col, bool=True)
                                    dragger.save_initial(event.pos)
                                    dragger.drag_piece(piece)

                elif event.type == pygame.MOUSEMOTION:
                    if not self.game_over:
                        motion_row = event.pos[1] // SQSIZE
                        motion_col = event.pos[0] // SQSIZE
                        
                        if 0 <= motion_row < ROWS and 0 <= motion_col < COLS:
                            game.set_hover(motion_row, motion_col)
                            if dragger.dragging:
                                dragger.update_mouse(event.pos)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if dragger.dragging and not self.game_over:
                        dragger.update_mouse(event.pos)
                        released_row = dragger.mouseY // SQSIZE
                        released_col = dragger.mouseX // SQSIZE

                        initial = Square(dragger.initial_row, dragger.initial_col)
                        final = Square(released_row, released_col)
                        move = Move(initial, final)

                        if (0 <= released_row < ROWS and 0 <= released_col < COLS and 
                            dragger.piece.color == game.next_player and
                            board.valid_move(dragger.piece, move)):
                            
                            captured = board.squares[released_row][released_col].has_piece()
                            board.move(dragger.piece, move)
                            self.safe_play_sound(captured)
                            game.next_turn()

                            # Check for checkmate after the move
                            if board.is_checkmate(game.next_player):
                                self.game_over = True
                            elif board.is_stalemate(game.next_player):
                                self.game_over = True
                            elif game.next_player == 'black' and not self.game_over:
                                # Make AI move immediately
                                self.ai_thinking = True
                                best_move = get_best_move(board, depth=2, player='black')
                                if best_move:
                                    piece = board.squares[best_move.initial.row][best_move.initial.col].piece
                                    if piece:
                                        captured = board.squares[best_move.final.row][best_move.final.col].has_piece()
                                        board.move(piece, best_move)
                                        self.safe_play_sound(captured)
                                        game.next_turn()
                                        if board.is_checkmate(game.next_player):
                                            self.game_over = True
                                self.ai_thinking = False
                    
                    dragger.undrag_piece()

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_t:
                        game.change_theme()
                    if event.key == pygame.K_r:
                        self.init_game()
                        game = self.game
                        board = game.board
                        dragger = game.dragger

                elif event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

if __name__ == "__main__":
    main = Main()
    main.mainloop()
