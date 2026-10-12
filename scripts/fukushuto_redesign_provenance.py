"""副首都・新デザインのページに出る件数を、公開JSON・再読データ・設定から独立に数え直して照合する。

皇室典範改正（scripts/koshitsu_redesign_provenance.py）と同じ役目。verify_number_provenance.py が
「正典の1次元集計では説明できない」数字（論点×立場・理由区分・理由区分×立場・主張に当たる投稿数・
資料にしかない話の検索件数・確認済みの文に含まれる件数）を、論点の欄ごとに1つずつ確かめる。
照合できた領域だけを返し、1つでも合わなければ ValueError で止める（領域ごと許可して素通りさせない）。
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import yaml
from bs4 import BeautifulSoup

COUNT_RE = re.compile(r"(?<![\d.,])(\d{1,3}(?:,\d{3})+|\d+)\s*(?:<[^>]{1,40}>\s*)*件")
NUM_IN_TEXT = re.compile(r"(\d[\d,]*)\s*件")
PUBLIC = "data/public/themes/fukushuto.json"
REREAD = "data/fukushuto_5issues-reread.json"
PLANET = "configs/planet/fukushuto.yaml"
READING = "configs/fukushuto-reading.json"
LEDGER = "data/verification/fukushuto-background.json"


def _numbers(node) -> list[int]:
    return [int(m.group(1).replace(",", "")) for m in COUNT_RE.finditer(str(node))]


def _fmt(n: int) -> str:
    return f"{n:,}"


def _check(cond: bool, message: str) -> None:
    if not cond:
        raise ValueError("新デザインの数字が元記録と一致しません: " + message)


def _norm(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _strings(node) -> list[str]:
    if isinstance(node, str):
        return [node]
    if isinstance(node, dict):
        return [s for v in node.values() for s in _strings(v)]
    if isinstance(node, list):
        return [s for v in node for s in _strings(v)]
    return []


def _confirmed_numbers(texts: list[str], shown: str) -> set[int]:
    """設定・記録の確認済みの文が画面にそのまま出ているときだけ、文中の件数を認める。"""
    found: set[int] = set()
    for text in texts:
        if "件" not in text or "{" in text:
            continue
        if _norm(text) in shown:
            found.update(int(m.replace(",", "")) for m in NUM_IN_TEXT.findall(text))
    return found


def _stance_numbers(node, stances: list[dict], counts: dict[str, int], where: str) -> None:
    """立場の帯（aria-label）と一覧の数字が、数え直した件数と一致するか。"""
    label = node.get("aria-label", "")
    expected = "、".join(f'{s["label"]} {_fmt(counts.get(s["id"], 0))}件' for s in stances)
    _check(label == expected, f"{where} の立場の帯（期待「{expected}」）")


def verified_selectors(source: str, root: Path) -> dict[str, str]:
    root = Path(root)
    soup = BeautifulSoup(source, "html.parser")
    public = json.loads((root / PUBLIC).read_text(encoding="utf-8"))
    raw = json.loads((root / REREAD).read_text(encoding="utf-8"))
    planet = yaml.safe_load((root / PLANET).read_text(encoding="utf-8"))
    reading = json.loads((root / READING).read_text(encoding="utf-8"))
    ledger = json.loads((root / LEDGER).read_text(encoding="utf-8"))
    opinions = int(public["opinion_count"])
    stances = list(planet["stances"])
    id_of_key = {s["key"]: s["id"] for s in stances}
    reread = {label: raw[sub["path"][0]] for label, sub in (planet.get("sub_issues") or {}).items()}
    common = _strings({k: v for k, v in reading.items() if k != "issues"})
    result: dict[str, str] = {}

    # 冒頭の件数欄：立場の合計（公開JSONの論点×立場を足し直す）と論点別件数
    totals: Counter = Counter()
    for issue in public["issues"]:
        for s in issue["stances"]:
            totals[s["id"]] += int(s["count"])
    _check(sum(totals.values()) == opinions, "立場の合計が意見数と違う")
    count = soup.select("#fuk-op-count")
    _check(len(count) == 1, "冒頭の件数欄が1つではない")
    allowed = {opinions, int(public["collected_count"]), *totals.values(), *(int(i["count"]) for i in public["issues"])}
    extra = set(_numbers(count[0])) - allowed
    _check(not extra, f"冒頭の件数欄に説明できない件数 {sorted(extra)}")
    result["#fuk-op-count"] = f"{PUBLIC} / collected_count・opinion_count・issues[].count・issues[].stances の合計"

    for issue in public["issues"]:
        iid, label, n = issue["id"], issue["label"], int(issue["count"])
        icfg = reading["issues"].get(iid, {})
        panel = soup.find(id="issue-" + iid)
        _check(panel is not None, f"論点 {iid} の欄が無い")
        _check(panel.select_one(".fr-count b").get_text() == _fmt(n), f"{iid} の件数")
        shown = _norm(panel.get_text())
        allowed = {n, opinions}
        # 論点×立場：公開JSONの論点ごとの立場
        by = {s["id"]: int(s["count"]) for s in issue["stances"]}
        _check(sum(by.values()) == n, f"{iid} の立場の合計")
        block = panel.select_one(".fr-stance")
        _check(block is not None, f"{iid} の立場の欄が無い")
        _stance_numbers(block.select_one(".fr-band"), stances, by, iid)
        _check([b.get_text() for b in block.select(".fr-stance-list b")] == [_fmt(by[s["id"]]) for s in stances],
               f"{iid} の立場の一覧")
        allowed.update(by.values())
        # 理由区分：再読データの明細を数え直す（区分の件数と、区分ごとの立場）
        rr = reread.get(label)
        if rr:
            for bid, bucket in rr["buckets"].items():
                items = [i for i in rr["items"] if i["bucket"] == bid]
                _check(len(items) == int(bucket["count"]), f"{iid} の理由 {bid} の集計と明細")
                li = panel.select_one(f'li.fr-reason[data-reason="{bid}"]')
                _check(li is not None, f"{iid} の理由 {bid} の行が無い")
                _check(li.select_one(".fr-reason-n b").get_text() == _fmt(len(items)), f"{iid} の理由 {bid}（期待 {len(items)}）")
                # 理由の説明（2026-10-12 から一覧の行とは別の欄。折りたたみ・非表示でもHTMLにはあるので数え直せる）
                detail = panel.select_one(f'article.fr-reason-detail[data-reason="{bid}"]')
                _check(detail is not None, f"{iid} の理由 {bid} の説明が無い")
                _check(_fmt(len(items)) + "件" in detail.select_one(".fr-eyebrow").get_text(),
                       f"{iid} の理由 {bid} の説明の件数（期待 {len(items)}）")
                per = Counter(id_of_key.get(i["stance"], i["stance"]) for i in items)
                _stance_numbers(detail.select_one(".fr-mini"), stances, per, f"{iid} の理由 {bid}")
                allowed.add(len(items))
                allowed.update(per.get(s["id"], 0) for s in stances)
                voice = detail.select_one(".fr-voice")
                if voice is not None:
                    expected = icfg.get("reasons", {}).get(bid, {}).get("voice", "")
                    _check(bool(expected) and voice.get_text().endswith(expected), f"{iid} の理由 {bid} の説明文が設定と違う")
        else:
            _check(panel.select_one("[data-unpublished]") is not None, f"{iid} は理由区分が無いのに未公開の表示が無い")
        # 主張の照合：主張に当たる投稿数
        for claim in public["claim_verification"]["claims"]:
            if iid in claim["issue_ids"]:
                node = panel.select_one(f'[data-claim="{claim["id"]}"]')
                _check(node is not None and _fmt(int(claim["matched_post_count"])) + "件" in node.get_text(),
                       f"{iid} の主張 {claim['id']} の投稿数")
                allowed.add(int(claim["matched_post_count"]))
                allowed |= _confirmed_numbers([claim["claim"], claim["finding"]], _norm(node.get_text()))
        # 資料にしかない話：検索の母数と件数。再検索の記録は、画面の文が記録と完全一致のときだけ文中の件数を認める
        for sunk in public["ocean_layer"]["sunk_continents"]:
            if sunk["nearest_issue_id"] == iid:
                node = panel.select_one(f'[data-sunk="{sunk["id"]}"]')
                _check(node is not None, f"{iid} の資料にしかない話 {sunk['id']} が無い")
                _check(any(p.get_text() == sunk["sns_note"] for p in node.select("p")),
                       f"{iid} の資料にしかない話 {sunk['id']} の検索記録")
                allowed.update({int(sunk["sns_base"]), int(sunk["sns_count"])})
                allowed |= _confirmed_numbers([sunk["sns_note"], sunk["life_impact"], sunk["topic"]], _norm(node.get_text()))
        # 制度の確認：背景台帳の文（この論点に紐づく項目だけ）
        for c in ledger["checklist"]["items"]:
            if iid in (c.get("issue_ids") or []):
                allowed |= _confirmed_numbers([c["ask"], c["found"]], shown)
        # 設定の確認済みの文（論点の説明・理由の言い換え・注記・投稿の要約）と共通の文
        allowed |= _confirmed_numbers(_strings(icfg) + common, shown)
        # 共通の文のうち {count} を差し込む文（「この論点の{count}件を…1件は1つの区分にだけ」など）
        filled = []
        for text in common:
            try:
                filled.append(text.format(count=_fmt(n)))
            except (KeyError, IndexError, ValueError):
                continue
        allowed |= _confirmed_numbers(filled, shown)
        # 投稿例の件数（最大2件）
        allowed.add(len(icfg.get("posts", {}).get("items", [])))
        extra = set(_numbers(panel)) - allowed
        _check(not extra, f"{iid} の欄に説明できない件数 {sorted(extra)}")
        result["#issue-" + iid] = f"{PUBLIC} / {REREAD}（明細の数え直し）/ {READING}（{iid}）"
    return result
