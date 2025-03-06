#!/bin/bash

# Create stockfish directory
mkdir -p stockfish

# Download the Stockfish Linux binary (precompiled)
curl -L -o stockfish/stockfish https://stockfishchess.org/files/latest/linux/stockfish_15.1_linux_x64.zip

# Unzip and move to stockfish folder
unzip stockfish/stockfish_15.1_linux_x64.zip -d stockfish/

# Give execute permissions
chmod +x stockfish/stockfish
