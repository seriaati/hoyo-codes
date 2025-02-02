from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from prisma.enums import Game


class CreateCode(BaseModel):
    code: str
    game: "Game"
