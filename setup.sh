#!/bin/bash
# Quick setup script for ChatBAZ Cursor Proxy

set -e

echo "🚀 ChatBAZ Cursor - Quick Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "❌ Python 3 not found. Please install Python 3.8+"; exit 1; }

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Set API key: python3 chatbaz-cursor-proxy.py set-key"
echo "  2. Start proxy: python3 chatbaz-cursor-proxy.py start"
echo ""
