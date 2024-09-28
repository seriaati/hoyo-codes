# pyright: reportOptionalMemberAccess=false, reportAttributeAccessIssue=false


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




    return [sanitize_code(code) for code in codes]


def parse_gamerant(content: str) -> list[str]:
    codes: list[str] = []

    soup = BeautifulSoup(content, "lxml")
    table = soup.find("table")
    tbody = table.find("tbody")
    trs = tbody.find_all("tr")

    for tr in trs:
        tds = tr.find_all("td")
        code = tds[0].text
        codes.append(code)

    return [sanitize_code(code) for code in codes]
