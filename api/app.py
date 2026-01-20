from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING

import genshin
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Response, Security
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from prisma import Prisma
from prisma.enums import CodeStatus, Game
from prisma.models import RedeemCode

from .codes.status_verifier import verify_code_status
from .codes.task import check_codes as run_check_codes
from .codes.task import update_codes as run_update_codes
from .logging import setup_logging
from .models import CreateCode  # noqa: TC001
from .utils import get_cookies, get_project_version

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from fastapi.security import HTTPAuthorizationCredentials


load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Context manager to contol the lifespan of the FastAPI app."""
    db = Prisma(auto_register=True)
    await db.connect()

    # Schedule tasks
    scheduler.add_job(run_update_codes, "interval", hours=1, id="update_codes")
    scheduler.add_job(
        run_check_codes, "cron", hour=1, minute=30, timezone="Asia/Taipei", id="check_codes"
    )
    scheduler.start()

    yield

    scheduler.shutdown()
    await db.disconnect()


setup_logging()
app = FastAPI(
    lifespan=lifespan,
    servers=[
        {"url": "https://hoyo-codes.seria.moe", "description": "Production server"},
        {"url": "http://127.0.0.1:1078", "description": "Local development server"},
    ],
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
    html_path = Path(__file__).parent.parent / "index.html"
    return FileResponse(html_path)


@app.get("/health")
async def health_check() -> Response:
    return JSONResponse(content={"status": "ok"})


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


@app.get("/version")
async def get_version() -> Response:
    version = await get_project_version()
    return JSONResponse(content={"version": version})


@app.post("/codes", dependencies=[Security(validate_token)])
async def create_code(code: CreateCode) -> Response:
    existing = await RedeemCode.prisma().find_first(where={"code": code.code, "game": code.game})
    if existing is not None:
        raise HTTPException(status_code=400, detail="Code already exists")

    cookies = await get_cookies(code.game)
    if cookies is None:
        raise HTTPException(status_code=400, detail=f"No cookies set for {code.game.value!r}")

    status, _ = await verify_code_status(cookies, code.code, genshin.Game(code.game.value))
    await RedeemCode.prisma().create(
        {"code": code.code, "game": code.game, "rewards": "", "status": status}
    )
    return Response(status_code=201)


@app.delete("/codes/{code_id}", dependencies=[Security(validate_token)])
async def delete_code(code_id: int) -> Response:
    code = await RedeemCode.prisma().find_unique(where={"id": code_id})
    if not code:
        raise HTTPException(status_code=404, detail="Code not found")
    await RedeemCode.prisma().delete(where={"id": code_id})
    return Response(status_code=204)


@app.post("/update-codes", dependencies=[Security(validate_token)])
async def update_codes_endpoint(background_tasks: BackgroundTasks) -> Response:
    background_tasks.add_task(run_update_codes)
    return Response(status_code=202)


@app.post("/check-codes", dependencies=[Security(validate_token)])
async def check_codes_endpoint(background_tasks: BackgroundTasks) -> Response:
    background_tasks.add_task(run_check_codes)
    return Response(status_code=202)
