class ChessGame {
    constructor() {
        this.gameId = null;
        this.selectedPiece = null;
        this.board = Array(8).fill().map(() => Array(8).fill(null));
        this.draggedPiece = null;
        this.draggedElement = null;
        this.validMoves = [];
        this.capturedPieces = {
            white: [],
            black: []
        };
        this.scores = {
            white: 0,
            black: 0
        };
        this.pieceValues = {
            'pawn': 1,
            'knight': 3,
            'bishop': 3,
            'rook': 5,
            'queen': 9,
            'king': 0
        };
        this.pieceImages = {
            'white_king': '/static/img/pieces/white_king.png',
            'white_queen': '/static/img/pieces/white_queen.png',
            'white_rook': '/static/img/pieces/white_rook.png',
            'white_bishop': '/static/img/pieces/white_bishop.png',
            'white_knight': '/static/img/pieces/white_knight.png',
            'white_pawn': '/static/img/pieces/white_pawn.png',
            'black_king': '/static/img/pieces/black_king.png',
            'black_queen': '/static/img/pieces/black_queen.png',
            'black_rook': '/static/img/pieces/black_rook.png',
            'black_bishop': '/static/img/pieces/black_bishop.png',
            'black_knight': '/static/img/pieces/black_knight.png',
            'black_pawn': '/static/img/pieces/black_pawn.png'
        };
        this.initializeGame();
        this.setupEventListeners();
    }

    async initializeGame() {
        try {
            const response = await fetch('/new_game', { method: 'POST' });
            const data = await response.json();
            if (data.error) {
                this.showStatus(data.error, 'danger');
                return;
            }
            this.gameId = data.game_id;
            await this.updateBoard();
            this.renderBoard();
            this.showStatus('Game started! Your turn (White)', 'success');
        } catch (error) {
            console.error('Error initializing game:', error);
            this.showStatus('Failed to initialize game', 'danger');
        }
    }

    setupEventListeners() {
        document.getElementById('new-game').addEventListener('click', () => this.initializeGame());
        const chessboard = document.getElementById('chessboard');
        
        // Handle both click and drag events
        chessboard.addEventListener('click', (e) => this.handleSquareClick(e));
        chessboard.addEventListener('dragstart', (e) => this.handleDragStart(e));
        chessboard.addEventListener('dragend', (e) => this.handleDragEnd(e));
        chessboard.addEventListener('dragover', (e) => this.handleDragOver(e));
        chessboard.addEventListener('drop', (e) => this.handleDrop(e));
    }

    async updateBoard() {
        try {
            const response = await fetch(`/get_board?game_id=${this.gameId}`);
            const data = await response.json();
            if (data.error) {
                this.showStatus(data.error, 'danger');
                return;
            }
            this.board = data.board;
        } catch (error) {
            console.error('Error updating board:', error);
            this.showStatus('Failed to update board', 'danger');
        }
    }

    renderBoard() {
        const chessboard = document.getElementById('chessboard');
        chessboard.innerHTML = '';

        for (let row = 0; row < 8; row++) {
            for (let col = 0; col < 8; col++) {
                const square = document.createElement('div');
                square.className = `square`;
                square.dataset.row = row;
                square.dataset.col = col;

                const piece = this.board[row][col];
                if (piece) {
                    const pieceDiv = document.createElement('div');
                    pieceDiv.className = 'piece';
                    pieceDiv.draggable = piece.color === 'white';
                    const imageKey = `${piece.color}_${piece.type}`;
                    pieceDiv.style.backgroundImage = `url('${this.pieceImages[imageKey]}')`;
                    pieceDiv.dataset.row = row;
                    pieceDiv.dataset.col = col;
                    pieceDiv.dataset.color = piece.color;
                    pieceDiv.dataset.type = piece.type;
                    square.appendChild(pieceDiv);
                }

                chessboard.appendChild(square);
            }
        }
    }

    async handleSquareClick(event) {
        const square = event.target.closest('.square');
        if (!square) return;

        const row = parseInt(square.dataset.row);
        const col = parseInt(square.dataset.col);
        const piece = square.querySelector('.piece');

        // If a piece is already selected
        if (this.selectedPiece) {
            // Check if clicked square is a valid move
            const isValidMove = this.validMoves.some(move => move.row === row && move.col === col);
            
            if (isValidMove) {
                // Make the move
                await this.makeMove({
                    from: this.selectedPiece,
                    to: { row, col }
                });
                this.clearSelection();
                return;
            } else if (piece && piece.dataset.color === 'white') {
                // If clicking another white piece, select it instead
                this.clearSelection();
                await this.selectPiece(row, col, piece);
                return;
            } else {
                // Invalid move, clear selection
                this.clearSelection();
                return;
            }
        } else if (piece && piece.dataset.color === 'white') {
            // Selecting a new piece
            await this.selectPiece(row, col, piece);
        }
    }

    async selectPiece(row, col, piece) {
        try {
            const response = await fetch('/get_valid_moves', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    game_id: this.gameId,
                    row: row,
                    col: col
                })
            });
            
            const data = await response.json();
            if (data.error) {
                this.showStatus(data.error, 'danger');
                return;
            }

            this.selectedPiece = { row, col };
            piece.closest('.square').classList.add('selected');
            this.validMoves = data.valid_moves;
            this.showValidMoves();
        } catch (error) {
            console.error('Error getting valid moves:', error);
            this.showStatus('Error getting valid moves', 'danger');
        }
    }

    async handleDragStart(e) {
        const piece = e.target.closest('.piece');
        if (!piece || piece.dataset.color !== 'white') {
            e.preventDefault();
            return;
        }

        const row = parseInt(piece.dataset.row);
        const col = parseInt(piece.dataset.col);
        
        // Get valid moves from the server
        try {
            const response = await fetch('/get_valid_moves', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    game_id: this.gameId,
                    row: row,
                    col: col
                })
            });
            const data = await response.json();
            if (data.valid_moves) {
                this.validMoves = data.valid_moves;
                this.showValidMoves();
            }
        } catch (error) {
            console.error('Error getting valid moves:', error);
        }
        
        this.draggedPiece = { row, col };
        this.draggedElement = piece;
        piece.classList.add('dragging');

        // Set drag image
        const dragImage = piece.cloneNode(true);
        dragImage.style.position = 'absolute';
        dragImage.style.top = '-1000px';
        document.body.appendChild(dragImage);
        e.dataTransfer.setDragImage(dragImage, 35, 35);
        setTimeout(() => document.body.removeChild(dragImage), 0);
    }

    showValidMoves() {
        this.validMoves.forEach(move => {
            const square = document.querySelector(`[data-row="${move.row}"][data-col="${move.col}"]`);
            if (square) {
                // Check if there's a piece that can be captured
                const targetPiece = square.querySelector('.piece');
                if (targetPiece && targetPiece.dataset.color === 'black') {
                    square.classList.add('valid-capture');
                } else {
                    square.classList.add('valid-move');
                }
            }
        });
    }

    clearValidMoves() {
        document.querySelectorAll('.valid-move, .valid-capture').forEach(square => {
            square.classList.remove('valid-move');
            square.classList.remove('valid-capture');
        });
        this.validMoves = [];
    }

    handleDragOver(e) {
        e.preventDefault();
        const square = e.target.closest('.square');
        if (square) {
            square.classList.add('drag-hover');
        }
    }

    handleDragEnd(e) {
        e.preventDefault();
        if (this.draggedElement) {
            this.draggedElement.classList.remove('dragging');
        }
        this.clearValidMoves();
        document.querySelectorAll('.square').forEach(sq => {
            sq.classList.remove('drag-hover');
        });
    }

    async handleDrop(e) {
        e.preventDefault();
        const square = e.target.closest('.square');
        if (!square || !this.draggedPiece) return;

        const toRow = parseInt(square.dataset.row);
        const toCol = parseInt(square.dataset.col);

        await this.makeMove({
            from: this.draggedPiece,
            to: { row: toRow, col: toCol }
        });

        this.draggedPiece = null;
        this.draggedElement = null;
        document.querySelectorAll('.square').forEach(sq => {
            sq.classList.remove('drag-hover');
        });
    }

    clearSelection() {
        this.selectedPiece = null;
        document.querySelectorAll('.square').forEach(sq => {
            sq.classList.remove('selected');
            sq.classList.remove('valid-move');
            sq.classList.remove('valid-capture');
        });
    }

    highlightMove(from, to) {
        const fromSquare = document.querySelector(`[data-row="${from.row}"][data-col="${from.col}"]`);
        const toSquare = document.querySelector(`[data-row="${to.row}"][data-col="${to.col}"]`);
        
        if (fromSquare) fromSquare.classList.add('highlight-from');
        if (toSquare) toSquare.classList.add('highlight-to');
        
        setTimeout(() => {
            if (fromSquare) fromSquare.classList.remove('highlight-from');
            if (toSquare) toSquare.classList.remove('highlight-to');
        }, 1500);
    }

    updateCapturedPieces(data) {
        if (!data.captured_pieces) return;
        
        this.capturedPieces = data.captured_pieces;
        this.scores = data.scores;

        // Update white's captured pieces
        const whiteCaptured = document.querySelector('.white-captured');
        whiteCaptured.innerHTML = '';
        this.capturedPieces.white.forEach(pieceType => {
            const pieceDiv = document.createElement('div');
            pieceDiv.className = 'captured-piece';
            pieceDiv.style.backgroundImage = `url('${this.pieceImages[`black_${pieceType}`]}')`;
            pieceDiv.title = `Captured ${pieceType}`;
            whiteCaptured.appendChild(pieceDiv);
        });

        // Update black's captured pieces
        const blackCaptured = document.querySelector('.black-captured');
        blackCaptured.innerHTML = '';
        this.capturedPieces.black.forEach(pieceType => {
            const pieceDiv = document.createElement('div');
            pieceDiv.className = 'captured-piece';
            pieceDiv.style.backgroundImage = `url('${this.pieceImages[`white_${pieceType}`]}')`;
            pieceDiv.title = `Captured ${pieceType}`;
            blackCaptured.appendChild(pieceDiv);
        });

        // Update scores with piece values
        const whiteScoreText = `Score: ${this.scores.white}`;
        const blackScoreText = `Score: ${this.scores.black}`;
        document.querySelector('.white-score').textContent = whiteScoreText;
        document.querySelector('.black-score').textContent = blackScoreText;
    }

    async makeMove(move) {
        try {
            // Clear any existing status messages
            this.clearStatus();
            
            // Show loading status
            this.showStatus('Making move...', 'info');

            // Check if this is a capture move
            const targetSquare = document.querySelector(`[data-row="${move.to.row}"][data-col="${move.to.col}"]`);
            const targetPiece = targetSquare && targetSquare.querySelector('.piece');
            const isCapture = targetPiece && targetPiece.dataset.color === 'black';

            const response = await fetch('/make_move', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    game_id: this.gameId,
                    from: move.from,
                    to: move.to
                })
            });

            const data = await response.json();
            
            if (!response.ok || data.error) {
                this.showStatus(data.error || 'Failed to make move', 'danger');
                return false;
            }

            // Update the board immediately after successful move
            await this.updateBoard();
            this.renderBoard();
            this.updateCapturedPieces(data);

            // Show appropriate message for captures
            if (isCapture) {
                const capturedType = targetPiece.dataset.type;
                this.showStatus(`Captured ${capturedType}!`, 'success');
            }

            // Handle game state
            if (data.status === 'checkmate') {
                this.showStatus(`Checkmate! ${data.winner === 'white' ? 'You win!' : 'AI wins!'}`, 'success');
                return true;
            } else if (data.status === 'stalemate') {
                this.showStatus('Stalemate! Game is a draw.', 'success');
                return true;
            }

            // Handle AI move
            if (data.move) {
                this.highlightMove(data.move.from, data.move.to);
                // Check if AI made a capture
                const aiTargetSquare = document.querySelector(`[data-row="${data.move.to.row}"][data-col="${data.move.to.col}"]`);
                const aiTargetPiece = aiTargetSquare && aiTargetSquare.querySelector('.piece');
                if (aiTargetPiece && aiTargetPiece.dataset.color === 'white') {
                    const capturedType = aiTargetPiece.dataset.type;
                    this.showStatus(`AI captured your ${capturedType}!`, 'warning');
                } else {
                    this.showStatus('Move completed', 'success');
                }
            }

            return true;
        } catch (error) {
            console.error('Error making move:', error);
            this.showStatus('Error making move', 'danger');
            return false;
        }
    }

    showStatus(message, type) {
        const statusDiv = document.querySelector('.game-status');
        statusDiv.textContent = message;
        statusDiv.className = `game-status alert alert-${type}`;
        statusDiv.classList.remove('d-none');
        
        setTimeout(() => {
            statusDiv.classList.add('d-none');
        }, 3000);
    }

    clearStatus() {
        const statusDiv = document.querySelector('.game-status');
        statusDiv.classList.add('d-none');
    }
}

// Initialize the game when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new ChessGame();
}); 