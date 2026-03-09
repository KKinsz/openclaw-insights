<div align="center">

# OpenClaw Insights

**Analytics dashboard & configuration manager for [OpenClaw](https://openclaw.ai)**

Visualize token usage, costs, caching efficiency, cron health, and manage your OpenClaw configuration — all from a single local web UI.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![No Dependencies](https://img.shields.io/badge/Dependencies-None-brightgreen.svg)](#requirements)

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
git clone https://github.com/lukeindev/openclaw-insights.git
cd openclaw-insights
python3 server.py
```

The server starts at `http://localhost:18800` and auto-opens your browser. On first launch, session data is analyzed automatically — no additional setup needed.

**Custom port:**

```bash
python3 server.py 9000
```

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

## License

[MIT](LICENSE)
