from __future__ import annotations

from prisma.enums import Game
from pydantic import BaseModel


class CreateCode(BaseModel):
    code: str
    game: Game
