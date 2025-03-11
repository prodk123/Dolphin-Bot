class Move:

    def __init__(self, initial, final):
        # initial and final are squares
        self.initial = initial
        self.final = final
        self.piece = None
        self.captured = None

    def __str__(self):
        s = ''
        s += f'({self.initial.col}, {self.initial.row})'
        s += f' -> ({self.final.col}, {self.final.row})'
        return s

    def __eq__(self, other):
        return (self.initial.row == other.initial.row and 
                self.initial.col == other.initial.col and 
                self.final.row == other.final.row and 
                self.final.col == other.final.col)