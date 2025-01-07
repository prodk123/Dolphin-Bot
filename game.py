import pygame

from constant import *
from board import *

class Game:
    def __init__(self):
        self.board =Board()

    def show_bg(self,screen):
        for r in range(rows):
            for c in range(columns):
                if ((r+c)%2==0):
                    colour= (173, 216, 230)
                else:
                    colour=(0, 0, 255)
                rect=(r*sq_size,c*sq_size,sq_size,sq_size)
                pygame.draw.rect(screen,colour,rect)
    
    def show_pieces(self,screen):
        for r in range(rows):
            for c in range(columns):
                if (self.board.square[r][c].has_piece()):
                    piece=self.board.square[r][c].piece

                    image = pygame.image.load(piece.texture)

                    image_center = c * sq_size+sq_size//2,r *sq_size+sq_size//2
                    piece.texture_rect=image.get_rect(center=image_center)
                    screen.blit(image,piece.texture_rect)
    # def show_pieces(self, surface):
    #     for row in range(rows):
    #         for col in range(columns):
    #             # piece ?
    #             if self.board.squares[row][col].has_piece():
    #                 piece = self.board.squares[row][col].piece
                    
    #                 # all pieces except dragger piece
    #                 if piece is not self.dragger.piece:
    #                     piece.set_texture(size=80)
    #                     img = pygame.image.load(piece.texture)
    #                     img_center = col * sq_size + sq_size // 2, row * sq_size + sq_size // 2
    #                     piece.texture_rect = img.get_rect(center=img_center)
    #                     surface.blit(img, piece.texture_rect)