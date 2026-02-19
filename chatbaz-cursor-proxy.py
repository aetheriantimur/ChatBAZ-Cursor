#!/usr/bin/env python3
"""
ChatBAZ Cursor Proxy

Intercepts Cursor IDE requests targeting api.anthropic.com and rewrites them to
chatbaz.app/claude while enforcing x-api-key authentication.

Usage:
    python chatbaz-cursor-proxy.py set-key
    python chatbaz-cursor-proxy.py start
    python chatbaz-cursor-proxy.py test
"""

import argparse
import getpass
import json
import logging
import sys
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import httpx
    from mitmproxy import http
    from mitmproxy.tools.main import mitmdump
    from rich.console import Console
    from rich.panel import Panel
except ImportError as e:
    print(f"Error: Missing required dependency: {e}")
    print("\nPlease install dependencies:")
    print("  pip install -r requirements.txt")
    sys.exit(1)


VERSION = "1.0.0"
APP_NAME = "ChatBAZ Cursor"
LOGGER_NAME = "chatbaz-cursor-proxy"

INTERCEPT_HOST = "api.anthropic.com"
UPSTREAM_HOST = "chatbaz.app"
UPSTREAM_SCHEME = "https"
UPSTREAM_PORT = 443
UPSTREAM_PREFIX = "/claude"

STORAGE_DIR = Path.home() / ".chatbaz-cursor"
CREDENTIAL_FILE = STORAGE_DIR / "credentials.json"
LOG_FILE = STORAGE_DIR / "proxy.log"

console = Console()


def setup_logger(verbose: bool = False) -> logging.Logger:
    """Setup logging with console and rotating file handlers."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.handlers.clear()

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,
        backupCount=3,
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-7s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_formatter = logging.Formatter("%(levelname)-7s - %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


class CredentialStorage:
    """Handles local API key storage with strict file permissions."""

    def __init__(self, storage_path: Path = CREDENTIAL_FILE):
        self.storage_path = storage_path

    def load(self) -> Optional[Dict[str, Any]]:
        if not self.storage_path.exists():
            return None

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logging.getLogger(LOGGER_NAME).error(f"Failed to load credentials: {e}")
            return None

    def save(self, api_key: str) -> None:
        now_ms = int(time.time() * 1000)
        existing = self.load() or {}
        created_at = existing.get("created_at", now_ms)

        payload = {
            "api_key": api_key,
            "created_at": created_at,
            "updated_at": now_ms,
        }

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        self.storage_path.chmod(0o600)

    def has_key(self) -> bool:
        data = self.load()
        return bool(data and isinstance(data.get("api_key"), str) and data["api_key"].strip())

    def get_key(self) -> Optional[str]:
        data = self.load()
        if not data:
            return None
        key = data.get("api_key")
        if not isinstance(key, str):
            return None
        key = key.strip()
        return key or None

    def get_masked_key(self) -> str:
        key = self.get_key()
        if not key:
            return "(not set)"
        if len(key) <= 8:
            return "*" * len(key)
        return f"{key[:4]}...{key[-4:]}"


def validate_api_key(api_key: str) -> bool:
    key = api_key.strip()
    return len(key) >= 10


def ensure_leading_slash(path: str) -> str:
    if not path:
        return "/"
    return path if path.startswith("/") else f"/{path}"


def build_upstream_path(original_path: str) -> str:
    path = ensure_leading_slash(original_path)
    if path == UPSTREAM_PREFIX or path.startswith(f"{UPSTREAM_PREFIX}/"):
        return path
    return f"{UPSTREAM_PREFIX}{path}"


def remove_header_case_insensitive(headers: Any, name: str) -> None:
    for key in list(headers.keys()):
        if key.lower() == name.lower():
            del headers[key]


class ChatBAZCursorAddon:
    """mitmproxy addon that rewrites source host traffic to ChatBAZ."""

    def __init__(self, storage: CredentialStorage, logger: logging.Logger):
        self.storage = storage
        self.logger = logger
        self.request_count = 0

    def request(self, flow: http.HTTPFlow) -> None:
        if flow.request.host != INTERCEPT_HOST:
            return

        self.request_count += 1
        request_id = self.request_count

        api_key = self.storage.get_key()
        if not api_key:
            self.logger.error("Request blocked: API key not configured")
            flow.response = http.Response.make(
                401,
                json.dumps(
                    {
                        "error": {
                            "type": "authentication_error",
                            "message": "ChatBAZ API key is not configured.",
                        },
                        "action": "Run: python chatbaz-cursor-proxy.py set-key",
                    }
                ),
                {"Content-Type": "application/json"},
            )
            return

        original_path = flow.request.path
        rewritten_path = build_upstream_path(original_path)

        flow.request.scheme = UPSTREAM_SCHEME
        flow.request.host = UPSTREAM_HOST
        flow.request.port = UPSTREAM_PORT
        flow.request.path = rewritten_path
        flow.request.headers["host"] = UPSTREAM_HOST

        remove_header_case_insensitive(flow.request.headers, "authorization")
        flow.request.headers["x-api-key"] = api_key

        flow.metadata["chatbaz_cursor_rewritten"] = True
        flow.metadata["chatbaz_cursor_request_id"] = request_id
        self.logger.info(
            f"Rewrote request #{request_id}: {INTERCEPT_HOST}{original_path} -> {UPSTREAM_HOST}{rewritten_path}"
        )

    def response(self, flow: http.HTTPFlow) -> None:
        if not flow.metadata.get("chatbaz_cursor_rewritten"):
            return

        request_id = flow.metadata.get("chatbaz_cursor_request_id", "?")
        if flow.response is None:
            return

        status = flow.response.status_code
        if status >= 500:
            self.logger.error(f"Upstream response #{request_id}: {status}")
        elif status >= 400:
            self.logger.warning(f"Upstream response #{request_id}: {status}")
        else:
            self.logger.debug(f"Upstream response #{request_id}: {status}")


addon_instance = None
addons = []


def cmd_set_key(args: argparse.Namespace) -> int:
    logger = setup_logger(args.verbose)
    storage = CredentialStorage()

    if args.api_key:
        api_key = args.api_key.strip()
    else:
        console.print(
            Panel.fit(
                f"[bold cyan]{APP_NAME} - API Key Setup[/bold cyan]",
                border_style="cyan",
            )
        )
        api_key = getpass.getpass("Enter ChatBAZ API key: ").strip()

    if not validate_api_key(api_key):
        console.print("[red]Invalid API key. Expected at least 10 characters.[/red]")
        return 1

    storage.save(api_key)
    logger.info("API key saved")

    console.print(
        Panel.fit(
            "[bold green]API key saved successfully[/bold green]\n\n"
            f"Location: [cyan]{CREDENTIAL_FILE}[/cyan]\n"
            f"Stored key: [yellow]{storage.get_masked_key()}[/yellow]\n\n"
            "Start proxy with:\n"
            "[bold]  python chatbaz-cursor-proxy.py start[/bold]",
            border_style="green",
        )
    )

    return 0


async def cmd_test(args: argparse.Namespace) -> int:
    logger = setup_logger(args.verbose)
    storage = CredentialStorage()

    console.print(
        Panel.fit(
            f"[bold cyan]{APP_NAME} - Connection Test[/bold cyan]",
            border_style="cyan",
        )
    )

    if not storage.has_key():
        console.print("[red]No API key configured[/red]")
        console.print("Run: [bold]python chatbaz-cursor-proxy.py set-key[/bold]")
        return 1

    api_key = storage.get_key()
    if not api_key:
        console.print("[red]Stored API key is unreadable[/red]")
        return 1

    console.print(f"[green]API key found:[/green] {storage.get_masked_key()}")
    console.print("[yellow]Testing ChatBAZ upstream...[/yellow]")

    test_url = f"{UPSTREAM_SCHEME}://{UPSTREAM_HOST}{UPSTREAM_PREFIX}/v1/models"

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                test_url,
                headers={
                    "x-api-key": api_key,
                },
            )

        if response.status_code == 200:
            console.print("[green]Connection OK: ChatBAZ upstream accepted credentials[/green]")
            return 0

        console.print(f"[red]Upstream returned {response.status_code}[/red]")
        preview = response.text[:300].strip()
        if preview:
            console.print(f"[dim]{preview}[/dim]")
        return 1
    except Exception as e:
        logger.exception("Test command failed")
        console.print(f"[red]Connection test failed: {e}[/red]")
        return 1


def start_proxy(args: argparse.Namespace) -> int:
    logger = setup_logger(args.verbose)
    storage = CredentialStorage()

    if not storage.has_key():
        console.print(
            Panel.fit(
                "[bold red]No API key configured[/bold red]\n\n"
                "Configure key first:\n"
                "[bold]  python chatbaz-cursor-proxy.py set-key[/bold]",
                border_style="red",
            )
        )
        return 1

    console.print(Panel.fit(f"[bold cyan]{APP_NAME} Proxy v{VERSION}[/bold cyan]", border_style="cyan"))
    console.print(f"[green]API key loaded:[/green] {storage.get_masked_key()}")
    console.print(f"[green]Proxy listening on[/green] [bold]127.0.0.1:{args.port}[/bold]")
    console.print(f"[dim]Logs: {LOG_FILE}[/dim]")
    console.print("━" * 50)
    console.print(f"Intercepting [cyan]{INTERCEPT_HOST}[/cyan]")
    console.print(
        f"Forwarding to [cyan]{UPSTREAM_SCHEME}://{UPSTREAM_HOST}{UPSTREAM_PREFIX}[/cyan]"
    )
    console.print("[dim]Press Ctrl+C to stop[/dim]")
    console.print("━" * 50)

    logger.info(f"Starting {APP_NAME} proxy on port {args.port}")

    global addon_instance, addons
    addon_instance = ChatBAZCursorAddon(storage, logger)
    addons = [addon_instance]

    sys.argv = [
        "mitmdump",
        "-s",
        __file__,
        "--listen-port",
        str(args.port),
        "--set",
        "confdir=~/.mitmproxy",
    ]

    if not args.verbose:
        sys.argv.extend(["--set", "termlog_verbosity=error"])

    try:
        mitmdump()
    except KeyboardInterrupt:
        console.print("\n[yellow]Proxy stopped[/yellow]")
        logger.info("Proxy stopped by user")

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ChatBAZ Cursor Proxy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python chatbaz-cursor-proxy.py set-key
  python chatbaz-cursor-proxy.py start
  python chatbaz-cursor-proxy.py start --port 9090
  python chatbaz-cursor-proxy.py test
        """,
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    set_key_parser = subparsers.add_parser("set-key", help="Store ChatBAZ API key")
    set_key_parser.add_argument(
        "--api-key",
        help="Set API key non-interactively (warning: shell history exposure)",
    )
    set_key_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    start_parser = subparsers.add_parser("start", help="Start proxy server")
    start_parser.add_argument(
        "--port", "-p", type=int, default=8080, help="Proxy port (default: 8080)"
    )
    start_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    test_parser = subparsers.add_parser("test", help="Test ChatBAZ connectivity")
    test_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if not args.command:
        args.command = "start"
        if not hasattr(args, "port"):
            args.port = 8080
        if not hasattr(args, "verbose"):
            args.verbose = False

    return args


def main() -> None:
    args = parse_args()

    if args.command == "set-key":
        raise SystemExit(cmd_set_key(args))
    if args.command == "test":
        import asyncio

        raise SystemExit(asyncio.run(cmd_test(args)))
    if args.command == "start":
        raise SystemExit(start_proxy(args))

    raise SystemExit(1)


if __name__ == "__main__":
    main()
