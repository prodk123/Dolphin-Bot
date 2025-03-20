import os
from flask import Flask, render_template, jsonify, request
from board import Board
from move import Move
from square import Square
from piece import *
from chess_ai_bot import get_best_move
from const import BOARD_HEIGHT, BOARD_WIDTH
import json
import traceback
from game import Game
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
    """Handle player move and AI response."""
    try:
        data = request.get_json()
        game_id = data.get('game_id')
        if game_id not in games:
            return jsonify({'error': 'Invalid game'}), 400

        board = games[game_id]
        from_square = Square(data['from']['row'], data['from']['col'])
        to_square = Square(data['to']['row'], data['to']['col'])

        # Get the piece at the initial position
        piece = board.squares[from_square.row][from_square.col].piece
        if not piece:
            return jsonify({'error': 'No piece at selected position'}), 400

        if piece.color != 'white':
            return jsonify({'error': 'Not your piece'}), 400

        # Create and validate the move
        move = Move(from_square, to_square)
        board.calc_moves(piece, from_square.row, from_square.col, bool=True)

        if not board.valid_move(piece, move):
            return jsonify({'error': 'Invalid move'}), 400

        # Make the player's move
        try:
            board.move(piece, move)
        except Exception as e:
            print(f"Error making player move: {str(e)}")
            traceback.print_exc()
            return jsonify({'error': 'Failed to make move'}), 500

        # Check game state after player's move
        try:
            if board.is_checkmate('black'):
                return jsonify({
                    'status': 'checkmate',
                    'winner': 'white',
                    'board': get_board_state(board),
                    'captured_pieces': board.captured_pieces,
                    'scores': {'white': board.white_score, 'black': board.black_score}
                })
            elif board.is_stalemate('black'):
                return jsonify({
                    'status': 'stalemate',
                    'board': get_board_state(board),
                    'captured_pieces': board.captured_pieces,
                    'scores': {'white': board.white_score, 'black': board.black_score}
                })
        except Exception as e:
            print(f"Error checking game state after player move: {str(e)}")
            traceback.print_exc()

        # Get all possible moves for black pieces
        try:
            black_moves = []
            for row in range(BOARD_HEIGHT):
                for col in range(BOARD_WIDTH):
                    piece = board.squares[row][col].piece
                    if piece and piece.color == 'black':
                        board.calc_moves(piece, row, col, bool=True)
                        for move in piece.moves:
                            if board.valid_move(piece, move):  # Only add valid moves
                                black_moves.append((piece, move))

            # If there are valid moves for black, make one
            if black_moves:
                try:
                    # Get AI's suggested move
                    ai_move = get_best_move(board)
                    made_move = False
                    
                    if ai_move and hasattr(ai_move, 'initial') and hasattr(ai_move, 'final'):
                        try:
                            # Find the corresponding piece for the AI move
                            ai_piece = board.squares[ai_move.initial.row][ai_move.initial.col].piece
                            if ai_piece and ai_piece.color == 'black':
                                # Verify the move is valid
                                board.calc_moves(ai_piece, ai_move.initial.row,
                                               ai_move.initial.col, bool=True)
                                if board.valid_move(ai_piece, ai_move):
                                    # Make the AI move
                                    board.move(ai_piece, ai_move)
                                    made_move = True
                        except Exception as e:
                            print(f"Error making AI's suggested move: {str(e)}")
                            traceback.print_exc()
                    
                    if not made_move and black_moves:
                        # If AI move failed or was invalid, make a random valid move
                        piece, move = random.choice(black_moves)
                        board.move(piece, move)

                    # Check game state after AI's move
                    if board.is_checkmate('white'):
                        return jsonify({
                            'status': 'checkmate',
                            'winner': 'black',
                            'board': get_board_state(board),
                            'captured_pieces': board.captured_pieces,
                            'scores': {'white': board.white_score, 'black': board.black_score}
                        })
                    elif board.is_stalemate('white'):
                        return jsonify({
                            'status': 'stalemate',
                            'board': get_board_state(board),
                            'captured_pieces': board.captured_pieces,
                            'scores': {'white': board.white_score, 'black': board.black_score}
                        })
                except Exception as e:
                    print(f"Error in AI move processing: {str(e)}")
                    traceback.print_exc()
                    # If AI move processing fails completely, make a random move
                    if black_moves:
                        piece, move = random.choice(black_moves)
                        board.move(piece, move)

        except Exception as e:
            print(f"Error processing black's moves: {str(e)}")
            traceback.print_exc()

        return jsonify({
            'board': get_board_state(board),
            'captured_pieces': board.captured_pieces,
            'scores': {'white': board.white_score, 'black': board.black_score}
        })

    except Exception as e:
        print(f"Error processing move: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
