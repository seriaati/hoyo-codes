from __future__ import annotations

import asyncio

import genshin
from loguru import logger
from prisma.enums import CodeStatus, Game
from prisma.models import RedeemCode

from api.utils import get_game_uids, set_cookies


async def same_family_code_exists(code: str, game: Game) -> bool:
    prefix = code[:5]
    existing_codes = await RedeemCode.prisma().find_many(
        where={"game": game, "code": {"startswith": prefix}}
    )
    return len(existing_codes) > 0


async def verify_code_status(  # noqa: PLR0911
    cookies: str, code: str, game: genshin.Game
) -> tuple[CodeStatus, bool]:
    game_uids = await get_game_uids()
    if game not in game_uids:
        # Assume code is valid for games not in GAME_UIDS
        logger.info(f"Game {game} does not have a UID, assuming code is valid.")
        return CodeStatus.OK, False

    if game is genshin.Game.ZZZ and code.startswith("ZZZ"):
        same_family_exists = await same_family_code_exists(code, Game.nap)
        if same_family_exists:
            logger.info(
                f"Code {code} belongs to the same family as an existing code, marking as NOT_OK."
            )
            return CodeStatus.NOT_OK, False

    client = genshin.Client(cookies)
    try:
        await client.redeem_code(code, game=game, uid=game_uids[game])
    except genshin.RedemptionClaimed:
        return CodeStatus.OK, True
    except genshin.RedemptionCooldown:
        await asyncio.sleep(60)
        return await verify_code_status(cookies, code, game)
    except genshin.RedemptionException:
        return CodeStatus.NOT_OK, True
    except genshin.InvalidCookies:
        new_cookies = await genshin.fetch_cookie_with_stoken_v2(cookies, token_types=[2, 4])
        dict_cookies = genshin.parse_cookie(cookies)
        dict_cookies.update(new_cookies)

        str_cookies = "; ".join(f"{key}={value}" for key, value in dict_cookies.items())
        await set_cookies(Game.genshin, str_cookies)
        logger.info("Updated cookies")

        return await verify_code_status(str_cookies, code, game)
    except genshin.GenshinException as e:
        if e.retcode == -2024:  # Code cannot be redeemed on web
            return CodeStatus.NOT_OK, True
        raise
    else:
        return CodeStatus.OK, True
