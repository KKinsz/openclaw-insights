#!/usr/bin/env python3
"""
OpenClaw Insights Analyzer
解析 ~/.openclaw 数据，生成洞察 JSON
"""

import json
import glob
import os
import re
from datetime import datetime, timezone, timedelta
from collections import defaultdict, Counter
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

BASE = os.environ.get("OPENCLAW_HOME", os.path.expanduser("~/.openclaw"))
AGENTS = ["main", "monitor", "note", "code", "image", "claude", "codex", "gemini", "glm-5"]
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")


# ── 工具函数 ──────────────────────────────────────────────────────────

def ts_to_dt(ts):
    if not ts:
        return None
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def dt_to_date(dt):
    if not dt:
        return None
    return dt.strftime("%Y-%m-%d")


def local_date_str(dt, tz):
    if not dt:
        return None
    return dt.astimezone(tz).strftime("%Y-%m-%d")


def is_internal_delivery_model(provider, model_id):
    return provider == "openclaw" and model_id == "delivery-mirror"


def safe_add(d, key, val):
    d[key] = d.get(key, 0) + (val or 0)


_PLACEHOLDER_RE = re.compile(
    r"todo|待补充|待填写|待完善|示例|暂无|your name|xxx|placeholder|填写你的|\[.*?\]",
    re.IGNORECASE,
)


def _meaningful_lines(path):
    """计算文件中有实质内容的行数（排除空行、纯标题、分隔符）"""
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except Exception:
        return 0
    count = 0
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if re.match(r"^#+\s+\S", s) and len(s) < 50:
            continue  # 短标题行
        if s in ("---", "===", "***", "...", "—"):
            continue
        count += 1
    return count


def _has_placeholder(path):
    """检测文件中是否含有常见占位符"""
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return False
    return bool(_PLACEHOLDER_RE.search(content))


# ── 解析 Session 文件 ────────────────────────────────────────────────

def parse_session_file(filepath, agent_id):
    events = []
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except Exception:
                pass

    if not events:
        return None

    session_event = next((e for e in events if e.get("type") == "session"), None)
    if not session_event:
        return None

    session_id = session_event.get("id")
    start_dt = ts_to_dt(session_event.get("timestamp"))

    messages = [e for e in events if e.get("type") == "message"]

    # 追踪使用的模型
    models_used = []
    for e in events:
        if e.get("type") == "model_change":
            models_used.append({
                "provider": e.get("provider"),
                "model_id": e.get("modelId"),
            })
        elif e.get("type") == "custom" and e.get("customType") == "model-snapshot":
            data = e.get("data", {})
            models_used.append({
                "provider": data.get("provider"),
                "model_id": data.get("modelId"),
            })

    # 聚合 token 使用和成本
    usage = {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0, "totalTokens": 0}
    cost = {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0, "total": 0}
    user_msg_count = 0
    assistant_msg_count = 0
    model_costs = defaultdict(lambda: {"cost": 0, "tokens": 0, "cache_hit": 0, "input": 0, "output": 0, "messages": 0})
    token_usage_events = []

    for msg_event in messages:
        m = msg_event.get("message", {})
        role = m.get("role")
        if role == "user":
            user_msg_count += 1
        elif role == "assistant":
            assistant_msg_count += 1
            u = m.get("usage", {})
            for key in ["input", "output", "cacheRead", "cacheWrite", "totalTokens"]:
                safe_add(usage, key, u.get(key, 0))
            c = u.get("cost", {})
            for key in ["input", "output", "cacheRead", "cacheWrite", "total"]:
                safe_add(cost, key, c.get(key, 0))
            model_id = m.get("model", "unknown")
            provider = m.get("provider", "unknown")
            if is_internal_delivery_model(provider, model_id):
                token_usage_events.append({
                    "timestamp": msg_event.get("timestamp"),
                    "total": u.get("input", 0) + u.get("output", 0) + u.get("cacheRead", 0) + u.get("cacheWrite", 0),
                    "cache_hit": u.get("cacheRead", 0),
                })
                continue
            mk = f"{provider}/{model_id}"
            model_costs[mk]["cost"] += c.get("total", 0)
            model_costs[mk]["tokens"] += u.get("input", 0) + u.get("output", 0) + u.get("cacheRead", 0) + u.get("cacheWrite", 0)
            model_costs[mk]["cache_hit"] += u.get("cacheRead", 0)
            model_costs[mk]["input"] += u.get("input", 0)
            model_costs[mk]["output"] += u.get("output", 0)
            model_costs[mk]["messages"] += 1
            token_usage_events.append({
                "timestamp": msg_event.get("timestamp"),
                "total": u.get("input", 0) + u.get("output", 0) + u.get("cacheRead", 0) + u.get("cacheWrite", 0),
                "cache_hit": u.get("cacheRead", 0),
            })
            # 标记该模型是否上报成本
            if c.get("total", 0) > 0:
                model_costs[mk]["has_cost_data"] = True
            elif "has_cost_data" not in model_costs[mk]:
                model_costs[mk]["has_cost_data"] = False

    # 判断是否 cron 触发
    is_cron = False
    cron_job_id = None
    cron_job_name = None
    first_user_msg = next(
        (msg for msg in messages if msg.get("message", {}).get("role") == "user"), None
    )
    if first_user_msg:
        content = first_user_msg.get("message", {}).get("content", [])
        text = ""
        if isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get("type") == "text":
                    text = c.get("text", "")
                    break
        elif isinstance(content, str):
            text = content
        match = re.match(r"\[cron:([a-f0-9-]+)\s+([^\]]+)\]", text)
        if match:
            is_cron = True
            cron_job_id = match.group(1)
            cron_job_name = match.group(2).strip()

    # ── 时长计算 ──
    # cron session: 首尾事件差（任务有明确完成边界）
    # 主动对话 session: 累积活跃时间（相邻消息间隔 < 30min 才计入，避免跨天偏差）
    IDLE_THRESHOLD_SEC = 30 * 60  # 30 分钟空闲即断开

    msg_timestamps = []
    for e in events:
        if e.get("type") == "message" and e.get("timestamp"):
            dt = ts_to_dt(e.get("timestamp"))
            if dt:
                msg_timestamps.append(dt)
    msg_timestamps.sort()

    active_duration_min = None
    if is_cron and msg_timestamps:
        # cron: 首尾差
        delta = (msg_timestamps[-1] - msg_timestamps[0]).total_seconds()
        active_duration_min = round(delta / 60, 1)
    elif len(msg_timestamps) >= 2:
        # 主动对话: 累积活跃窗口
        active_secs = 0
        for i in range(1, len(msg_timestamps)):
            gap = (msg_timestamps[i] - msg_timestamps[i - 1]).total_seconds()
            if gap < IDLE_THRESHOLD_SEC:
                active_secs += gap
        active_duration_min = round(active_secs / 60, 1)

    # 判断是否跨天的持久 session
    is_persistent = False
    if msg_timestamps:
        span_days = (msg_timestamps[-1] - msg_timestamps[0]).days
        is_persistent = span_days >= 1

    return {
        "id": session_id,
        "agent": agent_id,
        "start_time": session_event.get("timestamp"),
        "start_date": dt_to_date(start_dt),
        "is_persistent": is_persistent,
        "active_duration_min": active_duration_min,
        "models_used": models_used,
        "model_costs": dict(model_costs),
        "message_count": len(messages),
        "user_messages": user_msg_count,
        "assistant_messages": assistant_msg_count,
        "usage": usage,
        "token_usage_events": token_usage_events,
        "cost": cost,
        "is_cron": is_cron,
        "cron_job_id": cron_job_id,
        "cron_job_name": cron_job_name,
    }


def collect_sessions():
    all_sessions = []
    for agent_id in AGENTS:
        session_dir = os.path.join(BASE, "agents", agent_id, "sessions")
        if not os.path.exists(session_dir):
            continue
        for f in glob.glob(os.path.join(session_dir, "*.jsonl")):
            if ".deleted." in f or ".reset." in f:
                continue
            try:
                session = parse_session_file(f, agent_id)
                if session and session["message_count"] > 0:
                    all_sessions.append(session)
            except Exception:
                pass
    return all_sessions


# ── 解析 Cron ────────────────────────────────────────────────────────

def collect_cron_data():
    jobs_file = os.path.join(BASE, "cron", "jobs.json")
    runs_dir = os.path.join(BASE, "cron", "runs")

    jobs = []
    if os.path.exists(jobs_file):
        with open(jobs_file, encoding="utf-8") as f:
            d = json.load(f)
            jobs = d.get("jobs", []) if isinstance(d, dict) else d

    # 读取运行记录
    job_runs = defaultdict(list)
    if os.path.exists(runs_dir):
        for run_file in glob.glob(os.path.join(runs_dir, "*.jsonl")):
            job_id = os.path.basename(run_file).replace(".jsonl", "")
            with open(run_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        job_runs[job_id].append(json.loads(line))
                    except Exception:
                        pass

    enriched_jobs = []
    total_runs = 0
    total_success = 0

    for job in jobs:
        job_id = job.get("id", "")
        runs = job_runs.get(job_id, [])
        finished = [r for r in runs if r.get("action") == "finished"]
        success = [r for r in finished if r.get("status") == "ok"]
        durations = [r["durationMs"] for r in finished if r.get("durationMs")]

        run_count = len(finished)
        success_count = len(success)
        state = job.get("state", {})

        # 无本地记录时从 state 补充
        if run_count == 0 and state.get("lastRunAtMs"):
            run_count = 1
            success_count = 1 if state.get("lastRunStatus") == "ok" else 0
            durations = [state["lastDurationMs"]] if state.get("lastDurationMs") else []

        total_runs += run_count
        total_success += success_count

        success_rate = round(success_count / run_count, 3) if run_count > 0 else None
        avg_duration = round(sum(durations) / len(durations)) if durations else None
        errors = [r.get("error") for r in finished if r.get("status") != "ok" and r.get("error")]

        enriched_jobs.append({
            "id": job_id,
            "name": job.get("name", ""),
            "agent": job.get("agentId", ""),
            "schedule": job.get("schedule", {}).get("expr", ""),
            "tz": job.get("schedule", {}).get("tz", ""),
            "enabled": job.get("enabled", True),
            "delivery_mode": job.get("delivery", {}).get("mode", "none"),
            "delivery_channel": job.get("delivery", {}).get("channel", ""),
            "run_count": run_count,
            "success_rate": success_rate,
            "avg_duration_ms": avg_duration,
            "last_status": state.get("lastRunStatus"),
            "last_run_at_ms": state.get("lastRunAtMs"),
            "consecutive_errors": state.get("consecutiveErrors", 0),
            "recent_errors": errors[-3:],
        })

    overall_success_rate = round(total_success / total_runs, 3) if total_runs > 0 else None
    return {
        "total_jobs": len(jobs),
        "enabled_jobs": sum(1 for j in jobs if j.get("enabled", True)),
        "total_runs": total_runs,
        "overall_success_rate": overall_success_rate,
        "jobs": enriched_jobs,
    }


# ── 解析 Skills ──────────────────────────────────────────────────────

def collect_skills():
    skills_dir = os.path.join(BASE, "skills")
    skills = []
    if os.path.exists(skills_dir):
        for name in sorted(os.listdir(skills_dir)):
            skill_path = os.path.join(skills_dir, name)
            if os.path.isdir(skill_path):
                skill_md = os.path.join(skill_path, "SKILL.md")
                has_md = os.path.exists(skill_md)
                skills.append({
                    "name": name,
                    "has_skill_md": has_md,
                    "skill_md_lines": _meaningful_lines(skill_md) if has_md else 0,
                })
    return skills


# ── 配置健康检查 ──────────────────────────────────────────────────────

_CHECK_FILES = ["USER.md", "SOUL.md", "MEMORY.md", "IDENTITY.md", "HEARTBEAT.md"]


def collect_config_health(active_agent_ids):
    """读取 openclaw.json 和 workspace 文件，返回各 agent 的配置健康状态"""
    result = {
        "agents": [],
        "channels": {"telegram_enabled": False, "discord_enabled": False},
    }

    cfg = {}
    try:
        with open(os.path.join(BASE, "openclaw.json"), encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        pass

    channels = cfg.get("channels", {})
    result["channels"]["telegram_enabled"] = channels.get("telegram", {}).get("enabled", False)
    result["channels"]["discord_enabled"] = channels.get("discord", {}).get("enabled", False)

    agent_cfg_map = {
        a.get("id"): a
        for a in cfg.get("agents", {}).get("list", [])
        if a.get("id")
    }

    for agent_id in active_agent_ids:
        ag_cfg = agent_cfg_map.get(agent_id, {})
        workspace = (
            ag_cfg.get("agentDir")
            or ag_cfg.get("workspace")
            or os.path.join(BASE, "workspace", agent_id)
        )
        hb = ag_cfg.get("heartbeat", {})
        heartbeat_every = hb.get("every", "") if isinstance(hb, dict) else ""

        files = {}
        for fname in _CHECK_FILES:
            fpath = os.path.join(workspace, fname)
            exists = os.path.exists(fpath)
            files[fname] = {
                "exists": exists,
                "meaningful_lines": _meaningful_lines(fpath) if exists else 0,
                "has_placeholder": _has_placeholder(fpath) if exists else False,
            }

        result["agents"].append({
            "id": agent_id,
            "identity_name": ag_cfg.get("identity", {}).get("name", agent_id),
            "heartbeat_every": heartbeat_every,
            "files": files,
        })

    return result


def collect_channel_configuration_counts(cron_data):
    """统计当前配置中的交互渠道数量，而不是历史 session 来源。"""
    counts = {"discord": 0, "telegram": 0}

    cfg = {}
    try:
        with open(os.path.join(BASE, "openclaw.json"), encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        return counts

    binding_counts = Counter()
    for binding in cfg.get("bindings", []):
        if not isinstance(binding, dict):
            continue
        match = binding.get("match", {})
        channel = match.get("channel")
        if isinstance(channel, str) and channel in counts:
            binding_counts[channel] += 1

    channels_cfg = cfg.get("channels", {})
    for channel_name in ("discord", "telegram"):
        if binding_counts[channel_name] > 0:
            counts[channel_name] = binding_counts[channel_name]
            continue

        ch_cfg = channels_cfg.get(channel_name, {})
        if not isinstance(ch_cfg, dict) or not ch_cfg.get("enabled"):
            continue

        if channel_name == "discord":
            accounts = ch_cfg.get("accounts", {})
            named_accounts = [
                name for name, account in accounts.items()
                if name != "default" and isinstance(account, dict)
            ]
            counts[channel_name] = len(named_accounts) if named_accounts else 1
        else:
            counts[channel_name] = 1

    return counts


# ── 聚合分析 ─────────────────────────────────────────────────────────

def aggregate(sessions, cron_data, skills, config_health=None):
    now = datetime.now(tz=timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    recent = [
        s for s in sessions
        if (ts_to_dt(s.get("start_time")) or now) >= thirty_days_ago
    ]

    total_sessions = len(recent)
    total_messages = sum(s["message_count"] for s in recent)
    total_cost = sum(s["cost"].get("total", 0) for s in recent)
    cache_savings = sum(s["cost"].get("cacheRead", 0) for s in recent)
    cron_count = sum(1 for s in recent if s["is_cron"])
    manual_count = total_sessions - cron_count

    def _session_total_tokens(s):
        u = s["usage"]
        return u.get("input", 0) + u.get("output", 0) + u.get("cacheRead", 0) + u.get("cacheWrite", 0)

    total_tokens_all = sum(_session_total_tokens(s) for s in recent)
    total_cache_hit_tokens = sum(s["usage"].get("cacheRead", 0) for s in recent)

    # 按 Agent 统计
    agent_map = defaultdict(lambda: {
        "session_count": 0, "message_count": 0, "cost": 0,
        "total_tokens": 0, "cache_hit_tokens": 0,
        "cron_sessions": 0, "manual_sessions": 0, "durations": [], "dates": set(),
    })
    for s in recent:
        ag = s["agent"]
        agent_map[ag]["session_count"] += 1
        agent_map[ag]["message_count"] += s["message_count"]
        agent_map[ag]["cost"] += s["cost"].get("total", 0)
        agent_map[ag]["total_tokens"] += _session_total_tokens(s)
        agent_map[ag]["cache_hit_tokens"] += s["usage"].get("cacheRead", 0)
        agent_map[ag]["dates"].add(s.get("start_date"))
        if s["is_cron"]:
            agent_map[ag]["cron_sessions"] += 1
        else:
            agent_map[ag]["manual_sessions"] += 1
        if s.get("active_duration_min") and not s.get("is_persistent"):
            agent_map[ag]["durations"].append(s["active_duration_min"])

    agents_result = []
    for ag_id, stats in agent_map.items():
        durations = stats.pop("durations")
        dates = stats.pop("dates")
        avg_dur = round(sum(durations) / len(durations), 1) if durations else None
        agent_active_days = len(dates - {None})
        total_tok = stats["total_tokens"]
        daily_avg_tok = round(total_tok / agent_active_days) if agent_active_days > 0 else None
        agents_result.append({
            "id": ag_id,
            "session_count": stats["session_count"],
            "message_count": stats["message_count"],
            "cost": round(stats["cost"], 4),
            "total_tokens": total_tok,
            "cache_hit_tokens": stats["cache_hit_tokens"],
            "daily_avg_tokens": daily_avg_tok,
            "cron_sessions": stats["cron_sessions"],
            "manual_sessions": stats["manual_sessions"],
            "avg_active_duration_min": avg_dur,
        })
    agents_result.sort(key=lambda x: x["total_tokens"], reverse=True)

    # 按模型统计
    model_map = defaultdict(lambda: {"cost": 0, "tokens": 0, "cache_hit": 0, "messages": 0, "sessions": 0, "has_cost_data": False})
    for s in recent:
        for mk, mc in s.get("model_costs", {}).items():
            model_map[mk]["cost"] += mc.get("cost", 0)
            model_map[mk]["tokens"] += mc.get("tokens", 0)
            model_map[mk]["cache_hit"] += mc.get("cache_hit", 0)
            model_map[mk]["messages"] += mc.get("messages", 0)
            model_map[mk]["sessions"] += 1
            if mc.get("has_cost_data"):
                model_map[mk]["has_cost_data"] = True

    models_result = []
    for mk, stats in model_map.items():
        parts = mk.split("/", 1)
        models_result.append({
            "key": mk,
            "provider": parts[0] if len(parts) > 1 else "unknown",
            "model_id": parts[1] if len(parts) > 1 else parts[0],
            "cost": round(stats["cost"], 4),
            "tokens": stats["tokens"],
            "cache_hit_tokens": stats["cache_hit"],
            "messages": stats["messages"],
            "sessions": stats["sessions"],
            "cost_tracked": stats["has_cost_data"],
        })
    models_result.sort(key=lambda x: x["tokens"], reverse=True)

    # 用户时区：优先从 cron 任务中推断，兜底 Asia/Shanghai
    cron_tz_counter = Counter(j.get("tz") for j in cron_data.get("jobs", []) if j.get("tz"))
    user_tz_str = cron_tz_counter.most_common(1)[0][0] if cron_tz_counter else "Asia/Shanghai"
    try:
        user_tz = ZoneInfo(user_tz_str)
    except Exception:
        user_tz = ZoneInfo("Asia/Shanghai")
        user_tz_str = "Asia/Shanghai"

    # 7 日成本趋势（保留，不在 UI 展示）
    trend_map = {}
    for i in range(7):
        d = (now - timedelta(days=6 - i)).strftime("%Y-%m-%d")
        trend_map[d] = 0
    for s in recent:
        d = s.get("start_date")
        if d and d in trend_map:
            trend_map[d] += s["cost"].get("total", 0)
    trend_7d = [{"date": d, "cost": round(v, 4)} for d, v in sorted(trend_map.items())]

    # 7 日 Token 趋势
    token_trend_map = {}
    local_now = now.astimezone(user_tz)
    for i in range(7):
        d = (local_now - timedelta(days=6 - i)).strftime("%Y-%m-%d")
        token_trend_map[d] = {"total": 0, "cache_hit": 0}
    for s in recent:
        token_usage_events = s.get("token_usage_events") or []
        if token_usage_events:
            for event in token_usage_events:
                d = local_date_str(ts_to_dt(event.get("timestamp")), user_tz)
                if d and d in token_trend_map:
                    token_trend_map[d]["total"] += event.get("total", 0) or 0
                    token_trend_map[d]["cache_hit"] += event.get("cache_hit", 0) or 0
            continue

        start_dt = ts_to_dt(s.get("start_time"))
        d = local_date_str(start_dt, user_tz) if start_dt else s.get("start_date")
        if d and d in token_trend_map:
            token_trend_map[d]["total"] += _session_total_tokens(s)
            token_trend_map[d]["cache_hit"] += s["usage"].get("cacheRead", 0)
    token_trend_7d = [
        {"date": d, "total": v["total"], "cache_hit": v["cache_hit"]}
        for d, v in sorted(token_trend_map.items())
    ]

    channels = collect_channel_configuration_counts(cron_data)

    # 高峰小时（仅主动对话 session，转换到用户本地时区）
    hour_counts = defaultdict(int)
    for s in recent:
        if not s["is_cron"]:
            dt = ts_to_dt(s.get("start_time"))
            if dt:
                local_hour = dt.astimezone(user_tz).hour
                hour_counts[local_hour] += 1
    peak_hours = sorted(hour_counts, key=hour_counts.get, reverse=True)[:4]

    # 日期范围
    all_dates = [s.get("start_date") for s in recent if s.get("start_date")]
    date_from = min(all_dates) if all_dates else None
    date_to = max(all_dates) if all_dates else None
    active_days = len(set(all_dates))

    # Cron 分析摘要
    cron_jobs = cron_data.get("jobs", [])
    most_reliable = max(
        (j for j in cron_jobs if j.get("success_rate") is not None),
        key=lambda j: j.get("success_rate", 0),
        default=None,
    )
    most_durable = max(
        (j for j in cron_jobs if j.get("avg_duration_ms")),
        key=lambda j: j.get("avg_duration_ms", 0),
        default=None,
    )
    failing_jobs = [j for j in cron_jobs if j.get("consecutive_errors", 0) > 0]

    # 交互叙述
    top_agent = agents_result[0]["id"] if agents_result else "main"
    top_model = models_result[0]["model_id"] if models_result else "unknown"
    cron_cost = sum(s["cost"].get("total", 0) for s in recent if s["is_cron"])
    manual_cost = total_cost - cron_cost
    cron_tokens = sum(_session_total_tokens(s) for s in recent if s["is_cron"])
    manual_tokens = total_tokens_all - cron_tokens
    cache_hit_pct = round(total_cache_hit_tokens / total_tokens_all * 100) if total_tokens_all > 0 else 0

    daily_avg_tokens = round(total_tokens_all / active_days) if active_days > 0 else 0

    skill_names = [sk["name"] for sk in skills]

    return {
        "meta": {
            "generated_at": now.isoformat(),
            "period": {"from": date_from, "to": date_to},
            "openclaw_version": get_openclaw_version(),
        },
        "at_a_glance": {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "total_tokens": total_tokens_all,
            "cache_hit_tokens": total_cache_hit_tokens,
            "daily_avg_tokens": daily_avg_tokens,
            "cron_sessions": cron_count,
            "manual_sessions": manual_count,
            "active_agents": list(agent_map.keys()),
            "active_agent_count": len(agent_map),
            "active_days": active_days,
            "skills_count": len(skills),
            "cron_job_count": cron_data.get("total_jobs", 0),
            "model_count": len(models_result),
            # 以下保留，不在 UI 展示
            "total_cost_usd": round(total_cost, 4),
            "cache_savings_usd": round(cache_savings, 4),
        },
        "agents": agents_result,
        "token_analysis": {
            "total_tokens": total_tokens_all,
            "cache_hit_tokens": total_cache_hit_tokens,
            "daily_avg_tokens": daily_avg_tokens,
            "by_type": {
                "manual_tokens": manual_tokens,
                "cron_tokens": cron_tokens,
            },
            "trend_7d": token_trend_7d,
        },
        # 成本数据保留，不在 UI 展示
        "cost_analysis": {
            "total_usd": round(total_cost, 4),
            "cache_savings_usd": round(cache_savings, 4),
            "by_type": {
                "manual": round(manual_cost, 4),
                "cron_automated": round(cron_cost, 4),
            },
            "trend_7d": trend_7d,
        },
        "models": models_result,
        "cron": {
            **cron_data,
            "most_reliable": most_reliable.get("name") if most_reliable else None,
            "longest_running": most_durable.get("name") if most_durable else None,
            "failing_jobs": [j["name"] for j in failing_jobs],
        },
        "skills": {
            "installed": skill_names,
            "total": len(skills),
        },
        "interaction_patterns": {
            "channels": channels,
            "peak_hours": peak_hours,
            "hour_counts": dict(hour_counts),
            "avg_messages_per_session": round(total_messages / total_sessions, 1) if total_sessions > 0 else 0,
        },
        "suggestions": generate_suggestions(agents_result, models_result, cron_data, recent, skills, peak_hours, user_tz_str, hour_counts, config_health or {}),
    }


def get_openclaw_version():
    try:
        with open(os.path.join(BASE, "openclaw.json"), encoding="utf-8") as f:
            d = json.load(f)
        return d.get("meta", {}).get("lastTouchedVersion", "unknown")
    except Exception:
        return "unknown"


def generate_suggestions(agents, models, cron_data, sessions, skills, peak_hours=None, user_tz_str="Asia/Shanghai", hour_counts=None, config_health=None):
    suggestions = []

    # 连续失败的 Cron 任务
    failing = [j for j in cron_data.get("jobs", []) if j.get("consecutive_errors", 0) > 0]
    if failing:
        suggestions.append({
            "type": "cron",
            "subtype": "consecutive_errors",
            "data": {"count": len(failing), "jobs": [j["name"] for j in failing]},
            "title": f"{len(failing)} 个 Cron 任务连续失败",
            "detail": f"任务 {', '.join(j['name'] for j in failing)} 处于连续失败状态，建议检查配置或延长超时时间。",
            "jobs": [j["name"] for j in failing],
        })

    # B2：主动对话 Session 时长过长
    long_agents = [
        a for a in agents
        if a.get("avg_active_duration_min") and a["avg_active_duration_min"] > 60
        and a.get("manual_sessions", 0) > 0
    ]
    for a in long_agents:
        suggestions.append({
            "type": "session",
            "subtype": "long_session",
            "data": {"agent": a["id"], "avg_min": a["avg_active_duration_min"]},
            "title": f"{a['id']} Agent 单次 Session 时长较长",
            "detail": (
                f"{a['id']} 的主动对话 session 平均活跃时长为 {a['avg_active_duration_min']} 分钟。"
                f"长时间对话会积累大量 context，可能导致响应质量下降或 token 浪费，"
                f"建议考虑拆分任务或更频繁地开启新 session。"
            ),
            "agent": a["id"],
            "avg_duration_min": a["avg_active_duration_min"],
        })

    # B3：单 Agent Token 消耗高度集中（仅供参考，单 Agent 场景跳过）
    total_tokens = sum(a["total_tokens"] for a in agents)
    if total_tokens > 0 and len(agents) > 1:
        top_a = agents[0]  # agents 已按 total_tokens 降序排列
        ratio = top_a["total_tokens"] / total_tokens
        if ratio > 0.60:
            pct = round(ratio * 100)
            suggestions.append({
                "type": "agent",
                "subtype": "token_concentration",
                "data": {"agent": top_a["id"], "pct": pct},
                "title": f"{top_a['id']} 占据了 {pct}% 的 Token 消耗",
                "detail": (
                    f"过去 30 天中，{top_a['id']} 消耗了全部 token 的 {pct}%，"
                    f"远超其他 agent。仅供参考——如果这符合你的分工设计（如主控 agent 承担大部分协调工作），"
                    f"可以忽略此提示。"
                ),
                "agent": top_a["id"],
                "token_ratio": ratio,
            })

    # C1：Cron 整体成功率偏低
    overall_sr = cron_data.get("overall_success_rate")
    total_runs = cron_data.get("total_runs", 0)
    if overall_sr is not None and overall_sr < 0.7 and total_runs >= 5:
        suggestions.append({
            "type": "cron",
            "subtype": "overall_rate_low",
            "data": {"rate": round(overall_sr * 100), "total_runs": total_runs},
            "title": f"Cron 整体成功率偏低（{round(overall_sr * 100)}%）",
            "detail": (
                f"在 {total_runs} 次 Cron 运行记录中，整体成功率仅为 {round(overall_sr * 100)}%，"
                f"建议全面检查各任务的配置、超时设置及依赖服务的可用性。"
            ),
            "success_rate": overall_sr,
        })

    # C3：Cron 任务无 delivery 配置
    no_delivery = [
        j for j in cron_data.get("jobs", [])
        if j.get("delivery_mode") == "none"
        and j.get("enabled", True)
        and j.get("run_count", 0) >= 3
    ]
    if no_delivery:
        suggestions.append({
            "type": "cron",
            "subtype": "no_delivery",
            "data": {"count": len(no_delivery), "jobs": [j["name"] for j in no_delivery[:3]]},
            "title": f"{len(no_delivery)} 个 Cron 任务未配置消息推送",
            "detail": (
                f"{', '.join(j['name'] for j in no_delivery[:3])} 等任务已稳定运行但未配置 delivery，"
                f"执行结果只能通过日志查看。可考虑配置 discord 或 telegram 推送，方便及时感知运行状态。"
            ),
            "jobs": [j["name"] for j in no_delivery],
        })

    # C4：Cron 执行时段与用户活跃高峰冲突
    if hour_counts:
        # 构建更宽的高峰期窗口：
        # 取 top-8 高峰小时，再向前后各扩展 1 小时，覆盖早高峰/晚高峰整段
        top8 = sorted(hour_counts, key=hour_counts.get, reverse=True)[:8]
        peak_window = set()
        for h in top8:
            for delta in (-1, 0, 1):
                peak_window.add((h + delta) % 24)

        try:
            user_tz = ZoneInfo(user_tz_str)
        except Exception:
            user_tz = ZoneInfo("Asia/Shanghai")

        def _cron_hour_in_user_tz(job):
            """将 cron 表达式的小时字段从 job 时区转换到用户时区"""
            expr = job.get("schedule", "")
            parts = expr.split()
            if len(parts) < 2:
                return None
            try:
                h = int(parts[1])
            except ValueError:
                return None
            job_tz_str = job.get("tz") or user_tz_str
            if job_tz_str == user_tz_str:
                return h
            # 用一个固定参考日期做时区转换
            try:
                ref = datetime(2024, 6, 15, h, 0, tzinfo=ZoneInfo(job_tz_str))
                return ref.astimezone(user_tz).hour
            except Exception:
                return h

        conflicting = []
        for j in cron_data.get("jobs", []):
            if not j.get("enabled", True):
                continue
            h = _cron_hour_in_user_tz(j)
            if h is not None and h in peak_window:
                conflicting.append(j)

        if conflicting:
            display_peaks = sorted(top8)[:4]
            suggestions.append({
                "type": "cron",
                "subtype": "peak_conflict",
                "data": {
                    "count": len(conflicting),
                    "jobs": [j["name"] for j in conflicting[:3]],
                    "peaks": display_peaks,
                    "tz": user_tz_str,
                },
                "title": f"{len(conflicting)} 个 Cron 任务与活跃高峰时段重叠",
                "detail": (
                    f"你的主动对话高峰集中在 {'、'.join(f'{h}:00' for h in display_peaks)} 等时段（时区：{user_tz_str}），"
                    f"而 {', '.join(j['name'] for j in conflicting[:3])} 等 Cron 任务也在这些时间点附近执行。"
                    f"自动任务与主动对话并发可能导致响应变慢，建议将 Cron 调整至低峰时段。"
                ),
                "jobs": [j["name"] for j in conflicting],
                "peak_window": sorted(peak_window),
            })

    # ── 配置健康类规则 ──────────────────────────────────────────────────
    ch = config_health or {}
    ag_health_list = ch.get("agents", [])
    agent_session_map = {a["id"]: a for a in agents}

    def _file_sparse(f_info):
        """判断文件内容是否不充分：不存在、有效行 < 5、或含占位符"""
        return (
            not f_info.get("exists")
            or f_info.get("meaningful_lines", 0) < 5
            or f_info.get("has_placeholder", False)
        )

    # D1：USER.md 缺失或内容不充分
    user_md_issues = [
        ag for ag in ag_health_list
        if _file_sparse(ag["files"].get("USER.md", {}))
    ]
    if user_md_issues:
        if len(user_md_issues) == 1:
            ag = user_md_issues[0]
            f = ag["files"].get("USER.md", {})
            if not f.get("exists"):
                desc = "文件缺失"
            elif f.get("has_placeholder"):
                desc = f"内容包含未填写的占位符（{f['meaningful_lines']} 行有效内容）"
            else:
                desc = f"内容过少（仅 {f['meaningful_lines']} 行有效内容）"
            suggestions.append({
                "type": "config",
                "subtype": "user_md",
                "data": {"agents": [ag["id"]], "names": [ag["identity_name"]]},
                "severity": "critical",
                "title": f"{ag['identity_name']} · USER.md {desc}",
                "detail": (
                    f"USER.md 是 Agent 了解你的核心来源——包括你的偏好、习惯和常见任务背景。"
                    f"内容越详实，{ag['identity_name']} 的回应就越贴合你的实际需求，建议尽快完善。"
                ),
                "agent": ag["id"],
            })
        else:
            names = "、".join(ag["identity_name"] for ag in user_md_issues)
            suggestions.append({
                "type": "config",
                "subtype": "user_md",
                "data": {"agents": [ag["id"] for ag in user_md_issues], "names": [ag["identity_name"] for ag in user_md_issues]},
                "severity": "critical",
                "title": f"{len(user_md_issues)} 个 Agent 的 USER.md 内容不充分",
                "detail": (
                    f"{names} 的 USER.md 缺失或内容过少。USER.md 是 Agent 了解你的核心来源，"
                    f"建议逐一补充你的偏好、背景和常见任务类型。"
                ),
                "agents": [ag["id"] for ag in user_md_issues],
            })

    # D2：SOUL.md 缺失或内容不充分
    soul_md_issues = [
        ag for ag in ag_health_list
        if _file_sparse(ag["files"].get("SOUL.md", {}))
    ]
    if soul_md_issues:
        if len(soul_md_issues) == 1:
            ag = soul_md_issues[0]
            f = ag["files"].get("SOUL.md", {})
            desc = "文件缺失" if not f.get("exists") else f"内容过少（仅 {f['meaningful_lines']} 行）"
            suggestions.append({
                "type": "config",
                "subtype": "soul_md",
                "data": {"agents": [ag["id"]], "names": [ag["identity_name"]]},
                "severity": "critical",
                "title": f"{ag['identity_name']} · SOUL.md {desc}",
                "detail": (
                    f"SOUL.md 定义了 Agent 的价值观和行为准则，是让它'像它自己'的关键文件。"
                    f"缺少 SOUL.md 时，{ag['identity_name']} 的回应风格可能随对话上下文漂移，"
                    f"建议补充核心价值观和行为边界的描述。"
                ),
                "agent": ag["id"],
            })
        else:
            names = "、".join(ag["identity_name"] for ag in soul_md_issues)
            suggestions.append({
                "type": "config",
                "subtype": "soul_md",
                "data": {"agents": [ag["id"] for ag in soul_md_issues], "names": [ag["identity_name"] for ag in soul_md_issues]},
                "severity": "critical",
                "title": f"{len(soul_md_issues)} 个 Agent 的 SOUL.md 内容不充分",
                "detail": (
                    f"{names} 的 SOUL.md 缺失或内容过少。SOUL.md 定义 Agent 的价值观和行为准则，"
                    f"完善后回应风格会更稳定、更符合你的期望。"
                ),
                "agents": [ag["id"] for ag in soul_md_issues],
            })

    # D3：活跃 Agent 未启用 Heartbeat（合并为一条）
    active_manual_ids = {a["id"] for a in agents if a.get("manual_sessions", 0) > 0}
    no_heartbeat = [
        ag for ag in ag_health_list
        if ag["id"] in active_manual_ids
        and ag.get("heartbeat_every", "") in ("", "0", "off", "false", "never")
    ]
    if no_heartbeat:
        if len(no_heartbeat) == 1:
            ag = no_heartbeat[0]
            suggestions.append({
                "type": "config",
                "subtype": "heartbeat",
                "data": {"agents": [ag["id"]], "names": [ag["identity_name"]]},
                "severity": "warning",
                "title": f"{ag['identity_name']} · Heartbeat 未启用",
                "detail": (
                    f"{ag['identity_name']} 的 Heartbeat 当前处于关闭状态。"
                    f"启用后，Agent 可以在无人交互时主动执行后台任务、整理记忆或发送主动消息，"
                    f"让它更有'存在感'。"
                ),
                "agent": ag["id"],
            })
        else:
            names = "、".join(ag["identity_name"] for ag in no_heartbeat)
            suggestions.append({
                "type": "config",
                "subtype": "heartbeat",
                "data": {"agents": [ag["id"] for ag in no_heartbeat], "names": [ag["identity_name"] for ag in no_heartbeat]},
                "severity": "warning",
                "title": f"{len(no_heartbeat)} 个 Agent 未启用 Heartbeat",
                "detail": (
                    f"{names} 目前均处于被动等待状态，完全依赖手动触发。"
                    f"为需要后台自主运行的 Agent 启用 Heartbeat，可以解锁主动执行任务的能力。"
                ),
                "agents": [ag["id"] for ag in no_heartbeat],
            })

    # D4：未配置任何 Cron 任务
    if cron_data.get("total_jobs", 0) == 0:
        suggestions.append({
            "type": "config",
            "subtype": "no_cron_jobs",
            "severity": "warning",
            "data": {},
            "title": "尚未配置任何自动化任务",
            "detail": (
                "你目前没有任何 Cron 任务，所有 Agent 行为都依赖手动触发。"
                "Cron 可以让 Agent 定时完成日报生成、信息监控、数据同步等重复性工作。"
                "可以从一个最常用的场景开始，配置第一个自动化任务。"
            ),
        })

    # D5：有 Cron 任务但无消息推送渠道
    channels = ch.get("channels", {})
    has_channel = channels.get("telegram_enabled") or channels.get("discord_enabled")
    if not has_channel and cron_data.get("total_jobs", 0) > 0:
        suggestions.append({
            "type": "config",
            "subtype": "no_delivery_channels",
            "severity": "warning",
            "data": {},
            "title": "已有 Cron 任务但未配置消息推送渠道",
            "detail": (
                "你配置了 Cron 任务，但 Telegram 和 Discord 推送均未启用。"
                "任务执行结果只能通过主动查询日志获取，无法及时感知运行状态或异常。"
                "建议配置至少一个推送渠道。"
            ),
        })

    # D6：SKILL.md 内容为空的 Skill
    empty_skill_mds = [
        sk for sk in skills
        if sk.get("has_skill_md") and sk.get("skill_md_lines", 0) < 3
        and sk["name"] != "dist"
    ]
    if empty_skill_mds:
        names = "、".join(sk["name"] for sk in empty_skill_mds[:3])
        suggestions.append({
            "type": "config",
            "subtype": "empty_skill_md",
            "severity": "warning",
            "data": {"count": len(empty_skill_mds), "skills": [sk["name"] for sk in empty_skill_mds]},
            "title": f"{len(empty_skill_mds)} 个 Skill 的 SKILL.md 内容为空",
            "detail": (
                f"{names} 等 Skill 的 SKILL.md 几乎没有内容。"
                f"Agent 依赖 SKILL.md 理解如何调用该 Skill，文件缺失时 Skill 功能无法正常激活。"
                f"建议检查是否为未完成安装的残留目录。"
            ),
            "skills": [sk["name"] for sk in empty_skill_mds],
        })

    # MEMORY：长期活跃但记忆文件稀少
    for ag in ag_health_list:
        session_stats = agent_session_map.get(ag["id"])
        if not session_stats:
            continue
        session_count = session_stats.get("session_count", 0)
        mem = ag["files"].get("MEMORY.md", {})
        mem_lines = mem.get("meaningful_lines", 0)
        if session_count >= 10 and mem_lines < 3:
            suggestions.append({
                "type": "config",
                "subtype": "memory_sparse",
                "severity": "warning",
                "data": {
                    "agent": ag["id"],
                    "name": ag["identity_name"],
                    "session_count": session_count,
                    "memory_lines": mem_lines,
                },
                "title": f"{ag['identity_name']} · MEMORY.md 内容稀少",
                "detail": (
                    f"{ag['identity_name']} 已累积 {session_count} 个 session，"
                    f"但 MEMORY.md 目前只有 {mem_lines} 行有效内容。"
                    f"MEMORY.md 是 Agent 跨 session 保留关键信息的机制，内容过少意味着重要上下文可能在会话结束后丢失。"
                    f"建议检查 Agent 是否在正常写入记忆。"
                ),
                "agent": ag["id"],
                "session_count": session_count,
                "memory_lines": mem_lines,
            })

    return suggestions


# ── 主函数 ───────────────────────────────────────────────────────────

def main():
    print("正在解析 Session 文件...")
    sessions = collect_sessions()
    print(f"  找到 {len(sessions)} 个有效 session")

    print("正在解析 Cron 任务...")
    cron_data = collect_cron_data()
    print(f"  找到 {cron_data['total_jobs']} 个 Cron 任务，{cron_data['total_runs']} 条运行记录")

    print("正在收集 Skill 信息...")
    skills = collect_skills()
    print(f"  找到 {len(skills)} 个 Skill")

    print("正在检查配置健康状态...")
    active_agents = list({s["agent"] for s in sessions})
    config_health = collect_config_health(active_agents)
    print(f"  检查了 {len(config_health['agents'])} 个 Agent 的配置")

    print("正在聚合分析...")
    result = aggregate(sessions, cron_data, skills, config_health)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"完成，已写入 {OUTPUT_FILE}")
    return result


if __name__ == "__main__":
    main()
