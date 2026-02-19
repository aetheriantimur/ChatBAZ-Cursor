# ChatBAZ Cursor Quick Start

## macOS

### 1. Install dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Save API key

```bash
python3 chatbaz-cursor-proxy.py set-key
```

### 3. Generate and install cert

```bash
mitmproxy
# Ctrl+C after startup
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain \
  ~/.mitmproxy/mitmproxy-ca-cert.pem
```

### 4. Set proxy env vars

```bash
export HTTP_PROXY=http://127.0.0.1:8080
export HTTPS_PROXY=http://127.0.0.1:8080
export NODE_EXTRA_CA_CERTS=~/.mitmproxy/mitmproxy-ca-cert.pem
```

### 5. Run

```bash
python3 chatbaz-cursor-proxy.py start --verbose
cursor .
python3 chatbaz-cursor-proxy.py test
```

## Linux

### 1. Install dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Save API key

```bash
python3 chatbaz-cursor-proxy.py set-key
```

### 3. Generate and install cert

```bash
mitmproxy
# Ctrl+C after startup
```

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

### 4. Set proxy env vars

```bash
export HTTP_PROXY=http://127.0.0.1:8080
export HTTPS_PROXY=http://127.0.0.1:8080
export NODE_EXTRA_CA_CERTS=~/.mitmproxy/mitmproxy-ca-cert.pem
```

### 5. Run

```bash
python3 chatbaz-cursor-proxy.py start --verbose
cursor .
python3 chatbaz-cursor-proxy.py test
```

## Windows (PowerShell)

### 1. Install dependencies

```powershell
py -3 -m pip install -r requirements.txt
```

### 2. Save API key

```powershell
py -3 chatbaz-cursor-proxy.py set-key
```

### 3. Generate and install cert

```powershell
mitmproxy
# Ctrl+C after startup
```

Run PowerShell as Administrator:

```powershell
certutil -addstore "Root" "$env:USERPROFILE\.mitmproxy\mitmproxy-ca-cert.pem"
```

### 4. Set proxy env vars

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

### 5. Run

```powershell
py -3 chatbaz-cursor-proxy.py start --verbose
cursor .
py -3 chatbaz-cursor-proxy.py test
```

## Behavior

- Intercepts `api.anthropic.com`
- Forwards to `https://chatbaz.app/claude`
- Preserves original path/query
- Injects stored `x-api-key`
