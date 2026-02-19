# ChatBAZ Cursor Quickstart (Customer Safe)

## Absolute Minimum Rules

1. Cursor must have Anthropic API key set (use ChatBAZ key).
2. Proxy must run in Terminal 1.
3. Cursor must be started with proxy env in Terminal 2.
4. If step 3 is skipped, proxy cannot intercept anything.

---

## macOS (copy/paste)

Terminal 1:

```bash
pip3 install -r requirements.txt
mitmproxy
# Ctrl+C after startup
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain \
  ~/.mitmproxy/mitmproxy-ca-cert.pem
python3 chatbaz-cursor-proxy.py start --verbose
```

Terminal 2:

```bash
./scripts/start-cursor-with-proxy.sh
```

Check:

```bash
python3 chatbaz-cursor-proxy.py test --api-key <YOUR_KEY>
```

---

## Linux (copy/paste)

Terminal 1:

```bash
pip3 install -r requirements.txt
mitmproxy
# Ctrl+C after startup
```

Debian/Ubuntu cert install:

```bash
sudo cp ~/.mitmproxy/mitmproxy-ca-cert.pem /usr/local/share/ca-certificates/mitmproxy.crt
sudo update-ca-certificates
```

RHEL/CentOS/Fedora cert install:

```bash
sudo cp ~/.mitmproxy/mitmproxy-ca-cert.pem /etc/pki/ca-trust/source/anchors/mitmproxy.crt
sudo update-ca-trust
```

Then start proxy (Terminal 1):

```bash
python3 chatbaz-cursor-proxy.py start --verbose
```

Terminal 2:

```bash
./scripts/start-cursor-with-proxy.sh
```

Check:

```bash
python3 chatbaz-cursor-proxy.py test --api-key <YOUR_KEY>
```

---

## Windows PowerShell (copy/paste)

Terminal 1:

```powershell
py -3 -m pip install -r requirements.txt
mitmproxy
# Ctrl+C after startup
```

Admin PowerShell (once):

```powershell
certutil -addstore "Root" "$env:USERPROFILE\.mitmproxy\mitmproxy-ca-cert.pem"
```

Then start proxy (Terminal 1):

```powershell
py -3 chatbaz-cursor-proxy.py start --verbose
```

Terminal 2:

```powershell
./scripts/start-cursor-with-proxy.ps1
```

Check:

```powershell
py -3 chatbaz-cursor-proxy.py test --api-key <YOUR_KEY>
```

---

## Windows CMD (copy/paste)

Terminal 1:

```cmd
py -3 -m pip install -r requirements.txt
mitmproxy
REM Ctrl+C after startup
```

Admin CMD (once):

```cmd
certutil -addstore Root "%USERPROFILE%\.mitmproxy\mitmproxy-ca-cert.pem"
```

Then start proxy (Terminal 1):

```cmd
py -3 chatbaz-cursor-proxy.py start --verbose
```

Terminal 2:

```cmd
scripts\start-cursor-with-proxy.cmd
```

Check:

```cmd
py -3 chatbaz-cursor-proxy.py test --api-key <YOUR_KEY>
```

---

## Expected Behavior

- Intercepts only proxied requests to `api.anthropic.com`
- Forwards to `https://chatbaz.app/claude`
- Passes incoming `x-api-key` unchanged
