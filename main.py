# pyright: reportAttributeAccessIssue=false, reportOptionalMemberAccess=false

from __future__ import annotations

import asyncio
import logging
import sys
from enum import Enum

import aiohttp
import fake_useragent
from bs4 import BeautifulSoup
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse

app = FastAPI()
ua = fake_useragent.UserAgent()

LOGGER_ = logging.getLogger("main")
LOGGER_.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
stream_handler.setFormatter(log_formatter)
LOGGER_.addHandler(stream_handler)


class Game(Enum):
    GENSHIN = "genshin"
    STARRAIL = "hkrpg"
    HONKAI = "honkai3rd"


class Source(Enum):
    GAMESRADAR = "gamesradar"
    POCKETTACTICS = "pockettactics"


CODE_URLS: dict[Game, dict[Source, str]] = {
    Game.GENSHIN: {
        Source.GAMESRADAR: "https://www.gamesradar.com/genshin-impact-codes-redeem/",
        # Source.POCKETTACTICS: "https://www.pockettactics.com/genshin-impact/codes",
    },
    Game.STARRAIL: {
        Source.GAMESRADAR: "https://www.gamesradar.com/honkai-star-rail-codes-redeem/",
        # Source.POCKETTACTICS: "https://www.pockettactics.com/honkai-star-rail/codes",
    },
    Game.HONKAI: {
        Source.POCKETTACTICS: "https://www.pockettactics.com/honkai-impact/codes",
    },
}


async def parse_gamesradar_codes(session: aiohttp.ClientSession, codes: set[str], url: str) -> None:
    try:
        async with session.get(url) as response:
            content = await response.text()

        soup = BeautifulSoup(content, "lxml")
        # find div with id article-body
        div = soup.find("div", id="article-body")
        h2s = div.find_all("h2")
        uls = div.find_all("ul")
        lis = []

        for i, h2 in enumerate(h2s):
            if "livestream" in h2.text.strip().lower() or h2.text.strip() in {
                "Genshin Impact active codes",
                "Honkai Star Rail codes",
            }:
                ul = uls[i]
                lis.extend(ul.find_all("li"))

        for li in lis:
            if li.strong is None or not li.strong.text.strip().isupper():
                continue
            codes.add(li.strong.text.strip().split(" / ")[0].strip())
    except Exception:
        LOGGER_.exception("[GamesRadar] Error parsing codes")


async def parse_pockettactics_codes(
    session: aiohttp.ClientSession, codes: set[str], url: str
) -> None:
    try:
        async with session.get(url, headers={"User-Agent": ua.random}) as response:
            html = await response.text()

        soup = BeautifulSoup(html, "lxml")
        # find div with class entry-content
        div = soup.find("div", class_="entry-content")
        ul = div.find("ul")
        lis = ul.find_all("li")
        for li in lis:
            if li.strong is None or not li.strong.text.strip().isupper():
                continue
            codes.add(li.strong.text.strip())
    except Exception:
        LOGGER_.exception("[Pocket Tactics] Error parsing codes")


@app.get("/")
async def root() -> Response:
    return JSONResponse(content={"message": "Hoyo Codes API v1.2.4"})


@app.get("/codes")
async def get_codes(game: Game) -> Response:
    codes: set[str] = set()
    tasks = []

    async with aiohttp.ClientSession() as session:
        for source in Source:
            url = CODE_URLS[game].get(source)
            if url is None:
                continue

            if source is Source.GAMESRADAR:
                tasks.append(parse_gamesradar_codes(session, codes, url))
            elif source is Source.POCKETTACTICS:
                tasks.append(parse_pockettactics_codes(session, codes, url))
        await asyncio.gather(*tasks)
    return JSONResponse(content={"codes": list(codes)})
