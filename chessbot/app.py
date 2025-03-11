from flask import Flask, render_template, jsonify, request
from board import Board
from move import Move
from square import Square
from piece import *
from chess_ai_bot import get_best_move
import json
import traceback
from game import Game

app = Flask(__name__, static_folder='static', template_folder='templates')

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
        games[game_id] = Game().board
        return jsonify({'game_id': game_id})
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
    """Handle player move and get AI response."""
    try:
        data = request.json
        game_id = data.get('game_id')
        from_square = data.get('from')
        to_square = data.get('to')

        # Validate input data
        if not all([game_id is not None,
                   from_square is not None,
                   to_square is not None,
                   'row' in from_square,
                    'col' in from_square,
                    'row' in to_square,
                    'col' in to_square]):
            return jsonify({'error': 'Invalid move data provided'}), 400

        if game_id not in games:
            return jsonify({'error': 'Invalid game'}), 400

        board = games[game_id]

        # Get the piece at the initial position
        initial_row, initial_col = from_square['row'], from_square['col']
        final_row, final_col = to_square['row'], to_square['col']

        if not (0 <= initial_row < 8 and 0 <= initial_col < 8 and 0 <= final_row < 8 and 0 <= final_col < 8):
            return jsonify({'error': 'Invalid position'}), 400

        piece = board.squares[initial_row][initial_col].piece
        if not piece:
            return jsonify({'error': 'No piece at selected position'}), 400

        if piece.color != 'white':
            return jsonify({'error': 'Not your piece'}), 400

        # Check if there's a piece at the destination
        target_square = board.squares[final_row][final_col]
        target_piece = target_square.piece

        # Validate capture: can't capture your own pieces
        if target_piece and target_piece.color == piece.color:
            return jsonify({'error': 'Cannot capture your own piece'}), 400

        # Create and validate the move
        initial = Square(from_square['row'], from_square['col'])
        final = Square(to_square['row'], to_square['col'])
        move = Move(initial, final)

        # Calculate valid moves for the piece
        board.calc_moves(piece, initial.row, initial.col, bool=True)

        # Validate the move
        valid_move = None
        for m in piece.moves:
            if m.final.row == final.row and m.final.col == final.col:
                valid_move = m
                break

        if not valid_move:
            return jsonify({'error': 'Invalid move for this piece'}), 400

        # Make the player's move (this will handle the capture if valid)
        board.move(piece, move)

        # Check game state after player's move
        if board.is_checkmate('black'):
            return jsonify({
                'status': 'checkmate',
                'winner': 'white',
                'move': None,
                'captured_pieces': board.captured_pieces,
                'scores': {
                    'white': board.white_score,
                    'black': board.black_score
                }
            })
        elif board.is_stalemate('black'):
            return jsonify({
                'status': 'stalemate',
                'move': None,
                'captured_pieces': board.captured_pieces,
                'scores': {
                    'white': board.white_score,
                    'black': board.black_score
                }
            })

        # Get AI's move
        ai_move = get_best_move(board, depth=2, player='black')
        if not ai_move:
            return jsonify({'error': 'AI failed to generate a valid move'}), 500

        # Make AI's move
        ai_piece = board.squares[ai_move.initial.row][ai_move.initial.col].piece
        if not ai_piece:
            return jsonify({'error': 'AI move error: No piece at selected position'}), 500

        # Make the AI move (this will handle the capture if valid)
        board.move(ai_piece, ai_move)

        # Convert AI move to response format
        ai_response = {
            'from': {'row': ai_move.initial.row, 'col': ai_move.initial.col},
            'to': {'row': ai_move.final.row, 'col': ai_move.final.col}
        }

        # Check game state after AI's move
        if board.is_checkmate('white'):
            return jsonify({
                'status': 'checkmate',
                'winner': 'black',
                'move': ai_response,
                'captured_pieces': board.captured_pieces,
                'scores': {
                    'white': board.white_score,
                    'black': board.black_score
                }
            })
        elif board.is_stalemate('white'):
            return jsonify({
                'status': 'stalemate',
                'move': ai_response,
                'captured_pieces': board.captured_pieces,
                'scores': {
                    'white': board.white_score,
                    'black': board.black_score
                }
            })

        return jsonify({
            'status': 'success',
            'move': ai_response,
            'captured_pieces': board.captured_pieces,
            'scores': {
                'white': board.white_score,
                'black': board.black_score
            }
        })

    except Exception as e:
        print(f"Error making move: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'Move failed: {str(e)}'}), 500


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
    app.run(host='0.0.0.0', port=5000)
