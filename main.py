import pygame
import sys

from constant import *
from game import *


class Main:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((width,height))
        pygame.display.set_caption("Dolphin")
        self.game=Game()


    def mainloop(self):
       screen=self.screen
       game=self.game
       game.show_bg(screen)
       game.show_pieces(screen)
       while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                pygame.display.update()

main = Main()
main.mainloop()
