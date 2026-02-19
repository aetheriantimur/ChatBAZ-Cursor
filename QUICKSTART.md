# ChatBAZ Cursor Quickstart

## macOS

```bash
pip3 install -r requirements.txt
mitmproxy
# Ctrl+C
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain \
  ~/.mitmproxy/mitmproxy-ca-cert.pem
export HTTP_PROXY=http://127.0.0.1:8080
export HTTPS_PROXY=http://127.0.0.1:8080
export NODE_EXTRA_CA_CERTS=~/.mitmproxy/mitmproxy-ca-cert.pem
python3 chatbaz-cursor-proxy.py start --verbose
```

In a second terminal:

```bash
cursor .
python3 chatbaz-cursor-proxy.py test --api-key <YOUR_KEY>
```

## Linux

```bash
pip3 install -r requirements.txt
mitmproxy
# Ctrl+C
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

Then:

```bash
export HTTP_PROXY=http://127.0.0.1:8080
export HTTPS_PROXY=http://127.0.0.1:8080
export NODE_EXTRA_CA_CERTS=~/.mitmproxy/mitmproxy-ca-cert.pem
python3 chatbaz-cursor-proxy.py start --verbose
```

In a second terminal:

```bash
cursor .
python3 chatbaz-cursor-proxy.py test --api-key <YOUR_KEY>
```

## Windows (PowerShell)

```powershell
py -3 -m pip install -r requirements.txt
mitmproxy
# Ctrl+C
```

Admin PowerShell:

```powershell
certutil -addstore "Root" "$env:USERPROFILE\.mitmproxy\mitmproxy-ca-cert.pem"
```

PowerShell session for Cursor:

```powershell
$env:HTTP_PROXY="http://127.0.0.1:8080"
$env:HTTPS_PROXY="http://127.0.0.1:8080"
$env:NODE_EXTRA_CA_CERTS="$env:USERPROFILE\.mitmproxy\mitmproxy-ca-cert.pem"
py -3 chatbaz-cursor-proxy.py start --verbose
```

In another PowerShell window:

```powershell
cursor .
py -3 chatbaz-cursor-proxy.py test --api-key <YOUR_KEY>
```

## Behavior

- Intercepts `api.anthropic.com`
- Forwards to `https://chatbaz.app/claude`
- Preserves path/query and passes incoming `x-api-key` unchanged
