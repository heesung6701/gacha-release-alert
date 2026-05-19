from __future__ import annotations

from pathlib import Path
from typing import Literal, Union

import yaml
from pydantic import BaseModel, Field, HttpUrl, field_validator

SourceName = Literal["gashapon", "ichiban_kuji"]


class Subscription(BaseModel):
    character: str
    keywords: list[str] = Field(min_length=1)
    sources: list[SourceName] = Field(default_factory=lambda: ["gashapon", "ichiban_kuji"])

    @field_validator("character")
    @classmethod
    def character_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("character must not be blank")
        return value

    @field_validator("keywords")
    @classmethod
    def keywords_must_not_be_blank(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values if value.strip()]
        if not cleaned:
            raise ValueError("keywords must include at least one non-blank value")
        return cleaned


class AppConfig(BaseModel):
    discord_webhook_url: Union[HttpUrl, str] = ""
    database_path: str = "data/gacha_alert.sqlite3"
    request_timeout_seconds: int = Field(default=20, ge=1, le=120)
    subscriptions: list[Subscription] = Field(min_length=1)

    @property
    def webhook_url_str(self) -> str:
        return str(self.discord_webhook_url).strip()


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return AppConfig.model_validate(data)
