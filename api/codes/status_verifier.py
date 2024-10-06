from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Final

import genshin
from loguru import logger
from prisma.enums import CodeStatus

if TYPE_CHECKING:
    from collections.abc import Mapping

GAME_UIDS: Final[Mapping[genshin.Game, int]] = {
    genshin.Game.GENSHIN: 901211014,
    genshin.Game.STARRAIL: 809162009,
    genshin.Game.ZZZ: 1300025292,
}


async def verify_code_status(cookies: str, code: str, game: genshin.Game) -> CodeStatus:
    if game not in GAME_UIDS:
        # Assume code is valid for games not in GAME_UIDS
        logger.info(f"Game {game} does not have a UID, assuming code is valid.")
        return CodeStatus.OK

    client = genshin.Client(cookies)
    try:
        await client.redeem_code(code, game=game, uid=GAME_UIDS[game])
    except genshin.RedemptionClaimed:
        return CodeStatus.OK
    except genshin.RedemptionCooldown:
        await asyncio.sleep(60)
        return await verify_code_status(cookies, code, game)
    except genshin.RedemptionException:
        return CodeStatus.NOT_OK
    except genshin.InvalidCookies as e:
        new_cookies = await genshin.fetch_cookie_with_stoken_v2(cookies, token_types=[2, 4])
        dict_cookies = dict(pair.split("=", 1) for pair in cookies.split("; "))
        dict_cookies.update(new_cookies)

        string_cookies = "; ".join(f"{key}={value}" for key, value in dict_cookies.items())
        logger.warning(f"Updated cookie to {string_cookies}")

        msg = "Updated cookie"
        raise RuntimeError(msg) from e
    except genshin.GenshinException as e:
        if e.retcode == -2024:  # Code cannot be redeemed on web
            return CodeStatus.NOT_OK
        raise
    else:
        return CodeStatus.OK
