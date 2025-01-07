from constant import *
from square import *
from piece import * 

class Board:
    def __init__(self):
        self.square=[[0,0,0,0,0,0,0,0] for i in range(columns)]
        self.create()
        self.add_piece('white')
        self.add_piece('black')

    def create(self):
        for r in range (rows):
            for c in range(columns):
                self.square[r][c]= Square(r,c)

    def add_piece(self,colour):
        if (colour=='white'):
            row_pawn=6
            row_other=7
        else:
            row_pawn=1
            row_other=0
        #pawn
        for cols in range(columns):
            self.square[row_pawn][cols]= Square(row_pawn,cols,Pawn(colour))
        #knight
        self.square[row_other][1]= Square(row_other,1,Knight(colour))
        self.square[row_other][6]= Square(row_other,6,Knight(colour))
        #bishop
        self.square[row_other][2]= Square(row_other,2,Bishop(colour))
        self.square[row_other][5]= Square(row_other,5,Bishop(colour))
        #rook
        self.square[row_other][0]= Square(row_other,0,Rook(colour))
        self.square[row_other][7]= Square(row_other,7,Rook(colour))
        #queen
        self.square[row_other][3]= Square(row_other,3,Queen(colour))   
        #king
        self.square[row_other][4]= Square(row_other,4,King(colour))   
        