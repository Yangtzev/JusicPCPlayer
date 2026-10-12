"""Regression tests for custom server routing and saved addresses."""
import asyncio
import json
import os
import queue
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import websockets
from jusic_core import RoomClient, api_post, get_rooms, room_share_url
from jusic_server import DEFAULT_SERVER, ServerAddress, load_server_settings, save_server_settings


class ServerSettingsTests(unittest.TestCase):
    def test_public_server_and_custom_protocols(self):
        self.assertEqual(ServerAddress.parse("tx.alang.run").base_url, DEFAULT_SERVER)
        direct = ServerAddress.from_fields("192.168.1.10", "8080", "http", "")
        self.assertEqual(direct.base_url, "http://192.168.1.10:8080")
        self.assertEqual(direct.path("house/search"), "/house/search")
        self.assertEqual(direct.websocket_url("server/000/session/websocket"),
                         "ws://192.168.1.10:8080/server/000/session/websocket")
        proxy = ServerAddress.from_fields("music.example.com", "8443", "https", "/music/api/")
        self.assertEqual(proxy.path("house/search"), "/music/api/house/search")
        self.assertEqual(proxy.websocket_url("server/000/session/websocket"),
                         "wss://music.example.com:8443/music/api/server/000/session/websocket")
        self.assertEqual(ServerAddress.from_fields("::1", "8080").base_url, "http://[::1]:8080")

    def test_reject_invalid_addresses_before_connecting(self):
        for address in ("", "ftp://example.com", "http://host:0", "http://host:65536",
                        "http://host:abc", "http://user:pass@host", "http://host?token=x",
                        "http://host/#fragment", "http://host/a/../b", "http://bad host"):
            with self.subTest(address=address), self.assertRaises(ValueError):
                ServerAddress.parse(address)
        for port in ("0", "65536", "abc", "-1"):
            with self.subTest(port=port), self.assertRaises(ValueError):
                ServerAddress.from_fields("localhost", port)

    def test_save_reload_history_and_corrupt_config(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {"APPDATA": folder}):
            self.assertEqual(load_server_settings(), {})
            save_server_settings("http://localhost:8080", [DEFAULT_SERVER])
            history = save_server_settings(DEFAULT_SERVER, ["http://localhost:8080", DEFAULT_SERVER])
            self.assertEqual(history, [DEFAULT_SERVER, "http://localhost:8080"])
            self.assertEqual(load_server_settings(), {"server": DEFAULT_SERVER, "history": history})
            from jusic_server import server_settings_path
            with open(server_settings_path(), "w", encoding="utf-8") as fh:
                fh.write("broken config")
            self.assertEqual(load_server_settings(), {})

    def test_rest_reaches_real_http_server_with_configured_prefix(self):
        received = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                received.append((self.path, self.headers.get("Origin")))
                body = json.dumps({"code": 20000, "data": [{"id": "DEFAULT", "name": "test"}]}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            def log_message(self, *_args):
                pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        origin = f"http://127.0.0.1:{server.server_port}"
        try:
            self.assertEqual(get_rooms(origin)[0]["id"], "DEFAULT")
            self.assertEqual(get_rooms(origin + "/music/api")[0]["id"], "DEFAULT")
            self.assertEqual(received, [("/house/search", origin), ("/music/api/house/search", origin)])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(3)

    def test_https_uses_custom_port_and_prefix(self):
        with patch("jusic_core.http.client.HTTPSConnection") as connection:
            connection.return_value.getresponse.return_value.status = 200
            connection.return_value.getresponse.return_value.read.return_value = b"{}"
            api_post("https://music.example.com:8443/api", "/house/search", {})
            self.assertEqual(connection.call_args.args, ("music.example.com", 8443))
            self.assertEqual(connection.return_value.request.call_args.args[:2], ("POST", "/api/house/search"))
            self.assertTrue(connection.call_args.kwargs["context"].check_hostname)

    def test_websocket_connects_and_encodes_room_password(self):
        async def scenario():
            incoming = asyncio.Queue()
            async def handler(ws):
                await incoming.put((ws.request.path, ws.request.headers["Origin"], await ws.recv()))
                await ws.wait_closed()
            async with websockets.serve(handler, "127.0.0.1", 0) as server:
                port = server.sockets[0].getsockname()[1]
                for prefix in ("", "/api"):
                    with self.subTest(prefix=prefix):
                        client = RoomClient(host=f"http://127.0.0.1:{port}{prefix}")
                        client.start()
                        try:
                            client.enter_room("room & test", "password&=+#")
                            path, origin, message = await asyncio.wait_for(incoming.get(), 5)
                            self.assertTrue(path.startswith(prefix + "/server/000/"))
                            self.assertEqual(origin, f"http://127.0.0.1:{port}")
                            self.assertEqual(parse_qs(urlsplit(path).query), {
                                "houseId": ["room & test"], "housePwd": ["password&=+#"], "connectType": ["enter"]})
                            self.assertTrue(json.loads(message)[0].startswith("CONNECT"))
                        finally:
                            await asyncio.to_thread(client.stop)
                        self.assertFalse(client._thread.is_alive())
                        client.engine._ipc_thread.join(1)
                        self.assertFalse(client.engine._ipc_thread.is_alive())
                        self.assertFalse(client.engine.play("https://example.com/late.mp3"))
        asyncio.run(scenario())

    def test_share_uses_selected_server(self):
        self.assertTrue(room_share_url("DEFAULT").startswith("https://happy.alang.run/modern-ui?"))
        self.assertEqual(room_share_url("DEFAULT", "a&b", "http://localhost:8080"),
                         "http://localhost:8080?houseId=DEFAULT&housePwd=a%26b")


if __name__ == "__main__":
    unittest.main()
