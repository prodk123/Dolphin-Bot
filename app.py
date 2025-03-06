from flask import Flask, request, jsonify
import chess
import chess.engine

app = Flask(__name__)

STOCKFISH_PATH = "./stockfish/stockfish"

engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)

@app.route("/move", methods=["POST"])
def get_best_move():
    data = request.get_json()
    if "fen" not in data:
        return jsonify({"error": "FEN string is required"}), 400

    board = chess.Board(data["fen"])
    result = engine.play(board, chess.engine.Limit(time=0.1))
    best_move = result.move.uci()

    return jsonify({"botMove": best_move})

if __name__ == "__main__":
    app.run(debug=True)
