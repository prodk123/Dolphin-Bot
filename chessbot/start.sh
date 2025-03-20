#!/bin/bash
# Exit early on errors
set -eu

# Python buffers stdout. Without this, you won't see what you "print" in the Activity Log
export PYTHONUNBUFFERED=true

# Ensure we're using Python 3
python3 --version

# Install Python dependencies
pip3 install --user -r requirements.txt

# Run the app with gunicorn
~/.local/bin/gunicorn app:app --bind 0.0.0.0:3000 --timeout 600
