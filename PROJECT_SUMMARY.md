# ChatBAZ Cursor - Project Summary

## Overview

`ChatBAZ Cursor` is a local mitmproxy adapter for Cursor traffic.

Requests targeting `api.anthropic.com` are rewritten to `https://chatbaz.app/claude` and sent with stored `x-api-key` credentials.

## Main Files

- `chatbaz-cursor-proxy.py`: CLI + proxy runtime
- `scripts/install-ca-cert.sh`: certificate installer
- `scripts/start-cursor-with-proxy.sh`: starts Cursor with proxy vars
- `README.md`: full guide
- `QUICKSTART.md`: fast setup steps

## Runtime Paths

- Credentials: `~/.chatbaz-cursor/credentials.json`
- Logs: `~/.chatbaz-cursor/proxy.log`

## Credential Format

```json
{
  "api_key": "...",
  "created_at": 1735686000000,
  "updated_at": 1735689600000
}
```

## CLI

- `set-key`: save local API key
- `start`: run proxy on localhost
- `test`: validate upstream access

## Request Flow

1. Cursor sends request to `api.anthropic.com`.
2. Proxy intercepts request.
3. Request rewrite:
   - host -> `chatbaz.app`
   - scheme -> `https`
   - port -> `443`
   - path -> `/claude` + original path
4. Header enforcement:
   - remove `authorization` if present
   - set `x-api-key` from local credentials
5. Request forwarded upstream.

## Error Handling

- Missing key: `401` with `set-key` action.
- Upstream failures: logged with request id.

## Version

- Current version: `1.0.0`
