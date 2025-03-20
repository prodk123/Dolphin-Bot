#!/bin/bash
# Exit early on errors
set -eu

# Python buffers stdout. Without this, you won't see what you "print" in the Activity Log
export PYTHONUNBUFFERED=true

# Ensure we're using Python 3
python3 --version

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Run the app with gunicorn
gunicorn app:app --bind 0.0.0.0:3000 --timeout 600
