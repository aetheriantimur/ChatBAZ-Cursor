#!/usr/bin/env pwsh
# Start Cursor with ChatBAZ proxy environment variables (Windows PowerShell)

param(
    [int]$ProxyPort = 8080
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 ChatBAZ Cursor - Start Cursor With Proxy"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host ""
Write-Host "This script only starts Cursor with proxy env vars."
Write-Host "Run proxy first in another terminal:"
Write-Host "  py -3 chatbaz-cursor-proxy.py start --verbose"
Write-Host ""

$certFile = Join-Path $env:USERPROFILE ".mitmproxy\mitmproxy-ca-cert.pem"
if (-not (Test-Path $certFile)) {
    Write-Host "⚠️  Warning: mitmproxy certificate not found at: $certFile"
    Write-Host "   Run 'mitmproxy' once and install certificate to Windows Root store."
    Write-Host ""
}

$env:HTTP_PROXY = "http://127.0.0.1:$ProxyPort"
$env:HTTPS_PROXY = "http://127.0.0.1:$ProxyPort"
$env:NODE_EXTRA_CA_CERTS = $certFile

Write-Host "✓ Proxy environment configured:"
Write-Host "  HTTP_PROXY=$env:HTTP_PROXY"
Write-Host "  HTTPS_PROXY=$env:HTTPS_PROXY"
Write-Host "  NODE_EXTRA_CA_CERTS=$env:NODE_EXTRA_CA_CERTS"
Write-Host ""
Write-Host "Reminder: Cursor must have Anthropic API key filled (your ChatBAZ key)."
Write-Host ""
Write-Host "Starting Cursor..."
Write-Host ""

if (Get-Command cursor -ErrorAction SilentlyContinue) {
    cursor @args
} elseif (Get-Command code -ErrorAction SilentlyContinue) {
    Write-Host "⚠️  'cursor' command not found, trying 'code' instead..."
    code @args
} else {
    Write-Error "Neither 'cursor' nor 'code' command found in PATH."
}
