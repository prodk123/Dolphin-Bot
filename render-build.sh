#!/bin/bash
# Download Stockfish binary
mkdir -p stockfish
curl -L -o stockfish/stockfish https://stockfishchess.org/files/stockfish_15.1_linux_x64.zip
unzip stockfish/stockfish -d stockfish/
chmod +x stockfish/stockfish
chmod +x render-build.sh
