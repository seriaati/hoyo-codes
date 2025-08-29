from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import genshin
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response, Security
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from prisma import Prisma
from prisma.enums import CodeStatus, Game
from prisma.models import RedeemCode

from .codes.status_verifier import verify_code_status
from .models import CreateCode  # noqa: TC001
from .utils import get_cookies, get_project_version

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


app = FastAPI(
    lifespan=lifespan,
    servers=[{"url": "https://hoyo-codes.seria.moe", "description": "Production server"}],
)
security = HTTPBearer(auto_error=True)


async def validate_token(  # noqa: RUF029
    credentials: HTTPAuthorizationCredentials = Security(security),  # noqa: B008
) -> str:
    """Validate bearer token"""
    if credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API token")
    return credentials.credentials


@app.get("/")
async def root() -> Response:
    version = await get_project_version()
    return JSONResponse(content={"message": f"Hoyo Codes API v{version}"})


@app.get("/favicon.ico")
def get_favicon() -> Response:
    return Response(status_code=204)


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
    existing = await RedeemCode.prisma().find_first(where={"code": code.code, "game": code.game})
    if existing is not None:
        raise HTTPException(status_code=400, detail="Code already exists")

    cookies = await get_cookies(Game.genshin)
    status, _ = await verify_code_status(cookies, code.code, genshin.Game(code.game.value))
    await RedeemCode.prisma().create(
        {"code": code.code.upper(), "game": code.game, "rewards": "", "status": status}
    )
    return Response(status_code=201)


@app.delete("/codes/{code_id}", dependencies=[Security(validate_token)])
async def delete_code(code_id: int) -> Response:
    code = await RedeemCode.prisma().find_unique(where={"id": code_id})
    if not code:
        raise HTTPException(status_code=404, detail="Code not found")
    await RedeemCode.prisma().delete(where={"id": code_id})
    return Response(status_code=204)
