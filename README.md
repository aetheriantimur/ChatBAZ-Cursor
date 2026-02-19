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

## Install

```bash
pip install -r requirements.txt
```

Or:

```bash
chmod +x setup.sh
./setup.sh
```

## Quick Start

### 1. Set API key

```bash
python3 chatbaz-cursor-proxy.py set-key
```

### 2. Install mitmproxy certificate

```bash
mitmproxy
# Ctrl+C after startup
chmod +x scripts/install-ca-cert.sh
./scripts/install-ca-cert.sh
```

### 3. Configure proxy env vars

```bash
export HTTP_PROXY=http://127.0.0.1:8080
export HTTPS_PROXY=http://127.0.0.1:8080
export NODE_EXTRA_CA_CERTS=~/.mitmproxy/mitmproxy-ca-cert.pem
```

### 4. Start proxy

```bash
python3 chatbaz-cursor-proxy.py start
```

### 5. Validate connectivity

```bash
python3 chatbaz-cursor-proxy.py test
```

## Commands

```bash
python3 chatbaz-cursor-proxy.py set-key
python3 chatbaz-cursor-proxy.py start
python3 chatbaz-cursor-proxy.py start --port 9090
python3 chatbaz-cursor-proxy.py test
python3 chatbaz-cursor-proxy.py --version
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
