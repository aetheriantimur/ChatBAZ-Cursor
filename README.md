# ChatBAZ Cursor

ChatBAZ Cursor is a local proxy bridge for Cursor traffic.

It rewrites requests that reach the proxy as:

- `api.anthropic.com/...` -> `https://chatbaz.app/claude/...`

and forwards incoming `x-api-key` unchanged.

## Critical Rule (Must Read)

This proxy **does not** capture all system traffic automatically.

It only processes traffic that is explicitly sent to proxy (`127.0.0.1:8080`).

If Cursor is not started with proxy settings, **nothing is intercepted**.

## What Customers Must Configure in Cursor

On every customer machine:

1. Open Cursor settings.
2. Search `anthropic`.
3. Paste customer ChatBAZ key into Anthropic API key field.
4. Save and restart Cursor.

If this is missing, requests may reach proxy but upstream auth fails.

## Standard Operating Flow (All Platforms)

1. Install dependencies.
2. Generate and trust mitmproxy CA certificate.
3. Start proxy in Terminal 1.
4. Start Cursor with proxy env vars in Terminal 2.
5. Validate with `test` command.

## Commands

### Proxy

macOS/Linux:

```bash
python3 chatbaz-cursor-proxy.py start --verbose
```

Windows PowerShell:

```powershell
py -3 chatbaz-cursor-proxy.py start --verbose
```

### Upstream auth check

macOS/Linux:

```bash
python3 chatbaz-cursor-proxy.py test --api-key <YOUR_KEY>
```

Windows PowerShell:

```powershell
py -3 chatbaz-cursor-proxy.py test --api-key <YOUR_KEY>
```

---

## macOS Runbook

### 1. Install dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Generate certificate (once)

```bash
mitmproxy
# wait for startup, then Ctrl+C
```

### 3. Trust certificate (once)

```bash
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain \
  ~/.mitmproxy/mitmproxy-ca-cert.pem
```

### 4. Terminal 1: Start proxy

```bash
python3 chatbaz-cursor-proxy.py start --verbose
```

### 5. Terminal 2: Start Cursor with proxy env

```bash
./scripts/start-cursor-with-proxy.sh
```

Optional custom proxy port:

```bash
CHATBAZ_PROXY_PORT=9090 ./scripts/start-cursor-with-proxy.sh
```

### 6. Validate

```bash
python3 chatbaz-cursor-proxy.py test --api-key <YOUR_KEY>
```

---

## Linux Runbook

### 1. Install dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Generate certificate (once)

```bash
mitmproxy
# wait for startup, then Ctrl+C
```

### 3. Trust certificate (once)

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

### 4. Terminal 1: Start proxy

```bash
python3 chatbaz-cursor-proxy.py start --verbose
```

### 5. Terminal 2: Start Cursor with proxy env

```bash
./scripts/start-cursor-with-proxy.sh
```

Optional custom proxy port:

```bash
CHATBAZ_PROXY_PORT=9090 ./scripts/start-cursor-with-proxy.sh
```

### 6. Validate

```bash
python3 chatbaz-cursor-proxy.py test --api-key <YOUR_KEY>
```

---

## Windows Runbook (PowerShell)

### 1. Install dependencies

```powershell
py -3 -m pip install -r requirements.txt
```

### 2. Generate certificate (once)

```powershell
mitmproxy
# wait for startup, then Ctrl+C
```

### 3. Trust certificate (once, Admin PowerShell)

```powershell
certutil -addstore "Root" "$env:USERPROFILE\.mitmproxy\mitmproxy-ca-cert.pem"
```

### 4. Terminal 1: Start proxy

```powershell
py -3 chatbaz-cursor-proxy.py start --verbose
```

### 5. Terminal 2: Start Cursor with proxy env

```powershell
./scripts/start-cursor-with-proxy.ps1
```

Optional custom proxy port:

```powershell
./scripts/start-cursor-with-proxy.ps1 -ProxyPort 9090
```

### 6. Validate

```powershell
py -3 chatbaz-cursor-proxy.py test --api-key <YOUR_KEY>
```

---

## Request Mapping

Incoming (to proxy):

- Host: `api.anthropic.com`
- Path: `/v1/messages`
- Header: `x-api-key: <incoming-value>`

Outgoing (from proxy):

- Host: `chatbaz.app`
- Path: `/claude/v1/messages`
- Header: `x-api-key: <incoming-value>`

## Troubleshooting

- `401/403` upstream: Cursor key missing/invalid.
- No proxy logs: Cursor was not started through proxy env.
- TLS error: CA not trusted or `NODE_EXTRA_CA_CERTS` missing.
- Port in use: run proxy with `--port`, then start cursor scripts with same port.

## Runtime Files

- Logs: `~/.chatbaz-cursor/proxy.log`

## Security

- Proxy listens on localhost only.
- API keys are not persisted by this project.
