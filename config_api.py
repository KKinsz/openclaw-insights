#!/usr/bin/env python3
"""
OpenClaw Config API
配置读写 + 脱敏 + 备份逻辑
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import copy
from datetime import datetime

BASE = os.environ.get("OPENCLAW_HOME", os.path.expanduser("~/.openclaw"))
WORKSPACE = os.path.join(BASE, "workspace")
AGENTS = ["main", "monitor", "note", "code", "image"]
AGENT_FILES = ["SOUL", "USER", "IDENTITY", "AGENTS", "MEMORY", "HEARTBEAT", "TOOLS"]
GATEWAY_MODES = {"local", "remote"}
GATEWAY_BINDS = {"auto", "loopback", "lan", "tailnet", "custom"}
DM_POLICIES = {"pairing", "allowlist", "open", "disabled"}
GROUP_POLICIES = {"open", "disabled", "allowlist"}
CHUNK_MODES = {"length", "newline"}
STREAMING_MODES = {"off", "partial", "block", "progress"}


# ── 工具函数 ──────────────────────────────────────────────────────────

def mask_key(key: str) -> str:
    """脱敏 API Key：保留前缀 + 后6位"""
    if not key or len(key) < 12:
        return "***"
    # 保留 sk-xxx- 这种前缀结构，最多12个前缀字符
    prefix_match = re.match(r"^(sk-[a-z0-9-]{0,12})", key)
    prefix = prefix_match.group(1) if prefix_match else key[:6]
    suffix = key[-6:]
    return f"{prefix}***{suffix}"


def mask_token(token: str) -> str:
    """JWT token 脱敏：只保留稳定身份信息，不拼接本地化文案"""
    if not token:
        return ""
    try:
        import base64
        parts = token.split(".")
        if len(parts) == 3:
            # 补全 base64 padding
            payload = parts[1] + "=" * (4 - len(parts[1]) % 4)
            data = json.loads(base64.b64decode(payload).decode("utf-8"))
            email = data.get("https://api.openai.com/profile", {}).get("email", "")
            if email:
                return f"[JWT] {email}"
    except Exception:
        pass
    return f"***{token[-8:]}"


def backup_file(path: str) -> str:
    """写入前备份文件，返回备份路径"""
    if not os.path.exists(path):
        return ""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{path}.bak.{ts}"
    shutil.copy2(path, backup_path)
    return backup_path


def read_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, data: dict) -> str:
    backup = backup_file(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return backup


def read_md(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()


def write_md(path: str, content: str) -> str:
    backup = backup_file(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return backup


def md_summary(content: str, length: int = 60) -> str:
    """提取 Markdown 前 N 个有效字符作为摘要"""
    lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#")]
    text = " ".join(lines)
    return text[:length] + ("..." if len(text) > length else "")


def run_openclaw_json(args: list[str], timeout: int = 10, env=None):
    """运行 openclaw CLI 并解析 JSON 输出。失败时返回 None。"""
    try:
        run_kwargs = {
            "capture_output": True,
            "text": True,
            "timeout": timeout,
        }
        if env is not None:
            run_kwargs["env"] = env
        result = subprocess.run(args, **run_kwargs)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

    if result.returncode != 0:
        return None

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def mask_sensitive(value, key: str = ""):
    """递归脱敏渠道配置中的敏感字段。"""
    if isinstance(value, dict):
        return {k: mask_sensitive(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [mask_sensitive(v, key) for v in value]
    if isinstance(value, str) and any(s in key.lower() for s in ("token", "secret", "key", "password")):
        return mask_key(value) if value else ""
    return value


def normalize_channel_streaming_mode(channel_name: str, raw_value):
    """将 mixed-type streaming 字段归一化为 UI 可展示的模式值。"""
    if raw_value in (None, "", False):
        return "off"

    if isinstance(raw_value, str):
        normalized = raw_value.strip().lower()
    elif raw_value is True:
        normalized = "true"
    else:
        normalized = str(raw_value).strip().lower()

    if channel_name == "telegram":
        if normalized in ("off", "false", "0"):
            return "off"
        if normalized == "block":
            return "block"
        if normalized in ("partial", "true", "on"):
            return "partial"
        return normalized or "off"

    if normalized in ("off", "false", "0"):
        return "off"
    if normalized in ("block", "true", "on", "partial"):
        return "block"
    return normalized or "off"


def channel_streaming_options(channel_name: str):
    if channel_name == "telegram":
        return [
            {"value": "off", "label_key": "ch_streaming_off"},
            {"value": "partial", "label_key": "ch_streaming_partial"},
            {"value": "block", "label_key": "ch_streaming_block"},
        ]
    return [
        {"value": "off", "label_key": "ch_streaming_off"},
        {"value": "block", "label_key": "ch_streaming_block"},
    ]


def channel_streaming_overrides(channel_name: str, ch_data: dict):
    channel_mode = normalize_channel_streaming_mode(channel_name, ch_data.get("streaming"))
    accounts = ch_data.get("accounts", {})
    named_accounts = []
    has_default_account_override = False

    for account_name, account_cfg in accounts.items():
        if not isinstance(account_cfg, dict) or "streaming" not in account_cfg:
            continue
        account_mode = normalize_channel_streaming_mode(channel_name, account_cfg.get("streaming"))
        if account_name == "default":
            has_default_account_override = account_mode != channel_mode
            continue
        if account_mode != channel_mode:
            named_accounts.append(account_name)

    return {
        "count": len(named_accounts),
        "accounts": named_accounts,
        "has_default_account_override": has_default_account_override,
    }


def merge_patch(original: dict, patch: dict) -> dict:
    """深度合并：patch 中 None/空字符串不覆盖原值"""
    result = dict(original)
    for k, v in patch.items():
        if v is None or v == "":
            continue  # 空值不覆盖
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = merge_patch(result[k], v)
        else:
            result[k] = v
    return result


def validate_patch_keys(patch: dict, allowed_keys: set[str], label: str):
    if not isinstance(patch, dict):
        return {"error": f"{label} patch must be an object"}

    unknown = sorted(k for k in patch.keys() if k not in allowed_keys)
    if unknown:
        return {"error": f"unsupported {label} field(s): {', '.join(unknown)}"}
    return None


def validate_choice(value, allowed: set[str], label: str):
    if not isinstance(value, str) or value not in allowed:
        allowed_str = ", ".join(sorted(allowed))
        return {"error": f"{label} must be one of: {allowed_str}"}
    return None


def validate_positive_int(value, label: str):
    if isinstance(value, bool):
        return {"error": f"{label} must be a positive integer"}
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return {"error": f"{label} must be a positive integer"}
    if parsed <= 0:
        return {"error": f"{label} must be a positive integer"}
    return None


def validate_optional_string(value, label: str):
    if value == "":
        return None
    if not isinstance(value, str):
        return {"error": f"{label} must be a string"}
    return None


def validate_channel_streaming(value, label: str):
    if isinstance(value, bool):
        return None
    if isinstance(value, str) and value in STREAMING_MODES:
        return None
    allowed_str = ", ".join(sorted(STREAMING_MODES))
    return {"error": f"{label} must be boolean or one of: {allowed_str}"}


def apply_json_path_updates(original: dict, updates: list[dict]) -> dict:
    result = copy.deepcopy(original)
    for update in updates:
        path = update.get("path")
        if not isinstance(path, (list, tuple)) or not path:
            raise ValueError("update path must be a non-empty list")
        cursor = result
        for key in path[:-1]:
            child = cursor.get(key)
            if not isinstance(child, dict):
                child = {}
                cursor[key] = child
            cursor = child
        cursor[path[-1]] = update.get("value")
    return result


def validate_model_references(candidate_path: str):
    env = {**os.environ, "OPENCLAW_CONFIG_PATH": candidate_path}
    payload = run_openclaw_json(["openclaw", "models", "list", "--json"], timeout=15, env=env)
    if not isinstance(payload, dict) or not isinstance(payload.get("models"), list):
        return {"error": "unable to resolve configured models for validation"}

    allowed = {
        model.get("key")
        for model in payload["models"]
        if isinstance(model, dict)
        and isinstance(model.get("key"), str)
        and not model.get("missing", False)
    }
    cfg = read_json(candidate_path)
    defaults = cfg.get("agents", {}).get("defaults", {})
    checks = [
        ("agents.defaults.model.primary", defaults.get("model", {}).get("primary")),
        ("agents.defaults.imageModel.primary", defaults.get("imageModel", {}).get("primary")),
    ]
    checks.extend(
        (f"agents.defaults.model.fallbacks[{idx}]", value)
        for idx, value in enumerate(defaults.get("model", {}).get("fallbacks", []))
    )
    checks.extend(
        (f"agents.defaults.imageModel.fallbacks[{idx}]", value)
        for idx, value in enumerate(defaults.get("imageModel", {}).get("fallbacks", []))
    )

    missing = [path for path, value in checks if value and value not in allowed]
    if missing:
        return {"error": f"unresolved model reference(s): {', '.join(missing)}"}
    return None


def validate_openclaw_candidate(candidate_path: str):
    env = {**os.environ, "OPENCLAW_CONFIG_PATH": candidate_path}
    payload = run_openclaw_json(["openclaw", "config", "validate", "--json"], timeout=15, env=env)
    if not isinstance(payload, dict):
        return {"error": "unable to validate candidate config with openclaw"}
    if not payload.get("valid", False):
        issue = payload.get("issues", [{}])[0] if isinstance(payload.get("issues"), list) else {}
        issue_path = issue.get("path", "unknown")
        message = issue.get("message", "schema validation failed")
        return {"error": f"config validation failed at {issue_path}: {message}"}
    return validate_model_references(candidate_path)


def write_openclaw_json(path: str, data: dict) -> dict:
    fd, candidate_path = tempfile.mkstemp(prefix="openclaw.", suffix=".json", dir=os.path.dirname(path))
    os.close(fd)
    try:
        with open(candidate_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        error = validate_openclaw_candidate(candidate_path)
        if error:
            return error
        backup = backup_file(path)
        os.replace(candidate_path, path)
        return {"success": True, "backup": backup}
    finally:
        if os.path.exists(candidate_path):
            os.unlink(candidate_path)


# ── 全局配置 ─────────────────────────────────────────────────────────

def get_global_cron() -> dict:
    jobs_file = os.path.join(BASE, "cron", "jobs.json")
    runs_dir = os.path.join(BASE, "cron", "runs")
    data = read_json(jobs_file)
    jobs = data.get("jobs", []) if isinstance(data, dict) else []

    # 读取运行记录
    run_stats = {}
    if os.path.exists(runs_dir):
        for f in os.listdir(runs_dir):
            if not f.endswith(".jsonl"):
                continue
            job_id = f.replace(".jsonl", "")
            runs = []
            with open(os.path.join(runs_dir, f), encoding="utf-8") as fp:
                for line in fp:
                    line = line.strip()
                    if line:
                        try:
                            runs.append(json.loads(line))
                        except Exception:
                            pass
            finished = [r for r in runs if r.get("action") == "finished"]
            success = sum(1 for r in finished if r.get("status") == "ok")
            run_stats[job_id] = {
                "total": len(finished),
                "success": success,
                "rate": round(success / len(finished), 3) if finished else None,
            }

    enriched = []
    for job in jobs:
        jid = job.get("id", "")
        stats = run_stats.get(jid, {})
        state = job.get("state", {})
        enriched.append({
            "id": jid,
            "name": job.get("name", ""),
            "enabled": job.get("enabled", True),
            "agent": job.get("agentId", ""),
            "schedule": job.get("schedule", {}).get("expr", ""),
            "tz": job.get("schedule", {}).get("tz", ""),
            "payload_message": job.get("payload", {}).get("message", ""),
            "timeout_seconds": job.get("payload", {}).get("timeoutSeconds", 300),
            "thinking": job.get("payload", {}).get("thinking", "low"),
            "delivery_mode": job.get("delivery", {}).get("mode", "none"),
            "delivery_channel": job.get("delivery", {}).get("channel", ""),
            "failure_alert_after": job.get("failureAlert", {}).get("after", 1),
            "last_status": state.get("lastRunStatus"),
            "last_run_at": state.get("lastRunAtMs"),
            "consecutive_errors": state.get("consecutiveErrors", 0),
            "run_total": stats.get("total", 1 if state.get("lastRunAtMs") else 0),
            "run_success_rate": stats.get("rate"),
            "avg_duration_ms": state.get("lastDurationMs"),
        })

    enabled_count = sum(1 for j in enriched if j["enabled"])
    rates = [j["run_success_rate"] for j in enriched if j["run_success_rate"] is not None]
    avg_rate = round(sum(rates) / len(rates), 3) if rates else None

    return {
        "summary": {
            "total": len(enriched),
            "enabled": enabled_count,
            "avg_success_rate": avg_rate,
        },
        "jobs": enriched,
    }


def patch_cron_job(job_id: str, patch: dict) -> dict:
    jobs_file = os.path.join(BASE, "cron", "jobs.json")
    data = read_json(jobs_file)
    jobs = data.get("jobs", []) if isinstance(data, dict) else []

    updated = False
    for job in jobs:
        if job.get("id") == job_id:
            # 允许修改的字段白名单
            allowed = {
                "enabled", "schedule_expr", "tz", "payload_message",
                "timeout_seconds", "thinking", "delivery_mode"
            }
            if "enabled" in patch and patch["enabled"] is not None:
                job["enabled"] = bool(patch["enabled"])
            if "schedule_expr" in patch and patch["schedule_expr"]:
                job.setdefault("schedule", {})["expr"] = patch["schedule_expr"]
            if "tz" in patch and patch["tz"]:
                job.setdefault("schedule", {})["tz"] = patch["tz"]
            if "payload_message" in patch and patch["payload_message"]:
                job.setdefault("payload", {})["message"] = patch["payload_message"]
            if "timeout_seconds" in patch and patch["timeout_seconds"]:
                job.setdefault("payload", {})["timeoutSeconds"] = int(patch["timeout_seconds"])
            if "thinking" in patch and patch["thinking"]:
                job.setdefault("payload", {})["thinking"] = patch["thinking"]
            job["updatedAtMs"] = int(datetime.now().timestamp() * 1000)
            updated = True
            break

    if not updated:
        return {"error": f"job {job_id} not found"}

    backup = write_json(jobs_file, data)
    return {"success": True, "backup": backup}


def get_global_models() -> dict:
    cfg = read_json(os.path.join(BASE, "openclaw.json"))
    global_providers = cfg.get("models", {}).get("providers", {})

    providers = []
    for pid, pdata in global_providers.items():
        masked_key = mask_key(pdata.get("apiKey", "")) if pdata.get("apiKey") else None
        models = []
        for m in pdata.get("models", []):
            models.append({
                "id": m.get("id"),
                "name": m.get("name"),
                "reasoning": m.get("reasoning", False),
                "context_window": m.get("contextWindow"),
                "max_tokens": m.get("maxTokens"),
                "cost_input": m.get("cost", {}).get("input", 0),
                "cost_output": m.get("cost", {}).get("output", 0),
            })
        providers.append({
            "id": pid,
            "base_url": pdata.get("baseUrl", ""),
            "api": pdata.get("api", ""),
            "api_key_masked": masked_key,
            "has_api_key": bool(pdata.get("apiKey")),
            "model_count": len(models),
            "models": models,
        })

    return {
        "summary": {
            "provider_count": len(providers),
            "model_count": sum(p["model_count"] for p in providers),
        },
        "providers": providers,
    }


def patch_global_models(provider_id: str, patch: dict) -> dict:
    error = validate_patch_keys(patch, {"base_url", "api_key"}, "models")
    if error:
        return error

    for field in ("base_url", "api_key"):
        if field in patch:
            error = validate_optional_string(patch[field], field)
            if error:
                return error

    path = os.path.join(BASE, "openclaw.json")
    data = read_json(path)
    providers = data.get("models", {}).get("providers", {})

    if provider_id not in providers:
        return {"error": f"provider {provider_id} not found"}

    updates = []
    if patch.get("base_url"):
        updates.append({"path": ["models", "providers", provider_id, "baseUrl"], "value": patch["base_url"]})
    if patch.get("api_key"):
        updates.append({"path": ["models", "providers", provider_id, "apiKey"], "value": patch["api_key"]})

    data = apply_json_path_updates(data, updates)
    return write_openclaw_json(path, data)


def get_global_acp() -> dict:
    cfg = read_json(os.path.join(BASE, "openclaw.json"))
    acp = cfg.get("acp", {})
    return {
        "enabled": acp.get("enabled", True),
        "backend": acp.get("backend", ""),
        "default_agent": acp.get("defaultAgent", ""),
        "allowed_agents": acp.get("allowedAgents", []),
        "max_concurrent_sessions": acp.get("maxConcurrentSessions", 8),
        "coalesce_idle_ms": acp.get("stream", {}).get("coalesceIdleMs", 300),
        "max_chunk_chars": acp.get("stream", {}).get("maxChunkChars", 1200),
        "ttl_minutes": acp.get("runtime", {}).get("ttlMinutes", 120),
        "dispatch_enabled": acp.get("dispatch", {}).get("enabled", True),
    }


def patch_global_acp(patch: dict) -> dict:
    error = validate_patch_keys(
        patch,
        {"max_concurrent_sessions", "ttl_minutes", "default_agent", "coalesce_idle_ms"},
        "acp",
    )
    if error:
        return error

    for field in ("max_concurrent_sessions", "ttl_minutes", "coalesce_idle_ms"):
        if field in patch and patch[field] is not None:
            error = validate_positive_int(patch[field], field)
            if error:
                return error
    if "default_agent" in patch:
        error = validate_optional_string(patch["default_agent"], "default_agent")
        if error:
            return error

    path = os.path.join(BASE, "openclaw.json")
    data = read_json(path)
    updates = []
    if patch.get("max_concurrent_sessions") is not None:
        updates.append({"path": ["acp", "maxConcurrentSessions"], "value": int(patch["max_concurrent_sessions"])})
    if patch.get("ttl_minutes") is not None:
        updates.append({"path": ["acp", "runtime", "ttlMinutes"], "value": int(patch["ttl_minutes"])})
    if patch.get("default_agent"):
        updates.append({"path": ["acp", "defaultAgent"], "value": patch["default_agent"]})
    if patch.get("coalesce_idle_ms") is not None:
        updates.append({"path": ["acp", "stream", "coalesceIdleMs"], "value": int(patch["coalesce_idle_ms"])})

    data = apply_json_path_updates(data, updates)
    return write_openclaw_json(path, data)


def get_global_gateway() -> dict:
    cfg = read_json(os.path.join(BASE, "openclaw.json"))
    gw = cfg.get("gateway", {})
    return {
        "port": gw.get("port", 18789),
        "mode": gw.get("mode", "local"),
        "bind": gw.get("bind", "loopback"),
        "auth_mode": gw.get("auth", {}).get("mode", "password"),
        "tailscale_mode": gw.get("tailscale", {}).get("mode", ""),
        "tailscale_reset_on_exit": gw.get("tailscale", {}).get("resetOnExit", False),
    }


def patch_global_gateway(patch: dict) -> dict:
    error = validate_patch_keys(patch, {"bind", "mode"}, "gateway")
    if error:
        return error
    if "bind" in patch:
        error = validate_choice(patch["bind"], GATEWAY_BINDS, "gateway.bind")
        if error:
            return error
    if "mode" in patch:
        error = validate_choice(patch["mode"], GATEWAY_MODES, "gateway.mode")
        if error:
            return error

    path = os.path.join(BASE, "openclaw.json")
    data = read_json(path)
    updates = []
    if patch.get("bind") in GATEWAY_BINDS:
        updates.append({"path": ["gateway", "bind"], "value": patch["bind"]})
    if patch.get("mode") in GATEWAY_MODES:
        updates.append({"path": ["gateway", "mode"], "value": patch["mode"]})

    data = apply_json_path_updates(data, updates)
    return write_openclaw_json(path, data)


def get_global_channels() -> dict:
    cfg = read_json(os.path.join(BASE, "openclaw.json"))
    channels = cfg.get("channels", {})

    result = {}
    for ch_name, ch_data in channels.items():
        if isinstance(ch_data, dict):
            safe = mask_sensitive(ch_data)
            safe["streaming_mode"] = normalize_channel_streaming_mode(ch_name, ch_data.get("streaming"))
            safe["streaming_options"] = channel_streaming_options(ch_name)
            safe["streaming_overrides"] = channel_streaming_overrides(ch_name, ch_data)
            result[ch_name] = safe

    return result


def patch_global_channel(channel_name: str, patch: dict) -> dict:
    safe_fields = {"enabled", "dmPolicy", "groupPolicy", "streaming",
                   "chunkMode", "textChunkLimit", "maxLinesPerMessage"}
    error = validate_patch_keys(patch, safe_fields, f"channel {channel_name}")
    if error:
        return error
    if "enabled" in patch and not isinstance(patch["enabled"], bool):
        return {"error": "enabled must be a boolean"}
    if "dmPolicy" in patch:
        error = validate_choice(patch["dmPolicy"], DM_POLICIES, "dmPolicy")
        if error:
            return error
    if "groupPolicy" in patch:
        error = validate_choice(patch["groupPolicy"], GROUP_POLICIES, "groupPolicy")
        if error:
            return error
    if "streaming" in patch:
        error = validate_channel_streaming(patch["streaming"], f"{channel_name}.streaming")
        if error:
            return error
    if "chunkMode" in patch:
        error = validate_choice(patch["chunkMode"], CHUNK_MODES, "chunkMode")
        if error:
            return error
    for field in ("textChunkLimit", "maxLinesPerMessage"):
        if field in patch and patch[field] is not None:
            error = validate_positive_int(patch[field], field)
            if error:
                return error

    path = os.path.join(BASE, "openclaw.json")
    data = read_json(path)
    channels = data.setdefault("channels", {})

    if channel_name not in channels:
        return {"error": f"channel {channel_name} not found"}

    updates = []
    for k, v in patch.items():
        if k in safe_fields and v is not None:
            updates.append({"path": ["channels", channel_name, k], "value": v})

    data = apply_json_path_updates(data, updates)
    return write_openclaw_json(path, data)


def patch_global_channel_account(channel_name: str, account_name: str, patch: dict) -> dict:
    error = validate_patch_keys(patch, {"streaming"}, f"channel account {channel_name}/{account_name}")
    if error:
        return error
    if "streaming" in patch:
        error = validate_channel_streaming(patch["streaming"], f"{channel_name}.{account_name}.streaming")
        if error:
            return error

    path = os.path.join(BASE, "openclaw.json")
    data = read_json(path)
    channels = data.setdefault("channels", {})

    if channel_name not in channels:
        return {"error": f"channel {channel_name} not found"}

    channel = channels[channel_name]
    accounts = channel.get("accounts")
    if not isinstance(accounts, dict):
        return {"error": f"channel {channel_name} has no accounts"}
    if account_name not in accounts:
        return {"error": f"account {account_name} not found"}

    account = accounts[account_name]
    if not isinstance(account, dict):
        return {"error": f"account {account_name} is invalid"}

    updates = []
    if patch.get("streaming") is not None:
        updates.append({
            "path": ["channels", channel_name, "accounts", account_name, "streaming"],
            "value": patch["streaming"],
        })

    data = apply_json_path_updates(data, updates)
    return write_openclaw_json(path, data)


def scan_managed_skills() -> dict:
    """回退逻辑：只扫描 ~/.openclaw/skills。"""
    skills_dir = os.path.join(BASE, "skills")
    skills = []
    if not os.path.exists(skills_dir):
        return {"total": 0, "skills": []}

    for name in sorted(os.listdir(skills_dir)):
        skill_path = os.path.join(skills_dir, name)
        if not os.path.isdir(skill_path):
            continue
        skill_md_path = os.path.join(skill_path, "SKILL.md")
        if not os.path.exists(skill_md_path):
            continue
        content = read_md(skill_md_path)
        has_scripts = os.path.isdir(os.path.join(skill_path, "scripts"))
        skills.append({
            "name": name,
            "source": "openclaw-managed",
            "bundled": False,
            "eligible": True,
            "has_skill_md": bool(content),
            "has_scripts": has_scripts,
            "summary": md_summary(content, 80),
            "char_count": len(content),
        })

    return {"total": len(skills), "skills": skills}


def resolve_skill_base_dir(skill: dict, workspace_dir: str, managed_skills_dir: str) -> str:
    source = skill.get("source", "")
    if source == "openclaw-managed" and managed_skills_dir:
        return os.path.join(managed_skills_dir, skill["name"])
    if source == "openclaw-workspace" and workspace_dir:
        return os.path.join(workspace_dir, "skills", skill["name"])
    return ""


def get_global_skills() -> dict:
    payload = run_openclaw_json(
        ["openclaw", "skills", "list", "--eligible", "--json"],
        timeout=10,
    )
    if not isinstance(payload, dict):
        return scan_managed_skills()

    raw_skills = payload.get("skills")
    if not isinstance(raw_skills, list):
        return scan_managed_skills()

    workspace_dir = payload.get("workspaceDir", "")
    managed_skills_dir = payload.get("managedSkillsDir", "")
    skills = []
    for skill in raw_skills:
        if not isinstance(skill, dict):
            continue
        summary = skill.get("description", "") or ""
        base_dir = resolve_skill_base_dir(skill, workspace_dir, managed_skills_dir)
        skills.append({
            "name": skill.get("name", ""),
            "source": skill.get("source", ""),
            "bundled": bool(skill.get("bundled", False)),
            "eligible": bool(skill.get("eligible", False)),
            "has_skill_md": True,
            "has_scripts": bool(base_dir) and os.path.isdir(os.path.join(base_dir, "scripts")),
            "summary": md_summary(summary, 80) if summary else "",
        })

    return {"total": len(skills), "skills": skills}


def get_skill_content(skill_name: str) -> dict:
    info = run_openclaw_json(
        ["openclaw", "skills", "info", skill_name, "--json"],
        timeout=10,
    )
    path = info.get("filePath", "") if isinstance(info, dict) else ""
    if not path:
        path = os.path.join(BASE, "skills", skill_name, "SKILL.md")
    content = read_md(path)
    return {"name": skill_name, "content": content, "path": path}


def get_global_defaults() -> dict:
    cfg = read_json(os.path.join(BASE, "openclaw.json"))
    defaults = cfg.get("agents", {}).get("defaults", {})
    return {
        "primary_model": defaults.get("model", {}).get("primary", ""),
        "fallback_models": defaults.get("model", {}).get("fallbacks", []),
        "image_primary": defaults.get("imageModel", {}).get("primary", ""),
        "image_fallbacks": defaults.get("imageModel", {}).get("fallbacks", []),
    }


def patch_global_defaults(patch: dict) -> dict:
    error = validate_patch_keys(
        patch,
        {"primary_model", "fallback_models", "image_primary", "image_fallbacks"},
        "defaults",
    )
    if error:
        return error
    for field in ("primary_model", "image_primary"):
        if field in patch and not isinstance(patch[field], str):
            return {"error": f"{field} must be a string"}
    for field in ("fallback_models", "image_fallbacks"):
        if field in patch and not isinstance(patch[field], list):
            return {"error": f"{field} must be a list of strings"}
        if field in patch and any(not isinstance(m, str) for m in patch[field]):
            return {"error": f"{field} must be a list of strings"}

    path = os.path.join(BASE, "openclaw.json")
    data = read_json(path)
    updates = []
    if "primary_model" in patch and isinstance(patch["primary_model"], str):
        updates.append({"path": ["agents", "defaults", "model", "primary"], "value": patch["primary_model"]})
    if "fallback_models" in patch and isinstance(patch["fallback_models"], list):
        updates.append({
            "path": ["agents", "defaults", "model", "fallbacks"],
            "value": [m for m in patch["fallback_models"] if isinstance(m, str)],
        })
    if "image_primary" in patch and isinstance(patch["image_primary"], str):
        updates.append({"path": ["agents", "defaults", "imageModel", "primary"], "value": patch["image_primary"]})
    if "image_fallbacks" in patch and isinstance(patch["image_fallbacks"], list):
        updates.append({
            "path": ["agents", "defaults", "imageModel", "fallbacks"],
            "value": [m for m in patch["image_fallbacks"] if isinstance(m, str)],
        })

    data = apply_json_path_updates(data, updates)
    return write_openclaw_json(path, data)


# ── Agent 配置 ────────────────────────────────────────────────────────

def get_agent_config(agent_id: str) -> dict:
    ws_path = os.path.join(WORKSPACE, agent_id)
    if not os.path.exists(ws_path):
        return {"error": f"agent {agent_id} workspace not found"}

    files = {}
    for fname in AGENT_FILES:
        fpath = os.path.join(ws_path, f"{fname}.md")
        content = read_md(fpath)
        files[fname.lower()] = {
            "exists": bool(content),
            "char_count": len(content),
            "summary": md_summary(content, 80),
            "path": fpath,
        }

    return {
        "agent_id": agent_id,
        "files": files,
        "has_models": os.path.exists(os.path.join(ws_path, "models.json")),
        "has_auth": os.path.exists(os.path.join(ws_path, "auth-profiles.json")),
    }


def get_agent_file(agent_id: str, file_key: str) -> dict:
    """读取 agent 的 .md 文件内容"""
    fname = file_key.upper()
    if fname not in AGENT_FILES:
        return {"error": f"unknown file {file_key}"}
    fpath = os.path.join(WORKSPACE, agent_id, f"{fname}.md")
    content = read_md(fpath)
    return {
        "agent_id": agent_id,
        "file": file_key,
        "content": content,
        "path": fpath,
        "exists": os.path.exists(fpath),
    }


def put_agent_file(agent_id: str, file_key: str, content: str) -> dict:
    fname = file_key.upper()
    if fname not in AGENT_FILES:
        return {"error": f"unknown file {file_key}"}
    if not content and content != "":
        return {"error": "content required"}

    fpath = os.path.join(WORKSPACE, agent_id, f"{fname}.md")
    backup = write_md(fpath, content)
    return {"success": True, "backup": backup, "path": fpath}


def get_agent_models(agent_id: str) -> dict:
    path = os.path.join(WORKSPACE, agent_id, "models.json")
    data = read_json(path)
    providers = data.get("providers", {})

    result = []
    for pid, pdata in providers.items():
        masked_key = mask_key(pdata.get("apiKey", "")) if pdata.get("apiKey") else None
        result.append({
            "id": pid,
            "base_url": pdata.get("baseUrl", ""),
            "api": pdata.get("api", ""),
            "api_key_masked": masked_key,
            "has_api_key": bool(pdata.get("apiKey")),
            "model_count": len(pdata.get("models", [])),
            "models": [{"id": m.get("id"), "name": m.get("name")} for m in pdata.get("models", [])],
        })

    return {
        "agent_id": agent_id,
        "provider_count": len(result),
        "providers": result,
    }


def patch_agent_models(agent_id: str, provider_id: str, patch: dict) -> dict:
    error = validate_patch_keys(patch, {"base_url", "api_key"}, f"agent {agent_id} models")
    if error:
        return error

    path = os.path.join(WORKSPACE, agent_id, "models.json")
    data = read_json(path)
    providers = data.get("providers", {})

    if provider_id not in providers:
        return {"error": f"provider {provider_id} not found"}

    p = providers[provider_id]
    if patch.get("base_url"):
        p["baseUrl"] = patch["base_url"]
    if patch.get("api_key"):
        p["apiKey"] = patch["api_key"]

    backup = write_json(path, data)
    return {"success": True, "backup": backup}


def get_agent_auth(agent_id: str) -> dict:
    path = os.path.join(WORKSPACE, agent_id, "auth-profiles.json")
    data = read_json(path)
    profiles = data.get("profiles", {})
    usage = data.get("usageStats", {})

    result = []
    for pid, pdata in profiles.items():
        auth_type = pdata.get("type", "")
        safe = {
            "id": pid,
            "provider": pdata.get("provider", ""),
            "type": auth_type,
        }
        if auth_type == "api_key":
            safe["key_masked"] = mask_key(pdata.get("key", ""))
        elif auth_type == "token":
            safe["token_masked"] = mask_key(pdata.get("token", ""))
        elif auth_type == "oauth":
            safe["display"] = mask_token(pdata.get("access", ""))
            safe["expires"] = pdata.get("expires")

        stats = usage.get(pid, {})
        safe["last_used"] = stats.get("lastUsed")
        safe["error_count"] = stats.get("errorCount", 0)
        safe["last_failure"] = stats.get("lastFailureAt")
        result.append(safe)

    return {"agent_id": agent_id, "profiles": result}


def patch_agent_auth(agent_id: str, profile_id: str, patch: dict) -> dict:
    error = validate_patch_keys(patch, {"key", "token"}, f"agent {agent_id} auth")
    if error:
        return error

    path = os.path.join(WORKSPACE, agent_id, "auth-profiles.json")
    data = read_json(path)
    profiles = data.get("profiles", {})

    if profile_id not in profiles:
        return {"error": f"profile {profile_id} not found"}

    p = profiles[profile_id]
    auth_type = p.get("type", "")

    if auth_type == "api_key" and patch.get("key"):
        p["key"] = patch["key"]
    elif auth_type == "token" and patch.get("token"):
        p["token"] = patch["token"]
    else:
        return {"error": "oauth credentials cannot be updated manually"}

    backup = write_json(path, data)
    return {"success": True, "backup": backup}


# ── Gateway 重启 ──────────────────────────────────────────────────────

def restart_gateway() -> dict:
    """尝试重启 OpenClaw Gateway"""
    methods = [
        # 方法1: openclaw CLI
        lambda: subprocess.run(
            ["openclaw", "restart"], capture_output=True, timeout=10
        ),
        # 方法2: pm2
        lambda: subprocess.run(
            ["pm2", "restart", "openclaw"], capture_output=True, timeout=10
        ),
    ]

    for method in methods:
        try:
            result = method()
            if result.returncode == 0:
                return {"success": True, "method": "cli"}
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    # 方法3: 找进程发送 SIGHUP
    try:
        result = subprocess.run(
            ["pgrep", "-f", "openclaw"],
            capture_output=True, text=True, timeout=5
        )
        pids = result.stdout.strip().split()
        if pids:
            import signal
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGHUP)
                except Exception:
                    pass
            return {"success": True, "method": "sighup", "pids": pids}
    except Exception:
        pass

    return {"success": False, "error": "无法自动重启，请手动执行 openclaw restart"}
