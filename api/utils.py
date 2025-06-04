from __future__ import annotations

from typing import TYPE_CHECKING

import aiofiles
import orjson

if TYPE_CHECKING:
    from prisma.enums import Game


async def get_cookies(game: Game) -> str:
    async with aiofiles.open("cookies.json", encoding="utf-8") as f:
        data = orjson.loads(await f.read())

    return data[game.value]


async def set_cookies(game: Game, cookies: str) -> None:
    async with aiofiles.open("cookies.json", "w", encoding="utf-8") as f:
        data = orjson.loads(await f.read())
        data[game.value] = cookies
        await f.write(orjson.dumps(data).decode("utf-8"))
