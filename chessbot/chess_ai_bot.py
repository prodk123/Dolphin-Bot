import copy
import math
from board import Board
from move import Move
from piece import *

def evaluate_board(board):
    score = 0
    for row in range(8):
        for col in range(8):
            piece = board.squares[row][col].piece
            if piece:
                score += piece.value
    return score

def minimax(board, depth, alpha, beta, maximizing_player):
    if depth == 0:
        return evaluate_board(board), None
    
    best_move = None
    
    if maximizing_player:
        max_eval = -math.inf
        for row in range(8):
            for col in range(8):
                piece = board.squares[row][col].piece
                if piece and piece.color == 'white':
                    board.calc_moves(piece, row, col, bool=True)
                    for move in piece.moves:
                        temp_board = copy.deepcopy(board)
                        temp_board.move(piece, move)
                        eval, _ = minimax(temp_board, depth - 1, alpha, beta, False)
                        if eval > max_eval:
                            max_eval = eval
                            best_move = move
                        alpha = max(alpha, eval)
                        if beta <= alpha:
                            break
        return max_eval, best_move
    else:
        min_eval = math.inf
        for row in range(8):
            for col in range(8):
                piece = board.squares[row][col].piece
                if piece and piece.color == 'black':
                    board.calc_moves(piece, row, col, bool=True)
                    for move in piece.moves:
                        temp_board = copy.deepcopy(board)
                        temp_board.move(piece, move)
                        eval, _ = minimax(temp_board, depth - 1, alpha, beta, True)
                        if eval < min_eval:
                            min_eval = eval
                            best_move = move
                        beta = min(beta, eval)
                        if beta <= alpha:
                            break
        return min_eval, best_move

def get_best_move(board, depth=3, player='black'):
    maximizing_player = player == 'white'
    _, best_move = minimax(board, depth, -math.inf, math.inf, maximizing_player)
    return best_move
