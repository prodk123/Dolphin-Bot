import copy
import math
import random
from board import Board
from move import Move
from piece import *

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

def evaluate_board(board):
    """Fast board evaluation focusing on material and basic position."""
    try:
        if board.is_checkmate('white'): return -99999
        if board.is_checkmate('black'): return 99999
        if board.is_stalemate('white') or board.is_stalemate('black'): return 0

        score = 0
        # Quick material and basic position evaluation
        for row in range(8):
            for col in range(8):
                piece = board.squares[row][col].piece
                if not piece: continue
                
                value = PIECE_VALUES[type(piece)]
                
                # Basic positional bonuses
                if (row, col) in CENTER_SQUARES:
                    value += CENTER_SQUARES[(row, col)]
                elif 2 <= row <= 5 and 2 <= col <= 5:
                    value += 10
                
                # Simple pawn structure evaluation
                if isinstance(piece, Pawn):
                    if piece.color == 'white':
                        value += (6 - row) * 5
                    else:
                        value += (row - 1) * 5
                
                score += value if piece.color == 'white' else -value
        
        # Quick check evaluation
        if board.is_in_check('white'): score -= 50
        if board.is_in_check('black'): score += 50
        
        return score
    except Exception as e:
        print(f"Error in evaluate_board: {str(e)}")
        return 0

def quick_move_eval(board, move, piece, move_history):
    """Simplified move evaluation for speed."""
    try:
        score = 0
        target = board.squares[move.final.row][move.final.col].piece
        
        # Capture evaluation
        if target:
            score = PIECE_VALUES[type(target)] * 10
            if PIECE_VALUES[type(piece)] < PIECE_VALUES[type(target)]:
                score += 30
        
        # Basic positional evaluation
        if (move.final.row, move.final.col) in CENTER_SQUARES:
            score += 20
        elif 2 <= move.final.row <= 5 and 2 <= move.final.col <= 5:
            score += 10
        
        # Simple development scoring
        if len(move_history) < 10:
            if isinstance(piece, (Knight, Bishop)):
                if 2 <= move.final.row <= 5 and 2 <= move.final.col <= 5:
                    score += 30
        
        # Quick repetition check
        for prev_move in move_history[-4:]:
            if prev_move and prev_move.final.row == move.final.row and prev_move.final.col == move.final.col:
                score -= 50
        
        return score
    except Exception as e:
        print(f"Error in quick_move_eval: {str(e)}")
        return 0

def get_best_move(board, depth=2, player='black'):
    """Optimized move selection with faster evaluation."""
    try:
        all_valid_moves = []
        for row in range(8):
            for col in range(8):
                piece = board.squares[row][col].piece
                if piece and piece.color == player:
                    board.calc_moves(piece, row, col, bool=True)
                    all_valid_moves.extend((piece, move) for move in piece.moves if board.valid_move(piece, move))
        
        if not all_valid_moves:
            return None
        
        # Opening book for first few moves
        move_count = len(board.move_history)
        if move_count == 0 and player == 'white':
            center_moves = []
            for piece, move in all_valid_moves:
                if isinstance(piece, Pawn) and 2 <= move.final.col <= 5:
                    center_moves.append(move)
            if center_moves:
                return random.choice(center_moves)
        
        # Simplified minimax with basic pruning
        def minimax(board, depth, alpha, beta, maximizing_player):
            if depth == 0:
                return evaluate_board(board), None
            
            color = 'white' if maximizing_player else 'black'
            valid_moves = []
            for row in range(8):
                for col in range(8):
                    piece = board.squares[row][col].piece
                    if piece and piece.color == color:
                        board.calc_moves(piece, row, col, bool=True)
                        valid_moves.extend((piece, move) for move in piece.moves if board.valid_move(piece, move))
            
            if not valid_moves:
                if board.is_in_check(color):
                    return (-99999 if maximizing_player else 99999), None
                return 0, None
            
            best_move = None
            best_eval = -math.inf if maximizing_player else math.inf
            
            # Evaluate and sort moves for better pruning
            scored_moves = []
            for piece, move in valid_moves:
                score = quick_move_eval(board, move, piece, board.move_history)
                scored_moves.append((score, piece, move))
            
            scored_moves.sort(key=lambda x: x[0], reverse=maximizing_player)
            scored_moves = scored_moves[:6]  # Consider only top 6 moves
            
            for score, piece, move in scored_moves:
                captured = board.squares[move.final.row][move.final.col].piece
                board.move(piece, move, testing=True)
                
                eval, _ = minimax(board, depth - 1, alpha, beta, not maximizing_player)
                board.undo_move(piece, move, captured)
                
                if maximizing_player:
                    if eval > best_eval:
                        best_eval = eval
                        best_move = move
                    alpha = max(alpha, eval)
                else:
                    if eval < best_eval:
                        best_eval = eval
                        best_move = move
                    beta = min(beta, eval)
                
                if beta <= alpha:
                    break
            
            return best_eval, best_move
        
        # Use reduced depth for faster play
        depth = min(depth, 2)
        _, best_move = minimax(board, depth, -math.inf, math.inf, player == 'white')
        
        if best_move:
            for piece, move in all_valid_moves:
                if (move.initial.row == best_move.initial.row and 
                    move.initial.col == best_move.initial.col and
                    move.final.row == best_move.final.row and 
                    move.final.col == best_move.final.col):
                    return move
        
        # Simple fallback
        scored_moves = [(quick_move_eval(board, move, piece, board.move_history), move) 
                       for piece, move in all_valid_moves]
        scored_moves.sort(reverse=True)
        return scored_moves[0][1] if scored_moves else random.choice(all_valid_moves)[1]
        
    except Exception as e:
        print(f"Error in get_best_move: {str(e)}")
        if all_valid_moves:
            return random.choice(all_valid_moves)[1]
        return None
