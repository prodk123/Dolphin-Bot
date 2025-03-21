import copy
import math
import random
from board import Board
from move import Move
from piece import *

# Piece-Square tables for positional evaluation
PAWN_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5,  5, 10, 25, 25, 10,  5,  5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5, -5,-10,  0,  0,-10, -5,  5,
    5, 10, 10,-20,-20, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

# Simplified piece values for faster evaluation
PIECE_VALUES = {
    Pawn: 100,
    Knight: 320,
    Bishop: 330,
    Rook: 500,
    Queen: 900,
    King: 20000
}

# Simplified center control bonuses
CENTER_SQUARES = {(3, 3): 30, (3, 4): 30, (4, 3): 30, (4, 4): 30}

# Cache for move evaluations
MOVE_CACHE = {}
MAX_CACHE_SIZE = 500  # Reduced cache size

# Add capture value multiplier
CAPTURE_MULTIPLIER = 100

def get_square_value(piece, row, col, is_endgame):
    """Get positional value for a piece."""
    if isinstance(piece, Pawn):
        return PAWN_TABLE[row * 8 + col] if piece.color == 'white' else -PAWN_TABLE[(7-row) * 8 + col]
    elif isinstance(piece, Knight):
        return KNIGHT_TABLE[row * 8 + col] if piece.color == 'white' else -KNIGHT_TABLE[(7-row) * 8 + col]
    elif isinstance(piece, Bishop):
        return BISHOP_TABLE[row * 8 + col] if piece.color == 'white' else -BISHOP_TABLE[(7-row) * 8 + col]
    return 0

def evaluate_board(board):
    """Enhanced board evaluation focusing on material and position."""
    try:
        if board.is_checkmate('white'): return -99999
        if board.is_checkmate('black'): return 99999
        if board.is_stalemate('white') or board.is_stalemate('black'): return 0

        score = 0
        is_endgame = board.is_endgame()
        
        # Material and position evaluation
        for row in range(8):
            for col in range(8):
                piece = board.squares[row][col].piece
                if not piece: continue
                
                # Base piece value
                value = PIECE_VALUES[type(piece)]
                
                # Add positional value
                value += get_square_value(piece, row, col, is_endgame)
                
                # Mobility bonus (simplified)
                if not isinstance(piece, (Pawn, King)):
                    board.calc_moves(piece, row, col, bool=False)
                    value += len(piece.moves) * 5
                
                # Pawn structure evaluation
                if isinstance(piece, Pawn):
                    # Doubled pawns penalty
                    doubled = False
                    for r in range(8):
                        if r != row and isinstance(board.squares[r][col].piece, Pawn) and board.squares[r][col].piece.color == piece.color:
                            doubled = True
                            break
                    if doubled:
                        value -= 20
                    
                    # Passed pawn bonus
                    passed = True
                    pawn_direction = -1 if piece.color == 'white' else 1
                    for r in range(row + pawn_direction, 0 if pawn_direction == -1 else 7, pawn_direction):
                        if isinstance(board.squares[r][col].piece, Pawn):
                            passed = False
                            break
                    if passed:
                        value += 50
                
                score += value if piece.color == 'white' else -value
        
        # Quick check evaluation with higher penalty in endgame
        check_penalty = 80 if is_endgame else 50
        if board.is_in_check('white'): score -= check_penalty
        if board.is_in_check('black'): score += check_penalty
        
        return score
    except Exception as e:
        print(f"Error in evaluate_board: {str(e)}")
        return 0

def evaluate_capture(attacker, target):
    """Evaluate the value of a capture move."""
    if not target or isinstance(target, King):  # Never evaluate king captures
        return 0
    
    # Base capture value
    capture_value = PIECE_VALUES[type(target)]
    
    # Adjust value based on the attacking piece's value (prefer capturing with lower value pieces)
    attacker_value = PIECE_VALUES[type(attacker)]
    trade_bonus = max(0, capture_value - attacker_value)
    
    return capture_value * CAPTURE_MULTIPLIER + trade_bonus

def quick_move_eval(board, move, piece, move_history):
    """Enhanced move evaluation for better move ordering."""
    try:
        score = 0
        target = board.squares[move.final.row][move.final.col].piece
        
        # Never evaluate moves that would capture a king
        if target and isinstance(target, King):
            return float('-inf')
        
        # Strongly prioritize captures
        if target:
            capture_score = evaluate_capture(piece, target)
            score += capture_score
            
            # Extra bonus for capturing undefended pieces
            is_defended = False
            for r in range(8):
                for c in range(8):
                    defender = board.squares[r][c].piece
                    if defender and defender.color == target.color and (r, c) != (move.final.row, move.final.col):
                        board.calc_moves(defender, r, c, bool=False)
                        for def_move in defender.moves:
                            if def_move.final.row == move.final.row and def_move.final.col == move.final.col:
                                is_defended = True
                                break
                    if is_defended:
                        break
                if is_defended:
                    break
            
            if not is_defended:
                score += capture_score * 0.5  # 50% bonus for undefended pieces
        
        # Positional evaluation (reduced weight compared to captures)
        position_score = get_square_value(piece, move.final.row, move.final.col, board.is_endgame())
        score += position_score
        
        # Development bonus in opening (reduced weight)
        if len(move_history) < 10:
            if isinstance(piece, (Knight, Bishop)) and not piece.moved:
                score += 20
            if isinstance(piece, Pawn) and 2 <= move.final.row <= 5 and 2 <= move.final.col <= 5:
                score += 15
        
        # King safety
        if isinstance(piece, King):
            if len(move_history) < 15:
                score -= 100  # Strongly discourage early king movement
            elif abs(move.final.col - move.initial.col) == 2:
                score += 40  # Encourage castling but not as much as captures
            
            # Check if move puts king in danger
            temp_board = copy.deepcopy(board)
            temp_board.move(piece, move, testing=True)
            if temp_board.is_in_check(piece.color):
                score -= 500  # Heavily penalize moves that put king in check
        
        # Avoid repetition
        for prev_move in move_history[-6:]:
            if prev_move and prev_move.final.row == move.final.row and prev_move.final.col == move.final.col:
                score -= 30
        
        return score
    except Exception as e:
        print(f"Error in quick_move_eval: {str(e)}")
        return float('-inf')  # Return worst possible score on error

def get_best_move(board, depth=3, player='black'):
    """Enhanced move selection with better search."""
    try:
        all_valid_moves = []
        capture_moves = []
        
        # Collect all valid moves and identify captures
        for row in range(8):
            for col in range(8):
                piece = board.squares[row][col].piece
                if piece and piece.color == player:
                    # Calculate moves for this piece
                    board.calc_moves(piece, row, col, bool=True)
                    
                    # Check each move for validity
                    for move in piece.moves:
                        if board.valid_move(piece, move):
                            all_valid_moves.append((piece, move))
                            # Check if it's a capture move
                            if board.squares[move.final.row][move.final.col].has_piece():
                                capture_moves.append((piece, move))
        
        # If no valid moves available, return None
        if not all_valid_moves:
            return None
            
        # First, check for immediate captures that are favorable
        if capture_moves:
            # Evaluate all captures
            scored_captures = []
            for piece, move in capture_moves:
                target = board.squares[move.final.row][move.final.col].piece
                if target:  # Double check target exists
                    score = evaluate_capture(piece, target)
                    scored_captures.append((score, piece, move))
            
            if scored_captures:
                # Sort captures by score
                scored_captures.sort(reverse=True, key=lambda x: x[0])
                best_capture = scored_captures[0]
                
                # If the capture is good (capturing higher or equal value piece)
                target = board.squares[best_capture[2].final.row][best_capture[2].final.col].piece
                if target and PIECE_VALUES[type(target)] >= PIECE_VALUES[type(best_capture[1])]:
                    return best_capture[2]
        
        # Opening book for early game
        move_count = len(board.move_history)
        if move_count < 6:
            center_moves = []
            development_moves = []
            
            for piece, move in all_valid_moves:
                # Control center with pawns
                if isinstance(piece, Pawn) and 2 <= move.final.col <= 5:
                    if (player == 'white' and move.final.row == 3) or (player == 'black' and move.final.row == 4):
                        center_moves.append(move)
                # Develop knights and bishops
                elif isinstance(piece, (Knight, Bishop)) and not piece.moved:
                    if 2 <= move.final.row <= 5 and 1 <= move.final.col <= 6:
                        development_moves.append(move)
            
            if center_moves and move_count < 4:
                return random.choice(center_moves)
            elif development_moves:
                return random.choice(development_moves)
        
        # Use minimax for main game
        def minimax(board, depth, alpha, beta, maximizing_player):
            if depth == 0:
                return evaluate_board(board), None
            
            color = 'white' if maximizing_player else 'black'
            valid_moves = []
            
            # Collect valid moves
            for row in range(8):
                for col in range(8):
                    piece = board.squares[row][col].piece
                    if piece and piece.color == color:
                        board.calc_moves(piece, row, col, bool=True)
                        for move in piece.moves:
                            if board.valid_move(piece, move):
                                valid_moves.append((piece, move))
            
            if not valid_moves:
                if board.is_in_check(color):
                    return (-99999 if maximizing_player else 99999), None
                return 0, None
            
            best_move = None
            best_eval = float('-inf') if maximizing_player else float('inf')
            
            # Sort moves for better pruning
            scored_moves = []
            for piece, move in valid_moves:
                score = quick_move_eval(board, move, piece, board.move_history)
                if score != float('-inf'):  # Only consider valid moves
                    scored_moves.append((score, piece, move))
            
            # Limit number of moves to consider based on depth
            scored_moves.sort(key=lambda x: x[0], reverse=maximizing_player)
            scored_moves = scored_moves[:8 if depth >= 2 else 5]
            
            for score, piece, move in scored_moves:
                # Store captured piece
                captured = board.squares[move.final.row][move.final.col].piece
                
                # Make move
                board.move(piece, move, testing=True)
                
                # Recursive evaluation
                eval_score, _ = minimax(board, depth - 1, alpha, beta, not maximizing_player)
                
                # Undo move
                board.undo_move(piece, move, captured)
                
                # Update best move
                if maximizing_player:
                    if eval_score > best_eval:
                        best_eval = eval_score
                        best_move = move
                    alpha = max(alpha, eval_score)
                else:
                    if eval_score < best_eval:
                        best_eval = eval_score
                        best_move = move
                    beta = min(beta, eval_score)
                
                if beta <= alpha:
                    break
            
            return best_eval, best_move
        
        # Adjust search depth based on game phase
        if board.is_endgame():
            depth = min(depth + 1, 4)  # Deeper search in endgame
        elif len(board.move_history) < 10:
            depth = min(depth, 3)  # Standard depth in opening
        else:
            depth = min(depth, 3)  # Standard depth in middlegame
        
        # Get best move from minimax
        _, best_move = minimax(board, depth, float('-inf'), float('inf'), player == 'white')
        
        # If minimax found a move, return it
        if best_move:
            # Verify the move is still valid
            for piece, move in all_valid_moves:
                if (move.initial.row == best_move.initial.row and 
                    move.initial.col == best_move.initial.col and
                    move.final.row == best_move.final.row and 
                    move.final.col == best_move.final.col):
                    return move
        
        # Fallback: use move ordering to select best immediate move
        scored_moves = []
        for piece, move in all_valid_moves:
            score = quick_move_eval(board, move, piece, board.move_history)
            if score != float('-inf'):  # Only consider valid moves
                scored_moves.append((score, move))
        
        if scored_moves:
            scored_moves.sort(key=lambda x: x[0], reverse=True)
            return scored_moves[0][1]
        
        # Final fallback: return random valid move
        if all_valid_moves:
            return random.choice(all_valid_moves)[1]
        
        return None
        
    except Exception as e:
        print(f"Error in get_best_move: {str(e)}")
        # Emergency fallback: return any valid move
        if all_valid_moves:
            return random.choice(all_valid_moves)[1]
        return None
