from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional, Union

import yaml
from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

SourceName = Literal[
    "gashapon",
    "ichiban_kuji",
    "takaratomy_arts",
    "qualia",
    "ken_elephant",
    "kitan_club",
    "toys_cabin",
    "rement",
]


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


class CharacterFilter(BaseModel):
    id: str
    label: str
    enabled: bool = False
    keywords: list[str] = Field(min_length=1)
    sources: list[SourceName] = Field(default_factory=lambda: ["gashapon", "ichiban_kuji"])

    @field_validator("id", "label")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value

    @field_validator("keywords")
    @classmethod
    def keywords_must_not_be_blank(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values if value.strip()]
        if not cleaned:
            raise ValueError("keywords must include at least one non-blank value")
        return cleaned

    def to_subscription(self) -> Subscription:
        return Subscription(character=self.label, keywords=self.keywords, sources=self.sources)


class FilterConfig(BaseModel):
    characters: list[CharacterFilter] = Field(default_factory=list)


class AppConfig(BaseModel):
    discord_webhook_url: Union[HttpUrl, str] = ""
    webhook_secret: str = ""
    database_path: str = "data/gacha_alert.sqlite3"
    request_timeout_seconds: int = Field(default=20, ge=1, le=120)
    filters_path: Optional[str] = None
    subscriptions: list[Subscription] = Field(default_factory=list)
    available_characters: list[CharacterFilter] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_at_least_one_subscription(self) -> "AppConfig":
        if not self.subscriptions:
            raise ValueError("at least one enabled filter or inline subscription is required")
        return self

    @property
    def webhook_url_str(self) -> str:
        return str(self.discord_webhook_url).strip()

    @property
    def webhook_secret_str(self) -> str:
        return self.webhook_secret.strip()


def load_filter_config(path: str | Path) -> FilterConfig:
    filter_path = Path(path)
    data = yaml.safe_load(filter_path.read_text(encoding="utf-8")) or {}
    return FilterConfig.model_validate(data)


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    filters_path = data.get("filters_path")
    if filters_path:
        resolved_filters_path = Path(filters_path)
        if not resolved_filters_path.is_absolute():
            resolved_filters_path = config_path.parent / resolved_filters_path
        filter_config = load_filter_config(resolved_filters_path)
        data["available_characters"] = filter_config.characters
        data["subscriptions"] = [
            character.to_subscription().model_dump()
            for character in filter_config.characters
            if character.enabled
        ]
    return AppConfig.model_validate(data)
