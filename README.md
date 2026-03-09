<div align="center">

# OpenClaw Insights

**Analytics dashboard & configuration manager for [OpenClaw](https://openclaw.ai)**

100% local. Your data never leaves your machine.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![No Dependencies](https://img.shields.io/badge/Dependencies-None-brightgreen.svg)](#requirements)
[![Local Only](https://img.shields.io/badge/Privacy-Local%20Only-2ea44f.svg)](#privacy)

[English](README.md) · [简体中文](README.zh-CN.md)

</div>

---

## Features

- **Session Analytics** — Token consumption, cost breakdown, cache hit rates, 7-day trends
- **Agent Overview** — Per-agent metrics, model distribution, activity patterns
- **Cron Monitoring** — Success rates, durations, error tracking
- **Configuration Manager** — Edit global & agent configs with validation, backup, and atomic writes
- **Bilingual UI** — Chinese (zh-CN) and English (en-US), auto-detected

## Requirements

- **Python 3.9+** (stdlib only — zero third-party dependencies)
- **OpenClaw** installed and configured at `~/.openclaw`

## Quick Start

```bash
# Clone into your OpenClaw directory (recommended)
git clone https://github.com/lukeindev/openclaw-insights.git ~/.openclaw/insights
cd ~/.openclaw/insights
python3 server.py
```

**Custom OpenClaw path:** If your OpenClaw is not at `~/.openclaw`, set the environment variable:

```bash
OPENCLAW_HOME=/your/openclaw/path python3 server.py
```

**Custom port:**

```bash
python3 server.py 9000
```

---

## For Human Users

OpenClaw Insights auto-detects your environment and adjusts its behavior accordingly.

### Local desktop

The server starts at `http://localhost:18800` and **auto-opens your browser**. On first launch, session data is analyzed automatically — no additional setup needed.

### Remote server — SSH port forwarding (recommended)

The safest way to access the dashboard when OpenClaw is on a remote server:

```bash
# On your local machine
ssh -L 18800:localhost:18800 user@your-server

# On the server
python3 server.py
# → Detects SSH session and prints port-forwarding instructions automatically

# Then open in your local browser
open http://localhost:18800
```

### Remote server — bind to external interface

For environments where SSH tunneling is not practical (e.g., behind a VPN or internal network):

```bash
python3 server.py --host 0.0.0.0
```

> **Security warning:** This exposes the dashboard — including config write access — to the network. Use only behind a firewall or on a trusted private network.

---

## For Agents (AI Agents)

When an AI agent installs and runs this tool, it can interact with it in two ways.

### 1. Start the server and detect readiness

```bash
python3 server.py
```

The server emits a machine-parseable signal on stdout before any human-readable text:

```
READY http://localhost:18800
```

The agent can watch stdout for the `READY <url>` line to know the dashboard is up, then relay the URL to the user.

### 2. One-shot summary mode (no server, no browser)

```bash
# Human-readable report — relay directly to the user
python3 server.py --summary
```

Example output:

```
=== OpenClaw Insights ===
Sessions:       66  (活跃天数: 16)
Token 消耗:     106,354,923  (日均: 6,647,183)
活跃 Agent:     5 个
Skill 数量:     22
Cron 数量:      4  (成功率: 56.2%)
模型数量:       7
```

```bash
# Machine-parseable JSON — process programmatically
python3 server.py --json
```

Example output (fields mirror what the web dashboard displays):

```json
{
  "total_sessions": 66,
  "active_agents": 5,
  "total_tokens": 106354923,
  "daily_avg_tokens": 6647183,
  "skills_count": 22,
  "cron_job_count": 4,
  "model_count": 7,
  "active_days": 16,
  "cron_success_rate_pct": 56.2
}
```

Both modes run once and exit immediately.

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Data not found — OpenClaw may not be installed |
| `2` | Port already in use |
| `3` | Analysis failed (corrupt data) |

---

## How It Works

```
~/.openclaw/agents/*/sessions/*  ──→  analyze.py  ──→  data.json
                                                           │
                              ┌─────────────────────────────┘
                              ▼
               server.py (port 18800)  ──→  render.py  ──→  Web Dashboard
                    │
                    ▼
              config_api.py  ◄──►  ~/.openclaw/openclaw.json
              (validate / backup / atomic write)
```

| Module | Role |
|--------|------|
| **`analyze.py`** | Reads session logs from `~/.openclaw` and produces `data.json` |
| **`render.py`** | Generates the HTML dashboard with i18n support |
| **`server.py`** | HTTP server entry point, serves dashboard and REST APIs |
| **`config_api.py`** | Config CRUD with `openclaw config validate`, atomic writes, and automatic backups |

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Dashboard (HTML) |
| `GET` | `/api/data` | Analytics data (JSON) |
| `POST` | `/api/refresh` | Re-analyze session data |
| `GET` | `/api/config/global` | Global OpenClaw config |
| `PATCH` | `/api/config/global/{section}` | Update config section |
| `GET` | `/api/config/agent/{name}` | Agent-specific config |
| `POST` | `/api/gateway/restart` | Restart OpenClaw gateway |

## Privacy

OpenClaw Insights runs entirely on your local machine. It reads data only from your local `~/.openclaw` directory and serves the dashboard on `127.0.0.1`. No data is collected, transmitted, or shared — no analytics, no telemetry, no network calls. Your session logs, token usage, and configuration stay on your device and under your control.

## License

[MIT](LICENSE)
