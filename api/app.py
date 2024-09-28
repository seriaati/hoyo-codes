from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from prisma import Prisma
from prisma.enums import CodeStatus, Game
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


@app.get("/")
async def root() -> Response:  # noqa: RUF029
    return JSONResponse(content={"message": "Hoyo Codes API v2.2.0"})


@app.get("/codes")
async def get_codes(game: Game) -> Response:
    codes = await RedeemCode.prisma().find_many(where={"game": game, "status": CodeStatus.OK})
    return JSONResponse(
        content={"codes": [code.model_dump() for code in codes], "game": game.value}
    )
