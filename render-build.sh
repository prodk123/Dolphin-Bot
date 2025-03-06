#!/bin/bash

# Create stockfish directory
mkdir -p stockfish

# Download the correct precompiled Stockfish Linux binary
curl -L -o stockfish/stockfish https://stockfishchess.org/files/stockfish-ubuntu.zip

# Unzip and move to the stockfish directory
unzip stockfish/stockfish-ubuntu.zip -d stockfish/

# Find the correct binary inside the extracted folder and move it
mv stockfish/stockfish-ubuntu/* stockfish/

# Give execute permissions
chmod +x stockfish/stockfish
