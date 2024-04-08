from __future__ import annotations

import asyncio
import json
import logging
from enum import Enum

import aiohttp
from bs4 import BeautifulSoup, Tag
from fastapi import FastAPI, Response

app = FastAPI()
LOGGER_ = logging.getLogger(__name__)


class Game(Enum):
    GENSHIN = "genshin"
    STARRAIL = "starrail"


class Source(Enum):
    GAMESRADAR = "gamesradar"
    PROGAMEGUIDES = "progameguides"
    POCKETTACTICS = "pockettactics"


CODE_URLS: dict[Game, dict[Source, str]] = {
    Game.GENSHIN: {
        Source.GAMESRADAR: "https://www.gamesradar.com/genshin-impact-codes-redeem/",
        Source.PROGAMEGUIDES: "https://progameguides.com/genshin-impact/genshin-impact-codes/",
        Source.POCKETTACTICS: "https://www.pockettactics.com/genshin-impact/codes",
    },
    Game.STARRAIL: {
        Source.GAMESRADAR: "https://www.gamesradar.com/honkai-star-rail-codes-redeem/",
        Source.PROGAMEGUIDES: "https://progameguides.com/honkai-star-rail/honkai-star-rail-codes/",
        Source.POCKETTACTICS: "https://www.pockettactics.com/honkai-star-rail/codes",
    },
}


async def parse_gamesradar_codes(session: aiohttp.ClientSession, codes: set[str], url: str) -> None:
    try:
        async with session.get(url) as response:
            content = await response.text()

        soup = BeautifulSoup(content, "lxml")
        lis = soup.select(
            ".article .text-copy b, .article .text-copy strong, .news-article .text-copy b, .news-article .text-copy strong, .review-article .text-copy b, .review-article .text-copy strong, .static-article .text-copy b, .static-article .text-copy strong"
        )
        for li in lis:
            if not li.text.strip().isupper():
                continue
            codes.add(li.text.strip())
    except Exception:
        LOGGER_.exception("Error in get_code_from_gamesrader")


async def parse_progameguides_codes(
    session: aiohttp.ClientSession, codes: set[str], url: str
) -> None:
    try:
        async with session.get(url) as response:
            html = await response.text()

        soup = BeautifulSoup(html, "lxml")
        # find div with class wp-block-gamurs-article-content
        div = soup.find("div", class_="wp-block-gamurs-article-content")
        if div is None:
            return
        # find ul inside div
        ul = div.find("ul")
        if not isinstance(ul, Tag):
            return
        # find lis inside ul
        lis = ul.find_all("li")
        for li in lis:
            if li.strong is None or not li.strong.text.strip().isupper():
                continue
            codes.add(li.strong.text.strip())
    except Exception:
        LOGGER_.exception("Error in get_code_from_progameguides")


async def parse_pockettactics_codes(
    session: aiohttp.ClientSession, codes: set[str], url: str
) -> None:
    try:
        async with session.get(url) as response:
            html = await response.text()

        soup = BeautifulSoup(html, "lxml")
        entries = soup.select("div.entry-content > ul > li:not(:has(a)) > strong:not(:has(a))")

        for entry in entries:
            code = entry.get_text().strip()
            if code and code == code.upper():
                codes.add(code)
    except Exception:
        LOGGER_.exception("Error in get_code_from_pockettactics")


@app.get("/")
async def root() -> Response:
    return Response(content="Hoyo Codes API v1.1.0")


@app.get("/codes")
async def get_codes(game: Game) -> Response:
    codes: set[str] = set()
    tasks = []

    async with aiohttp.ClientSession() as session:
        for source in Source:
            url = CODE_URLS[game][source]
            if source == Source.GAMESRADAR:
                tasks.append(parse_gamesradar_codes(session, codes, url))
            elif source == Source.PROGAMEGUIDES:
                tasks.append(parse_progameguides_codes(session, codes, url))
            elif source == Source.POCKETTACTICS:
                tasks.append(parse_pockettactics_codes(session, codes, url))
        await asyncio.gather(*tasks)
    return Response(content=json.dumps(list(codes)))
