from __future__ import annotations

import contextlib
import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import prisma
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response, Security
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from prisma import Prisma
from prisma.enums import CodeStatus, Game
from prisma.models import RedeemCode

from .models import CreateCode  # noqa: TC001

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from fastapi.security import HTTPAuthorizationCredentials


load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Context manager to contol the lifespan of the FastAPI app."""
    db = Prisma(auto_register=True)
    await db.connect()
    yield
    await db.disconnect()


app = FastAPI(lifespan=lifespan)
security = HTTPBearer(auto_error=True)


async def validate_token(  # noqa: RUF029
    credentials: HTTPAuthorizationCredentials = Security(security),  # noqa: B008
) -> str:
    """Validate bearer token"""
    if credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API token")
    return credentials.credentials


@app.get("/")
async def root() -> Response:  # noqa: RUF029
    return JSONResponse(content={"message": "Hoyo Codes API v2.2.1"})


@app.get("/codes")
async def get_codes(game: Game) -> Response:
    codes = await RedeemCode.prisma().find_many(where={"game": game, "status": CodeStatus.OK})
    return JSONResponse(
        content={"codes": [code.model_dump() for code in codes], "game": game.value}
    )


@app.get("/games")
async def get_games() -> Response:
    return JSONResponse(content={"games": [game.value for game in Game]})


@app.post("/codes", dependencies=[Security(validate_token)])
async def create_code(code: CreateCode) -> Response:
    try:
        await RedeemCode.prisma().create(
            {"code": code.code, "game": code.game, "rewards": "", "status": CodeStatus.OK}
        )
    except prisma.errors.UniqueViolationError as e:
        raise HTTPException(status_code=400, detail="Code already exists") from e
    return Response(status_code=201)
