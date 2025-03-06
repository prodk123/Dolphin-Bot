#!/bin/bash
# Create directory for Stockfish
mkdir -p stockfish

# Download the correct Stockfish Linux binary
curl -L -o stockfish/stockfish https://api.github.com/repos/official-stockfish/Stockfish/releases/latest | grep "browser_download_url.*stockfish-linux-x86-64" | cut -d '"' -f 4 | wget -O stockfish/stockfish -i -

# Make it executable
chmod +x stockfish/stockfish
