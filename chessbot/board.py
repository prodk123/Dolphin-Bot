from chessbot.const import *
from chessbot.square import Square
from chessbot.piece import *
from chessbot.move import Move
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
        self.move_history = []
        self.last_move = None
        # Clear caches
        self.position_cache = {}
        self.move_cache = {}

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
        if not piece:  # Add check for piece existence
            return False
            
        if not (0 <= move.final.row < BOARD_HEIGHT and 0 <= move.final.col < BOARD_WIDTH):
            return False

        # Check if target square has a piece of the same color
        target_piece = self.squares[move.final.row][move.final.col].piece
        if target_piece and target_piece.color == piece.color:
            return False
            
        # Prevent king captures
        if target_piece and isinstance(target_piece, King):
            return False

        # Check if the move is in the piece's valid moves
        valid = False
        for valid_move in piece.moves:
            if move.initial.row == valid_move.initial.row and \
               move.initial.col == valid_move.initial.col and \
               move.final.row == valid_move.final.row and \
               move.final.col == valid_move.final.col:
                valid = True
                break
                
        if not valid:
            return False

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

    def _is_in_check_fast(self, color, board_state):
        """A faster version of is_in_check for move validation."""
        # Find the king position - cache it for repeated calls
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

        row, col = king_pos

        # Check knight attacks first (they're simpler)
        knight_moves = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        for dr, dc in knight_moves:
            r, c = row + dr, col + dc
            if 0 <= r < BOARD_HEIGHT and 0 <= c < BOARD_WIDTH:
                piece = board_state[r][c]
                if piece and piece.color != color and isinstance(piece, Knight):
                    return True

        # Check pawn attacks
        pawn_direction = -1 if color == 'white' else 1
        for dc in [-1, 1]:
            r, c = row + pawn_direction, col + dc
            if 0 <= r < BOARD_HEIGHT and 0 <= c < BOARD_WIDTH:
                piece = board_state[r][c]
                if piece and piece.color != color and isinstance(piece, Pawn):
                    return True

        # Check sliding pieces (more expensive, do last)
        # Combine diagonal and straight checks for efficiency
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        
        for dr, dc in directions:
            r, c = row + dr, col + dc
            diagonal = dr != 0 and dc != 0
            
            while 0 <= r < BOARD_HEIGHT and 0 <= c < BOARD_WIDTH:
                piece = board_state[r][c]
                if piece:
                    if piece.color != color:
                        if diagonal and (isinstance(piece, Bishop) or isinstance(piece, Queen)):
                            return True
                        if not diagonal and (isinstance(piece, Rook) or isinstance(piece, Queen)):
                            return True
                    break
                r, c = r + dr, c + dc

        return False

    def is_in_check(self, color):
        """Determine if the given color's king is in check."""
        # Find the king
        king_pos = None
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

        # Check if any opponent's piece can attack the king
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                piece = self.squares[row][col].piece
                if piece and piece.color != color:
                    # Calculate moves for the opponent's piece
                    self.calc_moves(piece, row, col, bool=False)
                    # Check if any move can capture the king
                    for move in piece.moves:
                        if move.final.row == king_pos[0] and move.final.col == king_pos[1]:
                            return True
                    piece.clear_moves()

        return False

    def _get_checking_pieces_and_squares(self, color):
        """Get the pieces giving check and the squares between them and the king."""
        # Find the king
        king_pos = None
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                piece = self.squares[row][col].piece
                if isinstance(piece, King) and piece.color == color:
                    king_pos = (row, col)
                    break
            if king_pos:
                break

        if not king_pos:
            return [], []

        checking_pieces = []
        blocking_squares = set()

        # Check for attacking pieces
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                piece = self.squares[row][col].piece
                if piece and piece.color != color:
                    self.calc_moves(piece, row, col, bool=False)
                    for move in piece.moves:
                        if move.final.row == king_pos[0] and move.final.col == king_pos[1]:
                            checking_pieces.append((piece, (row, col)))
                            
                            # For sliding pieces (Bishop, Rook, Queen), add squares between
                            if isinstance(piece, (Bishop, Rook, Queen)):
                                row_diff = king_pos[0] - row
                                col_diff = king_pos[1] - col
                                
                                # Determine direction of attack
                                row_step = 0 if row_diff == 0 else row_diff // abs(row_diff)
                                col_step = 0 if col_diff == 0 else col_diff // abs(col_diff)
                                
                                # Add all squares between piece and king
                                curr_row = row + row_step
                                curr_col = col + col_step
                                while (curr_row, curr_col) != king_pos:
                                    blocking_squares.add((curr_row, curr_col))
                                    curr_row += row_step
                                    curr_col += col_step

        return checking_pieces, list(blocking_squares)

    def is_checkmate(self, color):
        """Check if the given color is in checkmate."""
        # First verify if the king is in check
        if not self.is_in_check(color):
            return False

        # Find the king
        king = None
        king_pos = None
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                piece = self.squares[row][col].piece
                if isinstance(piece, King) and piece.color == color:
                    king = piece
                    king_pos = (row, col)
                    break
            if king:
                break

        if not king:
            return False

        # Try every piece's moves to see if they can prevent check
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                piece = self.squares[row][col].piece
                if piece and piece.color == color:
                    # Calculate all possible moves for this piece
                    self.calc_moves(piece, row, col, bool=True)
                    
                    # Try each move
                    for move in piece.moves:
                        # Store current state
                        captured_piece = self.squares[move.final.row][move.final.col].piece
                        
                        # Make the test move
                        self.move(piece, move, testing=True)
                        
                        # Check if we're still in check after this move
                        still_in_check = self.is_in_check(color)
                        
                        # Undo the test move
                        self.squares[move.initial.row][move.initial.col].piece = piece
                        self.squares[move.final.row][move.final.col].piece = captured_piece
                        piece.moved = False
                        
                        # If any move gets us out of check, it's not checkmate
                        if not still_in_check:
                            return False
                    
                    piece.clear_moves()

        # If no moves get us out of check, it's checkmate
        return True

    def is_stalemate(self, color):
        """Check if the given color is in stalemate."""
        # If in check, it's not stalemate
        if self.is_in_check(color):
            return False

        # Try every possible move
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                piece = self.squares[row][col].piece
                if piece and piece.color == color:
                    self.calc_moves(piece, row, col, bool=True)
                    for move in piece.moves:
                        if self.valid_move(piece, move):
                            return False
                    piece.clear_moves()

        # If no legal moves found and not in check, it's stalemate
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
        # For non-validation calls, skip caching
        if not bool:
            piece.clear_moves()
            self._calculate_piece_moves(piece, row, col)
            return

        # Use simpler cache key for better performance
        cache_key = (
            piece.__class__.__name__,
            piece.color,
            row,
            col,
            piece.moved,  # Important for kings and pawns
            self.last_move.final.row if self.last_move else None,  # For en passant
            self.last_move.final.col if self.last_move else None
        )
        
        if cache_key in self.move_cache:
            piece.moves = self.move_cache[cache_key].copy()
            return

        piece.clear_moves()
        self._calculate_piece_moves(piece, row, col)

        if bool:
            # Optimize check validation for endgame
            valid_moves = []
            # Create board state array once
            temp_squares = [[self.squares[r][c].piece for c in range(BOARD_WIDTH)]
                          for r in range(BOARD_HEIGHT)]
            
            # Find king position once for the color
            king_pos = None
            if not isinstance(piece, King):  # Only need king position for non-king pieces
                for r in range(BOARD_HEIGHT):
                    for c in range(BOARD_WIDTH):
                        p = self.squares[r][c].piece
                        if isinstance(p, King) and p.color == piece.color:
                            king_pos = (r, c)
                            break
                    if king_pos:
                        break

            for move in piece.moves:
                # Save original pieces
                moving_piece = temp_squares[move.initial.row][move.initial.col]
                captured_piece = temp_squares[move.final.row][move.final.col]
                
                # Make move
                temp_squares[move.final.row][move.final.col] = moving_piece
                temp_squares[move.initial.row][move.initial.col] = None

                # If the piece is a king, update king position for check validation
                check_pos = (move.final.row, move.final.col) if isinstance(piece, King) else king_pos
                
                # Faster check validation
                if not self._is_square_attacked(check_pos[0], check_pos[1], piece.color, temp_squares):
                    valid_moves.append(move)
                
                # Restore position
                temp_squares[move.initial.row][move.initial.col] = moving_piece
                temp_squares[move.final.row][move.final.col] = captured_piece
            
            piece.moves = valid_moves
            
            # Cache the results
            self.move_cache[cache_key] = piece.moves.copy()
            
            # Limit cache size to prevent memory issues
            if len(self.move_cache) > 10000:  # Increased cache size for endgame
                # Keep only the most recent entries
                self.move_cache = dict(list(self.move_cache.items())[-5000:])

    def _calculate_piece_moves(self, piece, row, col):
        """Calculate raw moves for a piece without validation."""
        if isinstance(piece, Pawn):
            self._pawn_moves(piece, row, col)
        elif isinstance(piece, Knight):
            self._knight_moves(piece, row, col)
        elif isinstance(piece, Bishop):
            self._straightline_moves(piece, row, col, [(-1, -1), (-1, 1), (1, -1), (1, 1)])
        elif isinstance(piece, Rook):
            self._straightline_moves(piece, row, col, [(-1, 0), (1, 0), (0, -1), (0, 1)])
        elif isinstance(piece, Queen):
            self._straightline_moves(piece, row, col, [
                (-1, -1), (-1, 1), (1, -1), (1, 1),
                (-1, 0), (1, 0), (0, -1), (0, 1)
            ])
        elif isinstance(piece, King):
            self._king_moves(piece, row, col)

    def _is_square_attacked(self, row, col, color, board_state):
        """Fast check if a square is attacked by any opponent piece."""
        # Check knight attacks first (they're simpler)
        knight_moves = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        for dr, dc in knight_moves:
            r, c = row + dr, col + dc
            if 0 <= r < BOARD_HEIGHT and 0 <= c < BOARD_WIDTH:
                piece = board_state[r][c]
                if piece and piece.color != color and isinstance(piece, Knight):
                    return True

        # Check pawn attacks
        pawn_direction = 1 if color == 'white' else -1
        for dc in [-1, 1]:
            r, c = row + pawn_direction, col + dc
            if 0 <= r < BOARD_HEIGHT and 0 <= c < BOARD_WIDTH:
                piece = board_state[r][c]
                if piece and piece.color != color and isinstance(piece, Pawn):
                    return True

        # Check sliding pieces
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        
        for dr, dc in directions:
            r, c = row + dr, col + dc
            diagonal = dr != 0 and dc != 0
            
            while 0 <= r < BOARD_HEIGHT and 0 <= c < BOARD_WIDTH:
                piece = board_state[r][c]
                if piece:
                    if piece.color != color:
                        if diagonal and (isinstance(piece, Bishop) or isinstance(piece, Queen)):
                            return True
                        if not diagonal and (isinstance(piece, Rook) or isinstance(piece, Queen)):
                            return True
                        if abs(r - row) <= 1 and abs(c - col) <= 1 and isinstance(piece, King):
                            return True
                    break
                r, c = r + dr, c + dc

        return False

    def _pawn_moves(self, piece, row, col):
        """Calculate pawn moves."""
        steps = -1 if piece.color == 'white' else 1
        start_row = 6 if piece.color == 'white' else 1

        # Forward moves
        if 0 <= row + steps < BOARD_HEIGHT:
            if not self.squares[row + steps][col].has_piece():
                piece.add_move(Move(Square(row, col), Square(row + steps, col)))
                if row == start_row and not self.squares[row + 2*steps][col].has_piece():
                    piece.add_move(Move(Square(row, col), Square(row + 2*steps, col)))

        # Captures
        for c in [-1, 1]:
            if 0 <= col + c < BOARD_WIDTH and 0 <= row + steps < BOARD_HEIGHT:
                if self.squares[row + steps][col + c].has_piece():
                    target = self.squares[row + steps][col + c].piece
                    if target.color != piece.color:
                        piece.add_move(Move(Square(row, col), Square(row + steps, col + c)))

    def _knight_moves(self, piece, row, col):
        """Calculate knight moves."""
        moves = [
            (row + 2, col + 1), (row + 2, col - 1),
            (row - 2, col + 1), (row - 2, col - 1),
            (row + 1, col + 2), (row + 1, col - 2),
            (row - 1, col + 2), (row - 1, col - 2)
        ]
        
        for r, c in moves:
            if 0 <= r < BOARD_HEIGHT and 0 <= c < BOARD_WIDTH:
                if not self.squares[r][c].has_piece() or \
                   self.squares[r][c].piece.color != piece.color:
                    piece.add_move(Move(Square(row, col), Square(r, c)))

    def _king_moves(self, piece, row, col):
        """Calculate king moves."""
        moves = [
            (row-1, col-1), (row-1, col), (row-1, col+1),
            (row, col-1),                 (row, col+1),
            (row+1, col-1), (row+1, col), (row+1, col+1)
        ]
        
        for r, c in moves:
            if 0 <= r < BOARD_HEIGHT and 0 <= c < BOARD_WIDTH:
                if not self.squares[r][c].has_piece() or \
                   self.squares[r][c].piece.color != piece.color:
                    piece.add_move(Move(Square(row, col), Square(r, c)))

        # Castling
        if not piece.moved:
            self._add_castling_moves(piece, row, col)

    def _add_castling_moves(self, king, row, col):
        """Add castling moves if available."""
        # Kingside
        if col + 3 < BOARD_WIDTH:
            rook = self.squares[row][col + 3].piece
            if isinstance(rook, Rook) and not rook.moved:
                if not any(self.squares[row][c].has_piece() for c in range(col + 1, col + 3)):
                    king.add_move(Move(Square(row, col), Square(row, col + 2)))
        
        # Queenside
        if col - 4 >= 0:
            rook = self.squares[row][col - 4].piece
            if isinstance(rook, Rook) and not rook.moved:
                if not any(self.squares[row][c].has_piece() for c in range(col - 3, col)):
                    king.add_move(Move(Square(row, col), Square(row, col - 2)))

    def _straightline_moves(self, piece, row, col, directions):
        """Calculate moves for sliding pieces (Bishop, Rook, Queen)."""
        for row_dir, col_dir in directions:
            r, c = row + row_dir, col + col_dir
            while 0 <= r < BOARD_HEIGHT and 0 <= c < BOARD_WIDTH:
                if not self.squares[r][c].has_piece():
                    piece.add_move(Move(Square(row, col), Square(r, c)))
                else:
                    if self.squares[r][c].piece.color != piece.color:
                        piece.add_move(Move(Square(row, col), Square(r, c)))
                    break
                r, c = r + row_dir, c + col_dir

    def is_endgame(self):
        """Determine if the position is in endgame phase."""
        # Simplified and faster endgame detection
        total_pieces = 0
        major_pieces = 0
        
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                piece = self.squares[row][col].piece
                if piece and not isinstance(piece, King):
                    total_pieces += 1
                    if isinstance(piece, (Queen, Rook)):
                        major_pieces += 1
                    if total_pieces > 10:  # Early exit if too many pieces
                        return False
        
        # Consider it endgame if:
        # 1. Less than 10 total pieces, or
        # 2. No queens and at most one rook per side
        return total_pieces < 10 or major_pieces <= 2

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
