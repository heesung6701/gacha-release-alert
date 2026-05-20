from __future__ import annotations

import hashlib
import hmac
import json

import httpx

from .models import ReleaseItem

SOURCE_LABELS = {
    "gashapon": "Bandai Gashapon",
    "ichiban_kuji": "Ichiban Kuji",
}


class DiscordNotifier:
    def __init__(self, webhook_url: str, timeout_seconds: int = 20, webhook_secret: str = "") -> None:
        self.webhook_url = webhook_url.strip()
        self.timeout_seconds = timeout_seconds
        self.webhook_secret = webhook_secret.strip()

    def send(self, item: ReleaseItem) -> None:
        if not self.webhook_url:
            raise ValueError("discord_webhook_url is empty")
        payload = self._payload(item)
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.webhook_secret:
            signature = hmac.new(self.webhook_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
            headers["X-Hub-Signature-256"] = f"sha256={signature}"
        with httpx.Client(timeout=self.timeout_seconds) as client:
            client.post(self.webhook_url, content=body, headers=headers).raise_for_status()

    def _payload(self, item: ReleaseItem) -> dict:
        fields = [
            {"name": "소스", "value": SOURCE_LABELS.get(item.source, item.source), "inline": True},
            {"name": "구독 캐릭터", "value": item.character, "inline": True},
            {"name": "검색 키워드", "value": item.keyword, "inline": True},
        ]
        if item.release_text:
            fields.append({"name": "발매/판매 정보", "value": item.release_text, "inline": False})
        if item.status_text:
            fields.append({"name": "상태", "value": item.status_text, "inline": True})
        if item.price:
            fields.append({"name": "가격", "value": item.price, "inline": True})
        if item.lineup_names:
            fields.append({"name": "라인업", "value": ", ".join(item.lineup_names), "inline": False})

        embed: dict = {
            "title": item.title,
            "url": item.url,
            "description": item.description or "새 공식 발매 정보가 감지됐어요.",
            "fields": fields,
            "footer": {"text": "Gacha Release Alert"},
        }
        if item.image_url:
            embed["thumbnail"] = {"url": item.image_url}

        return {
            "content": f"🔔 **{item.character}** 신규 굿즈 알림\n{item.title}\n{item.url}",
            "embeds": [embed],
        }
