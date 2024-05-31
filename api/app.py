from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import fake_useragent
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from prisma import Prisma
from prisma.enums import Game
from prisma.models import RedeemCode

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Context manager to contol the lifespan of the FastAPI app."""
    db = Prisma(auto_register=True)
    await db.connect()
    yield
    await db.disconnect()


app = FastAPI(lifespan=lifespan)
ua = fake_useragent.UserAgent()


@app.get("/")
async def root() -> Response:
    return JSONResponse(content={"message": "Hoyo Codes API v1.2.4"})


@app.get("/codes")
async def get_codes(game: Game) -> Response:
    codes = await RedeemCode.prisma().find_many(where={"game": game})
    return JSONResponse(content={"codes": codes, "game": game.value})