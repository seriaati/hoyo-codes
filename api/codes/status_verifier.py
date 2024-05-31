from __future__ import annotations

import os
from typing import TYPE_CHECKING, Final

import genshin
from prisma.enums import CodeStatus

if TYPE_CHECKING:
    from collections.abc import Mapping

GAME_UIDS: Final[Mapping[genshin.Game, int]] = {
    genshin.Game.GENSHIN: 901211014,
    genshin.Game.STARRAIL: 809162009,
}


async def verify_code_status(code: str, game: genshin.Game) -> CodeStatus:
    cookie = os.getenv("GENSHIN_COOKIE")
    if cookie is None:
        msg = "GENSHIN_COOKIE environment variable is not set."
        raise RuntimeError(msg)

    if game not in GAME_UIDS:
        # Assume code is valid for games not in GAME_UIDS
        return CodeStatus.OK

    client = genshin.Client(cookie)
    try:
        await client.redeem_code(code, game=game, uid=GAME_UIDS[game])
    except genshin.RedemptionClaimed:
        return CodeStatus.OK
    except genshin.RedemptionException:
        return CodeStatus.NOT_OK
    else:
        return CodeStatus.OK
