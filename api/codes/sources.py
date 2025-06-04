from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Final

from genshin import Game

if TYPE_CHECKING:
    from collections.abc import Mapping


class CodeSource(StrEnum):
    GAMESRADAR = "gamesradar"
    POCKETTACTICS = "pockettactics"
    PRYDWEN = "prydwen"
    GAMERANT = "gamerant"
    TRYHARD_GUIDES = "tryhardguides"
    HSR_FANDOM = "hsr_fandom"
    GI_FANDOM = "gi_fandom"
    ZZZ_FANDOM = "zzz_fandom"


CODE_URLS: Final[Mapping[Game, dict[CodeSource, str]]] = {
    Game.GENSHIN: {
        CodeSource.GAMESRADAR: "https://www.gamesradar.com/genshin-impact-codes-redeem/",
        CodeSource.POCKETTACTICS: "https://www.pockettactics.com/genshin-impact/codes",
        CodeSource.GI_FANDOM: "https://genshin-impact.fandom.com/wiki/Promotional_Code",
    },
    Game.STARRAIL: {
        CodeSource.GAMESRADAR: "https://www.gamesradar.com/honkai-star-rail-codes-redeem/",
        CodeSource.POCKETTACTICS: "https://www.pockettactics.com/honkai-star-rail/codes",
        CodeSource.PRYDWEN: "https://www.prydwen.gg/star-rail/",
        CodeSource.HSR_FANDOM: "https://honkai-star-rail.fandom.com/wiki/Redemption_Code",
    },
    Game.ZZZ: {
        CodeSource.GAMESRADAR: "https://www.gamesradar.com/games/action-rpg/zenless-zone-zero-codes/",
        CodeSource.POCKETTACTICS: "https://www.pockettactics.com/zenless-zone-zero/codes",
        CodeSource.ZZZ_FANDOM: "https://zenless-zone-zero.fandom.com/wiki/Redemption_Code",
    },
}
