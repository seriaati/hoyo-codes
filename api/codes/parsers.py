# pyright: reportOptionalMemberAccess=false, reportAttributeAccessIssue=false
# pyright: reportOperatorIssue=false, reportArgumentType=false
# pyright: reportCallIssue=false
from __future__ import annotations

import re
from typing import Any

import mwparserfromhell
from bs4 import BeautifulSoup
from pydantic import BaseModel


def sanitize_code(code: str) -> str:
    if "/" in code:
        code = code.split("/", maxsplit=1)[0]
    if ";" in code:
        code = code.split(";", maxsplit=1)[0]
    return (
        re.sub(r"\[\d+\]", "", code.strip().replace("Quick Redeem", ""))
        .replace("NEW!", "")
        .upper()
        .strip()
    )


def parse_gamesradar(content: str) -> list[tuple[str, str]]:
    codes: list[tuple[str, str]] = []

    soup = BeautifulSoup(content, "lxml")
    # find div with id article-body
    div = soup.find("div", id="article-body")
    uls = div.find_all("ul")
    lis = [li for ul in uls for li in ul.find_all("li")]

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


def _parse_hsr_rewards(rewards_text: str) -> str:
    wikicode = mwparserfromhell.parse(rewards_text)

    for node in wikicode.filter_templates():
        if node.name.matches("Item List") and len(node.params) > 0:
            items_param = str(node.params[0].value).strip()
            items = items_param.split(";")
            formatted_items = []

            for item_text in items:
                stripped_item = item_text.strip()
                if "*" in stripped_item:
                    name, quantity = stripped_item.rsplit("*", 1)
                    formatted_items.append(f"{name.strip()} x{quantity.strip()}")
                else:
                    formatted_items.append(stripped_item)

            return ", ".join(formatted_items)

    return rewards_text


def parse_hsr_fandom(data: dict[str, Any]) -> list[tuple[str, str]]:
    page = next(iter(data["query"]["pages"].values()))
    content = page["revisions"][0]["slots"]["main"]["*"]
    wikicode = mwparserfromhell.parse(content)

    codes: list[tuple[str, str]] = []
    is_active_section = False

    for node in wikicode.nodes:
        if isinstance(node, mwparserfromhell.nodes.Comment):
            comment_text = str(node).strip()
            if "active" in comment_text:
                is_active_section = True
            elif "expired" in comment_text:
                is_active_section = False

        if (
            is_active_section
            and isinstance(node, mwparserfromhell.nodes.Template)
            and node.name.matches("Redemption Code Row")
        ):
            try:
                code = str(node.params[0].value).strip()
                server = str(node.params[2].value).strip()
                rewards = str(node.params[3].value).strip()

                if server not in {"A", "G", "NA", "EU", "SEA", "SAR"}:
                    continue

                rewards = _parse_hsr_rewards(rewards)
                codes.append((code, rewards))
            except ValueError:
                continue

    return codes


def parse_gi_fandom(data: dict[str, Any]) -> list[tuple[str, str]]:
    page = next(iter(data["query"]["pages"].values()))
    content = page["revisions"][0]["slots"]["main"]["*"]
    wikicode = mwparserfromhell.parse(content)

    codes: list[tuple[str, str]] = []

    for node in wikicode.nodes:
        if isinstance(node, mwparserfromhell.nodes.Template) and node.name.matches("Code Row"):
            try:
                code = str(node.params[0].value).strip()
                server = re.sub(
                    r"<!--.*?-->", "", str(node.params[1].value), flags=re.DOTALL
                ).strip()

                notacode = "no"
                for param in node.params:
                    if param.name.strip() == "notacode":
                        notacode = str(param.value).strip()
                        break

                if notacode == "yes" or server not in {"G", "A", "NA", "EU", "SEA", "SAR"}:
                    continue

                rewards = ""
                if len(node.params) > 2:
                    rewards = re.sub(
                        r"<!--.*?-->", "", str(node.params[2].value), flags=re.DOTALL
                    ).strip()
                codes.append((code, rewards))
            except ValueError:
                continue

    return codes


def parse_zzz_fandom(data: dict[str, Any]) -> list[tuple[str, str]]:
    page = next(iter(data["query"]["pages"].values()))
    content = page["revisions"][0]["slots"]["main"]["*"]
    wikicode = mwparserfromhell.parse(content)
    results: list[tuple[str, str]] = []

    containers = wikicode.filter_templates(
        matches=lambda t: t.name.matches("Redemption Code Container")
    )
    if not containers:
        return results

    container = containers[0]
    if not container.has(1):
        return results

    section_nodes = container.get(1).value.nodes
    is_active_section = False

    for node in section_nodes:
        if isinstance(node, mwparserfromhell.nodes.Comment):
            comment_text = str(node).lower()
            if "active" in comment_text:
                is_active_section = True
            elif "expired" in comment_text:
                is_active_section = False
            continue

        if (
            is_active_section
            and isinstance(node, mwparserfromhell.nodes.Template)
            and node.name.matches("Redemption Code Row")
        ):
            if node.has("notacode") and node.get("notacode").value.strip().lower() == "yes":
                continue

            try:
                code = str(node.get(1).value).strip()
                rewards_raw = ""
                if node.has(3):
                    rewards_node = node.get(3).value
                    inner_templates = rewards_node.filter_templates()
                    item_list = next(
                        (t for t in inner_templates if t.name.matches("Item List")), None
                    )

                    if item_list and item_list.has(1):
                        rewards_raw = str(item_list.get(1).value).strip()
                    else:
                        rewards_raw = str(rewards_node).strip()

                results.append((code, rewards_raw))
            except ValueError:
                continue

    return results


class Bonus(BaseModel):
    exchange_code: str


class ExchangeGroup(BaseModel):
    bonuses: list[Bonus]


class Module(BaseModel):
    exchange_group: ExchangeGroup | None


def parse_hoyolab(data: dict[str, Any]) -> list[tuple[str, str]]:
    modules = [Module(**module) for module in data["data"]["modules"]]
    codes: list[tuple[str, str]] = []

    for module in modules:
        if module.exchange_group is None:
            continue
        for bonus in module.exchange_group.bonuses:
            code = sanitize_code(bonus.exchange_code)
            if code:
                codes.append((code, ""))

    return codes
