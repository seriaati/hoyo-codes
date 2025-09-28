from __future__ import annotations

from prisma.enums import Game
from pydantic import BaseModel, field_validator


class CreateCode(BaseModel):
    code: str
    game: Game

    @field_validator("code")
    @classmethod
    def __upper_code(cls, v: str) -> str:
        return v.upper()
