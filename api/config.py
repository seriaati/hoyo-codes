from __future__ import annotations

from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    proxy_url: str | None = None
    host: str = "127.0.0.1"
    port: int = 1078
    api_token: str | None = None
    discord_webhook_url: str | None = None


load_dotenv()
settings = Settings()
