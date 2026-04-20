#!/bin/bash

# Setup script for GAMS and Python environment
# Source this script in your terminal: source ./setup.sh

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Load environment variables from .env
if [ -f "$DIR/.env" ]; then
    source "$DIR/.env"
    echo "✓ Loaded GAMS configuration from .env"
else
    echo "✗ .env file not found"
    return 1
fi

# Activate Python virtual environment
if [ -f "$DIR/venv/bin/activate" ]; then
    source "$DIR/venv/bin/activate"
    echo "✓ Activated Python virtual environment"
else
    echo "✗ Virtual environment not found"
    return 1
fi

echo ""
echo "Environment ready!"
echo "You can now run:"
echo "  - gams <file.gms>"
echo "  - python <script.py>"
