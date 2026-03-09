#!/usr/bin/env python3
"""
OpenClaw Insights Renderer
读取 data.json，生成 report.html
"""

import json
import os
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "data.json")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "report.html")

# ── i18n ──────────────────────────────────────────────────────────────
I18N = {
    "zh": {
        "lang_attr": "zh-CN",
        "ui_locale": "zh-CN",
        "generated_at": "生成于",
        "tab_insights": "数据洞察",
        "tab_config": "配置管理",
        "stat_sessions": "总会话数",
        "stat_messages": "总消息数",
        "stat_active_agents": "活跃 Agent",
        "stat_tokens": "总消耗 Token",
        "stat_cache": "缓存命中 Token",
        "stat_daily": "日均 Token",
        "stat_skills": "Skill 数量",
        "stat_cron_jobs": "Cron 数量",
        "stat_models": "模型数量",
        "stat_active_days": "活跃天数",
        "sec_agents": "Agent 概览",
        "sec_tokens": "Token 消耗",
        "sec_models": "模型策略",
        "sec_cron": "Cron 健康状况",
        "sec_patterns": "交互模式",
        "sec_suggestions": "优化建议",
        "agent_sessions": "会话数",
        "agent_messages": "消息数",
        "agent_input": "输入 Token",
        "agent_output": "输出 Token",
        "agent_daily": "日均 Token",
        "chart_7d": "7 日 Token 趋势",
        "chart_manual_vs_cron": "主动对话 vs Cron",
        "chart_manual": "主动对话",
        "chart_cron": "Cron 自动",
        "chart_tokens": "总消耗 Token",
        "chart_cache": "缓存命中 Token",
        "chart_model_dist": "模型 Token 分布",
        "model_col_model": "模型",
        "model_col_tokens": "总消耗 Token",
        "model_col_cache": "命中缓存",
        "model_col_messages": "消息数",
        "cron_total": lambda n: f"共 <strong class='text-white'>{n}</strong> 个任务",
        "cron_runs": lambda n: f"运行 <strong class='text-white'>{n}</strong> 次",
        "cron_success_rate": "综合成功率",
        "cron_most_reliable": "最可靠",
        "cron_per_run": "/次",
        "cron_consec_errors": lambda n: f"连续失败 {n} 次",
        "cron_no_record": "无记录",
        "channel_dist": "渠道分布",
        "time_of_day": "按时段消息分布",
        "tod_morning": "早晨 (6-12)",
        "tod_afternoon": "下午 (12-18)",
        "tod_evening": "傍晚 (18-24)",
        "tod_night": "深夜 (0-6)",
        "agent_msg_rank": "Agent 消息数排行",
        "installed_skills": "已安装 Skills",
        "footer_range": "数据范围",
        "footer_source": "由你的本地数据生成",
        "sec_global_config": "全局配置",
        "sec_agent_config": "Agent 配置",
        "btn_save": "保存",
        "btn_cancel": "取消",
        "btn_restart_now": "立即重启",
        "btn_restart_later": "稍后重启",
        "btn_restarting": "重启中...",
        "modal_saved": "配置已保存",
        "modal_restart_confirm": "是否立即重启 Gateway 使配置生效？",
        "agent_names": {
            "main": "Orca · 主控", "monitor": "Manta · 监控",
            "note": "Coral · 笔记", "code": "Octo · 代码",
            "image": "Jelly · 图像", "claude": "Claude",
            "codex": "Codex", "gemini": "Gemini", "glm-5": "GLM-5",
        },
        # JS 动态字符串
        "js": {
            "loading": "加载中...", "not_configured": "未配置",
            "file_exists": "已存在", "file_not_exists": "缺失",
            "file_empty": "（空）", "chars": "字符",
            "status_ok": "正常", "status_enabled": "已启用", "status_disabled": "已禁用",
            "never": "从未", "last_used": "最近使用",
            "model_config": "模型配置", "auth_creds": "认证凭证",
            "unsaved": "● 有未保存的修改",
            "oauth_readonly": "OAuth 凭证（只读）", "expires": "过期时间",
            "no_creds": "请输入新的凭证值", "no_desc": "无描述",
            "no_fallback": "无 fallback",
            "field_base_url": "Base URL", "field_api_key": "API Key",
            "field_backend": "后端", "field_key": "密钥", "field_token": "令牌",
            "field_coalesce_idle": "空闲聚合 (ms)",
            "channels_subtitle": "Telegram · Discord",
            "skill_title_prefix": "Skill：",
            "consec_errors": "连续失败 {n} 次", "runs": "{n} 次运行",
            "error_count": "{n} 次错误",
            "restart_ok": "Gateway 重启指令已发送",
            "restart_fail": "重启失败",
            "no_connect": "无法连接到本地服务，请手动重启",
            "save_error": "保存失败：",
            "card_cron": "Cron 任务", "card_defaults": "默认模型",
            "card_models": "模型提供商", "card_acp": "ACP 配置",
            "card_gateway": "Gateway", "card_channels": "消息渠道",
            "card_skills": "全局 Skills",
            "drawer_cron": "Cron 任务", "drawer_defaults": "默认模型配置",
            "drawer_models": "模型提供商", "drawer_acp": "ACP 配置",
            "drawer_gateway": "Gateway 配置", "drawer_channels": "消息渠道",
            "drawer_skills": "全局 Skills",
            "cron_plan": "计划", "cron_msg": "消息",
            "cron_runs_lbl": "运行", "cron_success": "成功率",
            "cron_timeout": "超时", "cron_thinking": "思考",
            "cron_think_low": "低思考", "cron_think_off": "关闭", "cron_think_auto": "自动",
            "cron_save_btn": "保存此任务",
            "cron_enable_confirm": "已更改 Cron 状态，是否重启 Gateway？",
            "cron_save_confirm": "已更新 Cron 任务配置，是否重启 Gateway？",
            "defaults_primary": "主模型", "defaults_fallback": "备用模型（当前顺序）",
            "defaults_image": "图像主模型",
            "defaults_image_fallback": "图像备用模型（当前顺序）",
            "defaults_multiline_hint": "每行一个模型 ID，留空表示不配置",
            "defaults_confirm": "已更新默认模型，是否重启 Gateway？",
            "models_count": "{n} 个模型", "providers_count": "{n} 个 Provider · {m} 个模型",
            "models_confirm": "已更新提供商配置，是否重启 Gateway？",
            "acp_max_sessions": "最大并发会话数", "acp_ttl": "会话保留时长（分钟）",
            "acp_default_agent": "默认 Agent",
            "acp_readonly": "只读信息", "acp_allowed_agents": "允许的 Agents",
            "acp_dispatch": "Dispatch", "acp_concurrent": "并发",
            "acp_confirm": "已更新 ACP 配置，是否重启 Gateway？",
            "gw_port": "端口号（只读）", "gw_mode": "运行模式",
            "gw_bind": "绑定地址", "gw_auth": "认证模式",
            "gw_local": "local (本机运行)", "gw_remote": "remote (连接远端)",
            "gw_loopback": "loopback (仅本机)", "gw_auto": "auto (自动选择)",
            "gw_lan": "lan (所有接口)", "gw_tailnet": "tailnet (仅 Tailnet)",
            "gw_custom": "custom (自定义地址)",
            "gw_warn": "修改 Gateway 配置后必须重启方可生效。端口号变更需手动更新访问地址。",
            "gw_confirm": "已更新 Gateway 配置，是否立即重启？",
            "ch_enable": "启用", "ch_streaming": "流式输出",
            "ch_streaming_mode": "流式模式",
            "ch_streaming_off": "关闭",
            "ch_streaming_partial": "Partial",
            "ch_streaming_block": "Block",
            "ch_override_none": "无账号级流式覆盖",
            "ch_override_accounts": "{n} 个账号覆盖",
            "ch_override_default": "default 账号也覆盖了默认值",
            "ch_accounts": "账号级配置概览",
            "ch_accounts_empty": "无独立账号配置",
            "ch_account": "账号",
            "ch_account_default": "默认账号",
            "ch_account_streaming": "流式模式",
            "ch_account_inherits": "继承渠道默认值",
            "ch_account_overrides": "覆盖渠道默认值",
            "ch_account_save_confirm": "{ch}/{account} 账号流式模式已更新，是否重启 Gateway？",
            "ch_confirm": "{ch} 渠道配置已更新，是否重启 Gateway？",
            "skill_readonly": "SKILL.md · 只读", "skill_no_content": "（无内容）",
            "skill_installed": "{n} 个已安装",
            "agent_file_confirm": "{label}.md 已保存，是否重启 Gateway？",
            "agent_model_confirm": "已更新模型配置，是否重启 Gateway？",
            "auth_confirm": "已更新凭证，是否重启 Gateway？",
            "save_modal_default": "是否重启 Gateway 使配置生效？",
            "enabled_count": "启用 {n}",
        },
    },
    "en": {
        "lang_attr": "en",
        "ui_locale": "en-US",
        "generated_at": "Generated",
        "tab_insights": "Insights",
        "tab_config": "Config",
        "stat_sessions": "Sessions",
        "stat_messages": "Messages",
        "stat_active_agents": "Active Agents",
        "stat_tokens": "Total Tokens",
        "stat_cache": "Cache Hits",
        "stat_daily": "Daily Avg",
        "stat_skills": "Skills",
        "stat_cron_jobs": "Cron Jobs",
        "stat_models": "Models",
        "stat_active_days": "Active Days",
        "sec_agents": "Agent Overview",
        "sec_tokens": "Token Usage",
        "sec_models": "Model Strategy",
        "sec_cron": "Cron Health",
        "sec_patterns": "Interaction Patterns",
        "sec_suggestions": "Suggestions",
        "agent_sessions": "Sessions",
        "agent_messages": "Messages",
        "agent_input": "Input Tokens",
        "agent_output": "Output Tokens",
        "agent_daily": "Daily Avg Tokens",
        "chart_7d": "7-Day Token Trend",
        "chart_manual_vs_cron": "Manual vs Cron",
        "chart_manual": "Manual",
        "chart_cron": "Cron Auto",
        "chart_tokens": "Total Tokens",
        "chart_cache": "Cache Hits",
        "chart_model_dist": "Model Token Distribution",
        "model_col_model": "Model",
        "model_col_tokens": "Total Tokens",
        "model_col_cache": "Cache Hits",
        "model_col_messages": "Messages",
        "cron_total": lambda n: f"<strong class='text-white'>{n}</strong> job{'s' if n != 1 else ''} total",
        "cron_runs": lambda n: f"<strong class='text-white'>{n}</strong> run{'s' if n != 1 else ''}",
        "cron_success_rate": "Overall success rate",
        "cron_most_reliable": "Most reliable",
        "cron_per_run": "/run",
        "cron_consec_errors": lambda n: f"{n} consecutive failure{'s' if n != 1 else ''}",
        "cron_no_record": "no data",
        "channel_dist": "Channel Distribution",
        "time_of_day": "Messages by Time of Day",
        "tod_morning": "Morning (6-12)",
        "tod_afternoon": "Afternoon (12-18)",
        "tod_evening": "Evening (18-24)",
        "tod_night": "Night (0-6)",
        "agent_msg_rank": "Agent Message Ranking",
        "installed_skills": "Installed Skills",
        "footer_range": "Period",
        "footer_source": "Generated from your local data",
        "sec_global_config": "Global Config",
        "sec_agent_config": "Agent Config",
        "btn_save": "Save",
        "btn_cancel": "Cancel",
        "btn_restart_now": "Restart Now",
        "btn_restart_later": "Later",
        "btn_restarting": "Restarting...",
        "modal_saved": "Config Saved",
        "modal_restart_confirm": "Restart Gateway now to apply changes?",
        "agent_names": {
            "main": "Orca · Main", "monitor": "Manta · Monitor",
            "note": "Coral · Notes", "code": "Octo · Code",
            "image": "Jelly · Image", "claude": "Claude",
            "codex": "Codex", "gemini": "Gemini", "glm-5": "GLM-5",
        },
        # JS 动态字符串
        "js": {
            "loading": "Loading...", "not_configured": "Not configured",
            "file_exists": "Exists", "file_not_exists": "Missing",
            "file_empty": "(empty)", "chars": "chars",
            "status_ok": "OK", "status_enabled": "Enabled", "status_disabled": "Disabled",
            "never": "Never", "last_used": "Last used",
            "model_config": "Model Config", "auth_creds": "Auth Credentials",
            "unsaved": "● Unsaved changes",
            "oauth_readonly": "OAuth credential (read-only)", "expires": "Expires",
            "no_creds": "Please enter new credentials", "no_desc": "No description",
            "no_fallback": "No fallback",
            "field_base_url": "Base URL", "field_api_key": "API Key",
            "field_backend": "Backend", "field_key": "Key", "field_token": "Token",
            "field_coalesce_idle": "Coalesce Idle (ms)",
            "channels_subtitle": "Telegram · Discord",
            "skill_title_prefix": "Skill:",
            "consec_errors": "{n} consecutive failure(s)", "runs": "{n} run(s)",
            "error_count": "{n} error(s)",
            "restart_ok": "Gateway restart command sent",
            "restart_fail": "Restart failed",
            "no_connect": "Cannot connect to local service, please restart manually",
            "save_error": "Save failed: ",
            "card_cron": "Cron Jobs", "card_defaults": "Default Model",
            "card_models": "Model Providers", "card_acp": "ACP Config",
            "card_gateway": "Gateway", "card_channels": "Channels",
            "card_skills": "Global Skills",
            "drawer_cron": "Cron Jobs", "drawer_defaults": "Default Model Config",
            "drawer_models": "Model Providers", "drawer_acp": "ACP Config",
            "drawer_gateway": "Gateway Config", "drawer_channels": "Channels",
            "drawer_skills": "Global Skills",
            "cron_plan": "Schedule", "cron_msg": "Message",
            "cron_runs_lbl": "Runs", "cron_success": "Success",
            "cron_timeout": "Timeout", "cron_thinking": "Thinking",
            "cron_think_low": "Low", "cron_think_off": "Off", "cron_think_auto": "Auto",
            "cron_save_btn": "Save Job",
            "cron_enable_confirm": "Cron status changed. Restart Gateway?",
            "cron_save_confirm": "Cron job updated. Restart Gateway?",
            "defaults_primary": "Primary Model", "defaults_fallback": "Fallback Chain (current order)",
            "defaults_image": "Image Primary Model",
            "defaults_image_fallback": "Image Fallback Chain",
            "defaults_multiline_hint": "One model ID per line. Leave blank to clear.",
            "defaults_confirm": "Default model updated. Restart Gateway?",
            "models_count": "{n} model(s)", "providers_count": "{n} provider(s) · {m} model(s)",
            "models_confirm": "Provider config updated. Restart Gateway?",
            "acp_max_sessions": "Max Concurrent Sessions", "acp_ttl": "Session TTL (minutes)",
            "acp_default_agent": "Default Agent",
            "acp_readonly": "Read-only info", "acp_allowed_agents": "Allowed Agents",
            "acp_dispatch": "Dispatch", "acp_concurrent": "concurrent",
            "acp_confirm": "ACP config updated. Restart Gateway?",
            "gw_port": "Port (read-only)", "gw_mode": "Mode",
            "gw_bind": "Bind Address", "gw_auth": "Auth Mode",
            "gw_local": "local (run here)", "gw_remote": "remote (connect elsewhere)",
            "gw_loopback": "loopback (local only)", "gw_auto": "auto (pick bind mode)",
            "gw_lan": "lan (all interfaces)", "gw_tailnet": "tailnet (tailnet only)",
            "gw_custom": "custom (custom host)",
            "gw_warn": "Gateway must be restarted after config changes. Port changes require manual URL update.",
            "gw_confirm": "Gateway config updated. Restart now?",
            "ch_enable": "Enable", "ch_streaming": "Streaming",
            "ch_streaming_mode": "Streaming Mode",
            "ch_streaming_off": "Off",
            "ch_streaming_partial": "Partial",
            "ch_streaming_block": "Block",
            "ch_override_none": "No account-level streaming overrides",
            "ch_override_accounts": "{n} account override(s)",
            "ch_override_default": "default account also overrides the channel default",
            "ch_accounts": "Account Config Summary",
            "ch_accounts_empty": "No per-account configuration",
            "ch_account": "Account",
            "ch_account_default": "Default account",
            "ch_account_streaming": "Streaming mode",
            "ch_account_inherits": "Inherits channel default",
            "ch_account_overrides": "Overrides channel default",
            "ch_account_save_confirm": "{ch}/{account} account streaming updated. Restart Gateway?",
            "ch_confirm": "{ch} channel updated. Restart Gateway?",
            "skill_readonly": "SKILL.md · read-only", "skill_no_content": "(no content)",
            "skill_installed": "{n} installed",
            "agent_file_confirm": "{label}.md saved. Restart Gateway?",
            "agent_model_confirm": "Model config updated. Restart Gateway?",
            "auth_confirm": "Credentials updated. Restart Gateway?",
            "save_modal_default": "Restart Gateway to apply changes?",
            "enabled_count": "{n} enabled",
        },
    },
}


def _trim_trailing_zero(value):
    text = f"{value:.1f}"
    return text[:-2] if text.endswith(".0") else text


def format_compact_number(v, lang="zh"):
    """Format large numbers using locale-appropriate compact units."""
    if not v:
        return "0"
    value = float(v)
    abs_value = abs(value)
    if lang == "zh":
        if abs_value >= 100_000_000:
            return f"{_trim_trailing_zero(value / 100_000_000)}亿"
        if abs_value >= 10_000:
            return f"{_trim_trailing_zero(value / 10_000)}万"
        return str(int(value)) if float(value).is_integer() else str(value)

    if abs_value >= 1_000_000_000:
        return f"{_trim_trailing_zero(value / 1_000_000_000)}B"
    if abs_value >= 1_000_000:
        return f"{_trim_trailing_zero(value / 1_000_000)}M"
    if abs_value >= 1_000:
        return f"{_trim_trailing_zero(value / 1_000)}K"
    return str(int(value)) if float(value).is_integer() else str(value)


def format_percent(value, digits=0):
    if value is None:
        return "0%"
    percent = value * 100 if value <= 1 else value
    if digits == 0:
        return f"{round(percent)}%"
    return f"{percent:.{digits}f}%"


def _coerce_datetime(value):
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    if isinstance(value, str):
        iso_value = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(iso_value)
        except ValueError:
            try:
                return datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                return None
    return None


def format_date(value, lang="zh"):
    dt = _coerce_datetime(value)
    if not dt:
        return value or "-"
    if lang == "zh":
        return f"{dt.year}年{dt.month}月{dt.day}日"
    return f"{dt.strftime('%b')} {dt.day}, {dt.year}"


def format_datetime(value, lang="zh"):
    dt = _coerce_datetime(value)
    if not dt:
        return value or "-"
    if lang == "zh":
        return f"{dt.year}年{dt.month}月{dt.day}日 {dt.hour:02d}:{dt.minute:02d}"
    hour = dt.hour % 12 or 12
    suffix = "AM" if dt.hour < 12 else "PM"
    return f"{dt.strftime('%b')} {dt.day}, {dt.year}, {hour}:{dt.minute:02d} {suffix}"


def fmt_number(v, lang="zh"):
    """按语言习惯格式化大数字"""
    return format_compact_number(v, lang)


def _js_tick_callback(lang):
    """Chart.js y 轴刻度回调，按语言返回不同单位"""
    if lang == "zh":
        return "v => v >= 1e8 ? (v/1e8).toFixed(1)+'亿' : v >= 1e4 ? (v/1e4).toFixed(0)+'万' : v"
    return "v => v >= 1e9 ? (v/1e9).toFixed(1)+'B' : v >= 1e6 ? (v/1e6).toFixed(1)+'M' : v >= 1e3 ? (v/1e3).toFixed(0)+'K' : v"


def build_narrative(data, lang):
    """根据语言生成叙述摘要"""
    glance = data.get("at_a_glance", {})
    active_agents = glance.get("active_agent_count")
    if active_agents is None:
        active_agents = len(glance.get("active_agents", []))
    total_tok = glance.get("total_tokens", 0)
    daily_avg = glance.get("daily_avg_tokens", 0)
    skills_count = glance.get("skills_count", data.get("skills", {}).get("total", 0))
    cron_job_count = glance.get("cron_job_count", data.get("cron", {}).get("total_jobs", 0))
    model_count = glance.get("model_count")
    if model_count is None:
        model_count = len(data.get("models", []))
    fn = lambda v: fmt_number(v, lang)
    if lang == "zh":
        return (
            f"在过去 30 天里，共有 {active_agents} 个活跃 Agent。"
            f"总消耗 {fn(total_tok)} Token，日均 {fn(daily_avg)} Token。"
            f"你安装了 {skills_count} 个 Skill，配置了 {cron_job_count} 个 Cron 任务，"
            f"共使用了 {model_count} 个模型。"
        )
    return (
        f"Over the past 30 days, {active_agents} agents were active. "
        f"Total token consumption: {fn(total_tok)}, averaging {fn(daily_avg)} tokens/day. "
        f"You have {skills_count} skills, {cron_job_count} Cron jobs, and {model_count} models in active use."
    )


def build_suggestion_en(sg):
    """为 suggestion 生成英文 title/detail（仅用于 lang=en）"""
    subtype = sg.get("subtype", "")
    d = sg.get("data", {})
    if subtype == "high_usage":
        return (
            f"High Token Usage: {d['model_id']}",
            f"{d['model_id']} consumed {d['tokens']:,} tokens "
            f"(cache hits: {d.get('cache_hit_tokens', 0):,}) across {d['messages']} messages. "
            f"Consider trimming context or system prompts to reduce token usage."
        )
    if subtype == "consecutive_errors":
        n = d["count"]
        jobs = ", ".join(d["jobs"])
        return (
            f"{n} Cron Job{'s' if n != 1 else ''} Failing Consecutively",
            f"Job{'s' if n != 1 else ''} {jobs} {'are' if n != 1 else 'is'} in consecutive failure state. "
            f"Consider checking config or increasing timeout."
        )
    if subtype == "unused":
        n = d["count"]
        skills = ", ".join(d["skills"][:3])
        return (
            f"{n} Skill{'s' if n != 1 else ''} Not Scheduled in Cron",
            f"{skills} {'are' if n != 1 else 'is'} installed but not scheduled. "
            f"Consider adding automated triggers."
        )
    if subtype == "long_session":
        return (
            f"{d['agent']} Agent: Long Session Duration",
            f"{d['agent']} averages {d['avg_min']} minutes of active time per session. "
            f"Long sessions accumulate large contexts. Consider splitting tasks or starting new sessions more often."
        )
    if subtype == "token_concentration":
        return (
            f"{d['agent']} uses {d['pct']}% of all tokens",
            f"Over the past 30 days, {d['agent']} consumed {d['pct']}% of total tokens. "
            f"If this matches your design (e.g., a main orchestrator agent), this is expected."
        )
    if subtype == "overall_rate_low":
        return (
            f"Low Overall Cron Success Rate ({d['rate']}%)",
            f"Out of {d['total_runs']} Cron runs, the overall success rate is only {d['rate']}%. "
            f"Check all job configs, timeouts, and dependencies."
        )
    if subtype == "no_delivery":
        n = d["count"]
        jobs = ", ".join(d["jobs"])
        return (
            f"{n} Cron Job{'s' if n != 1 else ''} Without Delivery Config",
            f"{jobs} {'have' if n != 1 else 'has'} no delivery configured. "
            f"Results are only visible in logs. Consider adding Discord or Telegram notifications."
        )
    if subtype == "peak_conflict":
        n = d["count"]
        peaks = ", ".join(f"{h}:00" for h in d.get("peaks", []))
        jobs = ", ".join(d["jobs"])
        return (
            f"{n} Cron Job{'s' if n != 1 else ''} Overlap With Peak Hours",
            f"Your peak interaction hours include {peaks} (tz: {d.get('tz', '')}). "
            f"{jobs} run during these times. "
            f"Running Cron during peak hours may slow responses. Consider rescheduling to off-peak hours."
        )
    if subtype == "user_md":
        names = ", ".join(d.get("names", d.get("agents", [])))
        n = len(d.get("agents", []))
        return (
            f"{names} · USER.md Missing or Sparse",
            f"USER.md is the agent's primary source of context about you — your preferences, habits, and common tasks. "
            f"{'This file is' if n == 1 else 'These files are'} missing or too sparse. "
            f"Filling it in will significantly improve response quality."
        )
    if subtype == "soul_md":
        names = ", ".join(d.get("names", d.get("agents", [])))
        n = len(d.get("agents", []))
        return (
            f"{names} · SOUL.md Missing or Sparse",
            f"SOUL.md defines the agent's values and behavioral guidelines — it's what makes each agent feel like itself. "
            f"Without it, response style may drift with conversation context. "
            f"Consider adding core values and behavioral boundaries."
        )
    if subtype == "heartbeat":
        names = ", ".join(d.get("names", d.get("agents", [])))
        n = len(d.get("agents", []))
        return (
            f"{n} Agent{'s' if n != 1 else ''} Without Heartbeat",
            f"{names} {'are' if n != 1 else 'is'} in passive-only mode, fully dependent on manual triggers. "
            f"Enabling Heartbeat allows {'them' if n != 1 else 'it'} to run background tasks, organize memory, "
            f"or send proactive messages autonomously."
        )
    if subtype == "no_cron_jobs":
        return (
            "No automated jobs configured",
            "There are currently no Cron jobs, so every agent workflow depends on manual triggers. "
            "Start with one recurring task such as reporting, monitoring, or synchronization."
        )
    if subtype == "no_delivery_channels":
        return (
            "Cron jobs exist, but no delivery channel is configured",
            "Cron is enabled, but Telegram and Discord delivery are both disabled. "
            "Results are only visible in logs, so it is easy to miss failures or important updates."
        )
    if subtype == "empty_skill_md":
        names = ", ".join(d.get("skills", [])[:3])
        count = d.get("count", len(d.get("skills", [])))
        return (
            f"{count} skill description file(s) look empty",
            f"{names or 'Some skills'} have little or no SKILL.md content. "
            "Without clear instructions, agents cannot reliably activate those skills."
        )
    if subtype == "memory_sparse":
        name = d.get("name", d.get("agent", "Agent"))
        session_count = d.get("session_count", 0)
        memory_lines = d.get("memory_lines", 0)
        return (
            f"{name} has sparse memory",
            f"{name} has already accumulated {session_count} sessions, but MEMORY.md only contains {memory_lines} meaningful line(s). "
            "That usually means important cross-session context is not being retained."
        )
    # 无 subtype：回退到中文
    return sg.get("title", ""), sg.get("detail", "")


def build_suggestion_zh(sg):
    subtype = sg.get("subtype", "")
    d = sg.get("data", {})
    if subtype == "high_usage":
        return (
            f"高 Token 消耗模型：{d['model_id']}",
            f"{d['model_id']} 消耗了 {d['tokens']:,} Token（缓存命中 {d.get('cache_hit_tokens', 0):,}），"
            f"共 {d['messages']} 条消息。可考虑精简上下文或系统提示词，以减少 Token 消耗。"
        )
    if subtype == "consecutive_errors":
        jobs = "、".join(d.get("jobs", []))
        return (
            f"{d.get('count', 0)} 个 Cron 任务连续失败",
            f"任务 {jobs} 处于连续失败状态，建议检查配置或适当延长超时时间。"
        )
    if subtype == "unused":
        skills = "、".join(d.get("skills", [])[:3])
        return (
            f"发现 {d.get('count', 0)} 个未在 Cron 中使用的 Skill",
            f"{skills} 等 Skill 已安装但未配置定时任务，可考虑按场景接入自动化。"
        )
    if subtype == "long_session":
        return (
            f"{d['agent']} Agent 单次会话时长较长",
            f"{d['agent']} 的主动对话会话平均活跃时长为 {d['avg_min']} 分钟。"
            f"长会话会累积大量上下文，可能带来响应质量下降或 Token 浪费，"
            f"建议适当拆分任务，或更频繁地开启新会话。"
        )
    if subtype == "token_concentration":
        return (
            f"{d['agent']} 占用了 {d['pct']}% 的 Token 消耗",
            f"过去 30 天中，{d['agent']} 消耗了全部 Token 的 {d['pct']}%。"
            f"如果这符合你的分工设计，例如主控 Agent 承担大部分协调工作，可以忽略此提示。"
        )
    if subtype == "overall_rate_low":
        return (
            f"Cron 整体成功率偏低（{d['rate']}%）",
            f"在 {d['total_runs']} 次 Cron 运行记录中，整体成功率仅为 {d['rate']}%，"
            f"建议全面检查任务配置、超时时间和依赖服务状态。"
        )
    if subtype == "no_delivery":
        jobs = "、".join(d.get("jobs", []))
        return (
            f"{d.get('count', 0)} 个 Cron 任务未配置消息推送",
            f"{jobs} 等任务已稳定运行但未配置消息推送，执行结果只能通过日志查看。"
            f"可考虑接入 Discord 或 Telegram 推送，方便及时感知运行状态。"
        )
    if subtype == "peak_conflict":
        peaks = "、".join(f"{h}:00" for h in d.get("peaks", []))
        jobs = "、".join(d.get("jobs", []))
        return (
            f"{d.get('count', 0)} 个 Cron 任务与活跃高峰时段重叠",
            f"你的主动对话高峰集中在 {peaks} 等时段（时区：{d.get('tz', '')}），"
            f"而 {jobs} 等 Cron 任务也在这些时间点附近执行。"
            f"自动任务与主动对话并发可能拖慢响应，建议将 Cron 调整到低峰时段。"
        )
    if subtype == "user_md":
        names = "、".join(d.get("names", d.get("agents", [])))
        count = len(d.get("agents", []))
        if count == 1:
            return (
                f"{names} · USER.md 内容不足",
                f"USER.md 是 Agent 了解你的核心来源，包括偏好、习惯和常见任务背景。"
                f"建议尽快补全，让回应更贴合你的实际需求。"
            )
        return (
            f"{count} 个 Agent 的 USER.md 内容不足",
            f"{names} 的 USER.md 缺失或内容过少。建议逐一补充你的偏好、背景和常见任务类型。"
        )
    if subtype == "soul_md":
        names = "、".join(d.get("names", d.get("agents", [])))
        count = len(d.get("agents", []))
        if count == 1:
            return (
                f"{names} · SOUL.md 内容不足",
                f"SOUL.md 定义 Agent 的价值观和行为准则。缺少这部分内容时，回应风格更容易随上下文漂移。"
            )
        return (
            f"{count} 个 Agent 的 SOUL.md 内容不足",
            f"{names} 的 SOUL.md 缺失或内容过少，完善后回应风格会更稳定。"
        )
    if subtype == "heartbeat":
        names = "、".join(d.get("names", d.get("agents", [])))
        count = len(d.get("agents", []))
        return (
            f"{count} 个 Agent 未启用 Heartbeat",
            f"{names} 当前仍主要依赖手动触发。为需要后台自主运行的 Agent 启用 Heartbeat，"
            f"可以解锁后台任务、记忆整理和主动提醒能力。"
        )
    if subtype == "no_cron_jobs":
        return (
            "尚未配置任何自动化任务",
            "你目前没有任何 Cron 任务，所有 Agent 行为都依赖手动触发。"
            "可以先从日报、监控或同步这类高频场景开始配置第一个自动化任务。"
        )
    if subtype == "no_delivery_channels":
        return (
            "已有 Cron 任务但未配置消息推送渠道",
            "你已经配置了 Cron 任务，但 Telegram 和 Discord 推送均未启用。"
            "建议至少接入一个消息渠道，避免错过运行结果和异常告警。"
        )
    if subtype == "empty_skill_md":
        count = d.get("count", len(d.get("skills", [])))
        names = "、".join(d.get("skills", [])[:3])
        return (
            f"{count} 个 Skill 的 SKILL.md 内容为空",
            f"{names} 等 Skill 的 SKILL.md 几乎没有内容。Agent 依赖这些说明理解如何调用 Skill，建议尽快补全。"
        )
    if subtype == "memory_sparse":
        name = d.get("name", d.get("agent", "Agent"))
        return (
            f"{name} · MEMORY.md 内容稀少",
            f"{name} 已累积 {d.get('session_count', 0)} 个会话，但 MEMORY.md 目前只有 {d.get('memory_lines', 0)} 行有效内容。"
            f"这通常意味着跨会话的关键信息没有被稳定保留下来。"
        )
    return sg.get("title", ""), sg.get("detail", "")


def build_suggestion_copy(sg, lang):
    if lang == "zh" and sg.get("subtype"):
        return build_suggestion_zh(sg)
    if lang == "en" and sg.get("subtype"):
        return build_suggestion_en(sg)
    return sg.get("title", ""), sg.get("detail", "")

AGENT_NAMES = {
    "main": "Orca · 主控",
    "monitor": "Manta · 监控",
    "note": "Coral · 笔记",
    "code": "Octo · 代码",
    "image": "Jelly · 图像",
    "claude": "Claude",
    "codex": "Codex",
    "gemini": "Gemini",
    "glm-5": "GLM-5",
}

MODEL_COLORS = [
    "#3b82f6", "#60a5fa", "#06b6d4", "#10b981", "#f59e0b",
    "#ef4444", "#ec4899", "#84cc16", "#f97316", "#14b8a6",
]

SUGGESTION_ICONS = {
    "model": "💡",
    "cron": "⚠️",
    "cost": "💰",
    "skill": "🔧",
}


def fmt_cost(v):
    if v is None:
        return "$0.000"
    return f"${v:.3f}"


def fmt_tokens(v, lang="zh"):
    return fmt_number(v, lang)


def format_duration(ms, lang="zh"):
    if not ms:
        return "-"
    if ms < 1000:
        return f"{ms}ms"
    if ms < 60000:
        return f"{ms/1000:.0f}s"
    minutes = _trim_trailing_zero(ms / 60000)
    return f"{minutes}{'分钟' if lang == 'zh' else ' min'}"


def fmt_duration(ms, lang="zh"):
    return format_duration(ms, lang)


def pct_bar(rate, lang="zh", color="#3b82f6"):
    if rate is None:
        no_data = "无记录" if lang == "zh" else "no data"
        return f'<span class="text-gray-500 text-sm">{no_data}</span>'
    pct = int(rate * 100)
    bar_color = "#10b981" if rate >= 0.9 else "#f59e0b" if rate >= 0.7 else "#ef4444"
    return f"""<div class="flex items-center gap-2">
      <div class="flex-1 bg-gray-700 rounded-full h-2">
        <div class="h-2 rounded-full" style="width:{pct}%;background:{bar_color}"></div>
      </div>
      <span class="text-sm font-mono text-gray-300 w-10 text-right">{pct}%</span>
    </div>"""


def build_runtime_i18n(lang="zh"):
    """Build the runtime translation map consumed by browser-side JS."""
    t = I18N.get(lang, I18N["zh"])
    runtime = {}

    for key, value in t.items():
        if key == "js":
            continue
        try:
            json.dumps(value, ensure_ascii=False)
        except TypeError:
            continue
        runtime[key] = value

    runtime.update(t["js"])
    return runtime


def build_html(data, lang="zh"):
    t = I18N.get(lang, I18N["zh"])
    js_t = build_runtime_i18n(lang)

    meta = data.get("meta", {})
    glance = data.get("at_a_glance", {})
    agents = data.get("agents", [])
    models = data.get("models", [])
    token_data = data.get("token_analysis", {})
    cron = data.get("cron", {})
    skills = data.get("skills", {})
    patterns = data.get("interaction_patterns", {})
    suggestions = data.get("suggestions", [])

    period_from = meta.get("period", {}).get("from", "")
    period_to = meta.get("period", {}).get("to", "")

    # Chart.js 数据 — Token 趋势
    trend_7d = token_data.get("trend_7d", [])
    trend_labels = [r["date"][5:] for r in trend_7d]
    trend_total = [r["total"] for r in trend_7d]
    trend_cache = [r["cache_hit"] for r in trend_7d]

    top_models = models[:6]
    model_labels = [m["model_id"].split("-")[0] + "..." if len(m["model_id"]) > 12 else m["model_id"] for m in top_models]
    model_tokens = [m["tokens"] for m in top_models]
    model_colors = MODEL_COLORS[:len(top_models)]

    channels = patterns.get("channels", {})

    cron_jobs = cron.get("jobs", [])

    def agent_cards_html():
        cards = []
        cron_manual = ("Cron {c} · 主动对话 {m}") if lang == "zh" else ("Cron {c} · Manual {m}")
        for ag in agents:
            ag_id = ag["id"]
            name = t["agent_names"].get(ag_id, ag_id)
            daily_avg = fmt_tokens(ag.get("daily_avg_tokens"), lang) if ag.get("daily_avg_tokens") else "-"
            total_tok = fmt_tokens(ag.get("total_tokens", 0), lang)
            cache_tok = fmt_tokens(ag.get("cache_hit_tokens", 0), lang)
            sub = cron_manual.format(c=ag["cron_sessions"], m=ag["manual_sessions"])
            cards.append(f"""
        <div class="bg-gray-800 rounded-xl p-5 border border-gray-700 hover:border-blue-500 transition-colors">
          <div class="mb-4">
            <div class="font-bold text-white">{name}</div>
            <div class="text-xs text-gray-400">{ag_id}</div>
          </div>
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div class="bg-gray-700/50 rounded-lg p-3">
              <div class="text-gray-400 text-xs mb-1">{t["agent_sessions"]}</div>
              <div class="text-white font-bold text-lg">{ag["session_count"]}</div>
              <div class="text-gray-500 text-xs">{sub}</div>
            </div>
            <div class="bg-gray-700/50 rounded-lg p-3">
              <div class="text-gray-400 text-xs mb-1">{t["agent_messages"]}</div>
              <div class="text-white font-bold text-lg">{ag["message_count"]}</div>
            </div>
            <div class="bg-gray-700/50 rounded-lg p-3">
              <div class="text-gray-400 text-xs mb-1">{t["stat_tokens"]}</div>
              <div class="text-blue-400 font-bold text-xl">{total_tok}</div>
            </div>
            <div class="bg-gray-700/50 rounded-lg p-3">
              <div class="text-gray-400 text-xs mb-1">{t["stat_cache"]}</div>
              <div class="text-cyan-400 font-bold text-xl">{cache_tok}</div>
            </div>
            <div class="bg-gray-700/50 rounded-lg p-3 col-span-2">
              <div class="text-gray-400 text-xs mb-1">{t["agent_daily"]}</div>
              <div class="text-blue-400 font-bold">{daily_avg}</div>
            </div>
          </div>
        </div>""")
        return "\n".join(cards)

    def model_rows_html():
        rows = []
        max_tokens = models[0]["tokens"] if models else 1
        for i, m in enumerate(models[:8]):
            color = MODEL_COLORS[i % len(MODEL_COLORS)]
            bar_w = int(m["tokens"] / max_tokens * 100) if max_tokens > 0 else 0
            rows.append(f"""
          <tr class="border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors">
            <td class="py-3 pr-4">
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 rounded-full" style="background:{color}"></div>
                <span class="text-white font-medium text-sm">{m["model_id"]}</span>
              </div>
              <div class="text-gray-500 text-xs mt-0.5">{m["provider"]}</div>
            </td>
            <td class="py-3 pr-4">
              <div class="text-blue-400 font-mono font-bold">{fmt_tokens(m.get("tokens", 0), lang)}</div>
              <div class="w-24 bg-gray-700 rounded-full h-1 mt-1"><div class="h-1 rounded-full" style="width:{bar_w}%;background:{color}"></div></div>
            </td>
            <td class="py-3 pr-4">
              <div class="text-cyan-400 font-mono font-bold">{fmt_tokens(m.get("cache_hit_tokens", 0), lang)}</div>
            </td>
            <td class="py-3 text-gray-400 text-sm">{m["messages"]}</td>
          </tr>""")
        return "\n".join(rows)

    def cron_rows_html():
        rows = []
        for job in cron_jobs:
            name = job.get("name", "")
            agent = job.get("agent", "")
            enabled = job.get("enabled", True)
            rate = job.get("success_rate")
            runs = job.get("run_count", 0)
            duration = job.get("avg_duration_ms")
            errors = job.get("consecutive_errors", 0)
            status_text = "正常" if enabled and errors == 0 else "需关注" if enabled else "已停用"
            rows.append(f"""
          <div class="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <div class="flex items-start justify-between mb-3">
              <div>
                <div class="text-white font-medium text-sm">{name}</div>
                <div class="text-gray-500 text-xs mt-0.5">{agent} · <code class="text-blue-400">{job.get("schedule","")}</code> · {job.get("tz","")}</div>
              </div>
              <div class="text-right">
                <div class="text-gray-300 text-sm font-mono">{status_text}</div>
                <div class="text-gray-500 text-xs">{fmt_duration(duration, lang)}{t["cron_per_run"]}</div>
              </div>
            </div>
            {pct_bar(rate, lang)}
            {"<div class='mt-2 text-red-400 text-xs'>" + t["cron_consec_errors"](errors) + "</div>" if errors > 0 else ""}
          </div>""")
        return "\n".join(rows)

    def suggestions_html():
        items = []
        for sg in suggestions:
            icon = SUGGESTION_ICONS.get(sg.get("type", ""), "💡")
            title, detail = build_suggestion_copy(sg, lang)
            if not title:
                continue
            items.append(f"""
        <div class="bg-gray-800 rounded-xl p-5 border border-gray-700">
          <div class="flex items-start gap-3">
            <span class="text-2xl">{icon}</span>
            <div>
              <div class="font-bold text-white mb-1">{title}</div>
              <div class="text-gray-400 text-sm leading-relaxed">{detail}</div>
            </div>
          </div>
        </div>""")
        return "\n".join(items)

    # 渠道分布列表
    channel_rows_html = "".join(
        f"<div class='flex items-center justify-between py-1.5'>"
        f"<span class='text-gray-300 text-sm'>{k}</span>"
        f"<span class='text-white font-bold text-sm'>{v}</span>"
        f"</div>"
        for k, v in channels.items() if v > 0
    )

    # 时段分布
    hour_counts = patterns.get("hour_counts", {})
    tod_buckets = {
        "morning": sum(hour_counts.get(str(h), hour_counts.get(h, 0)) for h in range(6, 12)),
        "afternoon": sum(hour_counts.get(str(h), hour_counts.get(h, 0)) for h in range(12, 18)),
        "evening": sum(hour_counts.get(str(h), hour_counts.get(h, 0)) for h in range(18, 24)),
        "night": sum(hour_counts.get(str(h), hour_counts.get(h, 0)) for h in range(0, 6)),
    }
    tod_max = max(tod_buckets.values()) or 1
    def _tod_bar(key):
        label = t[f"tod_{key}"]
        count = tod_buckets[key]
        pct = int(count / tod_max * 100)
        return (
            f"<div class='flex items-center gap-3 py-1.5'>"
            f"<div class='text-gray-400 text-xs w-28 shrink-0'>{label}</div>"
            f"<div class='flex-1 bg-gray-700 rounded-full h-2'>"
            f"<div class='h-2 rounded-full bg-indigo-500' style='width:{pct}%'></div>"
            f"</div>"
            f"<div class='text-gray-300 text-xs w-6 text-right'>{count}</div>"
            f"</div>"
        )
    tod_html = "".join(_tod_bar(k) for k in ["morning", "afternoon", "evening", "night"])

    # Agent 消息数排行
    agents_by_msg = sorted(agents, key=lambda a: a.get("message_count", 0), reverse=True)
    ag_max_msg = agents_by_msg[0]["message_count"] if agents_by_msg else 1
    def _agent_rank_row(i, ag):
        pct = int(ag.get("message_count", 0) / ag_max_msg * 100)
        name = t["agent_names"].get(ag["id"], ag["id"])
        rank_color = ["text-yellow-400", "text-gray-300", "text-orange-400"]
        num_cls = rank_color[i] if i < 3 else "text-gray-500"
        return (
            f"<div class='flex items-center gap-2 py-1.5'>"
            f"<span class='{num_cls} text-xs font-bold w-4'>#{i+1}</span>"
            f"<div class='flex-1'>"
            f"<div class='flex items-center justify-between mb-0.5'>"
            f"<span class='text-gray-300 text-xs'>{name}</span>"
            f"<span class='text-white font-bold text-xs'>{ag.get('message_count',0)}</span>"
            f"</div>"
            f"<div class='bg-gray-700 rounded-full h-1.5'>"
            f"<div class='h-1.5 rounded-full bg-blue-500' style='width:{pct}%'></div>"
            f"</div>"
            f"</div>"
            f"</div>"
        )
    agent_rank_html = "".join(_agent_rank_row(i, ag) for i, ag in enumerate(agents_by_msg))

    narrative = build_narrative(data, lang)

    return f"""<!DOCTYPE html>
<html lang="{t["lang_attr"]}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OpenClaw Insights</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  body {{ background: #0f1117; color: #e2e8f0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
  .gradient-text {{ background: linear-gradient(135deg, #3b82f6, #60a5fa, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
  .card-glow {{ box-shadow: 0 0 20px rgba(59,130,246,0.1); }}
  .stat-card {{ background: linear-gradient(135deg, #0c1a3b22, #1e293b); display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 5.5rem; }}
  .stat-card .stat-value {{ font-size: 1.75rem; line-height: 2.25rem; font-weight: 700; white-space: nowrap; }}
</style>
</head>
<body class="min-h-screen">

<!-- Header -->
<div class="border-b border-gray-800 bg-gray-900/50 backdrop-blur sticky top-0 z-10">
  <div class="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
    <div class="flex items-center gap-4">
      <span class="text-3xl leading-none">🦞</span>
      <div class="font-bold text-white text-xl leading-none">OpenClaw Insights</div>
      <div class="ml-4 flex bg-gray-800 rounded-lg p-1">
        <button onclick="switchTab('insights')" id="tab-insights"
          class="tab-btn px-4 py-1.5 rounded-md text-sm font-medium transition-colors bg-gray-700 text-white">
          {t["tab_insights"]}
        </button>
        <button onclick="switchTab('config')" id="tab-config"
          class="tab-btn px-4 py-1.5 rounded-md text-sm font-medium transition-colors text-gray-400 hover:text-white">
          {t["tab_config"]}
        </button>
      </div>
    </div>
    <div class="flex items-center gap-4">
      <div class="text-gray-500 text-sm">{period_from} → {period_to}</div>
    </div>
  </div>
</div>

<div id="page-insights" class="max-w-6xl mx-auto px-6 py-10 space-y-12">
<script>
function switchTab(tab) {{
  document.getElementById('page-insights').classList.toggle('hidden', tab !== 'insights');
  document.getElementById('page-config').classList.toggle('hidden', tab !== 'config');
  document.querySelectorAll('.tab-btn').forEach(b => {{
    b.classList.remove('bg-gray-700','text-white');
    b.classList.add('text-gray-400');
  }});
  const active = document.getElementById('tab-' + tab);
  active.classList.add('bg-gray-700','text-white');
  active.classList.remove('text-gray-400');
  if (tab === 'config') initConfig();
}}
</script>

  <!-- At a Glance 统计条 -->
  <div>
    <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
      <div class="stat-card rounded-xl p-4 text-center border border-gray-700/50 card-glow">
        <div class="stat-value gradient-text">{glance.get("active_agent_count", len(glance.get("active_agents", [])))}</div>
        <div class="text-gray-400 text-xs mt-1">{t["stat_active_agents"]}</div>
      </div>
      <div class="stat-card rounded-xl p-4 text-center border border-gray-700/50 card-glow">
        <div class="stat-value text-blue-400">{fmt_tokens(glance.get("total_tokens",0), lang)}</div>
        <div class="text-gray-400 text-xs mt-1">{t["stat_tokens"]}</div>
      </div>
      <div class="stat-card rounded-xl p-4 text-center border border-gray-700/50 card-glow">
        <div class="stat-value text-cyan-400">{fmt_tokens(glance.get("daily_avg_tokens",0), lang)}</div>
        <div class="text-gray-400 text-xs mt-1">{t["stat_daily"]}</div>
      </div>
      <div class="stat-card rounded-xl p-4 text-center border border-gray-700/50 card-glow">
        <div class="stat-value text-blue-400">{glance.get("skills_count", data.get("skills", {}).get("total", 0))}</div>
        <div class="text-gray-400 text-xs mt-1">{t["stat_skills"]}</div>
      </div>
      <div class="stat-card rounded-xl p-4 text-center border border-gray-700/50">
        <div class="stat-value text-blue-400">{glance.get("cron_job_count", data.get("cron", {}).get("total_jobs", 0))}</div>
        <div class="text-gray-400 text-xs mt-1">{t["stat_cron_jobs"]}</div>
      </div>
      <div class="stat-card rounded-xl p-4 text-center border border-gray-700/50">
        <div class="stat-value text-cyan-400">{glance.get("model_count", len(data.get("models", [])))}</div>
        <div class="text-gray-400 text-xs mt-1">{t["stat_models"]}</div>
      </div>
    </div>

    <div class="mt-4 bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
      <p class="text-gray-300 leading-relaxed">{narrative}</p>
    </div>
  </div>

  <!-- Agent 概览 -->
  <div>
    <h2 class="text-xl font-bold text-white mb-5 flex items-center gap-2">
      <span class="text-blue-400">●</span> {t["sec_agents"]}
    </h2>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {agent_cards_html()}
    </div>
  </div>

  <!-- Token 消耗 -->
  <div>
    <h2 class="text-xl font-bold text-white mb-5 flex items-center gap-2">
      <span class="text-blue-400">●</span> {t["sec_tokens"]}
    </h2>
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

      <!-- 7 日趋势 -->
      <div class="lg:col-span-2 bg-gray-800 rounded-xl p-5 border border-gray-700">
        <div class="text-gray-400 text-sm mb-4">{t["chart_7d"]}</div>
        <canvas id="trendChart" height="120"></canvas>
      </div>

      <!-- 主动对话 vs Cron -->
      <div class="bg-gray-800 rounded-xl p-5 border border-gray-700">
        <div class="text-gray-400 text-sm mb-4">{t["chart_manual_vs_cron"]}</div>
        <canvas id="typeChart" height="120"></canvas>
        <div class="mt-4 space-y-2 text-sm">
          <div class="flex justify-between">
            <span class="text-gray-400">{t["chart_manual"]}</span>
            <span class="text-white font-mono">{fmt_tokens(token_data.get("by_type",{}).get("manual_tokens",0), lang)}</span>
          </div>
          <div class="flex justify-between border-t border-gray-700 pt-2 mt-2">
            <span class="text-gray-400">{t["chart_cron"]}</span>
            <span class="text-white font-mono">{fmt_tokens(token_data.get("by_type",{}).get("cron_tokens",0), lang)}</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 模型使用 -->
  <div>
    <h2 class="text-xl font-bold text-white mb-5 flex items-center gap-2">
      <span class="text-blue-400">●</span> {t["sec_models"]}
    </h2>
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 bg-gray-800 rounded-xl p-5 border border-gray-700 overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="text-gray-500 text-xs border-b border-gray-700">
              <th class="text-left pb-3 font-medium">{t["model_col_model"]}</th>
              <th class="text-left pb-3 font-medium">{t["model_col_tokens"]}</th>
              <th class="text-left pb-3 font-medium">{t["model_col_cache"]}</th>
              <th class="text-left pb-3 font-medium">{t["model_col_messages"]}</th>
            </tr>
          </thead>
          <tbody>
            {model_rows_html()}
          </tbody>
        </table>
      </div>
      <div class="bg-gray-800 rounded-xl p-5 border border-gray-700">
        <div class="text-gray-400 text-sm mb-4">{t["chart_model_dist"]}</div>
        <canvas id="modelChart" height="180"></canvas>
      </div>
    </div>
  </div>

  <!-- Cron 健康 -->
  <div>
    <h2 class="text-xl font-bold text-white mb-2 flex items-center gap-2">
      <span class="text-blue-400">●</span> {t["sec_cron"]}
    </h2>
    <div class="flex gap-6 text-sm text-gray-400 mb-5">
      <span>{t["cron_total"](cron.get("total_jobs",0))}</span>
      <span>{t["cron_runs"](cron.get("total_runs",0))}</span>
      <span>{t["cron_success_rate"]} <strong class="{'text-emerald-400' if (cron.get('overall_success_rate') or 0) >= 0.9 else 'text-yellow-400'}">{f"{int((cron.get('overall_success_rate') or 0)*100)}%" if cron.get("overall_success_rate") is not None else "N/A"}</strong></span>
      {"<span>" + t['cron_most_reliable'] + " <strong class='text-emerald-400'>" + cron.get("most_reliable","") + "</strong></span>" if cron.get("most_reliable") else ""}
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      {cron_rows_html()}
    </div>
  </div>

  <!-- 交互模式 -->
  <div>
    <h2 class="text-xl font-bold text-white mb-5 flex items-center gap-2">
      <span class="text-blue-400">●</span> {t["sec_patterns"]}
    </h2>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-gray-800 rounded-xl p-5 border border-gray-700">
        <div class="text-gray-400 text-sm mb-3">{t["channel_dist"]}</div>
        <div class="divide-y divide-gray-700/50">{channel_rows_html}</div>
      </div>
      <div class="bg-gray-800 rounded-xl p-5 border border-gray-700">
        <div class="text-gray-400 text-sm mb-3">{t["time_of_day"]}</div>
        <div class="mt-2">{tod_html}</div>
      </div>
      <div class="bg-gray-800 rounded-xl p-5 border border-gray-700">
        <div class="text-gray-400 text-sm mb-3">{t["agent_msg_rank"]}</div>
        <div class="mt-2">{agent_rank_html}</div>
      </div>
    </div>
  </div>

  <!-- 建议 -->
  {"<div><h2 class='text-xl font-bold text-white mb-5 flex items-center gap-2'><span class='text-blue-400'>●</span> " + t["sec_suggestions"] + "</h2><div class='space-y-4'>" + suggestions_html() + "</div></div>" if suggestions else ""}

  <!-- Footer -->
  <div class="border-t border-gray-800 mt-16">
    <div class="max-w-6xl mx-auto px-6 py-6 text-center text-gray-600 text-sm">
      🦞 OpenClaw Insights · {t["footer_range"]} {period_from} ~ {period_to} · {t["footer_source"]}
    </div>
  </div>

</div>

<script>
const T = {json.dumps(js_t, ensure_ascii=False)};
const UI_LOCALE = {json.dumps(t["ui_locale"])};
const CHART_DEFAULTS = {{
  responsive: true,
  plugins: {{ legend: {{ labels: {{ color: '#9ca3af', font: {{ size: 11 }} }} }} }},
}};

// 7 日 Token 趋势堆叠柱状图
new Chart(document.getElementById('trendChart'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(trend_labels)},
    datasets: [
      {{
        label: {json.dumps(t["chart_tokens"])},
        data: {json.dumps(trend_total)},
        backgroundColor: 'rgba(59,130,246,0.7)',
        borderRadius: 3,
      }},
      {{
        label: {json.dumps(t["chart_cache"])},
        data: {json.dumps(trend_cache)},
        backgroundColor: 'rgba(6,182,212,0.7)',
        borderRadius: 3,
      }}
    ]
  }},
  options: {{
    ...CHART_DEFAULTS,
    scales: {{
      x: {{ ticks: {{ color: '#6b7280' }}, grid: {{ color: '#1f2937' }} }},
      y: {{ ticks: {{ color: '#6b7280', callback: {_js_tick_callback(lang)} }}, grid: {{ color: '#1f2937' }} }},
    }},
    plugins: {{ legend: {{ position: 'top', labels: {{ color: '#9ca3af', font: {{ size: 10 }}, boxWidth: 10 }} }} }},
  }}
}});

// 主动对话 vs Cron Token 饼图
new Chart(document.getElementById('typeChart'), {{
  type: 'doughnut',
  data: {{
    labels: [{json.dumps(t["chart_manual"])}, {json.dumps(t["chart_cron"])}],
    datasets: [{{
      data: [{token_data.get("by_type",{}).get("manual_tokens",0)}, {token_data.get("by_type",{}).get("cron_tokens",0)}],
      backgroundColor: ['#3b82f6', '#0284c7'],
      borderWidth: 0,
    }}]
  }},
  options: {{
    ...CHART_DEFAULTS,
    cutout: '65%',
    plugins: {{ legend: {{ position: 'bottom', labels: {{ color: '#9ca3af', font: {{ size: 10 }}, boxWidth: 10 }} }} }},
  }}
}});

// 模型 Token 分布饼图
new Chart(document.getElementById('modelChart'), {{
  type: 'doughnut',
  data: {{
    labels: {json.dumps(model_labels)},
    datasets: [{{
      data: {json.dumps(model_tokens)},
      backgroundColor: {json.dumps(model_colors)},
      borderWidth: 0,
    }}]
  }},
  options: {{
    ...CHART_DEFAULTS,
    cutout: '60%',
    plugins: {{ legend: {{ position: 'bottom', labels: {{ color: '#9ca3af', font: {{ size: 9 }}, boxWidth: 10 }} }} }},
  }}
}});


</script>

</div><!-- /page-insights -->

<!-- ══════════════════════════════════════════════════
     CONFIG PAGE
══════════════════════════════════════════════════ -->
<div id="page-config" class="hidden max-w-6xl mx-auto px-6 py-10">

  <!-- 全局配置 -->
  <div class="mb-10">
    <h2 class="text-lg font-bold text-white mb-5 flex items-center gap-2">
      <span class="text-blue-400">●</span> {t["sec_global_config"]}
    </h2>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" id="global-cards">
      <div class="bg-gray-800 rounded-xl p-5 border border-gray-700 animate-pulse">
        <div class="h-4 bg-gray-700 rounded w-1/2 mb-3"></div>
        <div class="h-3 bg-gray-700 rounded w-3/4"></div>
      </div>
    </div>
  </div>

  <!-- Agent 配置 -->
  <div>
    <h2 class="text-lg font-bold text-white mb-5 flex items-center gap-2">
      <span class="text-blue-400">●</span> {t["sec_agent_config"]}
    </h2>
    <!-- Agent Tabs -->
    <div class="flex gap-2 mb-5 flex-wrap" id="agent-tabs"></div>
    <!-- Agent Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" id="agent-cards">
      <div class="bg-gray-800 rounded-xl p-5 border border-gray-700 animate-pulse">
        <div class="h-4 bg-gray-700 rounded w-1/2 mb-3"></div>
        <div class="h-3 bg-gray-700 rounded w-3/4"></div>
      </div>
    </div>
  </div>

  <!-- Footer -->
  <div class="border-t border-gray-800 mt-16">
    <div class="max-w-6xl mx-auto px-6 py-6 text-center text-gray-600 text-sm">
      🦞 OpenClaw Insights · {t["footer_range"]} {period_from} ~ {period_to} · {t["footer_source"]}
    </div>
  </div>
</div>

<!-- ══════════════════════════════════════════════════
     DRAWER (展开面板)
══════════════════════════════════════════════════ -->
<div id="drawer-overlay" class="fixed inset-0 bg-black/60 z-40 hidden" onclick="closeDrawer()"></div>
<div id="drawer" class="fixed right-0 top-0 h-full w-full max-w-2xl bg-gray-900 border-l border-gray-700 z-50 transform translate-x-full transition-transform duration-300 flex flex-col">
  <div class="flex items-center justify-between px-6 py-4 border-b border-gray-700 flex-shrink-0">
    <div>
      <div id="drawer-title" class="text-white font-bold text-lg"></div>
      <div id="drawer-subtitle" class="text-gray-500 text-xs mt-0.5"></div>
    </div>
    <button onclick="closeDrawer()" class="text-gray-400 hover:text-white text-2xl leading-none">×</button>
  </div>
  <div id="drawer-content" class="flex-1 overflow-y-auto p-6"></div>
  <div id="drawer-footer" class="px-6 py-4 border-t border-gray-700 flex-shrink-0 hidden">
    <div class="flex gap-3 justify-end">
      <button onclick="closeDrawer()" class="px-4 py-2 text-sm text-gray-400 hover:text-white border border-gray-600 rounded-lg">{t["btn_cancel"]}</button>
      <button id="drawer-save-btn" onclick="saveDrawer()" class="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium">
        {t["btn_save"]}
      </button>
    </div>
  </div>
</div>

<!-- ══════════════════════════════════════════════════
     CONFIRM MODAL (保存后重启确认)
══════════════════════════════════════════════════ -->
<div id="modal-overlay" class="fixed inset-0 bg-black/70 z-50 hidden flex items-center justify-center">
  <div class="bg-gray-800 rounded-2xl p-6 w-full max-w-md border border-gray-700 shadow-2xl">
    <div class="text-white font-bold text-lg mb-2">{t["modal_saved"]}</div>
    <div id="modal-msg" class="text-gray-400 text-sm mb-6">{t["modal_restart_confirm"]}</div>
    <div class="flex gap-3 justify-end">
      <button onclick="closeModal()" class="px-4 py-2 text-sm text-gray-400 hover:text-white border border-gray-600 rounded-lg">{t["btn_restart_later"]}</button>
      <button onclick="doRestart()" id="modal-restart-btn" class="px-4 py-2 text-sm bg-orange-600 hover:bg-orange-500 disabled:hover:bg-orange-600 disabled:opacity-70 disabled:cursor-not-allowed text-white rounded-lg font-medium inline-flex items-center justify-center gap-2 min-w-[120px]">
        <svg id="modal-restart-spinner" class="hidden h-4 w-4 animate-spin flex-shrink-0" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="12" cy="12" r="9" class="opacity-25" stroke="currentColor" stroke-width="3"></circle>
          <path class="opacity-90" fill="currentColor" d="M12 3a9 9 0 0 1 9 9h-3a6 6 0 0 0-6-6V3Z"></path>
        </svg>
        <span id="modal-restart-label">{t["btn_restart_now"]}</span>
      </button>
    </div>
  </div>
</div>

<!-- Toast -->
<div id="toast" class="fixed bottom-6 right-6 z-50 hidden">
  <div id="toast-body" class="bg-gray-800 border border-gray-600 text-white text-sm px-4 py-3 rounded-xl shadow-xl"></div>
</div>

<script>
const API = 'http://localhost:18800';
const AGENT_NAMES = T.agent_names;
const AGENT_FILE_LABELS = {{soul:'SOUL',user:'USER',identity:'IDENTITY',agents:'AGENTS',memory:'MEMORY',heartbeat:'HEARTBEAT',tools:'TOOLS'}};
let currentDrawerSave = null;
let currentAgentId = 'main';

function formatBrowserDate(value) {{
  return new Date(value).toLocaleDateString(UI_LOCALE);
}}

function formatBrowserDateTime(value) {{
  return new Date(value).toLocaleString(UI_LOCALE);
}}

function escapeHtml(value) {{
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}}

function parseModelLines(value) {{
  return String(value ?? '')
    .split(/\\r?\\n/)
    .map(line => line.trim())
    .filter(Boolean);
}}

// ── Drawer ────────────────────────────────────────
function openDrawer(title, subtitle, contentHtml, saveFn) {{
  document.getElementById('drawer-title').textContent = title;
  document.getElementById('drawer-subtitle').textContent = subtitle || '';
  document.getElementById('drawer-content').innerHTML = contentHtml;
  document.getElementById('drawer-overlay').classList.remove('hidden');
  document.getElementById('drawer').classList.remove('translate-x-full');
  const footer = document.getElementById('drawer-footer');
  if (saveFn) {{ footer.classList.remove('hidden'); currentDrawerSave = saveFn; }}
  else {{ footer.classList.add('hidden'); currentDrawerSave = null; }}
}}
function closeDrawer() {{
  document.getElementById('drawer').classList.add('translate-x-full');
  document.getElementById('drawer-overlay').classList.add('hidden');
}}
function saveDrawer() {{ if (currentDrawerSave) currentDrawerSave(); }}

// ── Modal ─────────────────────────────────────────
function showSaveModal(msg) {{
  document.getElementById('modal-msg').textContent = msg || T.save_modal_default;
  setRestartButtonLoading(false);
  document.getElementById('modal-overlay').classList.remove('hidden');
  document.getElementById('modal-overlay').style.display = 'flex';
}}
function closeModal() {{
  setRestartButtonLoading(false);
  document.getElementById('modal-overlay').classList.add('hidden');
  document.getElementById('modal-overlay').style.display = 'none';
}}
function setRestartButtonLoading(isLoading) {{
  const btn = document.getElementById('modal-restart-btn');
  const label = document.getElementById('modal-restart-label');
  const spinner = document.getElementById('modal-restart-spinner');
  if (!btn || !label || !spinner) return;
  btn.disabled = isLoading;
  label.textContent = isLoading ? T.btn_restarting : T.btn_restart_now;
  spinner.classList.toggle('hidden', !isLoading);
}}
async function doRestart() {{
  const btn = document.getElementById('modal-restart-btn');
  if (!btn || btn.disabled) return;
  setRestartButtonLoading(true);
  try {{
    const r = await fetch(API + '/api/gateway/restart', {{method:'POST'}});
    const d = await r.json();
    closeModal();
    showToast(d.success ? T.restart_ok : (d.error || T.restart_fail), d.success ? 'ok' : 'err');
  }} catch(e) {{
    closeModal();
    showToast(T.no_connect, 'err');
  }} finally {{
    setRestartButtonLoading(false);
  }}
}}

// ── Toast ─────────────────────────────────────────
function showToast(msg, type) {{
  const el = document.getElementById('toast');
  const body = document.getElementById('toast-body');
  body.textContent = msg;
  body.className = 'text-sm px-4 py-3 rounded-xl shadow-xl border ' +
    (type === 'ok' ? 'bg-emerald-900 border-emerald-600 text-emerald-100' : 'bg-red-900 border-red-600 text-red-100');
  el.classList.remove('hidden');
  setTimeout(() => el.classList.add('hidden'), 3500);
}}

// ── API 调用 ──────────────────────────────────────
async function apiGet(path) {{
  const r = await fetch(API + path, {{cache: 'no-store'}});
  return r.json();
}}
async function apiPatch(path, body) {{
  const r = await fetch(API + path, {{
    method: 'PATCH',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify(body)
  }});
  return r.json();
}}
async function apiPut(path, body) {{
  const r = await fetch(API + path, {{
    method: 'PUT',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify(body)
  }});
  return r.json();
}}

// ── 保存并弹窗 ────────────────────────────────────
async function saveAndConfirm(apiFn, successMsg) {{
  try {{
    const result = await apiFn();
    if (result.error) {{ showToast(result.error, 'err'); return; }}
    await refreshConfigViews();
    closeDrawer();
    showSaveModal(successMsg || T.save_modal_default);
  }} catch(e) {{
    showToast(T.save_error + e.message, 'err');
  }}
}}

// ── 全局配置初始化 ────────────────────────────────
let configLoaded = false;
async function initConfig() {{
  if (configLoaded) return;
  configLoaded = true;
  await renderGlobalCards();
  renderAgentTabs();
  await loadAgentCards('main');
}}

async function refreshConfigViews() {{
  await Promise.all([
    renderGlobalCards(),
    loadAgentCards(currentAgentId),
  ]);
}}

// ── 全局卡片 ─────────────────────────────────────
async function renderGlobalCards() {{
  const container = document.getElementById('global-cards');
  const cards = [
    {{ key:'cron', label:T.card_cron, load: loadCronCard }},
    {{ key:'defaults', label:T.card_defaults, load: loadDefaultsCard }},
    {{ key:'models', label:T.card_models, load: loadModelsCard }},
    {{ key:'acp', label:T.card_acp, load: loadAcpCard }},
    {{ key:'gateway', label:T.card_gateway, load: loadGatewayCard }},
    {{ key:'channels', label:T.card_channels, load: loadChannelsCard }},
    {{ key:'skills', label:T.card_skills, load: loadSkillsCard }},
  ];
  container.innerHTML = cards.map(c => `
    <div id="gcard-${{c.key}}" class="bg-gray-800 rounded-xl p-5 border border-gray-700 cursor-pointer hover:border-blue-500 transition-colors">
      <div class="font-medium text-white mb-3">${{c.label}}</div>
      <div data-role="config-summary" class="text-gray-500 text-sm">${{T.loading}}</div>
    </div>
  `).join('');
  await Promise.all(cards.map(c => c.load()));
}}

function globalCardSummaryEl(cardKey) {{
  return document.querySelector(`#gcard-${{cardKey}} [data-role="config-summary"]`);
}}

function resolveSkillDrawerPath(skills) {{
  const sources = new Set((skills || []).map(skill => skill.source).filter(Boolean));
  if (sources.has('openclaw-managed') && sources.has('openclaw-workspace')) {{
    return '$OPENCLAW_HOME/skills/*/SKILL.md · workspace/skills/*/SKILL.md';
  }}
  if (sources.has('openclaw-workspace')) {{
    return 'workspace/skills/*/SKILL.md';
  }}
  return '$OPENCLAW_HOME/skills/*/SKILL.md';
}}

async function loadCronCard() {{
  const d = await apiGet('/api/config/global/cron');
  const el = document.getElementById('gcard-cron');
  const s = d.summary || {{}};
  const rate = s.avg_success_rate != null ? Math.round(s.avg_success_rate * 100) + '%' : 'N/A';
  const rateColor = (s.avg_success_rate||0) >= 0.9 ? 'text-emerald-400' : (s.avg_success_rate||0) >= 0.6 ? 'text-yellow-400' : 'text-red-400';
  globalCardSummaryEl('cron').innerHTML =
    `${{s.total||0}} · ` + T.enabled_count.replace('{{n}}', s.enabled||0) + ` · <span class="${{rateColor}}">${{rate}}</span>`;
  el.onclick = async () => openCronDrawer((await apiGet('/api/config/global/cron')).jobs || []);
}}

async function loadDefaultsCard() {{
  const d = await apiGet('/api/config/global/defaults');
  const el = document.getElementById('gcard-defaults');
  globalCardSummaryEl('defaults').textContent = d.primary_model || T.not_configured;
  el.onclick = async () => openDefaultsDrawer(await apiGet('/api/config/global/defaults'));
}}

async function loadModelsCard() {{
  const d = await apiGet('/api/config/global/models');
  const el = document.getElementById('gcard-models');
  globalCardSummaryEl('models').textContent =
    T.providers_count.replace('{{n}}', d.summary?.provider_count||0).replace('{{m}}', d.summary?.model_count||0);
  el.onclick = async () => openModelsDrawer((await apiGet('/api/config/global/models')).providers || []);
}}

async function loadAcpCard() {{
  const d = await apiGet('/api/config/global/acp');
  const el = document.getElementById('gcard-acp');
  globalCardSummaryEl('acp').textContent =
    `${{d.backend}} · ${{T.acp_concurrent}} ${{d.max_concurrent_sessions}} · TTL ${{d.ttl_minutes}}min`;
  el.onclick = async () => openAcpDrawer(await apiGet('/api/config/global/acp'));
}}

async function loadGatewayCard() {{
  const d = await apiGet('/api/config/global/gateway');
  const el = document.getElementById('gcard-gateway');
  globalCardSummaryEl('gateway').textContent =
    `:${{d.port}} · ${{d.mode}} · ${{d.bind}}`;
  el.onclick = async () => openGatewayDrawer(await apiGet('/api/config/global/gateway'));
}}

async function loadChannelsCard() {{
  const d = await apiGet('/api/config/global/channels');
  const el = document.getElementById('gcard-channels');
  const names = Object.entries(d)
    .filter(([,v]) => v.enabled)
    .map(([k, v]) => {{
      const overrideCount = v.streaming_overrides?.count || 0;
      const suffix = overrideCount ? ` · ${{T.ch_override_accounts.replace('{{n}}', overrideCount)}}` : '';
      return k.charAt(0).toUpperCase()+k.slice(1)+' on'+suffix;
    }});
  globalCardSummaryEl('channels').textContent =
    names.length ? names.join(' · ') : T.not_configured;
  el.onclick = async () => openChannelsDrawer(await apiGet('/api/config/global/channels'));
}}

async function loadSkillsCard() {{
  const d = await apiGet('/api/config/global/skills');
  const el = document.getElementById('gcard-skills');
  globalCardSummaryEl('skills').textContent = T.skill_installed.replace('{{n}}', d.total||0);
  el.onclick = async () => openSkillsDrawer((await apiGet('/api/config/global/skills')).skills || []);
}}

// ── Drawer: Cron ──────────────────────────────────
function openCronDrawer(jobs) {{
  const thinkMap = {{low:T.cron_think_low,off:T.cron_think_off,auto:T.cron_think_auto}};
  const html = jobs.map(job => {{
    const rate = job.run_success_rate != null ? Math.round(job.run_success_rate*100) : null;
    const rateColor = rate==null?'text-gray-500': rate>=90?'text-emerald-400':rate>=60?'text-yellow-400':'text-red-400';
    const errBadge = job.consecutive_errors > 0
      ? `<span class="ml-2 text-xs bg-red-900/50 text-red-400 border border-red-700 rounded px-1.5 py-0.5">${{T.consec_errors.replace('{{n}}', job.consecutive_errors)}}</span>` : '';
    return `
    <div class="bg-gray-800 rounded-xl p-4 mb-3 border border-gray-700">
      <div class="flex items-start justify-between mb-3">
        <div class="flex-1">
          <div class="flex items-center gap-2">
            <span class="font-medium text-white text-sm">${{job.name}}</span>
            ${{errBadge}}
          </div>
          <div class="text-gray-500 text-xs mt-1">${{job.agent}} · <code class="text-blue-400">${{job.schedule}}</code> ${{job.tz||''}}</div>
        </div>
        <label class="relative inline-flex items-center cursor-pointer ml-3">
          <input type="checkbox" ${{job.enabled?'checked':''}} onchange="patchCronEnabled('${{job.id}}', this.checked)"
            class="sr-only peer">
          <div class="w-9 h-5 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
        </label>
      </div>
      <div class="grid grid-cols-2 gap-2 text-xs text-gray-400 mb-3">
        <div>${{T.cron_runs_lbl}} <span class="text-white">${{job.run_total}}</span></div>
        <div>${{T.cron_success}} <span class="${{rateColor}}">${{rate!=null?rate+'%':'N/A'}}</span></div>
        <div>${{T.cron_timeout}} <span class="text-white">${{job.timeout_seconds}}s</span></div>
        <div>${{T.cron_thinking}} <span class="text-white">${{thinkMap[job.thinking]||job.thinking}}</span></div>
      </div>
      <div class="space-y-2">
        <div class="flex gap-2 items-start">
          <span class="text-gray-500 text-xs w-12 pt-1.5 flex-shrink-0">${{T.cron_plan}}</span>
          <input type="text" value="${{job.schedule}}" id="cron-schedule-${{job.id}}"
            class="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:border-blue-500 focus:outline-none">
          <span class="text-gray-500 text-xs w-20 pt-1.5 flex-shrink-0">${{job.tz}}</span>
        </div>
        <div class="flex gap-2 items-start">
          <span class="text-gray-500 text-xs w-12 pt-1.5 flex-shrink-0">${{T.cron_msg}}</span>
          <textarea rows="2" id="cron-msg-${{job.id}}"
            class="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-3 py-1.5 text-xs text-white resize-none focus:border-blue-500 focus:outline-none">${{job.payload_message}}</textarea>
        </div>
        <div class="flex justify-end">
          <button onclick="saveCronJob('${{job.id}}')"
            class="px-3 py-1 text-xs bg-blue-700 hover:bg-blue-600 text-white rounded-lg">${{T.cron_save_btn}}</button>
        </div>
      </div>
    </div>`;
  }}).join('');
  openDrawer(T.drawer_cron, 'cron/jobs.json', html, null);
}}

async function patchCronEnabled(jobId, enabled) {{
  await saveAndConfirm(() => apiPatch(`/api/config/global/cron/${{jobId}}`, {{enabled}}), T.cron_enable_confirm);
}}
async function saveCronJob(jobId) {{
  const schedule_expr = document.getElementById('cron-schedule-' + jobId)?.value;
  const payload_message = document.getElementById('cron-msg-' + jobId)?.value;
  await saveAndConfirm(
    () => apiPatch(`/api/config/global/cron/${{jobId}}`, {{schedule_expr, payload_message}}),
    T.cron_save_confirm
  );
}}

// ── Drawer: 默认模型 ──────────────────────────────
function openDefaultsDrawer(d) {{
  const fallbackValue = (d.fallback_models || []).join('\\n');
  const imageFallbackValue = (d.image_fallbacks || []).join('\\n');
  const html = `
    <div class="space-y-4">
      <div class="bg-gray-800 rounded-xl p-4 border border-gray-700">
        <label class="text-gray-400 text-xs mb-2 block">${{T.defaults_primary}}</label>
        <input type="text" id="def-primary" value="${{escapeHtml(d.primary_model||'')}}"
          class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white font-mono focus:border-blue-500 focus:outline-none">
      </div>
      <div class="bg-gray-800 rounded-xl p-4 border border-gray-700">
        <label class="text-gray-400 text-xs mb-2 block">${{T.defaults_fallback}}</label>
        <textarea id="def-fallbacks" rows="4"
          class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white font-mono resize-none focus:border-blue-500 focus:outline-none">${{escapeHtml(fallbackValue)}}</textarea>
        <div class="text-gray-500 text-xs mt-2">${{T.defaults_multiline_hint}}</div>
      </div>
      <div class="bg-gray-800 rounded-xl p-4 border border-gray-700">
        <label class="text-gray-400 text-xs mb-2 block">${{T.defaults_image}}</label>
        <input type="text" id="def-image-primary" value="${{escapeHtml(d.image_primary||'')}}"
          class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white font-mono focus:border-blue-500 focus:outline-none">
      </div>
      <div class="bg-gray-800 rounded-xl p-4 border border-gray-700">
        <label class="text-gray-400 text-xs mb-2 block">${{T.defaults_image_fallback}}</label>
        <textarea id="def-image-fallbacks" rows="3"
          class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white font-mono resize-none focus:border-blue-500 focus:outline-none">${{escapeHtml(imageFallbackValue)}}</textarea>
        <div class="text-gray-500 text-xs mt-2">${{T.defaults_multiline_hint}}</div>
      </div>
    </div>`;
  openDrawer(T.drawer_defaults, 'openclaw.json > agents.defaults', html,
    () => saveAndConfirm(
      () => apiPatch('/api/config/global/defaults', {{
        primary_model: document.getElementById('def-primary').value.trim(),
        fallback_models: parseModelLines(document.getElementById('def-fallbacks').value),
        image_primary: document.getElementById('def-image-primary').value.trim(),
        image_fallbacks: parseModelLines(document.getElementById('def-image-fallbacks').value),
      }}),
      T.defaults_confirm
    )
  );
}}

// ── Drawer: 模型提供商 ────────────────────────────
function openModelsDrawer(providers) {{
  const html = providers.map(p => `
    <div class="bg-gray-800 rounded-xl p-4 mb-3 border border-gray-700">
      <div class="flex items-center justify-between mb-3">
        <div class="font-medium text-white">${{p.id}}</div>
        <span class="text-xs text-gray-500">${{T.models_count.replace('{{n}}', p.model_count)}}</span>
      </div>
      <div class="space-y-2 mb-3">
        <div class="flex gap-2 items-center">
          <span class="text-gray-500 text-xs w-16 flex-shrink-0">${{T.field_base_url}}</span>
          <input type="text" value="${{p.base_url}}" id="model-url-${{p.id}}"
            class="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:border-blue-500 focus:outline-none">
        </div>
        ${{p.has_api_key ? `
        <div class="flex gap-2 items-center">
          <span class="text-gray-500 text-xs w-16 flex-shrink-0">${{T.field_api_key}}</span>
          <input type="password" placeholder="${{p.api_key_masked||'sk-***...'}}" id="model-key-${{p.id}}"
            class="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:border-blue-500 focus:outline-none">
        </div>` : ''}}
      </div>
      <div class="flex flex-wrap gap-1 mb-3">
        ${{p.models.map(m => `<span class="text-xs bg-gray-700 text-gray-300 rounded px-2 py-0.5">${{m.id}}</span>`).join('')}}
      </div>
      <div class="flex justify-end">
        <button onclick="saveProvider('${{p.id}}')"
          class="px-3 py-1 text-xs bg-blue-700 hover:bg-blue-600 text-white rounded-lg">${{T.btn_save}}</button>
      </div>
    </div>`).join('');
  openDrawer(T.drawer_models, 'openclaw.json > models.providers', html, null);
}}
async function saveProvider(providerId) {{
  const base_url = document.getElementById('model-url-' + providerId)?.value;
  const api_key = document.getElementById('model-key-' + providerId)?.value;
  await saveAndConfirm(
    () => apiPatch(`/api/config/global/models/${{providerId}}`, {{base_url, api_key}}),
    T.models_confirm
  );
}}

// ── Drawer: ACP ───────────────────────────────────
function openAcpDrawer(d) {{
  const html = `
    <div class="space-y-4">
      <div class="bg-gray-800 rounded-xl p-4 border border-gray-700">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-gray-400 text-xs mb-1.5 block">${{T.acp_max_sessions}}</label>
            <input type="number" id="acp-concurrent" value="${{d.max_concurrent_sessions}}"
              class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none">
          </div>
          <div>
            <label class="text-gray-400 text-xs mb-1.5 block">${{T.acp_ttl}}</label>
            <input type="number" id="acp-ttl" value="${{d.ttl_minutes}}"
              class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none">
          </div>
          <div>
            <label class="text-gray-400 text-xs mb-1.5 block">${{T.acp_default_agent}}</label>
            <input type="text" id="acp-agent" value="${{d.default_agent}}"
              class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none">
          </div>
          <div>
            <label class="text-gray-400 text-xs mb-1.5 block">${{T.field_coalesce_idle}}</label>
            <input type="number" id="acp-coalesce" value="${{d.coalesce_idle_ms}}"
              class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none">
          </div>
        </div>
      </div>
      <div class="bg-gray-800 rounded-xl p-4 border border-gray-700 text-sm">
        <div class="text-gray-400 text-xs mb-2">${{T.acp_readonly}}</div>
        <div class="grid grid-cols-2 gap-2 text-xs">
          <div class="text-gray-500">${{T.field_backend}}</div><div class="text-gray-300 font-mono">${{d.backend}}</div>
          <div class="text-gray-500">${{T.acp_allowed_agents}}</div><div class="text-gray-300">${{(d.allowed_agents||[]).join(', ')}}</div>
          <div class="text-gray-500">${{T.acp_dispatch}}</div><div class="text-gray-300">${{d.dispatch_enabled ? T.status_enabled : T.status_disabled}}</div>
        </div>
      </div>
    </div>`;
  openDrawer(T.drawer_acp, 'openclaw.json > acp', html,
    () => saveAndConfirm(() => apiPatch('/api/config/global/acp', {{
      max_concurrent_sessions: document.getElementById('acp-concurrent').value,
      ttl_minutes: document.getElementById('acp-ttl').value,
      default_agent: document.getElementById('acp-agent').value,
      coalesce_idle_ms: document.getElementById('acp-coalesce').value,
    }}), T.acp_confirm)
  );
}}

// ── Drawer: Gateway ───────────────────────────────
function openGatewayDrawer(d) {{
  const html = `
    <div class="bg-gray-800 rounded-xl p-4 border border-gray-700 space-y-4">
      <div class="bg-yellow-900/20 border border-yellow-700/50 rounded-lg p-3 text-xs text-yellow-300">
        ${{T.gw_warn}}
      </div>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="text-gray-400 text-xs mb-1.5 block">${{T.gw_port}}</label>
          <div class="bg-gray-700 rounded-lg px-3 py-2 text-sm text-gray-400 font-mono">${{d.port}}</div>
        </div>
        <div>
          <label class="text-gray-400 text-xs mb-1.5 block">${{T.gw_mode}}</label>
          <select id="gw-mode" class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none">
            <option value="local" ${{d.mode==='local'?'selected':''}}>${{T.gw_local}}</option>
            <option value="remote" ${{d.mode==='remote'?'selected':''}}>${{T.gw_remote}}</option>
          </select>
        </div>
        <div>
          <label class="text-gray-400 text-xs mb-1.5 block">${{T.gw_bind}}</label>
          <select id="gw-bind" class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none">
            <option value="loopback" ${{d.bind==='loopback'?'selected':''}}>${{T.gw_loopback}}</option>
            <option value="auto" ${{d.bind==='auto'?'selected':''}}>${{T.gw_auto}}</option>
            <option value="lan" ${{d.bind==='lan'?'selected':''}}>${{T.gw_lan}}</option>
            <option value="tailnet" ${{d.bind==='tailnet'?'selected':''}}>${{T.gw_tailnet}}</option>
            <option value="custom" ${{d.bind==='custom'?'selected':''}}>${{T.gw_custom}}</option>
          </select>
        </div>
        <div>
          <label class="text-gray-400 text-xs mb-1.5 block">${{T.gw_auth}}</label>
          <div class="bg-gray-700 rounded-lg px-3 py-2 text-sm text-gray-400">${{d.auth_mode}}</div>
        </div>
      </div>
    </div>`;
  openDrawer(T.drawer_gateway, 'openclaw.json > gateway', html,
    () => saveAndConfirm(() => apiPatch('/api/config/global/gateway', {{
      mode: document.getElementById('gw-mode').value,
      bind: document.getElementById('gw-bind').value,
    }}), T.gw_confirm)
  );
}}

// ── Drawer: 消息渠道 ──────────────────────────────
function getChannelStreamingMeta(ch, cfg) {{
  const options = (cfg.streaming_options && cfg.streaming_options.length)
    ? cfg.streaming_options
    : legacyChannelStreamingOptions(ch);
  const allowed = new Set(options.map(opt => opt.value));
  let value = cfg.streaming_mode || normalizeChannelStreamingMode(ch, cfg.streaming);
  if (!allowed.has(value) && options.length) value = options[0].value;
  return {{ value, options }};
}}

function legacyChannelStreamingOptions(ch) {{
  if (ch === 'telegram') {{
    return [
      {{ value: 'off', label_key: 'ch_streaming_off' }},
      {{ value: 'partial', label_key: 'ch_streaming_partial' }},
      {{ value: 'block', label_key: 'ch_streaming_block' }},
    ];
  }}
  return [
    {{ value: 'off', label_key: 'ch_streaming_off' }},
    {{ value: 'block', label_key: 'ch_streaming_block' }},
  ];
}}

function normalizeChannelStreamingMode(ch, rawValue) {{
  if (rawValue === null || rawValue === undefined || rawValue === '' || rawValue === false) return 'off';
  const normalized = typeof rawValue === 'string' ? rawValue.trim().toLowerCase() : String(rawValue).trim().toLowerCase();
  if (ch === 'telegram') {{
    if (['off', 'false', '0'].includes(normalized)) return 'off';
    if (normalized === 'block') return 'block';
    if (['partial', 'true', 'on'].includes(normalized)) return 'partial';
    return normalized || 'off';
  }}
  if (['off', 'false', '0'].includes(normalized)) return 'off';
  if (['block', 'true', 'on', 'partial'].includes(normalized)) return 'block';
  return normalized || 'off';
}}

function channelStreamingPayload(ch, mode) {{
  if (ch === 'telegram') return mode;
  return mode === 'block';
}}

function selectField(id, label, value, options) {{
  const opts = options.map(opt => {{
    const text = T[opt.label_key] || opt.value;
    return `<option value="${{opt.value}}" ${{opt.value===value?'selected':''}}>${{text}}</option>`;
  }}).join('');
  return `<div class="py-2 border-b border-gray-700">
    <label for="${{id}}" class="text-gray-400 text-sm mb-2 block">${{label}}</label>
    <select id="${{id}}" class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none">
      ${{opts}}
    </select>
  </div>`;
}}

function renderStreamingOverrides(ch, cfg) {{
  const overrides = cfg.streaming_overrides || inferStreamingOverrides(ch, cfg);
  const parts = [];
  if (overrides.count) parts.push(T.ch_override_accounts.replace('{{n}}', overrides.count) + `: ${{(overrides.accounts || []).join(', ')}}`);
  if (overrides.has_default_account_override) parts.push(T.ch_override_default);
  if (!parts.length) return `<div class="mt-3 text-xs text-gray-500">${{T.ch_override_none}}</div>`;
  return `<div class="mt-3 text-xs text-amber-300 bg-amber-900/20 border border-amber-700/40 rounded-lg px-3 py-2">${{parts.join(' · ')}}</div>`;
}}

function inferStreamingOverrides(ch, cfg) {{
  const overrides = {{ count: 0, accounts: [], has_default_account_override: false }};
  const accounts = cfg.accounts || {{}};
  const channelMode = getChannelStreamingMeta(ch, cfg).value;
  Object.entries(accounts).forEach(([name, accountCfg]) => {{
    const mode = normalizeChannelStreamingMode(ch, accountCfg?.streaming);
    if (name === 'default') {{
      overrides.has_default_account_override = mode !== channelMode;
      return;
    }}
    if (mode !== channelMode) overrides.accounts.push(name);
  }});
  overrides.count = overrides.accounts.length;
  return overrides;
}}

function renderChannelAccounts(ch, cfg) {{
  const accounts = cfg.accounts || {{}};
  const names = Object.keys(accounts).sort((a, b) => {{
    if (a === 'default') return 1;
    if (b === 'default') return -1;
    return a.localeCompare(b);
  }});
  if (!names.length) {{
    return `<div class="mt-3 border-t border-gray-700 pt-3">
      <div class="text-xs text-gray-400 mb-2">${{T.ch_accounts}}</div>
      <div class="text-xs text-gray-500">${{T.ch_accounts_empty}}</div>
    </div>`;
  }}

  const channelMode = getChannelStreamingMeta(ch, cfg).value;
  const options = getChannelStreamingMeta(ch, cfg).options;
  const rows = names.map(name => {{
    const accountCfg = accounts[name] || {{}};
    const accountMode = normalizeChannelStreamingMode(ch, accountCfg.streaming);
    const inherited = accountMode === channelMode;
    const accountLabel = name === 'default' ? T.ch_account_default : name;
    const stateText = inherited ? T.ch_account_inherits : T.ch_account_overrides;
    const stateClass = inherited ? 'text-gray-500' : 'text-amber-300';
    const selectId = `ch-account-${{ch}}-${{name}}-streaming-mode`;
    const optionsHtml = options.map(opt => {{
      const text = T[opt.label_key] || opt.value;
      return `<option value="${{opt.value}}" ${{opt.value===accountMode?'selected':''}}>${{text}}</option>`;
    }}).join('');
    return `<div class="flex items-center justify-between gap-3 py-2 border-b border-gray-700/60 last:border-b-0">
      <div>
        <div class="text-sm text-white">${{accountLabel}}</div>
        <div class="text-xs ${{stateClass}}">${{stateText}}</div>
      </div>
      <div class="text-right">
        <div class="text-right">
          <div class="text-xs text-gray-500">${{T.ch_account_streaming}}</div>
          <select id="${{selectId}}" class="mt-1 min-w-[120px] bg-gray-700 border border-gray-600 rounded-lg px-2 py-1.5 text-sm text-white focus:border-blue-500 focus:outline-none">
            ${{optionsHtml}}
          </select>
        </div>
      </div>
    </div>`;
  }}).join('');

  return `<div class="mt-3 border-t border-gray-700 pt-3">
    <div class="text-xs text-gray-400 mb-2">${{T.ch_accounts}}</div>
    <div class="bg-gray-900/30 rounded-lg px-3">${{rows}}</div>
  </div>`;
}}

function openChannelsDrawer(d) {{
  const boolField = (id, label, val) =>
    `<div class="flex items-center justify-between py-2 border-b border-gray-700">
      <span class="text-gray-400 text-sm">${{label}}</span>
      <label class="relative inline-flex items-center cursor-pointer">
        <input type="checkbox" ${{val?'checked':''}} id="${{id}}" class="sr-only peer">
        <div class="w-9 h-5 bg-gray-600 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
      </label>
    </div>`;
  const html = Object.entries(d).map(([ch, cfg]) => `
    <div class="bg-gray-800 rounded-xl p-4 mb-3 border border-gray-700">
      <div class="flex items-center gap-2 mb-3">
        <span class="font-medium text-white capitalize">${{ch}}</span>
        <span class="text-xs ${{cfg.enabled?'text-emerald-400':'text-gray-500'}}">${{cfg.enabled?T.status_enabled:T.status_disabled}}</span>
      </div>
      ${{boolField(`ch-${{ch}}-enabled`, T.ch_enable, cfg.enabled)}}
      ${{selectField(`ch-${{ch}}-streaming-mode`, T.ch_streaming_mode, getChannelStreamingMeta(ch, cfg).value, getChannelStreamingMeta(ch, cfg).options)}}
      ${{renderStreamingOverrides(ch, cfg)}}
      ${{renderChannelAccounts(ch, cfg)}}
    </div>`).join('');
  openDrawer(T.drawer_channels, 'openclaw.json > channels', html, () => saveAllChannels(d));
}}

async function saveAllChannels(channelsData) {{
  try {{
    for (const [ch, cfg] of Object.entries(channelsData)) {{
      const enabled = document.getElementById(`ch-${{ch}}-enabled`)?.checked;
      const streamingMode = document.getElementById(`ch-${{ch}}-streaming-mode`)?.value || 'off';
      const streaming = channelStreamingPayload(ch, streamingMode);
      const channelResult = await apiPatch(`/api/config/global/channels/${{ch}}`, {{enabled, streaming}});
      if (channelResult.error) {{ showToast(channelResult.error, 'err'); return; }}

      const accounts = cfg.accounts || {{}};
      for (const accountName of Object.keys(accounts)) {{
        const accountStreaming = document.getElementById(`ch-account-${{ch}}-${{accountName}}-streaming-mode`)?.value;
        if (accountStreaming == null) continue;
        const accountResult = await apiPatch(`/api/config/global/channels/${{ch}}/accounts/${{accountName}}`, {{streaming: accountStreaming}});
        if (accountResult.error) {{ showToast(accountResult.error, 'err'); return; }}
      }}
    }}

    await refreshConfigViews();
    closeDrawer();
    showSaveModal(T.save_modal_default);
  }} catch(e) {{
    showToast(T.save_error + e.message, 'err');
  }}
}}

// ── Drawer: Skills ────────────────────────────────
function openSkillsDrawer(skills) {{
  const html = skills.map(s => `
    <div class="bg-gray-800 rounded-xl p-4 mb-2 border border-gray-700 cursor-pointer hover:border-blue-500 transition-colors"
      onclick="openSkillContent('${{s.name}}')">
      <div class="flex items-center justify-between">
        <div class="font-medium text-white text-sm">${{s.name}}</div>
        <div class="flex gap-2">
          ${{s.has_scripts ? '<span class="text-xs bg-gray-700 text-gray-400 rounded px-1.5 py-0.5">scripts</span>' : ''}}
          ${{s.has_skill_md ? '<span class="text-xs bg-blue-900/50 text-blue-400 rounded px-1.5 py-0.5">SKILL.md</span>' : ''}}
        </div>
      </div>
      <div class="text-gray-500 text-xs mt-1">${{s.summary||T.no_desc}}</div>
    </div>`).join('');
  openDrawer(T.drawer_skills, resolveSkillDrawerPath(skills), html, null);
}}
async function openSkillContent(name) {{
  const d = await apiGet(`/api/config/global/skills/${{name}}`);
  openDrawer(`${{T.skill_title_prefix}} ${{name}}`, T.skill_readonly, `
    <pre class="text-xs text-gray-300 whitespace-pre-wrap bg-gray-800 rounded-xl p-4 border border-gray-700 overflow-x-auto">${{
      d.content ? d.content.replace(/</g,'&lt;').replace(/>/g,'&gt;') : T.skill_no_content
    }}</pre>`, null);
}}

// ── Agent Tabs ────────────────────────────────────
function renderAgentTabs() {{
  const agents = ['main','monitor','note','code','image'];
  document.getElementById('agent-tabs').innerHTML = agents.map(a => `
    <button id="atab-${{a}}" onclick="switchAgentTab('${{a}}')"
      class="agent-tab-btn px-4 py-2 rounded-lg text-sm font-medium border transition-colors ${{
        a==='main' ? 'bg-gray-700 border-blue-500 text-white' : 'bg-gray-800 border-gray-700 text-gray-400 hover:text-white'
      }}">
      ${{AGENT_NAMES[a]||a}}
    </button>`).join('');
}}

function switchAgentTab(agentId) {{
  currentAgentId = agentId;
  document.querySelectorAll('.agent-tab-btn').forEach(b => {{
    b.className = 'agent-tab-btn px-4 py-2 rounded-lg text-sm font-medium border transition-colors bg-gray-800 border-gray-700 text-gray-400 hover:text-white';
  }});
  const active = document.getElementById('atab-' + agentId);
  active.className = 'agent-tab-btn px-4 py-2 rounded-lg text-sm font-medium border transition-colors bg-gray-700 border-blue-500 text-white';
  loadAgentCards(agentId);
}}

// ── Agent 卡片 ────────────────────────────────────
async function loadAgentCards(agentId) {{
  const container = document.getElementById('agent-cards');
  container.innerHTML = `<div class="bg-gray-800 rounded-xl p-5 border border-gray-700 animate-pulse col-span-3">
    <div class="h-4 bg-gray-700 rounded w-1/3 mb-3"></div><div class="h-3 bg-gray-700 rounded w-2/3"></div></div>`;

  const d = await apiGet(`/api/config/agent/${{agentId}}`);
  if (d.error) {{
    container.innerHTML = `<div class="text-red-400 text-sm">${{d.error}}</div>`;
    return;
  }}

  const fileCards = Object.entries(AGENT_FILE_LABELS).map(([key, label]) => {{
    const info = d.files?.[key] || {{}};
    return `
      <div class="bg-gray-800 rounded-xl p-5 border border-gray-700 cursor-pointer hover:border-blue-500 transition-colors"
        onclick="openAgentFileDrawer('${{agentId}}', '${{key}}', '${{label}}')">
        <div class="flex items-center justify-between mb-2">
          <span class="font-medium text-white text-sm">${{label}}.md</span>
          ${{info.exists ? `<span class="text-xs text-emerald-400">${{T.file_exists}}</span>` : `<span class="text-xs text-gray-500">${{T.file_not_exists}}</span>`}}
        </div>
        <div class="text-gray-500 text-xs leading-relaxed line-clamp-2">${{info.summary||T.file_empty}}</div>
        <div class="mt-2 text-gray-600 text-xs">${{info.char_count||0}} ${{T.chars}}</div>
      </div>`;
  }});

  const extraCards = [
    d.has_models ? `
      <div class="bg-gray-800 rounded-xl p-5 border border-gray-700 cursor-pointer hover:border-blue-500 transition-colors"
        onclick="openAgentModelsDrawer('${{agentId}}')">
        <div class="font-medium text-white text-sm mb-2">${{T.model_config}}</div>
        <div class="text-gray-500 text-xs">models.json</div>
      </div>` : '',
    d.has_auth ? `
      <div class="bg-gray-800 rounded-xl p-5 border border-gray-700 cursor-pointer hover:border-blue-500 transition-colors"
        onclick="openAgentAuthDrawer('${{agentId}}')">
        <div class="font-medium text-white text-sm mb-2">${{T.auth_creds}}</div>
        <div class="text-gray-500 text-xs">auth-profiles.json</div>
      </div>` : '',
  ];

  container.innerHTML = [...fileCards, ...extraCards].join('');
}}

// ── Drawer: Agent File ────────────────────────────
async function openAgentFileDrawer(agentId, fileKey, label) {{
  const d = await apiGet(`/api/config/agent/${{agentId}}/${{fileKey}}`);
  const html = `
    <div class="mb-3 text-xs text-gray-500">${{d.path}}</div>
    <textarea id="agent-file-editor" rows="28"
      class="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm text-gray-200 font-mono resize-none focus:border-blue-500 focus:outline-none leading-relaxed"
      oninput="markDirty()">${{d.content ? d.content.replace(/</g,'&lt;').replace(/>/g,'&gt;') : ''}}</textarea>
    <div id="dirty-indicator" class="hidden mt-2 text-xs text-orange-400">${{T.unsaved}}</div>`;
  openDrawer(
    `${{AGENT_NAMES[agentId]||agentId}} · ${{label}}.md`,
    `workspace/${{agentId}}/${{label}}.md`,
    html,
    () => saveAndConfirm(
      () => apiPut(`/api/config/agent/${{agentId}}/${{fileKey}}`, {{
        content: document.getElementById('agent-file-editor')?.value
      }}),
      T.agent_file_confirm.replace('{{label}}', label)
    )
  );
}}
function markDirty() {{
  document.getElementById('dirty-indicator')?.classList.remove('hidden');
  const editor = document.getElementById('agent-file-editor');
  if (editor) editor.style.borderColor = '#f97316';
}}

// ── Drawer: Agent Models ──────────────────────────
async function openAgentModelsDrawer(agentId) {{
  const d = await apiGet(`/api/config/agent/${{agentId}}/models`);
  const html = d.providers.map(p => `
    <div class="bg-gray-800 rounded-xl p-4 mb-3 border border-gray-700">
      <div class="font-medium text-white mb-3">${{p.id}}</div>
      <div class="space-y-2">
        <div class="flex gap-2 items-center">
          <span class="text-gray-500 text-xs w-16 flex-shrink-0">${{T.field_base_url}}</span>
          <input type="text" value="${{p.base_url}}" id="amod-url-${{agentId}}-${{p.id}}"
            class="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:border-blue-500 focus:outline-none">
        </div>
        ${{p.has_api_key ? `
        <div class="flex gap-2 items-center">
          <span class="text-gray-500 text-xs w-16 flex-shrink-0">${{T.field_api_key}}</span>
          <input type="password" placeholder="${{p.api_key_masked}}" id="amod-key-${{agentId}}-${{p.id}}"
            class="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:border-blue-500 focus:outline-none">
        </div>` : ''}}
        <div class="flex flex-wrap gap-1 mt-1">
          ${{p.models.map(m => `<span class="text-xs bg-gray-700 text-gray-400 rounded px-1.5 py-0.5">${{m.id}}</span>`).join('')}}
        </div>
        <div class="flex justify-end mt-2">
          <button onclick="saveAgentProvider('${{agentId}}', '${{p.id}}')"
            class="px-3 py-1 text-xs bg-blue-700 hover:bg-blue-600 text-white rounded-lg">${{T.btn_save}}</button>
        </div>
      </div>
    </div>`).join('');
  openDrawer(`${{T.model_config}}`, `${{agentId}} · models.json`, html, null);
}}
async function saveAgentProvider(agentId, providerId) {{
  const base_url = document.getElementById(`amod-url-${{agentId}}-${{providerId}}`)?.value;
  const api_key = document.getElementById(`amod-key-${{agentId}}-${{providerId}}`)?.value;
  await saveAndConfirm(
    () => apiPatch(`/api/config/agent/${{agentId}}/models/${{providerId}}`, {{base_url, api_key}}),
    T.agent_model_confirm
  );
}}

// ── Drawer: Agent Auth ────────────────────────────
async function openAgentAuthDrawer(agentId) {{
  const d = await apiGet(`/api/config/agent/${{agentId}}/auth`);
  const typeLabel = {{api_key:T.field_api_key, token:T.field_token, oauth:'OAuth'}};
  const html = d.profiles.map(p => {{
    const lastUsed = p.last_used ? formatBrowserDate(p.last_used) : T.never;
    return `
    <div class="bg-gray-800 rounded-xl p-4 mb-3 border border-gray-700">
      <div class="flex items-center justify-between mb-3">
        <div>
          <div class="text-white font-medium text-sm">${{p.provider}}</div>
          <div class="text-gray-500 text-xs">${{typeLabel[p.type]||p.type}} · ${{T.last_used}} ${{lastUsed}}</div>
        </div>
        ${{p.error_count > 0 ? `<span class="text-xs text-red-400">${{T.error_count.replace('{{n}}', p.error_count)}}</span>` : `<span class="text-xs text-emerald-400">${{T.status_ok}}</span>`}}
      </div>
      ${{p.type === 'oauth' ? `
        <div class="bg-gray-700 rounded-lg p-2 text-xs text-gray-400">${{p.display||T.oauth_readonly}}</div>
        ${{p.expires ? `<div class="text-xs text-gray-500 mt-1">${{T.expires}} ${{formatBrowserDateTime(p.expires)}}</div>` : ''}}` :
      p.type === 'api_key' ? `
        <div class="flex gap-2 items-center">
          <span class="text-gray-500 text-xs w-12 flex-shrink-0">${{T.field_key}}</span>
          <input type="password" placeholder="${{p.key_masked}}" id="auth-key-${{agentId}}-${{p.id}}"
            class="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:border-blue-500 focus:outline-none">
          <button onclick="saveAuthKey('${{agentId}}','${{p.id}}','api_key')"
            class="px-3 py-1 text-xs bg-blue-700 hover:bg-blue-600 text-white rounded-lg">${{T.btn_save}}</button>
        </div>` :
      p.type === 'token' ? `
        <div class="flex gap-2 items-center">
          <span class="text-gray-500 text-xs w-12 flex-shrink-0">${{T.field_token}}</span>
          <input type="password" placeholder="${{p.token_masked}}" id="auth-token-${{agentId}}-${{p.id}}"
            class="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:border-blue-500 focus:outline-none">
          <button onclick="saveAuthKey('${{agentId}}','${{p.id}}','token')"
            class="px-3 py-1 text-xs bg-blue-700 hover:bg-blue-600 text-white rounded-lg">${{T.btn_save}}</button>
        </div>` : ''}}
    </div>`;
  }}).join('');
  openDrawer(`${{T.auth_creds}}`, `${{agentId}} · auth-profiles.json`, html, null);
}}
async function saveAuthKey(agentId, profileId, type) {{
  const keyEl = document.getElementById(`auth-key-${{agentId}}-${{profileId}}`);
  const tokenEl = document.getElementById(`auth-token-${{agentId}}-${{profileId}}`);
  const key = keyEl?.value;
  const token = tokenEl?.value;
  if (!key && !token) {{ showToast(T.no_creds, 'err'); return; }}
  await saveAndConfirm(
    () => apiPatch(`/api/config/agent/${{agentId}}/auth/${{profileId}}`, {{key, token}}),
    T.auth_confirm
  );
}}
</script>
</body>
</html>"""


def main():
    import sys
    lang = "zh"
    for arg in sys.argv[1:]:
        if arg.startswith("--lang="):
            lang = arg.split("=", 1)[1]
        elif arg in ("--en", "--zh"):
            lang = arg[2:]

    print(f"正在读取 data.json... (lang={lang})")
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    print("正在生成 report.html...")
    html = build_html(data, lang)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"完成: file://{OUTPUT_FILE}")


if __name__ == "__main__":
    main()
