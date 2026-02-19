#!/bin/bash
# Install mitmproxy CA certificate for different platforms

set -e

echo "🔐 Installing mitmproxy CA Certificate"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if mitmproxy has been run
CERT_FILE=~/.mitmproxy/mitmproxy-ca-cert.pem

if [ ! -f "$CERT_FILE" ]; then
    echo "❌ mitmproxy certificate not found!"
    echo ""
    echo "Please run mitmproxy once to generate certificates:"
    echo "  mitmproxy"
    echo "Then press Ctrl+C to quit, and run this script again."
    exit 1
fi

echo "✓ Certificate found: $CERT_FILE"
echo ""

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Detected: macOS"
    echo "Installing to System Keychain (requires sudo)..."
    echo ""
    sudo security add-trusted-cert -d -r trustRoot \
        -k /Library/Keychains/System.keychain \
        "$CERT_FILE"
    echo ""
    echo "✅ Certificate installed successfully!"
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "Detected: Linux"
    
    if [ -d "/usr/local/share/ca-certificates" ]; then
        # Debian/Ubuntu
        echo "Installing for Debian/Ubuntu (requires sudo)..."
        sudo cp "$CERT_FILE" /usr/local/share/ca-certificates/mitmproxy.crt
        sudo update-ca-certificates
        echo ""
        echo "✅ Certificate installed successfully!"
        
    elif [ -d "/etc/pki/ca-trust/source/anchors" ]; then
        # RHEL/CentOS/Fedora
        echo "Installing for RHEL/CentOS/Fedora (requires sudo)..."
        sudo cp "$CERT_FILE" /etc/pki/ca-trust/source/anchors/mitmproxy.crt
        sudo update-ca-trust
        echo ""
        echo "✅ Certificate installed successfully!"
        
    else
        echo "❌ Unknown Linux distribution"
        echo "Please install the certificate manually:"
        echo "  Certificate: $CERT_FILE"
        exit 1
    fi
    
else
    echo "❌ Unsupported OS: $OSTYPE"
    echo ""
    echo "Please install the certificate manually:"
    echo "  Certificate: $CERT_FILE"
    echo ""
    echo "For Windows (PowerShell as Admin):"
    echo "  certutil -addstore \"Root\" %USERPROFILE%\\.mitmproxy\\mitmproxy-ca-cert.pem"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Additional step for Electron apps (like Cursor):"
echo ""
echo "Add this to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
echo "  export NODE_EXTRA_CA_CERTS=~/.mitmproxy/mitmproxy-ca-cert.pem"
echo ""
echo "Or run before starting Cursor:"
echo "  export NODE_EXTRA_CA_CERTS=~/.mitmproxy/mitmproxy-ca-cert.pem"
echo "  cursor ."
echo ""
