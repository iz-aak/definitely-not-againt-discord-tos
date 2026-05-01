import requests
import time
from datetime import datetime
from webhook_config import WEBHOOK_URL, FLASK_URL

_health_message_id = None
_health_webhook_id = None
_health_webhook_token = None

def get_time():
    return datetime.now().strftime("%H:%M:%S")

def _parse_webhook(url):
    parts = url.rstrip("/").split("/")
    return parts[-2], parts[-1]

def send_log(lines: list[str], title: str, color: int):
    if not WEBHOOK_URL:
        return
    body = "\n".join(lines)
    payload = {
        "embeds": [{
            "title": title,
            "description": f"```\n{body}\n```",
            "color": color
        }]
    }
    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=5)
    except Exception:
        pass

def log_startup(username, userid, heartbeat_interval, status, custom_status):
    lines = [
        f"[INFO] Authenticated as: {username} ({userid})",
        f"[{get_time()}] [CONNECTING] Establishing Gateway connection...",
        f"[{get_time()}] [SUCCESS] Handshake complete. Interval: {heartbeat_interval}ms",
        f"[{get_time()}] [SUCCESS] Presence set to: {custom_status}",
    ]
    send_log(lines, "Session Started", 0x5865F2)

def log_heartbeat(success: bool, error: str = ""):
    if success:
        lines = [
            f"[{get_time()}] [HEARTBEAT] Sending keep-alive pulse...",
            f"[{get_time()}] [SUCCESS] Pulse sent.",
        ]
        send_log(lines, "Pulse", 0x9B59B6)
    else:
        lines = [
            f"[{get_time()}] [FAILURE] Pulse failed: {error}",
            f"[{get_time()}] [RETRYING] Reconnecting in 5s...",
        ]
        send_log(lines, "Reconnecting", 0xE74C3C)

def send_health(state: dict):
    global _health_message_id, _health_webhook_id, _health_webhook_token

    if not WEBHOOK_URL:
        return

    if _health_webhook_id is None:
        _health_webhook_id, _health_webhook_token = _parse_webhook(WEBHOOK_URL)

    uptime_secs = int(time.time() - state["start_time"])
    hours, rem = divmod(uptime_secs, 3600)
    mins, secs = divmod(rem, 60)
    uptime_str = f"{hours}h {mins}m {secs}s"

    last_hb = state.get("last_heartbeat")
    if last_hb:
        ago = int(time.time() - last_hb)
        last_hb_str = f"`{datetime.fromtimestamp(last_hb).strftime('%H:%M:%S')}` (`{ago}` seconds ago)"
    else:
        last_hb_str = "`never`"

    secs_to_next = state.get("secs_to_next_pulse", 0)
    connected = state.get("connected", False)
    color = 0x2ECC71 if connected else 0xE74C3C

    description = "\n".join([
        f"Currently: Waiting `{secs_to_next}` secs to send next pulse",
        "---",
        f"Presence `{state.get('status', 'idle')}`",
        "---",
        f"Status `{state.get('custom_status') or 'empty'}`",
        "---",
        f"Uptime `{uptime_str}`",
        "---",
        f"Reconnects `{state.get('reconnects', 0)}`",
        "---",
        f"Last Heartbeat {last_hb_str}",
        "---",
        f"Flask `{FLASK_URL}`",
        "---",
        f"-# Last updated: {get_time()}",
    ])

    payload = {
        "embeds": [{
            "title": "🟢 Onliner Health" if connected else "🔴 Onliner Health",
            "description": description,
            "color": color,
        }]
    }

    try:
        if _health_message_id:
            url = f"https://discord.com/api/webhooks/{_health_webhook_id}/{_health_webhook_token}/messages/{_health_message_id}"
            requests.patch(url, json=payload, timeout=5)
        else:
            r = requests.post(f"{WEBHOOK_URL}?wait=true", json=payload, timeout=5)
            if r.status_code == 200:
                _health_message_id = r.json()["id"]
    except Exception:
        pass
