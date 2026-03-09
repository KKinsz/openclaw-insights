# OpenClaw Insights

A local analytics dashboard and configuration manager for [OpenClaw](https://openclaw.ai).
Visualize token usage, costs, caching efficiency, cron health, and manage your OpenClaw configuration — all from a single web UI.

## Features

- **Session Analytics** — Token consumption, cost breakdown, cache hit rates, 7-day trends
- **Agent Overview** — Per-agent metrics, model distribution, activity patterns
- **Cron Monitoring** — Success rates, durations, error tracking
- **Configuration Manager** — Edit global & agent configs with validation, backup, and atomic writes
- **Bilingual UI** — Chinese (zh-CN) and English (en-US), auto-detected

## Requirements

- **Python 3.9+** (uses `zoneinfo` from stdlib)
- **OpenClaw** installed and configured at `~/.openclaw`
- No third-party Python packages required (stdlib only)

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/lukeindev/openclaw-insights.git
cd openclaw-insights

# 2. Start the server (auto-opens browser)
python3 server.py

# 3. Visit http://localhost:18800
```

On first launch, session data is analyzed automatically. No additional setup needed.

### Custom Port

```bash
python3 server.py 9000
```

## How It Works

```
~/.openclaw/agents/*/sessions/* → analyze.py → data.json → render.py → Web Dashboard
                                                              ↕
                                   config_api.py ← REST API ← server.py (port 18800)
                                        ↕
                                ~/.openclaw/openclaw.json
```

1. **`analyze.py`** reads session logs from `~/.openclaw/agents/*/sessions/` and produces `data.json`
2. **`render.py`** generates the HTML dashboard from `data.json`
3. **`server.py`** serves the dashboard and exposes REST APIs for configuration management
4. **`config_api.py`** handles config reads/writes with validation (via `openclaw config validate`), atomic file operations, and automatic backups

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Dashboard (HTML) |
| `GET` | `/api/data` | Analytics data (JSON) |
| `POST` | `/api/refresh` | Re-analyze session data |
| `GET` | `/api/config/global` | Global OpenClaw config |
| `PATCH` | `/api/config/global/{section}` | Update config section |
| `GET` | `/api/config/agent/{name}` | Agent-specific config |
| `POST` | `/api/gateway/restart` | Restart OpenClaw gateway |

## Running Tests

```bash
python3 -m unittest discover -s . -p 'test_*.py'
```

## Project Structure

```
├── server.py          # HTTP server & API routing (entry point)
├── analyze.py         # Session data parser & analytics engine
├── config_api.py      # Config CRUD with validation & backup
├── render.py          # HTML dashboard renderer (i18n)
└── test_*.py          # Unit tests
```

## License

MIT
