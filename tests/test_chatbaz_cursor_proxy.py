import importlib.util
import logging
import os
import sys
import tempfile
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

    def test_credential_storage_permissions(self):
        with tempfile.TemporaryDirectory() as td:
            cred_path = Path(td) / "credentials.json"
            storage = proxy.CredentialStorage(storage_path=cred_path)
            storage.save("test-api-key-12345")

            self.assertTrue(cred_path.exists())
            mode = os.stat(cred_path).st_mode & 0o777
            self.assertEqual(mode, 0o600)

            loaded = storage.load()
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded["api_key"], "test-api-key-12345")

    def test_addon_rewrites_request(self):
        with tempfile.TemporaryDirectory() as td:
            cred_path = Path(td) / "credentials.json"
            storage = proxy.CredentialStorage(storage_path=cred_path)
            storage.save("chatbaz-test-key-12345")

            logger = logging.getLogger("test-addon-rewrite")
            logger.handlers = []
            logger.addHandler(logging.NullHandler())

            addon = proxy.ChatBAZCursorAddon(storage, logger)
            flow = FakeFlow(
                "api.anthropic.com",
                "/v1/messages?stream=true",
                headers={
                    "authorization": "Bearer old-token",
                    "custom-header": "keep-me",
                },
            )

            addon.request(flow)

            self.assertEqual(flow.request.host, "chatbaz.app")
            self.assertEqual(flow.request.scheme, "https")
            self.assertEqual(flow.request.port, 443)
            self.assertEqual(flow.request.path, "/claude/v1/messages?stream=true")
            self.assertEqual(flow.request.headers["x-api-key"], "chatbaz-test-key-12345")
            self.assertNotIn("authorization", flow.request.headers)
            self.assertEqual(flow.request.headers.get("custom-header"), "keep-me")
            self.assertTrue(flow.metadata.get("chatbaz_cursor_rewritten"))

    def test_addon_blocks_when_key_missing(self):
        with tempfile.TemporaryDirectory() as td:
            cred_path = Path(td) / "credentials.json"
            storage = proxy.CredentialStorage(storage_path=cred_path)

            logger = logging.getLogger("test-addon-missing-key")
            logger.handlers = []
            logger.addHandler(logging.NullHandler())

            addon = proxy.ChatBAZCursorAddon(storage, logger)
            flow = FakeFlow("api.anthropic.com", "/v1/messages", headers={})

            addon.request(flow)

            self.assertIsNotNone(flow.response)
            self.assertEqual(flow.response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
