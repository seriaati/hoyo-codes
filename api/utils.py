from __future__ import annotations

import io
import tomllib
from typing import TYPE_CHECKING

import aiofiles
import orjson

if TYPE_CHECKING:
    from prisma.enums import Game


async def get_cookies(game: Game) -> str | None:
    try:
        async with aiofiles.open("cookies.json", encoding="utf-8") as f:
            data = orjson.loads(await f.read())
    except FileNotFoundError:
        return None

    return data.get(game.value)


async def set_cookies(game: Game, cookies: str) -> None:
    async with aiofiles.open("cookies.json", "w", encoding="utf-8") as f:
        try:
            data = orjson.loads(await f.read())
        except io.UnsupportedOperation:
            data = {}
        data[game.value] = cookies
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
