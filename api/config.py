from __future__ import annotations

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    proxy_url: str | None = None
    host: str = "127.0.0.1"
    port: int = 1078
    api_token: str | None = None

    alert_webhook: str | None = Field(alias="DISCORD_WEBHOOK_URL", default=None)

    gi_new_code_webhook: str | None = None
    hsr_new_code_webhook: str | None = None
    zzz_new_code_webhook: str | None = None


load_dotenv()
settings = Settings()
