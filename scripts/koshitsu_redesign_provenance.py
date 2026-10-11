"""皇室典範改正・新デザインのページに出る件数を、公開JSON・再読データ・設定から独立に数え直して照合する。

verify_number_provenance.py が「正典の1次元集計では説明できない」数字（理由区分・論点×立場・
共通の心配の確認件数・主張に当たる投稿数・資料にしかない話の検索件数）を、ここで1つずつ確かめる。
照合できた領域だけを返し、1つでも合わなければ ValueError で止める（領域ごと許可して素通りさせない）。
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup

COUNT_RE = re.compile(r"(?<![\d.,])(\d{1,3}(?:,\d{3})+|\d+)\s*(?:<[^>]{1,40}>\s*)*件")
PUBLIC = "data/public/themes/koshitsu-tenpakai.json"
REREAD = "data/koshitsu-tenpakai_issues-reread.json"
OPENING = "configs/koshitsu-tenpakai-opening.json"
READING = "configs/koshitsu-tenpakai-reading.json"


def _numbers(node) -> list[int]:
    return [int(m.group(1).replace(",", "")) for m in COUNT_RE.finditer(str(node))]


def _fmt(n: int) -> str:
    return f"{n:,}"


def _check(cond: bool, message: str) -> None:
    if not cond:
        raise ValueError("新デザインの数字が元記録と一致しません: " + message)


def _groups(config: dict, by: dict[str, int]) -> list[tuple[str, int]]:
    return [(g["id"], sum(by.get(s, 0) for s in g["stance_ids"])) for g in config["counts"]["stance_groups"]]


def _check_group_list(node, groups: list[tuple[str, int]], where: str) -> None:
    for gid, n in groups:
        dd = node.select_one(f".ko-group-{gid} dd b")
        _check(dd is not None and dd.get_text() == _fmt(n), f"{where} の {gid}（期待 {n}）")


def verified_selectors(source: str, root: Path) -> dict[str, str]:
    root = Path(root)
    soup = BeautifulSoup(source, "html.parser")
    public = json.loads((root / PUBLIC).read_text(encoding="utf-8"))
    reread = json.loads((root / REREAD).read_text(encoding="utf-8"))
    opening = json.loads((root / OPENING).read_text(encoding="utf-8"))
    reading = json.loads((root / READING).read_text(encoding="utf-8"))
    opinions = int(public["opinion_count"])
    result: dict[str, str] = {}

    # 冒頭の「全体の賛否」：立場の合計（公開JSONの論点×立場を足し直す）
    totals: Counter = Counter()
    for issue in public["issues"]:
        for s in issue["stances"]:
            totals[s["id"]] += int(s["count"])
    _check(sum(totals.values()) == opinions, "立場の合計が意見数と違う")
    stance = soup.select(".ko-stance")
    _check(len(stance) == 1, "冒頭の立場の図が1つではない")
    groups = _groups(opening, totals)
    _check_group_list(stance[0], groups, "冒頭の立場の図")
    allowed = {opinions, *dict(groups).values(), *totals.values()}
    extra = set(_numbers(stance[0])) - allowed
    _check(not extra, f"冒頭の立場の図に説明できない件数 {sorted(extra)}")
    result["ko-stance"] = f"{PUBLIC} / issues[].stances の合計と {OPENING} counts.stance_groups"

    recount = Counter((i["main_issue"], i["bucket"]) for i in reread["items"])
    for issue in public["issues"]:
        iid, n = issue["id"], int(issue["count"])
        panel = soup.find(id="issue-" + iid)
        _check(panel is not None, f"論点 {iid} の欄が無い")
        _check(panel.select_one(".kr-count b").get_text() == _fmt(n), f"{iid} の件数")
        allowed = {n, opinions}
        # 理由区分：再読データの明細を数え直す
        buckets = reread["buckets"].get(issue["label"], {})
        for bid, bucket in buckets.items():
            count = recount[(issue["label"], bid)]
            _check(count == int(bucket["count"]), f"{iid} の理由 {bid} の集計と明細")
            node = panel.select_one(f'li.kr-reason[data-reason="{bid}"] .kr-reason-n b')
            if node is not None:
                _check(node.get_text() == _fmt(count), f"{iid} の理由 {bid}（期待 {count}）")
                allowed.add(count)
        # 「どんな声か」は設定の確認済みの文。文中の件数（読み直した件数など）は設定の文と完全一致のときだけ認める
        voices = reading["issues"].get(iid, {}).get("reasons", {})
        for li in panel.select("li.kr-reason"):
            voice = li.select_one(".kr-voice")
            if voice is None:
                continue
            expected = voices.get(li["data-reason"], {}).get("voice", "")
            text = voice.get_text()
            _check(text.endswith(expected) and expected, f"{iid} の理由 {li['data-reason']} の説明文が設定と違う")
            allowed.update(int(m.replace(",", "")) for m in re.findall(r"(\d[\d,]*)件", expected))
        # 数え方の説明文（「1件は1つの区分にだけ」など）：設定の共通文に書いた件数だけ認める
        common = json.dumps(reading["reasons_common"], ensure_ascii=False)
        allowed.update(int(m) for m in re.findall(r"(?<![\d{])(\d+)件", re.sub(r"\{[^}]*\}", "", common)))
        # 論点×立場：公開JSONの論点ごとの立場
        by = {s["id"]: int(s["count"]) for s in issue["stances"]}
        _check(sum(by.values()) == n, f"{iid} の立場の合計")
        block = panel.select_one(".kr-stance")
        if block is not None:
            g = _groups(opening, by)
            _check_group_list(block, g, f"{iid} の立場")
            allowed.update(by.values())
            allowed.update(dict(g).values())
        # 共通の心配：確認した投稿例の件数
        for vein in public["ocean_layer"]["veins"]:
            if iid in vein["issue_ids"]:
                allowed.update(int(s["post_count"]) for s in vein["sides"])
        # 主張の照合：主張に当たる投稿数
        for claim in public["claim_verification"]["claims"]:
            if iid in claim["issue_ids"]:
                node = panel.select_one(f'[data-claim="{claim["id"]}"]')
                _check(node is not None and _fmt(int(claim["matched_post_count"])) + "件" in node.get_text(),
                       f"{iid} の主張 {claim['id']} の投稿数")
                allowed.add(int(claim["matched_post_count"]))
        # 資料にしかない話：検索の母数と件数
        for sunk in public["ocean_layer"]["sunk_continents"]:
            if sunk["nearest_issue_id"] == iid:
                allowed.update({int(sunk["sns_base"]), int(sunk["sns_count"])})
                # 再検索の記録（公開JSON sns_note）は、画面の文が記録と完全一致のときだけ、文中の件数を認める
                node = panel.select_one(f'[data-sunk="{sunk["id"]}"]')
                _check(node is not None and any(p.get_text() == sunk["sns_note"] for p in node.select("p")),
                       f"{iid} の資料にしかない話 {sunk['id']} の検索記録")
                allowed.update(int(m.replace(",", "")) for m in re.findall(r"(\d[\d,]*)件", sunk["sns_note"]))
        # 投稿例の件数（最大2件）
        allowed.add(len(reading["issues"].get(iid, {}).get("posts", {}).get("items", [])))
        extra = set(_numbers(panel)) - allowed
        _check(not extra, f"{iid} の欄に説明できない件数 {sorted(extra)}")
        result["#issue-" + iid] = f"{PUBLIC} / {REREAD}（明細の数え直し）/ {READING}（{iid}）"
    return result
