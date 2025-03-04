from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
from board import Board
from move import Move
from chess_ai_bot import get_best_move

# ✅ Define Flask app BEFORE using @app.route
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ✅ Create the board instance
board = Board()

@app.route("/reset", methods=["POST"])
def reset():
    global board
    board = Board()
    return jsonify({"message": "Game reset!"})

@app.route("/move", methods=["POST"])
def make_move():
    global board
    data = request.json
    initial = data["initial"]
    final = data["final"]
    
    piece = board.squares[initial["row"]][initial["col"]].piece
    if piece:
        move = Move(initial, final)
        if board.valid_move(piece, move):
            board.move(piece, move)

            # AI makes a move
            ai_move = get_best_move(board, depth=3)
            if ai_move:
                ai_initial = {"row": ai_move.initial.row, "col": ai_move.initial.col}
                ai_final = {"row": ai_move.final.row, "col": ai_move.final.col}
                return jsonify({"player_move": data, "ai_move": {"initial": ai_initial, "final": ai_final}})
    
    return jsonify({"error": "Invalid move"}), 400

if __name__ == "__main__":
    socketio.run(app, debug=True)
