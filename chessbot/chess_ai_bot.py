import copy
import math
import random
from board import Board
from move import Move
from piece import *

# Piece values with positional bonuses
PIECE_VALUES = {
    Pawn: 100,
    Knight: 320,
    Bishop: 330,
    Rook: 500,
    Queen: 900,
    King: 20000
}

# Simplified piece-square tables for faster evaluation
PIECE_SQUARES = {
    Pawn: [
        0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5,  5, 10, 25, 25, 10,  5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5, -5,-10,  0,  0,-10, -5,  5,
        5, 10, 10,-20,-20, 10, 10,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ],
    Knight: [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ]
}

def get_piece_value(piece, row, col, is_endgame):
    """Fast piece evaluation with position consideration."""
    base_value = PIECE_VALUES[type(piece)]
    
    # Position value for pawns and knights (most important for these pieces)
    if isinstance(piece, (Pawn, Knight)):
        pos_idx = row * 8 + col if piece.color == 'white' else (7-row) * 8 + col
        position_bonus = PIECE_SQUARES[type(piece)][pos_idx] * 0.01
        base_value += position_bonus * base_value
    
    # Center control bonus for all pieces
    if 2 <= row <= 5 and 2 <= col <= 5:
        base_value += 10
    
    # Endgame adjustments
    if is_endgame:
        if isinstance(piece, King):
            base_value += 200  # Kings should be more active in endgame
        elif isinstance(piece, Pawn):
            base_value += row * 10 if piece.color == 'black' else (7-row) * 10
    
    return base_value

def evaluate_board(board):
    """Enhanced evaluation function optimized for speed and accuracy."""
    if board.is_checkmate('white'): return -99999
    if board.is_checkmate('black'): return 99999
    if board.is_stalemate('white') or board.is_stalemate('black'): return 0

    # Quick material count to determine game phase
    total_material = 0
    for row in range(8):
        for col in range(8):
            piece = board.squares[row][col].piece
            if piece and not isinstance(piece, King):
                total_material += PIECE_VALUES[type(piece)]
    
    is_endgame = total_material < 5000  # Roughly queen + 2 minor pieces

    score = 0
    white_pawns_cols = set()
    black_pawns_cols = set()
    
    # Main evaluation loop
    for row in range(8):
        for col in range(8):
            piece = board.squares[row][col].piece
            if not piece: continue
            
            value = get_piece_value(piece, row, col, is_endgame)
            
            # Track pawn structure
            if isinstance(piece, Pawn):
                if piece.color == 'white':
                    white_pawns_cols.add(col)
                else:
                    black_pawns_cols.add(col)
            
            # Add/subtract value based on color
            if piece.color == 'white':
                score += value
            else:
                score -= value
    
    # Quick positional bonuses
    if board.is_in_check('white'): score -= 50
    if board.is_in_check('black'): score += 50
    
    # Pawn structure penalties (doubled/isolated pawns)
    pawn_struct_score = (len(white_pawns_cols) - len(black_pawns_cols)) * 10
    score += pawn_struct_score
    
    return score

def get_best_move(board, depth=2, player='black'):
    """Optimized move selection with adaptive depth."""
    def quick_move_eval(move, piece):
        """Ultra-fast move scoring for ordering."""
        score = 0
        target = board.squares[move.final.row][move.final.col].piece
        
        # Captures
        if target:
            score = PIECE_VALUES[type(target)] - PIECE_VALUES[type(piece)] // 10
            
        # Basic positional gain
        if 2 <= move.final.row <= 5 and 2 <= move.final.col <= 5:
            score += 5
            
        # Promotion
        if isinstance(piece, Pawn) and move.final.row in (0, 7):
            score += 800
            
        return score

    def minimax(board, depth, alpha, beta, maximizing_player, move_count=0):
        """Enhanced minimax with smart pruning."""
        if depth == 0 or move_count > 50:
            return evaluate_board(board), None

        best_move = None
        color = 'white' if maximizing_player else 'black'
        best_eval = -math.inf if maximizing_player else math.inf
        
        # Get and pre-score moves
        moves = []
        for row in range(8):
            for col in range(8):
                piece = board.squares[row][col].piece
                if piece and piece.color == color:
                    board.calc_moves(piece, row, col, bool=True)
                    for move in piece.moves:
                        score = quick_move_eval(move, piece)
                        moves.append((score, move, piece))
        
        # Smart move ordering and pruning
        moves.sort(key=lambda x: x[0], reverse=maximizing_player)
        if depth <= 2:
            moves = moves[:8]  # More moves at shallow depth
        else:
            moves = moves[:4]  # Fewer moves at deeper depth

        for score, move, piece in moves:
            captured = board.squares[move.final.row][move.final.col].piece
            board.move(piece, move, testing=True)
            
            eval, _ = minimax(board, depth - 1, alpha, beta, not maximizing_player, move_count + 1)
            board.undo_move(piece, move, captured)

            if maximizing_player and eval > best_eval:
                best_eval = eval
                best_move = move
                alpha = max(alpha, eval)
            elif not maximizing_player and eval < best_eval:
                best_eval = eval
                best_move = move
                beta = min(beta, eval)
            
            if beta <= alpha:
                break

        return best_eval, best_move

    # Adaptive depth based on position
    piece_count = sum(1 for row in range(8) for col in range(8) 
                     if board.squares[row][col].piece is not None)
    
    if piece_count <= 10:  # Endgame
        depth = 3
    elif piece_count <= 20:  # Middlegame
        depth = 2
    else:  # Opening
        depth = 2
    
    # Add randomness for opening moves
    if len(board.move_history) < 10:
        depth = 2
        if random.random() < 0.1:  # 10% chance of random good move
            _, best_move = minimax(board, 1, -math.inf, math.inf, player == 'white')
            return best_move

    _, best_move = minimax(board, depth, -math.inf, math.inf, player == 'white')
    return best_move
