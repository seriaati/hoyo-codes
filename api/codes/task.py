import asyncio
from collections.abc import Sequence

import aiohttp
from genshin import Game
from prisma import Prisma
from prisma.models import RedeemCode

from .parsers import parse_gamesradar_codes, parse_pockettactics_codes
from .sources import CODE_URLS, CodeSource


async def fetch_content(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url) as response:
        return await response.text()


async def save_codes(codes: Sequence[str], game: Game) -> None: ...


async def fetch_codes() -> None:
    async with aiohttp.ClientSession() as session:
        for game, game_urls in CODE_URLS.items():
            game_codes: list[str] = []
            for source, url in game_urls.items():
                content = await fetch_content(session, url)
                match source:
                    case CodeSource.GAMESRADAR:
                        game_codes.extend(parse_gamesradar_codes(content))
                    case CodeSource.POCKETTACTICS:
                        game_codes.extend(parse_pockettactics_codes(content))
            await save_codes(game_codes, game)


async def main() -> None:
    db = Prisma(auto_register=True)
    await db.connect()

    await fetch_codes()

    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
