# pyright: reportOptionalMemberAccess=false, reportAttributeAccessIssue=false

import datetime

from bs4 import BeautifulSoup


def sanitize_code(code: str) -> str:
    if "/" in code:
        return code.split("/")[0].strip()
    return code.strip()


def parse_gamesradar(content: str) -> list[str]:
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

    return [sanitize_code(code) for code in codes]


def parse_pockettactics(content: str) -> list[str]:
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

    return [sanitize_code(code) for code in codes]


def parse_prydwen(content: str) -> list[str]:
    codes: list[str] = []

    soup = BeautifulSoup(content, "lxml")
    # find div with class "codes"
    div = soup.find("div", class_="codes")
    ps = div.find_all("p", class_="code")
    for p in ps:
        codes.append(p.text.strip())

    return [sanitize_code(code) for code in codes]


def parse_tot_wiki(content: str) -> list[str]:
    codes: list[str] = []

    soup = BeautifulSoup(content, "lxml")
    # Find table with class name "wikitable"
    utc_9 = datetime.timezone(datetime.timedelta(hours=9))
    table = soup.find("table", class_="wikitable")

    for tr in table.find_all("tr")[1:]:
        tds = tr.find_all("td")
        end_date = tds[4].text.strip().replace(" UTC+9", "")  # Example: "2024-07-31 04:00:00"
        parsed_end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=utc_9
        )
        now = datetime.datetime.now(utc_9)
        if parsed_end_date < now:
            continue
        code = tds[1].text.strip()
        codes.append(code)

    return [sanitize_code(code) for code in codes]
