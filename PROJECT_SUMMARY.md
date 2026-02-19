# ChatBAZ Cursor - Project Summary

## Overview

`ChatBAZ Cursor` is a local mitmproxy adapter for Cursor traffic.

Requests targeting `api.anthropic.com` are rewritten to `https://chatbaz.app/claude`. Incoming `x-api-key` is forwarded unchanged.

## Main Files

- `chatbaz-cursor-proxy.py`: CLI + proxy runtime
- `scripts/install-ca-cert.sh`: certificate installer
- `scripts/start-cursor-with-proxy.sh`: starts Cursor with proxy vars (macOS/Linux)
- `scripts/start-cursor-with-proxy.ps1`: starts Cursor with proxy vars (Windows PowerShell)
- `README.md`: full guide
- `QUICKSTART.md`: fast setup steps

## Runtime Paths

- Logs: `~/.chatbaz-cursor/proxy.log`

## CLI

- `start`: run proxy on localhost
- `test --api-key <KEY>`: validate upstream access

## Request Flow

1. Cursor sends request to `api.anthropic.com`.
2. Proxy intercepts request.
3. Request rewrite:
   - host -> `chatbaz.app`
   - scheme -> `https`
   - port -> `443`
   - path -> `/claude` + original path
4. Headers:
   - `x-api-key` is passed through unchanged.
5. Request forwarded upstream.

## Error Handling

- Missing incoming `x-api-key`: request is still forwarded; upstream decides auth result.
- Upstream failures: logged with request id.

## Version

- Current version: `1.1.0`
