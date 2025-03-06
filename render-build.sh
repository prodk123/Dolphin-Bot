#!/bin/bash

# Create stockfish directory
mkdir -p stockfish

# Download the correct Linux Stockfish binary (precompiled)
curl -L -o stockfish/stockfish https://api.github.com/repos/official-stockfish/Stockfish/releases/latest \
    | grep "browser_download_url.*stockfish-linux-x86-64" \
    | cut -d '"' -f 4 \
    | xargs wget -O stockfish/stockfish

# Give execute permissions
chmod +x stockfish/stockfish
