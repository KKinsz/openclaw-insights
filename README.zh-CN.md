<div align="center">

# OpenClaw Insights

**[OpenClaw](https://openclaw.ai) 数据洞察与配置管理工具**

完全本地运行，数据不会离开你的设备。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![No Dependencies](https://img.shields.io/badge/Dependencies-None-brightgreen.svg)](#环境要求)
[![Local Only](https://img.shields.io/badge/隐私-仅本地运行-2ea44f.svg)](#隐私)

[English](README.md) · [简体中文](README.zh-CN.md)

</div>

---

## 功能特性

- **Session 分析** — Token 消耗、成本明细、缓存命中率、7 日趋势
- **Agent 总览** — 各 Agent 指标、模型分布、活跃度
- **Cron 监控** — 成功率、执行时长、错误追踪
- **配置管理** — 全局 & Agent 配置的在线编辑，支持校验、备份与原子写入
- **中英双语 UI** — 支持 zh-CN / en-US，自动检测浏览器语言

## 环境要求

- **Python 3.9+**（仅使用标准库，无任何第三方依赖）
- **OpenClaw** 已安装并配置于 `~/.openclaw`

## 快速开始

```bash
# 推荐 clone 到 OpenClaw 目录下
git clone https://github.com/lukeindev/openclaw-insights.git ~/.openclaw/insights
cd ~/.openclaw/insights
python3 server.py
```

**自定义 OpenClaw 路径：** 如果你的 OpenClaw 不在 `~/.openclaw`，设置环境变量即可：

```bash
OPENCLAW_HOME=/your/openclaw/path python3 server.py
```

**自定义端口：**

```bash
python3 server.py 9000
```

---

## 人类用户

OpenClaw Insights 会自动检测运行环境，并给出对应的访问提示。

### 本地桌面

服务启动后会**自动打开浏览器**访问 `http://localhost:18800`。首次启动会自动分析 session 数据，无需额外配置。

### 远程服务器 — SSH 端口转发（推荐）

OpenClaw 安装在远程服务器时最安全的访问方式：

```bash
# 在本地执行
ssh -L 18800:localhost:18800 user@your-server

# 在服务器上正常启动
python3 server.py
# → 检测到 SSH 会话后，自动打印端口转发命令提示

# 然后在本地浏览器访问
open http://localhost:18800
```

### 远程服务器 — 绑定外部 IP

适用于 VPN 或内网等不方便使用 SSH 隧道的场景：

```bash
python3 server.py --host 0.0.0.0
```

> **安全警告：** 此操作会将 Dashboard（含配置写入权限）暴露到网络。请仅在防火墙保护或可信内网环境下使用。

---

## AI Agent 用户

当 AI Agent 自动安装并运行本工具时，有以下两种交互方式。

### 1. 启动服务并检测就绪状态

```bash
python3 server.py
```

服务启动后，会在 stdout 最先输出一行机器可解析的就绪信号：

```
READY http://localhost:18800
```

Agent 监听 stdout 中的 `READY <url>` 行，即可确认服务已就绪，并将 URL 转告给用户。

### 2. 一次性摘要模式（无需启动服务器或浏览器）

```bash
# 人类可读格式 — 直接转述给用户
python3 server.py --summary
```

示例输出：

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
# JSON 格式 — 程序化解析
python3 server.py --json
```

示例输出（字段与网页 Dashboard 完全对应）：

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

两种模式均为一次性运行，输出后自动退出。

### 退出码

| 退出码 | 含义 |
|--------|------|
| `0` | 正常退出 |
| `1` | 数据不存在，OpenClaw 可能未安装 |
| `2` | 端口已被占用 |
| `3` | 数据分析失败（数据损坏等） |

---

## 工作原理

```
~/.openclaw/agents/*/sessions/*  ──→  analyze.py  ──→  data.json
                                                           │
                              ┌─────────────────────────────┘
                              ▼
               server.py (port 18800)  ──→  render.py  ──→  Web Dashboard
                    │
                    ▼
              config_api.py  ◄──►  ~/.openclaw/openclaw.json
              (校验 / 备份 / 原子写入)
```

| 模块 | 职责 |
|------|------|
| **`analyze.py`** | 读取 `~/.openclaw` 下的 session 日志，生成 `data.json` |
| **`render.py`** | 基于分析数据生成 HTML Dashboard（支持 i18n） |
| **`server.py`** | HTTP 服务入口，提供 Dashboard 页面和 REST API |
| **`config_api.py`** | 配置读写，集成 `openclaw config validate` 校验、原子写入与自动备份 |

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/` | Dashboard 页面 |
| `GET` | `/api/data` | 分析数据（JSON） |
| `POST` | `/api/refresh` | 重新分析 session 数据 |
| `GET` | `/api/config/global` | 全局配置 |
| `PATCH` | `/api/config/global/{section}` | 更新配置分区 |
| `GET` | `/api/config/agent/{name}` | Agent 配置 |
| `POST` | `/api/gateway/restart` | 重启 OpenClaw Gateway |

## 隐私

OpenClaw Insights 完全在本地运行。它仅读取本机 `~/.openclaw` 目录下的数据，Dashboard 仅监听 `127.0.0.1`。没有数据收集、没有遥测上报、没有任何外部网络请求。你的 session 日志、Token 用量和配置信息始终留在你的设备上，完全由你掌控。

## 开源协议

[MIT](LICENSE)
