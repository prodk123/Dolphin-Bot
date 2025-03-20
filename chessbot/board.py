from const import *
from square import Square
from piece import *
from move import Move
from sound import Sound
import copy
import os


class Board:
    def __init__(self):
        self.squares = [[Square(row, col) for col in range(BOARD_WIDTH)]
                        for row in range(BOARD_HEIGHT)]
        self.last_move = None
        self.reset_scores()
        self.move_history = []
        self._create()
        self._add_pieces('white')
        self._add_pieces('black')
        # Cache for position evaluations
        self.position_cache = {}
        # Cache for move calculations
        self.move_cache = {}

    def reset_scores(self):
        """Reset all score-related attributes for a new game."""
        self.captured_pieces = {"white": [], "black": []}
        self.white_score = 0
        self.black_score = 0

    def _create(self):
        """Initialize the board with empty squares."""
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                self.squares[row][col] = Square(row, col)

    def _add_pieces(self, color):
        """Initialize all chess pieces on the board."""
        row_pawn, row_main = (6, 7) if color == 'white' else (1, 0)

        # Place pawns
        for col in range(BOARD_WIDTH):
            self.squares[row_pawn][col].piece = Pawn(color)

        # Place main pieces
        self.squares[row_main][0].piece = Rook(color)
        self.squares[row_main][7].piece = Rook(color)
        self.squares[row_main][1].piece = Knight(color)
        self.squares[row_main][6].piece = Knight(color)
        self.squares[row_main][2].piece = Bishop(color)
        self.squares[row_main][5].piece = Bishop(color)
        self.squares[row_main][3].piece = Queen(color)
        self.squares[row_main][4].piece = King(color)

    def move(self, piece, move, testing=False):
        """Execute a move on the board."""
        initial, final = move.initial, move.final
        
        # Clear caches on actual moves
        if not testing:
            self.position_cache.clear()
            self.move_cache.clear()
        
        # Store the captured piece if any
        captured_piece = self.squares[final.row][final.col].piece
        
        if captured_piece and not testing:
            piece_type = captured_piece.__class__.__name__.lower()
            self.captured_pieces[piece.color].append(piece_type)
            if piece.color == "white":
                self.white_score += captured_piece.value
            else:
                self.black_score += captured_piece.value

        # Move the piece
        self.squares[initial.row][initial.col].piece = None
        self.squares[final.row][final.col].piece = piece
        
        # Handle pawn promotion
        if isinstance(piece, Pawn) and final.row in (0, 7):
            promoted_piece = Queen(piece.color)
            self.squares[final.row][final.col].piece = promoted_piece
            if not testing:
                promoted_piece.moved = True
        
        if not testing:
            piece.moved = True
            piece.clear_moves()
            self.last_move = move
            self.move_history.append(move)
            
            # Handle castling
            if isinstance(piece, King) and abs(final.col - initial.col) == 2:
                # Kingside castling
                if final.col > initial.col:
                    rook = self.squares[initial.row][7].piece
                    self.squares[initial.row][7].piece = None
                    self.squares[initial.row][5].piece = rook
                    rook.moved = True
                # Queenside castling
                else:
                    rook = self.squares[initial.row][0].piece
                    self.squares[initial.row][0].piece = None
                    self.squares[initial.row][3].piece = rook
                    rook.moved = True

    def undo_move(self, piece, move, captured_piece):
        """Undo a move on the board."""
        # Restore pieces to their original positions
        self.squares[move.initial.row][move.initial.col].piece = piece
        self.squares[move.final.row][move.final.col].piece = captured_piece
        
        # Only update game state if this wasn't a testing move
        if self.last_move == move:
            piece.moved = False
            if captured_piece:
                piece_type = captured_piece.__class__.__name__.lower()
                if piece_type in self.captured_pieces[piece.color]:
                    self.captured_pieces[piece.color].remove(piece_type)
                if piece.color == "white":
                    self.white_score -= captured_piece.value
                else:
                    self.black_score -= captured_piece.value
            self.last_move = None
            piece.clear_moves()

    def valid_move(self, piece, move):
        """Validate if a move is legal."""
        if not (0 <= move.final.row < BOARD_HEIGHT and 0 <= move.final.col < BOARD_WIDTH):
            return False

        # Check if the move is in the piece's valid moves
        for valid_move in piece.moves:
            if move == valid_move:
                # Create a lightweight board copy for check testing
                temp_squares = [[self.squares[r][c].piece for c in range(BOARD_WIDTH)]
                              for r in range(BOARD_HEIGHT)]
                
                # Simulate the move
                temp_squares[move.final.row][move.final.col] = temp_squares[move.initial.row][move.initial.col]
                temp_squares[move.initial.row][move.initial.col] = None
                
                # Check if the move puts or leaves the king in check
                if self._is_in_check_fast(piece.color, temp_squares):
                    return False
                    
                return True
                
        return False

    def _is_in_check_fast(self, color, board_state):
        """Faster version of is_in_check that works with a simple board state array."""
        # Find king position
        king_pos = None
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                piece = board_state[row][col]
                if piece and isinstance(piece, King) and piece.color == color:
                    king_pos = (row, col)
                    break
            if king_pos:
                break

        if not king_pos:
            return False

        # Check knight attacks
        knight_moves = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        for dr, dc in knight_moves:
            r, c = king_pos[0] + dr, king_pos[1] + dc
            if (0 <= r < BOARD_HEIGHT and 0 <= c < BOARD_WIDTH and
                board_state[r][c] and isinstance(board_state[r][c], Knight) and
                board_state[r][c].color != color):
                return True

        # Check diagonal attacks (bishop/queen)
        diagonals = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in diagonals:
            r, c = king_pos[0] + dr, king_pos[1] + dc
            while 0 <= r < BOARD_HEIGHT and 0 <= c < BOARD_WIDTH:
                piece = board_state[r][c]
                if piece:
                    if piece.color != color and (isinstance(piece, Bishop) or isinstance(piece, Queen)):
                        return True
                    break
                r, c = r + dr, c + dc

        # Check straight attacks (rook/queen)
        straights = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in straights:
            r, c = king_pos[0] + dr, king_pos[1] + dc
            while 0 <= r < BOARD_HEIGHT and 0 <= c < BOARD_WIDTH:
                piece = board_state[r][c]
                if piece:
                    if piece.color != color and (isinstance(piece, Rook) or isinstance(piece, Queen)):
                        return True
                    break
                r, c = r + dr, c + dc

        # Check pawn attacks
        pawn_dir = 1 if color == 'white' else -1
        for dc in [-1, 1]:
            r, c = king_pos[0] - pawn_dir, king_pos[1] + dc
            if (0 <= r < BOARD_HEIGHT and 0 <= c < BOARD_WIDTH and
                board_state[r][c] and isinstance(board_state[r][c], Pawn) and
                board_state[r][c].color != color):
                return True

        return False

    def is_in_check(self, color):
        """Check if the king of the given color is in check."""
        king_pos = None
        # Find the king's position
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                piece = self.squares[row][col].piece
                if isinstance(piece, King) and piece.color == color:
                    king_pos = (row, col)
                    break
            if king_pos:
                break
        
        if not king_pos:
            return False

        # Check if any opponent's piece can capture the king
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                piece = self.squares[row][col].piece
                if piece and piece.color != color:
                    self.calc_moves(piece, row, col, bool=False)
                    for move in piece.moves:
                        if move.final.row == king_pos[0] and move.final.col == king_pos[1]:
                            return True
        return False

    def is_checkmate(self, color):
        """Check if the given color is in checkmate."""
        if not self.is_in_check(color):
            return False

        # Try all possible moves for all pieces
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                piece = self.squares[row][col].piece
                if piece and piece.color == color:
                    # Calculate all possible moves for this piece
                    self.calc_moves(piece, row, col, bool=True)
                    
                    # Try each move
                    for move in piece.moves:
                        # Make temporary move
                        temp_board = copy.deepcopy(self)
                        temp_piece = temp_board.squares[row][col].piece
                        temp_board.move(temp_piece, move, testing=True)
                        
                        # If this move gets us out of check, it's not checkmate
                        if not temp_board.is_in_check(color):
                            return False

        # If we've tried all moves and none work, it's checkmate
        return True

    def is_stalemate(self, color):
        if self.is_in_check(color):
            return False
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                piece = self.squares[row][col].piece
                if piece and piece.color == color:
                    self.calc_moves(piece, row, col, bool=True)
                    for move in piece.moves:
                        temp_board = copy.deepcopy(self)
                        temp_board.move(piece, move, testing=True)
                        if not temp_board.is_in_check(color):
                            return False
        return True

    def castling(self, initial, final):
        king = self.squares[initial.row][initial.col].piece
        if not isinstance(king, King) or king.moved:
            return False
        diff = final.col - initial.col
        if abs(diff) != 2:
            return False
        rook_col = 0 if diff < 0 else 7
        rook = self.squares[initial.row][rook_col].piece
        if not isinstance(rook, Rook) or rook.moved:
            return False
        step = -1 if diff < 0 else 1
        for col in range(initial.col + step, rook_col, step):
            if self.squares[initial.row][col].has_piece() or self.is_in_check(king.color):
                return False
        return True

    def calc_moves(self, piece, row, col, bool=True):
        """Calculate all the possible moves for a piece at the given position."""
        # Check cache first
        cache_key = (piece.__class__.__name__, piece.color, row, col, bool)
        if cache_key in self.move_cache:
            piece.moves = self.move_cache[cache_key].copy()
            return

        piece.clear_moves()

        def pawn_moves():
            # Movement direction
            steps = -1 if piece.color == 'white' else 1
            start_row = 6 if piece.color == 'white' else 1

            # Vertical moves
            if 0 <= row + steps < BOARD_HEIGHT:
                # Forward one step
                if not self.squares[row + steps][col].has_piece():
                    move = Move(Square(row, col), Square(row + steps, col))
                    piece.add_move(move)
                    
                    # Forward two steps from starting position
                    if row == start_row and not self.squares[row + 2*steps][col].has_piece():
                        move = Move(Square(row, col), Square(row + 2*steps, col))
                        piece.add_move(move)

            # Diagonal captures
            for c in [-1, 1]:
                if 0 <= col + c < BOARD_WIDTH and 0 <= row + steps < BOARD_HEIGHT:
                    if self.squares[row + steps][col + c].has_piece():
                        target_piece = self.squares[row + steps][col + c].piece
                        if target_piece.color != piece.color:
                            move = Move(Square(row, col), Square(row + steps, col + c))
                            piece.add_move(move)

        def knight_moves():
            possible_moves = [
                (row + 2, col + 1), (row + 2, col - 1),
                (row - 2, col + 1), (row - 2, col - 1),
                (row + 1, col + 2), (row + 1, col - 2),
                (row - 1, col + 2), (row - 1, col - 2)
            ]
            
            for possible_move in possible_moves:
                possible_row, possible_col = possible_move
                if 0 <= possible_row < BOARD_HEIGHT and 0 <= possible_col < BOARD_WIDTH:
                    if not self.squares[possible_row][possible_col].has_piece():
                        move = Move(Square(row, col), Square(possible_row, possible_col))
                        piece.add_move(move)
                    elif self.squares[possible_row][possible_col].piece.color != piece.color:
                        move = Move(Square(row, col), Square(possible_row, possible_col))
                        piece.add_move(move)

        def straightline_moves(directions):
            for direction in directions:
                row_dir, col_dir = direction
                possible_row = row + row_dir
                possible_col = col + col_dir
                
                while 0 <= possible_row < BOARD_HEIGHT and 0 <= possible_col < BOARD_WIDTH:
                    if not self.squares[possible_row][possible_col].has_piece():
                        move = Move(Square(row, col), Square(possible_row, possible_col))
                        piece.add_move(move)
                    else:
                        if self.squares[possible_row][possible_col].piece.color != piece.color:
                            move = Move(Square(row, col), Square(possible_row, possible_col))
                            piece.add_move(move)
                        break
                    
                    possible_row += row_dir
                    possible_col += col_dir

        def king_moves():
            directions = [
                (-1, -1), (-1, 0), (-1, 1),
                (0, -1),           (0, 1),
                (1, -1),  (1, 0),  (1, 1)
            ]
            
            for direction in directions:
                possible_row = row + direction[0]
                possible_col = col + direction[1]
                
                if 0 <= possible_row < BOARD_HEIGHT and 0 <= possible_col < BOARD_WIDTH:
                    if not self.squares[possible_row][possible_col].has_piece():
                        move = Move(Square(row, col), Square(possible_row, possible_col))
                        piece.add_move(move)
                    elif self.squares[possible_row][possible_col].piece.color != piece.color:
                        move = Move(Square(row, col), Square(possible_row, possible_col))
                        piece.add_move(move)

            # Castling
            if not piece.moved:
                # Kingside castling
                if col + 3 < BOARD_WIDTH:
                    rook = self.squares[row][col + 3].piece
                    if isinstance(rook, Rook) and not rook.moved:
                        if not any(self.squares[row][c].has_piece() for c in range(col + 1, col + 3)):
                            move = Move(Square(row, col), Square(row, col + 2))
                            piece.add_move(move)
                
                # Queenside castling
                if col - 4 >= 0:
                    rook = self.squares[row][col - 4].piece
                    if isinstance(rook, Rook) and not rook.moved:
                        if not any(self.squares[row][c].has_piece() for c in range(col - 3, col)):
                            move = Move(Square(row, col), Square(row, col - 2))
                            piece.add_move(move)

        if isinstance(piece, Pawn):
            pawn_moves()
        elif isinstance(piece, Knight):
            knight_moves()
        elif isinstance(piece, Bishop):
            straightline_moves([(-1, -1), (-1, 1), (1, -1), (1, 1)])
        elif isinstance(piece, Rook):
            straightline_moves([(-1, 0), (1, 0), (0, -1), (0, 1)])
        elif isinstance(piece, Queen):
            straightline_moves([
                (-1, -1), (-1, 1), (1, -1), (1, 1),
                (-1, 0), (1, 0), (0, -1), (0, 1)
            ])
        elif isinstance(piece, King):
            king_moves()

        if bool:
            # Use faster check validation
            valid_moves = []
            for move in piece.moves:
                temp_squares = [[self.squares[r][c].piece for c in range(BOARD_WIDTH)]
                              for r in range(BOARD_HEIGHT)]
                temp_squares[move.final.row][move.final.col] = temp_squares[move.initial.row][move.initial.col]
                temp_squares[move.initial.row][move.initial.col] = None
                
                if not self._is_in_check_fast(piece.color, temp_squares):
                    valid_moves.append(move)
            piece.moves = valid_moves

        # Cache the results
        self.move_cache[cache_key] = piece.moves.copy()

    def is_endgame(self):
        """Determine if the position is in endgame phase."""
        # Count material for both sides
        white_material = 0
        black_material = 0
        queens_present = False
        
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                piece = self.squares[row][col].piece
                if piece:
                    if isinstance(piece, Queen):
                        queens_present = True
                    if piece.color == 'white':
                        white_material += piece.value
                    else:
                        black_material += piece.value
        
        # Endgame conditions:
        # 1. No queens
        # 2. Both sides have <= 13 points of material (excluding king)
        # 3. One side has only king and pawns
        return (not queens_present or 
                (white_material <= 13 and black_material <= 13) or
                white_material <= 3 or black_material <= 3)

    def make_move(self, from_square, to_square):
        """Validate and execute a move."""
        piece = self.squares[from_square.row][from_square.col].piece
        
        if not piece:
            return False
            
        if piece.color != 'white':  # Only white pieces can be moved by the player
            return False
            
        move = Move(from_square, to_square)
        
        # Calculate valid moves for the piece
        self.calc_moves(piece, from_square.row, from_square.col, bool=True)
        
        # Check if the move is valid
        if not self.valid_move(piece, move):
            return False
            
        # Execute the move
        self.move(piece, move)
        return True
