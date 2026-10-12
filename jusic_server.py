# SPDX-License-Identifier: GPL-3.0-only
"""Server addresses shared by REST, WebSocket and both desktop interfaces."""
import json
import os
import re
from dataclasses import dataclass
from urllib.parse import urlsplit

DEFAULT_SERVER = "https://tx.alang.run/api"


@dataclass(frozen=True)
class ServerAddress:
    scheme: str
    hostname: str
    port: int | None = None
    prefix: str = ""

    @classmethod
    def parse(cls, address):
        text = str(address or "").strip()
        if not text:
            raise ValueError("请输入服务器 IP 或域名")
        # Keep the existing --host domain-only syntax compatible with the public API.
        if "://" not in text:
            text = "https://" + text.rstrip("/") + "/api"
        try:
            parts = urlsplit(text)
            port = parts.port
        except ValueError as exc:
            raise ValueError("服务器地址或端口格式错误") from exc
        if parts.scheme not in ("http", "https"):
            raise ValueError("协议只能选择 HTTP 或 HTTPS")
        if (not parts.hostname or parts.username is not None or parts.password is not None
                or parts.query or parts.fragment or any(c.isspace() for c in text)
                or "\\" in text):
            raise ValueError("请输入有效服务器地址，不要包含账号、查询参数或空格")
        if port is not None and not 1 <= port <= 65535:
            raise ValueError("端口必须是 1 到 65535 的数字")
        prefix = parts.path.rstrip("/")
        if not re.fullmatch(r"[/A-Za-z0-9_.~%-]*", prefix) or any(
                segment in (".", "..") for segment in prefix.split("/")):
            raise ValueError("API 路径格式错误，例如 /api；直接部署时留空")
        return cls(parts.scheme, parts.hostname, port, prefix)

    @classmethod
    def from_fields(cls, hostname, port="", scheme="http", prefix=""):
        hostname, port, prefix = hostname.strip(), port.strip(), prefix.strip()
        if not hostname or any(c in hostname for c in "/?#@"):
            raise ValueError("IP / 域名只填写主机地址，端口填写在下方端口栏")
        if port and (not port.isascii() or not port.isdecimal()):
            raise ValueError("端口必须是 1 到 65535 的数字")
        host = hostname if hostname.startswith("[") or ":" not in hostname else f"[{hostname}]"
        return cls.parse(f"{scheme}://{host}" + (f":{port}" if port else "")
                         + ("/" + prefix.lstrip("/") if prefix else ""))

    @property
    def authority(self):
        host = f"[{self.hostname}]" if ":" in self.hostname else self.hostname
        return host + (f":{self.port}" if self.port is not None else "")

    @property
    def origin(self):
        return f"{self.scheme}://{self.authority}"

    @property
    def base_url(self):
        return self.origin + self.prefix

    def path(self, route):
        return self.prefix + "/" + route.lstrip("/")

    def websocket_url(self, route):
        scheme = "wss" if self.scheme == "https" else "ws"
        return f"{scheme}://{self.authority}{self.path(route)}"


def server_settings_path():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "JusicRoomPlayer", "server.json")


def load_server_settings():
    try:
        with open(server_settings_path(), encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return {}
        current = ServerAddress.parse(data.get("server")).base_url
        raw_history = data.get("history", [])
        history = []
        for value in raw_history if isinstance(raw_history, list) else []:
            try:
                url = ServerAddress.parse(value).base_url
                if url not in history:
                    history.append(url)
            except ValueError:
                continue
        return {"server": current, "history": history[:10]}
    except (OSError, ValueError, TypeError):
        return {}


def save_server_settings(server, history):
    url = ServerAddress.parse(server).base_url
    recent = list(dict.fromkeys([url, *history]))[:10]
    path = server_settings_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as fh:
        json.dump({"server": url, "history": recent}, fh, ensure_ascii=False, indent=2)
    os.replace(temporary, path)
    return recent
