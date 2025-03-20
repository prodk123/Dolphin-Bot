#!/bin/bash
# Exit early on errors
set -eu

# Python buffers stdout. Without this, you won't see what you "print" in the Activity Log
export PYTHONUNBUFFERED=true

# Install Python 3 virtual env
python3 -m venv .venv
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Install dependencies
pip3 install -r requirements.txt

# Start the application using gunicorn
gunicorn app:app --bind 0.0.0.0:3000 