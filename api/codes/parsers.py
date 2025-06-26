# pyright: reportOptionalMemberAccess=false, reportAttributeAccessIssue=false
# pyright: reportOperatorIssue=false, reportArgumentType=false
# pyright: reportCallIssue=false
from __future__ import annotations

import re
from typing import Any

import genshin
from bs4 import BeautifulSoup


def sanitize_code(code: str) -> str:
    if "/" in code:
        code = code.split("/", maxsplit=1)[0]
    return re.sub(r"\[\d+\]", "", code.strip().replace("Quick Redeem", "")).upper().strip()


def parse_gamesradar(content: str) -> list[tuple[str, str]]:
    codes: list[tuple[str, str]] = []

    soup = BeautifulSoup(content, "lxml")
    # find div with id article-body
    div = soup.find("div", id="article-body")
    h2s = div.find_all("h2")
    uls = div.find_all("ul")
    lis = []

    for i, h2 in enumerate(h2s):
        if "livestream" in h2.text.strip().lower() or h2.text.strip() in {
            "Genshin Impact active codes",
            "Honkai Star Rail codes",
        }:
            ul = uls[i]
            lis.extend(ul.find_all("li"))

    for li in lis:
        if li.strong is None or not li.strong.text.strip().isupper():
            continue
        code = li.strong.text.strip().split("/")[0].strip()
        rewards = li.text.strip().split("–")[1].strip()  # noqa: RUF001
        codes.append((code, rewards))

    return codes


def parse_pockettactics(content: str) -> list[tuple[str, str]]:
    codes: list[tuple[str, str]] = []

    soup = BeautifulSoup(content, "lxml")
    # find div with class entry-content
    div = soup.find("div", class_="entry-content")
    ul = div.find("ul")
    lis = ul.find_all("li")
    for li in lis:
        if li.strong is None or not li.strong.text.strip().isupper():
            continue

        code = li.strong.text.strip()
        rewards = li.text.strip().split("-")[1].strip().replace(" (new!)", "")
        codes.append((code, rewards))

    return codes


def parse_prydwen(content: str) -> list[tuple[str, str]]:
    codes: list[tuple[str, str]] = []

    soup = BeautifulSoup(content, "lxml")
    # find div with class "codes"
    div = soup.find("div", class_="codes")
    divs = div.find_all("div")

    for div in divs:
        code = div.find("p", class_="code").text.strip()
        rewards = div.find("p", class_="rewards").text.strip()
        codes.append((code, rewards))

    return codes


def parse_gamerant(content: str) -> list[tuple[str, str]]:
    codes: list[tuple[str, str]] = []

    soup = BeautifulSoup(content, "lxml")
    table = soup.find("table")
    tbody = table.find("tbody")
    trs = tbody.find_all("tr")

    for tr in trs:
        tds = tr.find_all("td")
        code = tds[0].text.strip()
        rewards = tds[1].text.strip()
        codes.append((code, rewards))

    return codes


def parse_tryhard_guides(content: str) -> list[tuple[str, str]]:
    codes: list[tuple[str, str]] = []

    soup = BeautifulSoup(content, "lxml")
    div = soup.find("div", class_="entry-content")
    ul = div.find("ul")
    lis = ul.find_all("li")

    for li in lis:
        code = li.strong.text.strip()
        rewards = li.text.strip().split("–")[1].strip()  # noqa: RUF001
        codes.append((code, rewards))

    return codes


def _parse_fandom(content: str, game: genshin.Game) -> list[tuple[str, str]]:
    def is_valid_code(td: Any) -> bool:
        if game is genshin.Game.STARRAIL:
            return "bg-new" in td.get("class", [])
        if game is genshin.Game.GENSHIN:
            return td.get("style", "") == "background-color:rgb(153,255,153,0.5)"
        if game is genshin.Game.ZZZ:
            return "bg-green" in td.get("class", [])
        return False

    codes: list[tuple[str, str]] = []

    soup = BeautifulSoup(content, "lxml")
    table = soup.find("table", class_="wikitable")
    tbody = table.find("tbody")
    trs = tbody.find_all("tr")

    for tr in trs:
        tds = tr.find_all("td")
        if len(tds) < 4 or tds[1].text.strip() == "China" or not is_valid_code(tds[3]):
            continue
        code = tds[0].text.strip()
        rewards = tds[2].text.strip()
        codes.append((code, rewards))

    return codes


def parse_hsr_fandom(content: str) -> list[tuple[str, str]]:
    return _parse_fandom(content, genshin.Game.STARRAIL)


def parse_gi_fandom(content: str) -> list[tuple[str, str]]:
    return _parse_fandom(content, genshin.Game.GENSHIN)


def parse_zzz_fandom(content: str) -> list[tuple[str, str]]:
    return _parse_fandom(content, genshin.Game.ZZZ)
