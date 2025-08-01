from __future__ import annotations

import asyncio
from typing import Final

import aiohttp
import genshin
import orjson
from fake_useragent import UserAgent
from loguru import logger
from prisma import Prisma, enums
from prisma.models import RedeemCode

from ..codes.status_verifier import verify_code_status
from ..utils import get_cookies
from . import parsers
from .sources import CODE_URLS, CodeSource

GPY_GAME_TO_DB_GAME: Final[dict[genshin.Game, enums.Game]] = {
    genshin.Game.GENSHIN: enums.Game.genshin,
    genshin.Game.HONKAI: enums.Game.honkai3rd,
    genshin.Game.STARRAIL: enums.Game.hkrpg,
    genshin.Game.ZZZ: enums.Game.nap,
    genshin.Game.TOT: enums.Game.tot,
}
DB_GAME_TO_GPY_GAME: Final[dict[enums.Game, genshin.Game]] = {
    v: k for k, v in GPY_GAME_TO_DB_GAME.items()
}

ua = UserAgent()


async def fetch_content(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url, headers={"x-rpc-client_type": "4"}) as response:
        logger.info(f"Fetching content from {url}")
        response.raise_for_status()
        return await response.text()


async def save_codes(codes: list[tuple[str, str]], game: genshin.Game) -> None:
    cookies = await get_cookies(enums.Game.genshin)

    for code_tuple in codes:
        code, rewards = code_tuple

        existing_row = await RedeemCode.prisma().find_first(
            where={"code": code, "game": GPY_GAME_TO_DB_GAME[game]}
        )
        if existing_row is not None:
            if not existing_row.rewards:
                await RedeemCode.prisma().update(
                    where={"id": existing_row.id}, data={"rewards": rewards}
                )
                logger.info(f"Updated rewards for code {code_tuple} for {game}")
            continue

        status, redeemed = await verify_code_status(cookies, code, game)

        await RedeemCode.prisma().create(
            data={
                "code": code,
                "game": GPY_GAME_TO_DB_GAME[game],
                "status": status,
                "rewards": rewards,
            }
        )
        logger.info(f"Saved code {code_tuple} for {game} with status {status}")
        if redeemed:
            await asyncio.sleep(10)


async def fetch_codes_task(  # noqa: PLR0912
    session: aiohttp.ClientSession, url: str, source: CodeSource, game: genshin.Game
) -> list[tuple[str, str]] | None:
    try:
        content = await fetch_content(session, url)
    except Exception:
        logger.exception(f"Failed to fetch content from {url}")
        return None

    try:
        codes = None
        match source:
            case CodeSource.GAMESRADAR:
                codes = parsers.parse_gamesradar(content)
            case CodeSource.POCKETTACTICS:
                codes = parsers.parse_pockettactics(content)
            case CodeSource.PRYDWEN:
                codes = parsers.parse_prydwen(content)
            case CodeSource.GAMERANT:
                codes = parsers.parse_gamerant(content)
            case CodeSource.TRYHARD_GUIDES:
                codes = parsers.parse_tryhard_guides(content)
            case CodeSource.HSR_FANDOM:
                codes = parsers.parse_hsr_fandom(content)
            case CodeSource.GI_FANDOM:
                codes = parsers.parse_gi_fandom(content)
            case CodeSource.ZZZ_FANDOM:
                codes = parsers.parse_zzz_fandom(content)
            case CodeSource.HOYOLAB:
                codes = parsers.parse_hoyolab(orjson.loads(content))
            case _:
                logger.error(f"Unknown code source {source!r}")

        if codes is not None:
            return [(parsers.sanitize_code(code), rewards) for code, rewards in codes]
    except Exception:
        logger.exception(f"Failed to parse codes from {source!r} for {game!r}")
        return None


async def fetch_codes() -> dict[genshin.Game, list[tuple[str, str]]]:
    result: dict[genshin.Game, list[tuple[str, str]]] = {}
    headers = {"User-Agent": ua.random}

    async with aiohttp.ClientSession(headers=headers) as session:
        for game, code_sources in CODE_URLS.items():
            game_codes: list[tuple[str, str]] = []

            for source, url in code_sources.items():
                codes = await fetch_codes_task(session, url, source, game)
                if codes is None:
                    continue
                game_codes.extend(codes)

            game_codes = list(set(game_codes))
            result[game] = game_codes

    return result


async def update_codes() -> None:
    logger.info("Update codes task started")

    db = Prisma(auto_register=True)
    await db.connect()
    logger.info("Connected to database")

    logger.info("Fetching codes")
    game_codes = await fetch_codes()
    for game, codes in game_codes.items():
        await save_codes(codes, game)

    await db.disconnect()

    logger.info("Done")


async def check_codes() -> None:
    logger.info("Check codes task started")

    db = Prisma(auto_register=True)
    await db.connect()
    logger.info("Connected to database")

    cookies = await get_cookies(enums.Game.genshin)
    codes = await RedeemCode.prisma().find_many(where={"status": enums.CodeStatus.OK})

    try:
        for code in codes:
            logger.info(f"Checking status of code {code.code!r}, game {code.game!r}")

            status, redeemed = await verify_code_status(
                cookies, code.code, DB_GAME_TO_GPY_GAME[code.game]
            )
            if status != code.status:
                await RedeemCode.prisma().update(where={"id": code.id}, data={"status": status})
                logger.info(f"Updated status of code {code.code} to {status}")

            if redeemed:
                await asyncio.sleep(10)
    finally:
        await db.disconnect()
        logger.info("Done")
