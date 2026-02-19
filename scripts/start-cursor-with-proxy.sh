#!/bin/bash
# Start Cursor with ChatBAZ proxy environment variables (macOS/Linux)

set -e

echo "🚀 ChatBAZ Cursor - Start Cursor With Proxy"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "This script only starts Cursor with proxy env vars."
echo "Run proxy first in another terminal:"
echo "  python3 chatbaz-cursor-proxy.py start --verbose"
echo ""

# Check if mitmproxy cert exists
CERT_FILE=~/.mitmproxy/mitmproxy-ca-cert.pem
if [ ! -f "$CERT_FILE" ]; then
    echo "⚠️  Warning: mitmproxy certificate not found!"
    echo "   Run 'mitmproxy' once to generate it, then install with:"
    echo "   ./scripts/install-ca-cert.sh"
    echo ""
fi

# Set proxy environment variables (allow override via CHATBAZ_PROXY_PORT)
PROXY_PORT="${CHATBAZ_PROXY_PORT:-8080}"
export HTTP_PROXY="http://127.0.0.1:${PROXY_PORT}"
export HTTPS_PROXY="http://127.0.0.1:${PROXY_PORT}"
export NODE_EXTRA_CA_CERTS="$CERT_FILE"

echo "✓ Proxy environment configured:"
echo "  HTTP_PROXY=$HTTP_PROXY"
echo "  HTTPS_PROXY=$HTTPS_PROXY"
echo "  NODE_EXTRA_CA_CERTS=$NODE_EXTRA_CA_CERTS"
echo ""
echo "Reminder: Cursor must have Anthropic API key filled (your ChatBAZ key)."
echo ""
echo "Starting Cursor..."
echo ""

# Start Cursor
if command -v cursor &> /dev/null; then
    cursor "$@"
elif command -v code &> /dev/null; then
    # Fallback to VSCode if cursor not found
    echo "⚠️  'cursor' command not found, trying 'code' instead..."
    code "$@"
else
    echo "❌ Neither 'cursor' nor 'code' command found!"
    echo ""
    echo "Please install Cursor or add it to your PATH."
    echo "Or run Cursor manually with these environment variables set."
    exit 1
fi
