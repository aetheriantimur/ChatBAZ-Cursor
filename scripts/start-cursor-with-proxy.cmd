@echo off
setlocal
REM Start Cursor with ChatBAZ proxy environment variables (Windows CMD)

set "PROXY_PORT=8080"
if not "%~1"=="" (
  echo %~1| findstr /r "^[0-9][0-9]*$" >nul
  if not errorlevel 1 (
    set "PROXY_PORT=%~1"
    shift
  )
)

echo 🚀 ChatBAZ Cursor - Start Cursor With Proxy (CMD)
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo This script only starts Cursor with proxy env vars.
echo Run proxy first in another terminal:
echo   py -3 chatbaz-cursor-proxy.py start --verbose
echo.

set "CERT_FILE=%USERPROFILE%\.mitmproxy\mitmproxy-ca-cert.pem"
if not exist "%CERT_FILE%" (
  echo ⚠️  Warning: mitmproxy certificate not found at:
  echo    %CERT_FILE%
  echo.
)

set "HTTP_PROXY=http://127.0.0.1:%PROXY_PORT%"
set "HTTPS_PROXY=http://127.0.0.1:%PROXY_PORT%"
set "NODE_EXTRA_CA_CERTS=%CERT_FILE%"

echo ✓ Proxy environment configured:
echo   HTTP_PROXY=%HTTP_PROXY%
echo   HTTPS_PROXY=%HTTPS_PROXY%
echo   NODE_EXTRA_CA_CERTS=%NODE_EXTRA_CA_CERTS%
echo.
echo Reminder: Cursor must have Anthropic API key filled ^(your ChatBAZ key^).
echo.
echo Starting Cursor...
echo.

where cursor >nul 2>&1
if %ERRORLEVEL%==0 (
  cursor %*
  exit /b %ERRORLEVEL%
)

where code >nul 2>&1
if %ERRORLEVEL%==0 (
  echo ⚠️  'cursor' command not found, trying 'code' instead...
  code %*
  exit /b %ERRORLEVEL%
)

echo ❌ Neither 'cursor' nor 'code' command found in PATH.
exit /b 1
