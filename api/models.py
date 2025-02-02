from prisma.enums import Game  # noqa: TC002
from pydantic import BaseModel


class CreateCode(BaseModel):
    code: str
    game: Game
