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


CODE_URLS: Final[Mapping[Game, dict[CodeSource, str]]] = {
    Game.GENSHIN: {
        CodeSource.GAMESRADAR: "https://www.gamesradar.com/genshin-impact-codes-redeem/",
        CodeSource.POCKETTACTICS: "https://www.pockettactics.com/genshin-impact/codes",
    },
    Game.STARRAIL: {
        CodeSource.GAMESRADAR: "https://www.gamesradar.com/honkai-star-rail-codes-redeem/",
        CodeSource.POCKETTACTICS: "https://www.pockettactics.com/honkai-star-rail/codes",
        CodeSource.PRYDWEN: "https://www.prydwen.gg/star-rail/",
    },
    Game.ZZZ: {
        CodeSource.GAMESRADAR: "https://www.gamesradar.com/games/action-rpg/zenless-zone-zero-codes/",
        CodeSource.POCKETTACTICS: "https://www.pockettactics.com/zenless-zone-zero/codes",
    },
}
