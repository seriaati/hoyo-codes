from __future__ import annotations

import io
import tomllib
from typing import TYPE_CHECKING

import aiofiles
import aiohttp
import genshin
import orjson

from api.config import settings

if TYPE_CHECKING:
    from prisma.enums import Game


async def get_cookies(game: Game) -> str | None:
    try:
        async with aiofiles.open("cookies.json", encoding="utf-8") as f:
            data = orjson.loads(await f.read())
    except FileNotFoundError:
        return None

    return data.get(str(game))


async def set_cookies(game: Game, cookies: str) -> None:
    async with aiofiles.open("cookies.json", "w", encoding="utf-8") as f:
        try:
            data = orjson.loads(await f.read())
        except io.UnsupportedOperation:
            data = {}
        data[str(game)] = cookies
        await f.write(orjson.dumps(data).decode("utf-8"))


async def get_game_uids() -> dict[str, int]:
    try:
        async with aiofiles.open("uids.json", encoding="utf-8") as f:
            data = orjson.loads(await f.read())
    except FileNotFoundError:
        return {}

    return data


async def get_project_version() -> str:
    try:
        async with aiofiles.open("pyproject.toml", "rb") as f:
            data = tomllib.loads((await f.read()).decode("utf-8"))
    except FileNotFoundError:
        return "unknown"

    try:
        return data["project"]["version"]
    except KeyError:
        return "unknown"


async def send_discord_webhook(message: str, *, url: str) -> bool:
    async with (
        aiohttp.ClientSession() as session,
        session.post(url, json={"content": message}) as resp,
    ):
        return resp.status == 204


async def send_alert(message: str) -> bool:
    if settings.alert_webhook is None:
        return False

    return await send_discord_webhook(message, url=settings.alert_webhook)


async def send_new_codes(codes: list[str], *, game: genshin.Game) -> bool:
    if not codes:
        return False

    webhook_url = None
    redeem_url = None

    if game is genshin.Game.GENSHIN:
        webhook_url = settings.gi_new_code_webhook
        redeem_url = "https://genshin.hoyoverse.com/en/gift?code={code}"
    elif game is genshin.Game.STARRAIL:
        webhook_url = settings.hsr_new_code_webhook
        redeem_url = "https://hsr.hoyoverse.com/gift?code={code}"
    elif game is genshin.Game.ZZZ:
        webhook_url = settings.zzz_new_code_webhook
        redeem_url = "https://zenless.hoyoverse.com/redemption?code={code}"

    if webhook_url is None or redeem_url is None:
        return False

    message = "\n".join(f"* [{code}]({redeem_url.format(code=code)})" for code in codes)
    return await send_discord_webhook(message, url=webhook_url)
