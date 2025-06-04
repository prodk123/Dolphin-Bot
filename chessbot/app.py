import os
from flask import Flask, render_template, jsonify, request
from chessbot.board import Board
from chessbot.move import Move
from chessbot.square import Square
from chessbot.piece import *
from chessbot.chess_ai_bot import get_best_move
from chessbot.const import BOARD_HEIGHT, BOARD_WIDTH
import json
import traceback
from chessbot.game import Game
import random

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Configure for production
if os.environ.get('FLASK_ENV') == 'production':
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
else:
    app.config['DEBUG'] = True

# Store active games in memory (in production, use a proper database)
games = {}


@app.route('/')
def index():
    """Render the landing page."""
    return render_template('index.html')


@app.route('/game')
def game():
    """Render the chess game page."""
    return render_template('game.html')


@app.route('/new_game', methods=['POST'])
def new_game():
    """Create a new game instance."""
    try:
        game_id = len(games)
        new_game = Game()
        new_game.reset()  # Ensure complete reset including captured pieces
        games[game_id] = new_game.board  # This will be a fresh board with reset scores
        return jsonify({
            'game_id': game_id,
            'board': get_board_state(games[game_id]),
            'captured_pieces': games[game_id].captured_pieces,
            'scores': {'white': games[game_id].white_score, 'black': games[game_id].black_score}
        })
    except Exception as e:
        print(f"Error creating new game: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Failed to create new game'}), 500


@app.route('/get_valid_moves', methods=['POST'])
def get_valid_moves():
    """Get valid moves for a piece."""
    try:
        data = request.json
        game_id = data.get('game_id')
        row = data.get('row')
        col = data.get('col')

        if game_id not in games:
            return jsonify({'error': 'Invalid game'}), 400

        board = games[game_id]
        piece = board.squares[row][col].piece

        if not piece:
            return jsonify({'error': 'No piece at selected position'}), 400

        # Calculate valid moves
        board.calc_moves(piece, row, col, bool=True)

        # Convert moves to list of coordinates
        valid_moves = [{'row': move.final.row, 'col': move.final.col}
                       for move in piece.moves]

        return jsonify({'valid_moves': valid_moves})

    except Exception as e:
        print(f"Error getting valid moves: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/make_move', methods=['POST'])
def make_move():
    """Handle a move request."""
    try:
        data = request.get_json()
        game_id = data.get('game_id')
        
        if game_id not in games:
            return jsonify({'error': 'Invalid game'}), 400

        board = games[game_id]
        
        # Create move from the data
        from_square = Square(data['from_row'], data['from_col'])
        to_square = Square(data['to_row'], data['to_col'])
        move = Move(from_square, to_square)

        # Get the piece at the starting position
        piece = board.squares[from_square.row][from_square.col].piece
        if not piece:
            return jsonify({'error': 'No piece at starting position'}), 400

        # Validate and make the move
        if board.valid_move(piece, move):
            board.move(piece, move)
            
            # Check for game end conditions after player's move
            if board.is_checkmate('black'):
                return jsonify({
                    'board': get_board_state(board),
                    'captured_pieces': board.captured_pieces,
                    'scores': {'white': board.white_score, 'black': board.black_score},
                    'status': 'checkmate',
                    'winner': 'white'
                })
            elif board.is_stalemate('black'):
                return jsonify({
                    'board': get_board_state(board),
                    'captured_pieces': board.captured_pieces,
                    'scores': {'white': board.white_score, 'black': board.black_score},
                    'status': 'stalemate'
                })

            # Get AI's move
            ai_move = get_best_move(board, 'black')
            if ai_move:
                # Make AI's move
                ai_piece = board.squares[ai_move.initial.row][ai_move.initial.col].piece
                board.move(ai_piece, ai_move)
                
                # Check for game end conditions after AI's move
                if board.is_checkmate('white'):
                    return jsonify({
                        'board': get_board_state(board),
                        'captured_pieces': board.captured_pieces,
                        'scores': {'white': board.white_score, 'black': board.black_score},
                        'status': 'checkmate',
                        'winner': 'black',
                        'ai_move': {
                            'from_row': ai_move.initial.row,
                            'from_col': ai_move.initial.col,
                            'to_row': ai_move.final.row,
                            'to_col': ai_move.final.col
                        }
                    })
                elif board.is_stalemate('white'):
                    return jsonify({
                        'board': get_board_state(board),
                        'captured_pieces': board.captured_pieces,
                        'scores': {'white': board.white_score, 'black': board.black_score},
                        'status': 'stalemate',
                        'ai_move': {
                            'from_row': ai_move.initial.row,
                            'from_col': ai_move.initial.col,
                            'to_row': ai_move.final.row,
                            'to_col': ai_move.final.col
                        }
                    })

            # Return normal move response
            return jsonify({
                'board': get_board_state(board),
                'captured_pieces': board.captured_pieces,
                'scores': {'white': board.white_score, 'black': board.black_score},
                'ai_move': {
                    'from_row': ai_move.initial.row,
                    'from_col': ai_move.initial.col,
                    'to_row': ai_move.final.row,
                    'to_col': ai_move.final.col
                } if ai_move else None
            })
        else:
            return jsonify({'error': 'Invalid move'}), 400

    except Exception as e:
        print(f"Error making move: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Failed to make move'}), 500


def get_board_state(board):
    """Helper function to get current board state."""
    board_state = []
    for row in range(8):
        board_row = []
        for col in range(8):
            piece = board.squares[row][col].piece
            if piece:
                board_row.append({
                    'type': piece.__class__.__name__.lower(),
                    'color': piece.color
                })
            else:
                board_row.append(None)
        board_state.append(board_row)
    return board_state


@app.route('/get_board', methods=['GET'])
def get_board():
    """Get current board state."""
    try:
        game_id = int(request.args.get('game_id', 0))
        if game_id not in games:
            return jsonify({'error': 'Invalid game'}), 400

        board = games[game_id]
        board_state = []

        for row in range(8):
            board_row = []
            for col in range(8):
                piece = board.squares[row][col].piece
                if piece:
                    board_row.append({
                        'type': piece.__class__.__name__.lower(),
                        'color': piece.color
                    })
                else:
                    board_row.append(None)
            board_state.append(board_row)

        return jsonify({
            'board': board_state,
            'captured_pieces': board.captured_pieces,
            'scores': {
                'white': board.white_score,
                'black': board.black_score
            }
        })
    except Exception as e:
        print(f"Error getting board state: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # Get port from environment variable or use 3000 as default
    port = int(os.environ.get('PORT', 3000))
    # Run the app on 0.0.0.0 to make it accessible externally
    app.run(host='0.0.0.0', port=port)
