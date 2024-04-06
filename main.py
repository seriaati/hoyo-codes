from __future__ import annotations

import asyncio
import json
import logging

import aiohttp
from bs4 import BeautifulSoup
from fastapi import FastAPI, Response

app = FastAPI()
LOGGER_ = logging.getLogger(__name__)


async def get_code_from_gamesrader(
    session: aiohttp.ClientSession, codes: set[str]
) -> None:
    try:
        async with session.get(
            "https://www.gamesradar.com/genshin-impact-codes-redeem/"
        ) as response:
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


async def get_code_from_programguide(
    session: aiohttp.ClientSession, codes: set[str]
) -> None:
    try:
        async with session.get(
            "https://progameguides.com/genshin-impact/genshin-impact-codes/"
        ) as response:
            html = await response.text()

        soup = BeautifulSoup(html, "lxml")
        lis = soup.select("div.entry-content li:not(:has(a)):has(strong)")

        for li in lis:
            if li.strong is None or not li.strong.text.strip().isupper():
                continue
            codes.add(li.strong.text.strip())
    except Exception:
        LOGGER_.exception("Error in get_code_from_progameguides")


async def get_code_from_gipn(session: aiohttp.ClientSession, codes: set[str]) -> None:
    async with session.get(
        "https://raw.githubusercontent.com/ataraxyaffliction/gipn-json/main/gipn-update.json"
    ) as response:
        content = await response.text()
        data = json.loads(content)

    codes_ = data.get("set[str]", {})
    for code in codes_:
        if code.get("is_expired", False):
            continue
        codes.add(code["code"])


async def get_code_from_pockettactics(
    session: aiohttp.ClientSession, codes: set[str]
) -> None:
    try:
        async with session.get(
            "https://www.pockettactics.com/genshin-impact/codes"
        ) as response:
            html = await response.text()

        soup = BeautifulSoup(html, "lxml")
        entries = soup.select(
            "div.entry-content > ul > li:not(:has(a)) > strong:not(:has(a))"
        )

        for entry in entries:
            code = entry.get_text().strip()
            if code and code == code.upper():
                codes.add(code)
    except Exception:
        LOGGER_.exception("Error in get_code_from_pockettactics")


@app.get("/")
async def root() -> Response:
    return Response(content="Hoyo Codes API v1.0.0")


@app.get("/codes")
async def get_codes() -> Response:
    codes: set[str] = set()

    async with aiohttp.ClientSession() as session:
        tasks = [
            get_code_from_pockettactics(session, codes),
            get_code_from_programguide(session, codes),
            get_code_from_gamesrader(session, codes),
        ]
        await asyncio.gather(*tasks)
    return Response(content=json.dumps(list(codes)))
