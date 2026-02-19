import importlib.util
import logging
import sys
import types
import unittest
from pathlib import Path


def _install_dependency_stubs() -> None:
    if "httpx" not in sys.modules:
        httpx_mod = types.ModuleType("httpx")

        class AsyncClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def get(self, *args, **kwargs):
                raise RuntimeError("httpx stub: network not available in tests")

        httpx_mod.AsyncClient = AsyncClient
        sys.modules["httpx"] = httpx_mod

    if "rich" not in sys.modules:
        rich_mod = types.ModuleType("rich")
        rich_mod.print = print
        sys.modules["rich"] = rich_mod

        console_mod = types.ModuleType("rich.console")

        class Console:
            def print(self, *args, **kwargs):
                return None

        console_mod.Console = Console
        sys.modules["rich.console"] = console_mod

        panel_mod = types.ModuleType("rich.panel")

        class Panel:
            @staticmethod
            def fit(text, border_style=None):
                return text

        panel_mod.Panel = Panel
        sys.modules["rich.panel"] = panel_mod

    if "mitmproxy" not in sys.modules:
        mitmproxy_mod = types.ModuleType("mitmproxy")
        http_mod = types.ModuleType("mitmproxy.http")

        class DummyResponse:
            def __init__(self, status_code, content, headers):
                self.status_code = status_code
                self.content = content
                self.headers = headers

            @staticmethod
            def make(status_code, content, headers):
                return DummyResponse(status_code, content, headers)

        http_mod.Response = DummyResponse
        http_mod.HTTPFlow = object
        mitmproxy_mod.http = http_mod

        tools_mod = types.ModuleType("mitmproxy.tools")
        tools_main_mod = types.ModuleType("mitmproxy.tools.main")

        def mitmdump():
            return None

        tools_main_mod.mitmdump = mitmdump

        sys.modules["mitmproxy"] = mitmproxy_mod
        sys.modules["mitmproxy.http"] = http_mod
        sys.modules["mitmproxy.tools"] = tools_mod
        sys.modules["mitmproxy.tools.main"] = tools_main_mod


_install_dependency_stubs()

MODULE_PATH = Path(__file__).resolve().parent.parent / "chatbaz-cursor-proxy.py"
spec = importlib.util.spec_from_file_location("chatbaz_cursor_proxy", MODULE_PATH)
proxy = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(proxy)


class FakeRequest:
    def __init__(self, host, path, headers=None):
        self.host = host
        self.path = path
        self.headers = headers or {}
        self.scheme = "http"
        self.port = 80


class FakeFlow:
    def __init__(self, host, path, headers=None):
        self.request = FakeRequest(host, path, headers=headers)
        self.response = None
        self.metadata = {}


class ChatBAZCursorProxyTests(unittest.TestCase):
    def test_build_upstream_path(self):
        self.assertEqual(proxy.build_upstream_path("/v1/messages"), "/claude/v1/messages")
        self.assertEqual(
            proxy.build_upstream_path("v1/messages?stream=true"),
            "/claude/v1/messages?stream=true",
        )
        self.assertEqual(proxy.build_upstream_path("/claude/v1/models"), "/claude/v1/models")

    def test_addon_rewrites_and_preserves_incoming_x_api_key(self):
        logger = logging.getLogger("test-addon-rewrite")
        logger.handlers = []
        logger.addHandler(logging.NullHandler())

        addon = proxy.ChatBAZCursorAddon(logger)
        flow = FakeFlow(
            "api.anthropic.com",
            "/v1/messages?stream=true",
            headers={
                "x-api-key": "incoming-key-123",
                "custom-header": "keep-me",
            },
        )

        addon.request(flow)

        self.assertEqual(flow.request.host, "chatbaz.app")
        self.assertEqual(flow.request.scheme, "https")
        self.assertEqual(flow.request.port, 443)
        self.assertEqual(flow.request.path, "/claude/v1/messages?stream=true")
        self.assertEqual(flow.request.headers.get("host"), "chatbaz.app")
        self.assertEqual(flow.request.headers.get("x-api-key"), "incoming-key-123")
        self.assertEqual(flow.request.headers.get("custom-header"), "keep-me")
        self.assertTrue(flow.metadata.get("chatbaz_cursor_rewritten"))

    def test_addon_rewrites_even_when_x_api_key_missing(self):
        logger = logging.getLogger("test-addon-no-key")
        logger.handlers = []
        logger.addHandler(logging.NullHandler())

        addon = proxy.ChatBAZCursorAddon(logger)
        flow = FakeFlow("api.anthropic.com", "/v1/messages", headers={})

        addon.request(flow)

        self.assertIsNone(flow.response)
        self.assertEqual(flow.request.host, "chatbaz.app")
        self.assertEqual(flow.request.path, "/claude/v1/messages")
        self.assertNotIn("x-api-key", flow.request.headers)


if __name__ == "__main__":
    unittest.main()
