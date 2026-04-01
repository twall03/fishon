"""Alert notifications via webhook (Slack/Discord)."""

import json
import requests
from pipeline.config import ALERT_WEBHOOK_URL


def send_alert(message: str, level: str = "warning"):
    """Send an alert to configured webhook. No-op if no webhook configured."""
    if not ALERT_WEBHOOK_URL:
        print(f"[ALERT] {level.upper()}: {message}")
        return

    payload = {"content": f"**[FishOn {level.upper()}]** {message}"}

    try:
        requests.post(ALERT_WEBHOOK_URL, json=payload, timeout=10)
    except Exception as e:
        print(f"[ALERT] Failed to send webhook: {e}")
        print(f"[ALERT] {level.upper()}: {message}")
