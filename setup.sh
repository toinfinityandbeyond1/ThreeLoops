#!/bin/bash

# Setup script for Autonomous AI System

echo "========================================"
echo "Autonomous AI Setup"
echo "========================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Install requirements
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Check for OpenAI API key
echo ""
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠ OPENAI_API_KEY environment variable not set"
    echo ""
    echo "To set your API key, run:"
    echo "  export OPENAI_API_KEY='your-api-key-here'"
    echo ""
    echo "Or add it to your ~/.bashrc or ~/.zshrc:"
    echo "  echo \"export OPENAI_API_KEY='your-api-key-here'\" >> ~/.bashrc"
    echo ""
else
    echo "✓ OPENAI_API_KEY is set"
fi

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "To run the AI in interactive mode:"
echo "  python3 AutonomousAI.py"
echo ""
echo "To run a simulation:"
echo "  python3 AutonomousAI.py --simulate 365"
echo ""
