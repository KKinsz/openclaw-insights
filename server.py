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


def detect_environment() -> str:
    """检测当前运行环境。

    返回值:
        "ssh"      — SSH 远程会话（优先级最高）
        "desktop"  — 本地桌面环境（macOS 或有图形界面的 Linux）
        "headless" — 无图形界面的纯终端环境
    """
    # SSH 会话优先：存在 SSH_CLIENT 或 SSH_TTY 环境变量
    if os.environ.get("SSH_CLIENT") or os.environ.get("SSH_TTY"):
        return "ssh"
    # macOS 本地终端
    if sys.platform == "darwin":
        return "desktop"
    # Linux 有图形界面
    if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
        return "desktop"
    return "headless"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PORT = 18800

# 懒加载 config_api，确保路径正确
sys.path.insert(0, SCRIPT_DIR)
import config_api
import analyze
import render as render_module

# 缓存 data.json 内容，避免每次请求都读磁盘
_cached_data = None

# 启动时缓存系统语言，避免每次请求调用子进程
_system_lang_cache: str = ""


def build_summary_dict(data: dict) -> dict:
    """从 data.json 提取关键指标，与网页 Dashboard 展示内容保持一致。"""
    g = data.get("at_a_glance", {})
    cron = data.get("cron", {})
    active_agents = g.get("active_agent_count")
    if active_agents is None:
        active_agents = len(g.get("active_agents", []))
    model_count = g.get("model_count", len(data.get("models", [])))
    skills_count = g.get("skills_count", data.get("skills", {}).get("total", 0))
    cron_job_count = g.get("cron_job_count", cron.get("total_jobs", 0))
    success_rate = cron.get("overall_success_rate")
    cron_success_rate_pct = round(success_rate * 100, 1) if success_rate is not None else None
    return {
        "total_sessions": g.get("total_sessions", 0),
        "active_agents": active_agents,
        "total_tokens": g.get("total_tokens", 0),
        "daily_avg_tokens": g.get("daily_avg_tokens", 0),
        "skills_count": skills_count,
        "cron_job_count": cron_job_count,
        "model_count": model_count,
        "active_days": g.get("active_days", 0),
        "cron_success_rate_pct": cron_success_rate_pct,
    }


def build_summary_text(data: dict) -> str:
    """生成人类可读的摘要文本（--summary 模式）。"""
    s = build_summary_dict(data)
    cron_rate = f"{s['cron_success_rate_pct']}%" if s["cron_success_rate_pct"] is not None else "N/A"
    lines = [
        "=== OpenClaw Insights ===",
        f"Sessions:       {s['total_sessions']}  (活跃天数: {s['active_days']})",
        f"Token 消耗:     {s['total_tokens']:,}  (日均: {s['daily_avg_tokens']:,})",
        f"活跃 Agent:     {s['active_agents']} 个",
        f"Skill 数量:     {s['skills_count']}",
        f"Cron 数量:      {s['cron_job_count']}  (成功率: {cron_rate})",
        f"模型数量:       {s['model_count']}",
    ]
    return "\n".join(lines)


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


def _init_system_lang():
    global _system_lang_cache
    _system_lang_cache = _detect_system_lang()


def _detect_system_lang() -> str:
    """检测系统语言，返回 'zh'、'en' 或 ''（未知）。
    优先读取 macOS UI 语言，再回退到 LANG 环境变量。"""
    if sys.platform == "darwin":
        try:
            import subprocess as _sp
            out = _sp.check_output(
                ["defaults", "read", "NSGlobalDomain", "AppleLanguages"],
                stderr=_sp.DEVNULL, text=True, timeout=2,
            )
            first = next((t.strip().strip('"') for t in out.splitlines() if t.strip().strip('"').isalpha() is False and len(t.strip().strip('"')) >= 2), "")
            if first.lower().startswith("zh"):
                return "zh"
            if first.lower().startswith("en"):
                return "en"
        except Exception:
            pass
    env_lang = os.environ.get("LANG", "")
    if env_lang.lower().startswith("zh"):
        return "zh"
    if env_lang.lower().startswith("en"):
        return "en"
    return ""


def detect_lang(handler):
    """检测语言：1) URL ?lang= 参数；2) 系统语言（macOS UI / LANG）；3) Accept-Language"""
    qs = parse_qs(urlparse(handler.path).query)
    if "lang" in qs:
        return qs["lang"][0] if qs["lang"][0] in ("zh", "en") else "zh"
    sys_lang = _system_lang_cache or _detect_system_lang()
    if sys_lang:
        return sys_lang
    accept_language = handler.headers.get("Accept-Language", "").lower()
    for token in [part.strip() for part in accept_language.split(",") if part.strip()]:
        if token.startswith("en"):
            return "en"
        if token.startswith("zh"):
            return "zh"
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


def _print_startup_message(url: str, env: str, port: int):
    """根据运行环境输出启动信息，并在 Agent 可解析的固定行输出 READY 信号。"""
    print("OpenClaw Insights 已启动")
    # READY 行：固定格式，Agent 可 grep 此行获取服务地址
    print(f"READY {url}")

    if env == "desktop":
        print("按 Ctrl+C 停止")
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception:
            pass
    elif env == "ssh":
        print()
        print("检测到 SSH 会话，无法自动打开浏览器。")
        print("在本地执行以下命令进行端口转发，然后用浏览器访问：")
        print(f"  ssh -L {port}:localhost:{port} $SSH_CONNECTION_HOST")
        print(f"  open {url}")
    else:  # headless
        print()
        print("检测到无图形界面环境。访问方式：")
        print(f"  SSH 端口转发: ssh -L {port}:localhost:{port} <用户名@服务器IP>")
        print(f"  或绑定外部IP: python3 server.py --host 0.0.0.0（需配合防火墙使用）")
    print()


def _parse_args(argv=None):
    import argparse
    parser = argparse.ArgumentParser(
        prog="server.py",
        description="OpenClaw Insights — 本地数据洞察与配置管理服务",
    )
    parser.add_argument("port", nargs="?", type=int, default=DEFAULT_PORT,
                        help=f"监听端口（默认 {DEFAULT_PORT}）")
    parser.add_argument("--host", default="127.0.0.1",
                        help="绑定地址（默认 127.0.0.1；使用 0.0.0.0 可对外暴露，需配合防火墙）")
    parser.add_argument("--summary", action="store_true",
                        help="输出人类可读的摘要报告后退出（不启动服务）")
    parser.add_argument("--json", dest="json_out", action="store_true",
                        help="输出 JSON 格式摘要后退出（不启动服务，适合 Agent 解析）")
    return parser.parse_args(argv)


def main(argv=None):
    opts = _parse_args(argv)
    _init_system_lang()

    # --summary / --json 一次性输出模式
    if opts.summary or opts.json_out:
        data_path = os.path.join(SCRIPT_DIR, "data.json")
        if not os.path.exists(data_path):
            print("错误: data.json 不存在，请先运行 analyze.py 或正常启动服务", file=sys.stderr)
            sys.exit(1)
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)
        if opts.json_out:
            print(json.dumps(build_summary_dict(data), ensure_ascii=False, indent=2))
        else:
            print(build_summary_text(data))
        return

    # 正常服务器模式
    host = opts.host
    port = opts.port

    if host != "127.0.0.1":
        print("⚠ 安全警告：服务绑定到非本地地址，请确保已配置防火墙或仅在可信网络中使用。")

    # 首次启动时生成数据
    data_path = os.path.join(SCRIPT_DIR, "data.json")
    if not os.path.exists(data_path):
        print("首次启动，正在生成数据...")
        try:
            analyze.main()
        except Exception as e:
            print(f"ERROR: 数据分析失败: {e}", file=sys.stderr)
            sys.exit(3)
    try:
        _load_data()
    except Exception as e:
        print(f"ERROR: 无法读取数据，请检查 OpenClaw 是否已安装: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        srv = HTTPServer((host, port), Handler)
    except OSError as e:
        import errno
        if e.errno == errno.EADDRINUSE:
            print(f"ERROR: 端口 {port} 已被占用，请指定其他端口: python3 server.py {port + 1}", file=sys.stderr)
            sys.exit(2)
        raise

    display_host = "localhost" if host == "127.0.0.1" else host
    url = f"http://{display_host}:{port}"

    env = detect_environment()
    _print_startup_message(url, env, port)

    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")


if __name__ == "__main__":
    main()
