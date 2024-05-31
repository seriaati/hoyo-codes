from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING, Final

import aiohttp
import genshin
from fake_useragent import UserAgent
from loguru import logger
from prisma import Prisma, enums
from prisma.models import RedeemCode

from ..codes.status_verifier import verify_code_status
from .parsers import parse_gamesradar_codes, parse_pockettactics_codes
from .sources import CODE_URLS, CodeSource

if TYPE_CHECKING:
    from collections.abc import Sequence

GPY_GAME_TO_DB_GAME: Final[dict[genshin.Game, enums.Game]] = {
    genshin.Game.GENSHIN: enums.Game.genshin,
    genshin.Game.HONKAI: enums.Game.honkai3rd,
    genshin.Game.STARRAIL: enums.Game.hkrpg,
    genshin.Game.ZZZ: enums.Game.nap,
}


async def fetch_content(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url) as response:
        logger.info(f"Fetching content from {url}")
        return await response.text()


async def save_codes(codes: Sequence[str], game: genshin.Game) -> None:
    cookies = os.getenv("GENSHIN_COOKIES")
    if cookies is None:
        logger.error("GENSHIN_COOKIES environment variable is not set")
        return

    for code in codes:
        status = await verify_code_status(cookies, code, game)

        await RedeemCode.prisma().upsert(
            where={"code_game": {"code": code, "game": GPY_GAME_TO_DB_GAME[game]}},
            data={
                "create": {"code": code, "game": GPY_GAME_TO_DB_GAME[game], "status": status},
                "update": {"status": status},
            },
        )
        logger.info(f"Saved code {code} for {game} with status {status}")
        await asyncio.sleep(10)


async def fetch_codes() -> dict[genshin.Game, list[str]]:
    result: dict[genshin.Game, list[str]] = {}
    ua = UserAgent()
    headers = {"User-Agent": ua.random}

    async with aiohttp.ClientSession(headers=headers) as session:
        for game, game_urls in CODE_URLS.items():
            game_codes: list[str] = []
            for source, url in game_urls.items():
                content = await fetch_content(session, url)
                match source:
                    case CodeSource.GAMESRADAR:
                        game_codes.extend(parse_gamesradar_codes(content))
                    case CodeSource.POCKETTACTICS:
                        game_codes.extend(parse_pockettactics_codes(content))

            game_codes = list(set(game_codes))
            result[game] = game_codes

    return result


async def update_codes() -> None:
    db = Prisma(auto_register=True)
    await db.connect()
    logger.info("Connected to database")

    logger.info("Fetching codes")
    game_codes = await fetch_codes()
    for game, codes in game_codes.items():
        await save_codes(codes, game)

    await db.disconnect()

    logger.info("Done")
