#!/usr/bin/env python3
"""
OpenClaw Insights Server
本地 HTTP 服务，同时提供 report.html 和 Config API
用法: python3 server.py [port]
"""

import json
import os
import sys
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import traceback

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 18800

# 懒加载 config_api，确保路径正确
sys.path.insert(0, SCRIPT_DIR)
import config_api
import analyze
import render as render_module

# 缓存 data.json 内容，避免每次请求都读磁盘
_cached_data = None


def _load_data():
    global _cached_data
    data_path = os.path.join(SCRIPT_DIR, "data.json")
    with open(data_path, encoding="utf-8") as f:
        _cached_data = json.load(f)
    return _cached_data


def _get_data():
    global _cached_data
    if _cached_data is None:
        _load_data()
    return _cached_data


def detect_lang(handler):
    """检测语言：1) URL ?lang= 参数；2) Accept-Language；3) 系统 LANG"""
    qs = parse_qs(urlparse(handler.path).query)
    if "lang" in qs:
        return qs["lang"][0] if qs["lang"][0] in ("zh", "en") else "zh"
    accept_language = handler.headers.get("Accept-Language", "").lower()
    for token in [part.strip() for part in accept_language.split(",") if part.strip()]:
        if token.startswith("en"):
            return "en"
        if token.startswith("zh"):
            return "zh"
    system_lang = os.environ.get("LANG", "")
    if system_lang.lower().startswith("en"):
        return "en"
    return "zh"


def json_response(handler, data: dict, status: int = 200):
    body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(body)


def html_response(handler, html: str):
    body = html.encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def read_body(handler) -> dict:
    length = int(handler.headers.get("Content-Length", 0))
    if length == 0:
        return {}
    raw = handler.rfile.read(length)
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return {}


class Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"  {self.command} {self.path} → {args[1] if len(args) > 1 else ''}")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        try:
            self._handle_get()
        except Exception as e:
            traceback.print_exc()
            json_response(self, {"error": str(e)}, 500)

    def do_POST(self):
        try:
            self._handle_post()
        except Exception as e:
            traceback.print_exc()
            json_response(self, {"error": str(e)}, 500)

    def do_PATCH(self):
        try:
            self._handle_patch()
        except Exception as e:
            traceback.print_exc()
            json_response(self, {"error": str(e)}, 500)

    def do_PUT(self):
        try:
            self._handle_put()
        except Exception as e:
            traceback.print_exc()
            json_response(self, {"error": str(e)}, 500)

    def _handle_get(self):
        path = urlparse(self.path).path.rstrip("/")

        # 主页 — 动态按语言渲染
        if path in ("", "/"):
            data_path = os.path.join(SCRIPT_DIR, "data.json")
            if not os.path.exists(data_path):
                json_response(self, {"error": "data.json not found, run analyze.py first"}, 404)
                return
            lang = detect_lang(self)
            html = render_module.build_html(_get_data(), lang)
            html_response(self, html)
            return

        # ── 全局配置 ──
        if path == "/api/config/global/cron":
            json_response(self, config_api.get_global_cron())
        elif path == "/api/config/global/models":
            json_response(self, config_api.get_global_models())
        elif path == "/api/config/global/acp":
            json_response(self, config_api.get_global_acp())
        elif path == "/api/config/global/gateway":
            json_response(self, config_api.get_global_gateway())
        elif path == "/api/config/global/channels":
            json_response(self, config_api.get_global_channels())
        elif path == "/api/config/global/skills":
            json_response(self, config_api.get_global_skills())
        elif path == "/api/config/global/defaults":
            json_response(self, config_api.get_global_defaults())

        # Skill 内容
        elif path.startswith("/api/config/global/skills/"):
            skill_name = path.split("/api/config/global/skills/")[1]
            json_response(self, config_api.get_skill_content(skill_name))

        # ── Agent 配置 ──
        elif path.startswith("/api/config/agent/"):
            parts = path.split("/")
            # /api/config/agent/{id}
            if len(parts) == 5:
                agent_id = parts[4]
                json_response(self, config_api.get_agent_config(agent_id))
            # /api/config/agent/{id}/{file}
            elif len(parts) == 6:
                agent_id = parts[4]
                file_key = parts[5]
                if file_key == "models":
                    json_response(self, config_api.get_agent_models(agent_id))
                elif file_key == "auth":
                    json_response(self, config_api.get_agent_auth(agent_id))
                else:
                    json_response(self, config_api.get_agent_file(agent_id, file_key))
            else:
                json_response(self, {"error": "invalid path"}, 400)

        # 刷新数据（重新分析，清除缓存）
        elif path == "/api/refresh":
            global _cached_data
            data = analyze.main()
            _cached_data = data
            json_response(self, {"success": True, "sessions": data["at_a_glance"]["total_sessions"]})

        else:
            json_response(self, {"error": f"not found: {path}"}, 404)

    def _handle_post(self):
        path = urlparse(self.path).path.rstrip("/")

        if path == "/api/gateway/restart":
            result = config_api.restart_gateway()
            json_response(self, result)
        else:
            json_response(self, {"error": "not found"}, 404)

    def _handle_patch(self):
        path = urlparse(self.path).path.rstrip("/")
        body = read_body(self)

        if path == "/api/config/global/acp":
            json_response(self, config_api.patch_global_acp(body))
        elif path == "/api/config/global/gateway":
            json_response(self, config_api.patch_global_gateway(body))
        elif path.startswith("/api/config/global/cron/"):
            job_id = path.split("/api/config/global/cron/")[1]
            json_response(self, config_api.patch_cron_job(job_id, body))
        elif path.startswith("/api/config/global/models/"):
            provider_id = path.split("/api/config/global/models/")[1]
            json_response(self, config_api.patch_global_models(provider_id, body))
        elif path == "/api/config/global/defaults":
            json_response(self, config_api.patch_global_defaults(body))
        elif "/accounts/" in path and path.startswith("/api/config/global/channels/"):
            parts = path.split("/")
            if len(parts) == 8 and parts[6] == "accounts":
                channel_name = parts[5]
                account_name = parts[7]
                json_response(self, config_api.patch_global_channel_account(channel_name, account_name, body))
            else:
                json_response(self, {"error": "invalid channel account patch path"}, 400)
        elif path.startswith("/api/config/global/channels/"):
            ch = path.split("/api/config/global/channels/")[1]
            json_response(self, config_api.patch_global_channel(ch, body))
        elif path.startswith("/api/config/agent/"):
            parts = path.split("/")
            # /api/config/agent/{id}/models/{provider_id}
            if len(parts) == 7 and parts[5] == "models":
                agent_id = parts[4]
                provider_id = parts[6]
                json_response(self, config_api.patch_agent_models(agent_id, provider_id, body))
            # /api/config/agent/{id}/auth/{profile_id}
            elif len(parts) == 7 and parts[5] == "auth":
                agent_id = parts[4]
                profile_id = parts[6]
                json_response(self, config_api.patch_agent_auth(agent_id, profile_id, body))
            else:
                json_response(self, {"error": "invalid patch path"}, 400)
        else:
            json_response(self, {"error": "not found"}, 404)

    def _handle_put(self):
        path = urlparse(self.path).path.rstrip("/")
        body = read_body(self)

        # /api/config/agent/{id}/{file}
        if path.startswith("/api/config/agent/"):
            parts = path.split("/")
            if len(parts) == 6:
                agent_id = parts[4]
                file_key = parts[5]
                content = body.get("content", "")
                json_response(self, config_api.put_agent_file(agent_id, file_key, content))
            else:
                json_response(self, {"error": "invalid path"}, 400)
        else:
            json_response(self, {"error": "not found"}, 404)


def main():
    # 首次启动时生成数据
    data_path = os.path.join(SCRIPT_DIR, "data.json")
    if not os.path.exists(data_path):
        print("首次启动，正在生成数据...")
        analyze.main()
    _load_data()

    server = HTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://localhost:{PORT}"
    print(f"OpenClaw Insights Server 启动")
    print(f"访问地址: {url}")
    print(f"按 Ctrl+C 停止")
    print()

    # 自动打开浏览器（跨平台）
    try:
        import webbrowser
        webbrowser.open(url)
    except Exception:
        pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")


if __name__ == "__main__":
    main()
