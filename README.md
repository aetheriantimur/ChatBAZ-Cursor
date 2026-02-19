# ChatBAZ Cursor

`ChatBAZ Cursor` is a local mitmproxy adapter for Cursor.

It intercepts requests targeting `api.anthropic.com`, rewrites them to `https://chatbaz.app/claude`, and injects your stored `x-api-key` automatically.

## Features

- API key based authentication via `x-api-key`
- Host rewrite: `api.anthropic.com` -> `chatbaz.app/claude`
- Path and query preservation
- Local credential storage with `0600` permissions
- Rotating logs under `~/.chatbaz-cursor/`

## Requirements

- Python 3.8+
- Cursor IDE
- `mitmproxy` CA certificate installed on your OS

## Install Dependencies

### macOS / Linux

```bash
pip3 install -r requirements.txt
```

Or:

```bash
chmod +x setup.sh
./setup.sh
```

### Windows (PowerShell)

```powershell
py -3 -m pip install -r requirements.txt
```

## Platform Setup and Usage

### 1. Save API key

#### macOS / Linux

```bash
python3 chatbaz-cursor-proxy.py set-key
```

#### Windows (PowerShell)

```powershell
py -3 chatbaz-cursor-proxy.py set-key
```

### 2. Generate mitmproxy certificate

#### macOS / Linux

```bash
mitmproxy
# Ctrl+C after startup
```

#### Windows (PowerShell)

```powershell
mitmproxy
# Ctrl+C after startup
```

### 3. Install certificate (mandatory)

#### macOS

```bash
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain \
  ~/.mitmproxy/mitmproxy-ca-cert.pem
```

#### Linux (Debian / Ubuntu)

```bash
sudo cp ~/.mitmproxy/mitmproxy-ca-cert.pem /usr/local/share/ca-certificates/mitmproxy.crt
sudo update-ca-certificates
```

#### Linux (RHEL / CentOS / Fedora)

```bash
sudo cp ~/.mitmproxy/mitmproxy-ca-cert.pem /etc/pki/ca-trust/source/anchors/mitmproxy.crt
sudo update-ca-trust
```

#### Windows (PowerShell as Administrator)

```powershell
certutil -addstore "Root" "$env:USERPROFILE\.mitmproxy\mitmproxy-ca-cert.pem"
```

### 4. Set proxy environment variables (mandatory)

#### macOS / Linux

```bash
export HTTP_PROXY=http://127.0.0.1:8080
export HTTPS_PROXY=http://127.0.0.1:8080
export NODE_EXTRA_CA_CERTS=~/.mitmproxy/mitmproxy-ca-cert.pem
```

#### Windows (PowerShell - current session)

```powershell
$env:HTTP_PROXY="http://127.0.0.1:8080"
$env:HTTPS_PROXY="http://127.0.0.1:8080"
$env:NODE_EXTRA_CA_CERTS="$env:USERPROFILE\.mitmproxy\mitmproxy-ca-cert.pem"
```

#### Windows (PowerShell - persistent)

```powershell
setx HTTP_PROXY "http://127.0.0.1:8080"
setx HTTPS_PROXY "http://127.0.0.1:8080"
setx NODE_EXTRA_CA_CERTS "%USERPROFILE%\.mitmproxy\mitmproxy-ca-cert.pem"
```

### 5. Start proxy

#### macOS / Linux

```bash
python3 chatbaz-cursor-proxy.py start
```

#### Windows (PowerShell)

```powershell
py -3 chatbaz-cursor-proxy.py start
```

### 6. Start Cursor

#### macOS / Linux

```bash
cursor .
```

#### Windows (PowerShell)

```powershell
cursor .
```

### 7. Validate connectivity

#### macOS / Linux

```bash
python3 chatbaz-cursor-proxy.py test
```

#### Windows (PowerShell)

```powershell
py -3 chatbaz-cursor-proxy.py test
```

## Commands

### macOS / Linux

```bash
python3 chatbaz-cursor-proxy.py set-key
python3 chatbaz-cursor-proxy.py start
python3 chatbaz-cursor-proxy.py start --port 9090
python3 chatbaz-cursor-proxy.py test
python3 chatbaz-cursor-proxy.py --version
```

### Windows (PowerShell)

```powershell
py -3 chatbaz-cursor-proxy.py set-key
py -3 chatbaz-cursor-proxy.py start
py -3 chatbaz-cursor-proxy.py start --port 9090
py -3 chatbaz-cursor-proxy.py test
py -3 chatbaz-cursor-proxy.py --version
```

## Request Mapping

Incoming:

- Host: `api.anthropic.com`
- Path: `/v1/messages`

Outgoing:

- Host: `chatbaz.app`
- Path: `/claude/v1/messages`
- Header: `x-api-key: <stored key>`

## Storage

- Credentials: `~/.chatbaz-cursor/credentials.json`
- Logs: `~/.chatbaz-cursor/proxy.log`

Credential schema:

```json
{
  "api_key": "...",
  "created_at": 1735686000000,
  "updated_at": 1735689600000
}
```

## Troubleshooting

No API key configured:

```bash
python3 chatbaz-cursor-proxy.py set-key
```

Certificate errors:

```bash
export NODE_EXTRA_CA_CERTS=~/.mitmproxy/mitmproxy-ca-cert.pem
```

Proxy check:

```bash
lsof -i :8080
python3 chatbaz-cursor-proxy.py start --verbose
```

## Notes

- Proxy listens on localhost only.
- Keep your API key private.
