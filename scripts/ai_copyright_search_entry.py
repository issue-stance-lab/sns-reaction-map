"""検索意図の入口UIを、生成AIページの表紙直下へ挿入する。"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- AI_COPYRIGHT_SEARCH_ENTRY_START -->"
END = "<!-- AI_COPYRIGHT_SEARCH_ENTRY_END -->"
TEMPLATE = ROOT / "scripts/templates/ai_copyright_search_entry.html"


def render() -> str:
    """テンプレートを読み、目印がちょうど1組あることを確認して返す。"""
    markup = TEMPLATE.read_text(encoding="utf-8")
    if markup.count(START) != 1 or markup.count(END) != 1:
        raise ValueError("検索入口UI: テンプレートの目印が1組ではありません")
    return markup.strip("\r\n")


def apply(source: str) -> str:
    """既存の検索入口を更新、またはmainの先頭（表紙直下）へ初回挿入する。"""
    markup = render()
    if START in source or END in source:
        if source.count(START) != 1 or source.count(END) != 1:
            raise ValueError("検索入口UI: ページ上の目印が1組ではありません")
        pattern = re.escape(START) + r".*?" + re.escape(END) + r"(?:\r?\n)*"
        return re.sub(pattern, lambda _: markup + "\n\n", source, count=1, flags=re.S)

    main_open = re.search(r"<main\b[^>]*>", source, flags=re.I)
    if not main_open or len(re.findall(r"<main\b", source, flags=re.I)) != 1:
        raise ValueError("検索入口UI: main要素を一意に見つけられません")
    remainder = source[main_open.end():].lstrip("\r\n")
    return source[:main_open.end()] + "\n\n" + markup + "\n\n" + remainder


def validate(source: str) -> list[str]:
    """検索入口が表紙直下にあり、既存マップを置き換えていないか調べる。"""
    from bs4 import BeautifulSoup

    problems: list[str] = []
    if source.count(START) != 1 or source.count(END) != 1:
        return ["検索入口UIの目印が1組ではありません"]

    soup = BeautifulSoup(source, "html.parser")
    main = soup.select_one("main")
    entry = soup.select_one("#aic-search-entry")
    map_root = soup.select_one("#planet-block")
    hero = soup.select_one(".hero")
    if not main or not entry or not map_root or not hero:
        return ["表紙・検索入口・反応マップのいずれかが見つかりません"]
    first_element = next((child for child in main.children if getattr(child, "name", None)), None)
    if first_element is not entry:
        problems.append("検索入口がmain直下の先頭（表紙直下）にありません")
    if source.index("</section>", source.index('<section class="hero"')) > source.index(START):
        problems.append("検索入口が元の表紙より前にあります")
    if source.index(START) > source.index('id="planet-block"'):
        problems.append("検索入口が反応マップより後ろにあります")
    if source.count('id="aic-search-entry"') != 1:
        problems.append("検索入口が1つではありません")
    if len(soup.select('#aic-search-entry [role="tab"]')) != 3:
        problems.append("検索入口の論点切替が3つではありません")
    if not soup.select_one('#aic-search-entry [data-aic-search-question]'):
        problems.append("検索入口の疑問ボタンがありません")
    if not soup.select_one('#aic-search-entry [data-aic-search-source]'):
        problems.append("検索入口の一次資料リンクがありません")
    if not soup.select_one('#aic-search-entry a[data-aic-search-map]'):
        problems.append("反応マップへの接続リンクがありません")
    return problems
