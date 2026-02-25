#!/bin/bash

# Helper script to set OpenAI API key

echo "========================================"
echo "OpenAI API Key Configuration"
echo "========================================"
echo ""

if [ -z "$1" ]; then
    echo "Usage: ./set_api_key.sh YOUR_API_KEY"
    echo ""
    echo "Or to make it permanent:"
    echo "  ./set_api_key.sh YOUR_API_KEY --permanent"
    echo ""
    echo "Current API key status:"
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "  ✗ OPENAI_API_KEY is not set"
    else
        echo "  ✓ OPENAI_API_KEY is set"
    fi
    exit 0
fi

API_KEY="$1"
PERMANENT="$2"

# Set for current session
export OPENAI_API_KEY="$API_KEY"
echo "✓ API key set for current session"

# Make it permanent if requested
if [ "$PERMANENT" = "--permanent" ]; then
    SHELL_RC=""
    
    # Detect shell
    if [ -n "$BASH_VERSION" ]; then
        SHELL_RC="$HOME/.bashrc"
    elif [ -n "$ZSH_VERSION" ]; then
        SHELL_RC="$HOME/.zshrc"
    else
        SHELL_RC="$HOME/.profile"
    fi
    
    # Check if already exists
    if grep -q "OPENAI_API_KEY" "$SHELL_RC" 2>/dev/null; then
        echo "⚠ OPENAI_API_KEY already exists in $SHELL_RC"
        echo "  Please edit it manually to update"
    else
        echo "export OPENAI_API_KEY='$API_KEY'" >> "$SHELL_RC"
        echo "✓ Added to $SHELL_RC"
        echo "  Run 'source $SHELL_RC' or restart your terminal"
    fi
fi

echo ""
echo "You can now run: python3 AutonomousAI.py"
echo "========================================"
