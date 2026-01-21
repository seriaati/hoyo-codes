from __future__ import annotations

import io
import os
import tomllib
from typing import TYPE_CHECKING

import aiofiles
import aiohttp
import orjson
from dotenv import load_dotenv

if TYPE_CHECKING:
    from prisma.enums import Game

load_dotenv()
webhook_url = os.getenv("DISCORD_WEBHOOK")


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


async def send_alert(message: str) -> bool:
    if webhook_url is None:
        return False

    async with (
        aiohttp.ClientSession() as session,
        session.post(webhook_url, json={"content": f"[hoyo-codes] {message}"}) as resp,
    ):
        return resp.status == 204
