#!/usr/bin/env python3
"""
ChatBAZ Cursor Proxy

Intercepts Cursor IDE requests targeting api.anthropic.com and rewrites them to
chatbaz.app/claude while preserving incoming x-api-key headers.

Usage:
    python chatbaz-cursor-proxy.py start
    python chatbaz-cursor-proxy.py test --api-key <KEY>
"""

import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

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


VERSION = "1.1.0"
APP_NAME = "ChatBAZ Cursor"
LOGGER_NAME = "chatbaz-cursor-proxy"

INTERCEPT_HOST = "api.anthropic.com"
UPSTREAM_HOST = "chatbaz.app"
UPSTREAM_SCHEME = "https"
UPSTREAM_PORT = 443
UPSTREAM_PREFIX = "/claude"

STORAGE_DIR = Path.home() / ".chatbaz-cursor"
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


def ensure_leading_slash(path: str) -> str:
    if not path:
        return "/"
    return path if path.startswith("/") else f"/{path}"


def build_upstream_path(original_path: str) -> str:
    path = ensure_leading_slash(original_path)
    if path == UPSTREAM_PREFIX or path.startswith(f"{UPSTREAM_PREFIX}/"):
        return path
    return f"{UPSTREAM_PREFIX}{path}"


def has_x_api_key(headers: Any) -> bool:
    value = headers.get("x-api-key", "")
    return isinstance(value, str) and bool(value.strip())


class ChatBAZCursorAddon:
    """mitmproxy addon that rewrites source host traffic to ChatBAZ."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.request_count = 0

    def request(self, flow: http.HTTPFlow) -> None:
        if flow.request.host != INTERCEPT_HOST:
            return

        self.request_count += 1
        request_id = self.request_count

        original_path = flow.request.path
        rewritten_path = build_upstream_path(original_path)

        flow.request.scheme = UPSTREAM_SCHEME
        flow.request.host = UPSTREAM_HOST
        flow.request.port = UPSTREAM_PORT
        flow.request.path = rewritten_path
        flow.request.headers["host"] = UPSTREAM_HOST

        key_present = has_x_api_key(flow.request.headers)
        if not key_present:
            self.logger.warning(f"Request #{request_id} forwarded without x-api-key")

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


addons = []


async def cmd_test(args: argparse.Namespace) -> int:
    logger = setup_logger(args.verbose)

    console.print(
        Panel.fit(
            f"[bold cyan]{APP_NAME} - Connection Test[/bold cyan]",
            border_style="cyan",
        )
    )

    if not args.api_key or not args.api_key.strip():
        console.print("[red]test command requires --api-key[/red]")
        return 1

    console.print("[yellow]Testing ChatBAZ upstream...[/yellow]")
    test_url = f"{UPSTREAM_SCHEME}://{UPSTREAM_HOST}{UPSTREAM_PREFIX}/v1/models"

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                test_url,
                headers={
                    "x-api-key": args.api_key.strip(),
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

    console.print(Panel.fit(f"[bold cyan]{APP_NAME} Proxy v{VERSION}[/bold cyan]", border_style="cyan"))
    console.print(f"[green]Proxy listening on[/green] [bold]127.0.0.1:{args.port}[/bold]")
    console.print(f"[dim]Logs: {LOG_FILE}[/dim]")
    console.print("━" * 50)
    console.print(f"Intercepting [cyan]{INTERCEPT_HOST}[/cyan]")
    console.print(
        f"Forwarding to [cyan]{UPSTREAM_SCHEME}://{UPSTREAM_HOST}{UPSTREAM_PREFIX}[/cyan]"
    )
    console.print("Passing through incoming [cyan]x-api-key[/cyan] header")
    console.print("[dim]Press Ctrl+C to stop[/dim]")
    console.print("━" * 50)

    logger.info(f"Starting {APP_NAME} proxy on port {args.port}")

    global addons
    addons = [ChatBAZCursorAddon(logger)]

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
  python chatbaz-cursor-proxy.py start
  python chatbaz-cursor-proxy.py start --port 9090
  python chatbaz-cursor-proxy.py test --api-key <KEY>
        """,
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    start_parser = subparsers.add_parser("start", help="Start proxy server")
    start_parser.add_argument(
        "--port", "-p", type=int, default=8080, help="Proxy port (default: 8080)"
    )
    start_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    test_parser = subparsers.add_parser("test", help="Test ChatBAZ connectivity")
    test_parser.add_argument("--api-key", required=True, help="x-api-key value for test request")
    test_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if not args.command:
        args.command = "start"
        args.port = 8080
        args.verbose = False

    return args


def main() -> None:
    args = parse_args()

    if args.command == "test":
        import asyncio

        raise SystemExit(asyncio.run(cmd_test(args)))
    if args.command == "start":
        raise SystemExit(start_proxy(args))

    raise SystemExit(1)


if __name__ == "__main__":
    main()
