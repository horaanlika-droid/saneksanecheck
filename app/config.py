"""Конфигурация приложения. Всё настраивается через переменные окружения.

Для запуска на хостинге достаточно задать только:
    BOT_TOKEN — токен Telegram-бота
    ADMIN_IDS — telegram user id администраторов через запятую
    WEBAPP_URL — публичный https-адрес веб-приложения (для кнопки меню бота)

Остальное имеет разумные значения по умолчанию.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    BOT_TOKEN: str = ""
    ADMIN_IDS: str = ""
    WEBAPP_URL: str = ""

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DATA_DIR: str = "./data"
    LOG_LEVEL: str = "INFO"

    @property
    def admin_ids(self) -> list[int]:
        ids: list[int] = []
        for part in self.ADMIN_IDS.replace(";", ",").split(","):
            part = part.strip()
            if part.isdigit():
                ids.append(int(part))
        return ids

    @property
    def data_dir(self) -> Path:
        return Path(self.DATA_DIR)

    @property
    def upload_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "app.db"

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
