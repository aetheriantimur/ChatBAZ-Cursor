# ChatBAZ Cursor Quick Start

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

## 2. Save API key

```bash
python3 chatbaz-cursor-proxy.py set-key
```

## 3. Install local CA cert

```bash
mitmproxy
# Ctrl+C after startup
./scripts/install-ca-cert.sh
```

## 4. Set proxy env vars

```bash
export HTTP_PROXY=http://127.0.0.1:8080
export HTTPS_PROXY=http://127.0.0.1:8080
export NODE_EXTRA_CA_CERTS=~/.mitmproxy/mitmproxy-ca-cert.pem
```

## 5. Start proxy

```bash
python3 chatbaz-cursor-proxy.py start --verbose
```

## 6. Start Cursor

```bash
cursor .
```

## 7. Run connectivity test

```bash
python3 chatbaz-cursor-proxy.py test
```

## Behavior

- Intercepts `api.anthropic.com`
- Forwards to `https://chatbaz.app/claude`
- Preserves original path/query
- Injects stored `x-api-key`
