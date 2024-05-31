# pyright: reportOptionalMemberAccess=false, reportAttributeAccessIssue=false

from bs4 import BeautifulSoup


def parse_gamesradar_codes(content: str) -> list[str]:
    codes: list[str] = []

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
        codes.append(li.strong.text.strip().split(" / ")[0].strip())

    return codes


def parse_pockettactics_codes(content: str) -> list[str]:
    codes: list[str] = []

    soup = BeautifulSoup(content, "lxml")
    # find div with class entry-content
    div = soup.find("div", class_="entry-content")
    ul = div.find("ul")
    lis = ul.find_all("li")
    for li in lis:
        if li.strong is None or not li.strong.text.strip().isupper():
            continue
        codes.append(li.strong.text.strip())

    return codes
