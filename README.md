# ChatBAZ Cursor

ChatBAZ Cursor is a local proxy layer for Cursor traffic.

It captures requests sent to `api.anthropic.com`, rewrites them to `https://chatbaz.app/claude`, and forwards the incoming `x-api-key` header unchanged.

## What It Does

- Rewrites host and base path:
  - `api.anthropic.com/*` -> `chatbaz.app/claude/*`
- Preserves request path and query string
- Keeps incoming `x-api-key` as-is (no local key storage)
- Writes rotating logs to `~/.chatbaz-cursor/proxy.log`

## Architecture

```text
Cursor IDE
  -> Local Proxy (127.0.0.1:8080)
     -> https://chatbaz.app/claude
```

## Requirements

- Python 3.8+
- Cursor IDE
- `mitmproxy` certificate trusted by your OS

## Cursor Inside Mandatory Setup

`ChatBAZ Cursor` only forwards what Cursor sends.  
If Cursor does not send `x-api-key`, upstream auth fails.

Do this on every client machine:

1. Open Cursor settings.
2. Find Anthropic provider/API key settings (search: `anthropic`).
3. Paste the customer ChatBAZ key into Anthropic API key field.
4. Save settings and fully restart Cursor.
5. Start proxy in verbose mode and confirm there is no `forwarded without x-api-key` warning.

## Command Reference

### macOS / Linux

```bash
python3 chatbaz-cursor-proxy.py start
python3 chatbaz-cursor-proxy.py start --port 9090
python3 chatbaz-cursor-proxy.py test --api-key <YOUR_KEY>
python3 chatbaz-cursor-proxy.py --version
```

### Windows (PowerShell)

```powershell
py -3 chatbaz-cursor-proxy.py start
py -3 chatbaz-cursor-proxy.py start --port 9090
py -3 chatbaz-cursor-proxy.py test --api-key <YOUR_KEY>
py -3 chatbaz-cursor-proxy.py --version
```

## macOS Runbook

### 1. Install dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Generate mitmproxy CA cert

```bash
mitmproxy
# Wait until it starts, then Ctrl+C
```

### 3. Trust CA cert in system keychain

```bash
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain \
  ~/.mitmproxy/mitmproxy-ca-cert.pem
```

### 4. Export proxy env vars

```bash
export HTTP_PROXY=http://127.0.0.1:8080
export HTTPS_PROXY=http://127.0.0.1:8080
export NODE_EXTRA_CA_CERTS=~/.mitmproxy/mitmproxy-ca-cert.pem
```

### 5. Start proxy and Cursor

```bash
python3 chatbaz-cursor-proxy.py start --verbose
cursor .
```

### 6. Validate upstream access

```bash
python3 chatbaz-cursor-proxy.py test --api-key <YOUR_KEY>
```

## Linux Runbook

### 1. Install dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Generate mitmproxy CA cert

```bash
mitmproxy
# Wait until it starts, then Ctrl+C
```

### 3. Trust CA cert

Debian / Ubuntu:

```bash
sudo cp ~/.mitmproxy/mitmproxy-ca-cert.pem /usr/local/share/ca-certificates/mitmproxy.crt
sudo update-ca-certificates
```

RHEL / CentOS / Fedora:

```bash
sudo cp ~/.mitmproxy/mitmproxy-ca-cert.pem /etc/pki/ca-trust/source/anchors/mitmproxy.crt
sudo update-ca-trust
```

### 4. Export proxy env vars

```bash
export HTTP_PROXY=http://127.0.0.1:8080
export HTTPS_PROXY=http://127.0.0.1:8080
export NODE_EXTRA_CA_CERTS=~/.mitmproxy/mitmproxy-ca-cert.pem
```

### 5. Start proxy and Cursor

```bash
python3 chatbaz-cursor-proxy.py start --verbose
cursor .
```

### 6. Validate upstream access

```bash
python3 chatbaz-cursor-proxy.py test --api-key <YOUR_KEY>
```

## Windows Runbook (PowerShell)

### 1. Install dependencies

```powershell
py -3 -m pip install -r requirements.txt
```

### 2. Generate mitmproxy CA cert

```powershell
mitmproxy
# Wait until it starts, then Ctrl+C
```

### 3. Trust CA cert (Admin PowerShell)

```powershell
certutil -addstore "Root" "$env:USERPROFILE\.mitmproxy\mitmproxy-ca-cert.pem"
```

### 4. Configure proxy env vars

Current session:

```powershell
$env:HTTP_PROXY="http://127.0.0.1:8080"
$env:HTTPS_PROXY="http://127.0.0.1:8080"
$env:NODE_EXTRA_CA_CERTS="$env:USERPROFILE\.mitmproxy\mitmproxy-ca-cert.pem"
```

Persistent:

```powershell
setx HTTP_PROXY "http://127.0.0.1:8080"
setx HTTPS_PROXY "http://127.0.0.1:8080"
setx NODE_EXTRA_CA_CERTS "%USERPROFILE%\.mitmproxy\mitmproxy-ca-cert.pem"
```

### 5. Start proxy and Cursor

```powershell
py -3 chatbaz-cursor-proxy.py start --verbose
cursor .
```

### 6. Validate upstream access

```powershell
py -3 chatbaz-cursor-proxy.py test --api-key <YOUR_KEY>
```

## Request Mapping

Incoming request:

- Host: `api.anthropic.com`
- Path: `/v1/messages`
- Header: `x-api-key: <incoming-value>`

Outgoing request:

- Host: `chatbaz.app`
- Path: `/claude/v1/messages`
- Header: `x-api-key: <incoming-value>`

## Troubleshooting

- `401/403` from upstream: verify Cursor is sending valid `x-api-key`.
- TLS errors in Cursor: verify `NODE_EXTRA_CA_CERTS` and trusted CA installation.
- No traffic in proxy logs: verify Cursor starts after proxy env vars are set.
- Port conflict: use `--port` and update proxy env vars accordingly.

## Runtime Files

- Logs: `~/.chatbaz-cursor/proxy.log`

## Security Notes

- Proxy binds to localhost.
- API keys are not persisted by this project.
- Keep your OS trust store controlled; remove unneeded CAs when done.
