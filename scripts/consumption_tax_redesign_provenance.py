"""消費税減税・新デザインのページに出る件数を、公開JSON・再読データ・立場の対応表・設定から独立に数え直して照合する。

辺野古（scripts/henoko_redesign_provenance.py）・あだ名禁止（nickname_redesign_provenance.py）と同じ役目。
消費税の再読データは論点ごとの入れ子（planet 設定の sub_issues の path・items_path）で、どの区分にも当てはまらないとして除いた明細
（excluded_items）を持つ。区分ごとの立場は立場の対応表（data/consumption-tax-cut_reread-stances.json。post_key → 立場の名前）から数える。
旧ページ（新デザインの目印が無いページ）では何も照合せず、空を返す（旧ページは scripts/consumption_tax_count_provenance.py が照合する）。
verify_number_provenance.py が「正典の1次元集計では説明できない」数字（論点×立場・理由区分・理由区分×立場・主張に当たる投稿数・
資料にしかない話の検索件数・重なる心配で読んだ投稿の数・推移の要約の件数の幅）を、冒頭の件数欄・論点の欄・推移の要約ごとに1つずつ確かめる。
照合できた領域だけを返し、1つでも合わなければ ValueError で止める（領域ごと許可して素通りさせない）。
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import yaml
from bs4 import BeautifulSoup

COUNT_RE = re.compile(r"(?<![\d.,])(\d{1,3}(?:,\d{3})+|\d+)\s*(?:<[^>]{1,40}>\s*)*件")
NUM_IN_TEXT = re.compile(r"(\d[\d,]*)\s*件")
PUBLIC = "data/public/themes/consumption-tax-cut.json"
REREAD = "data/consumption-tax-cut_4issues-reread.json"
STANCES = "data/consumption-tax-cut_reread-stances.json"
PLANET = "configs/planet/consumption-tax-cut.yaml"
READING = "configs/consumption-tax-cut-reading.json"
MARKER = 'name="consumption-tax-layout"'
COUNT_ID = "cto-count"
RECHECK = re.compile(r"[（(](\d{4}-\d{2}-\d{2})再?確認[:：]\s*([^)）]*)[)）]")


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
        if _norm(text).rstrip("。") in shown:
            found.update(int(m.replace(",", "")) for m in NUM_IN_TEXT.findall(text))
    return found


def _note_parts(note: str) -> list[str]:
    """公開JSONの sns_note を、読書面の表示と同じく本文と再確認の履歴の本文に分ける（日付の書き方は表示で変わるので比べない）。"""
    parts = [RECHECK.sub("", note).strip().rstrip("。")]
    parts += [text.strip().rstrip("。") for _when, text in RECHECK.findall(note)]
    return [p for p in parts if p]


def _band(node, stances: list[dict], counts: dict[str, int], where: str) -> None:
    """立場の帯（aria-label）の数字が、数え直した件数と一致するか。"""
    _check(node is not None, f"{where} の立場の帯が無い")
    expected = "、".join(f'{s["label"]} {_fmt(counts.get(s["id"], 0))}件' for s in stances)
    _check(node.get("aria-label", "") == expected, f"{where} の立場の帯（期待「{expected}」）")


def _dig(node, path):
    for key in path:
        node = node[key]
    return node


def _reread(root: Path, planet: dict, table: dict) -> dict:
    """論点名 → 理由区分（buckets）・明細（立場つき）・除いた明細。消費税の再読データは論点ごとの入れ子。"""
    raw = json.loads((root / REREAD).read_text(encoding="utf-8"))
    out, keys = {}, set()
    for label, sub in (planet.get("sub_issues") or {}).items():
        path, items_path = list(sub["path"]), list(sub["items_path"])
        node = _dig(raw, path[:-1])

        def row(i: dict) -> dict:
            key = hashlib.sha256(str(i["tweet_id"]).encode()).hexdigest()
            keys.add(key)
            return {"bucket": i.get("bucket"), "stance": table.get(key)}

        out[label] = {"buckets": _dig(raw, path), "items": [row(i) for i in _dig(raw, items_path)],
                      "excluded": [row(i) for i in node.get("excluded_items", [])]}
    _check(keys == set(table), "立場の対応表と再読データの明細の投稿が一致しない")
    return out


def verified_selectors(source: str, root: Path) -> dict[str, str]:
    if MARKER not in source:
        return {}
    root = Path(root)
    soup = BeautifulSoup(source, "html.parser")
    public = json.loads((root / PUBLIC).read_text(encoding="utf-8"))
    planet = yaml.safe_load((root / PLANET).read_text(encoding="utf-8"))
    reading = json.loads((root / READING).read_text(encoding="utf-8"))
    table = json.loads((root / STANCES).read_text(encoding="utf-8"))["stances"]
    opinions = int(public["opinion_count"])
    stances = list(planet["stances"])
    id_of_label = {}
    for s in stances:
        id_of_label[s["key"]] = s["id"]
        id_of_label[s["label"]] = s["id"]
    reread = _reread(root, planet, table)
    common = _strings({k: v for k, v in reading.items() if k != "issues"})
    result: dict[str, str] = {}

    # 冒頭の件数欄：立場の合計（公開JSONの論点×立場を足し直す）・論点別件数
    totals: Counter = Counter()
    for issue in public["issues"]:
        for s in issue["stances"]:
            totals[s["id"]] += int(s["count"])
    _check(sum(totals.values()) == opinions, "立場の合計が意見数と違う")
    _check({s["id"] for s in stances} == set(totals), "公開JSONの立場と planet 設定の立場が違う")
    count = soup.select(f"#{COUNT_ID}")
    _check(len(count) == 1, "冒頭の件数欄が1つではない")
    allowed = {opinions, int(public["collected_count"]), *totals.values(), *(int(i["count"]) for i in public["issues"])}
    extra = set(_numbers(count[0])) - allowed
    _check(not extra, f"冒頭の件数欄に説明できない件数 {sorted(extra)}")
    shown = [b.get_text() for b in count[0].select(".cto-stance__list small")]
    _check(shown == [f"{_fmt(totals[s['id']])}件" for s in stances], "冒頭の立場の件数の並び")
    result[f"#{COUNT_ID}"] = f"{PUBLIC} / collected_count・opinion_count・issues[].count・issues[].stances の合計"

    for issue in public["issues"]:
        iid, label, n = issue["id"], issue["label"], int(issue["count"])
        icfg = reading["issues"].get(iid, {})
        panel = soup.find(id="issue-" + iid)
        if panel is None and n == 0:
            continue
        _check(panel is not None, f"論点 {iid} の欄が無い")
        _check(panel.select_one(".fr-count b").get_text() == _fmt(n), f"{iid} の件数")
        shown = _norm(panel.get_text())
        allowed = {n, opinions}
        # 論点×立場：公開JSONの論点ごとの立場（見出しの帯と一覧、折りたたみの立場別集計）
        by = {s["id"]: int(s["count"]) for s in issue["stances"]}
        _check(sum(by.values()) == n, f"{iid} の立場の合計")
        head = panel.select_one(".fr-head-stance")
        _check(head is not None, f"{iid} の見出しの立場の帯が無い")
        _band(head.select_one(".fr-band"), stances, by, iid + " の見出し")
        _check([b.get_text() for b in head.select(".fr-stance-list b")] == [_fmt(by[s["id"]]) for s in stances],
               f"{iid} の見出しの立場の一覧")
        block = panel.select_one(".fr-stance")
        _check(block is not None, f"{iid} の立場の欄が無い")
        _band(block.select_one(".fr-band"), stances, by, iid)
        _check([b.get_text() for b in block.select(".fr-stance-list b")] == [_fmt(by[s["id"]]) for s in stances],
               f"{iid} の立場の一覧")
        allowed.update(by.values())
        # 理由区分：再読データの明細を数え直す（区分の件数・区分ごとの立場・除いた明細）
        rr = reread.get(label)
        if rr:
            for bid, bucket in rr["buckets"].items():
                items = [i for i in rr["items"] if i["bucket"] == bid]
                _check(len(items) == int(bucket["count"]), f"{iid} の理由 {bid} の集計と明細")
                li = panel.select_one(f'li.fr-reason[data-reason="{bid}"]')
                _check(li is not None, f"{iid} の理由 {bid} の行が無い")
                _check(li.select_one(".fr-reason-n b").get_text() == _fmt(len(items)), f"{iid} の理由 {bid}（期待 {len(items)}）")
                detail = panel.select_one(f'article.fr-reason-detail[data-reason="{bid}"]')
                _check(detail is not None, f"{iid} の理由 {bid} の説明が無い")
                _check(_fmt(len(items)) + "件" in detail.select_one(".fr-eyebrow").get_text(),
                       f"{iid} の理由 {bid} の説明の件数（期待 {len(items)}）")
                _check(all(i.get("stance") in id_of_label for i in items), f"{iid} の理由 {bid} の明細に立場が無い")
                per = Counter(id_of_label[i["stance"]] for i in items)
                line = detail.select_one(".fr-reason-stance")
                _check(line is not None, f"{iid} の理由 {bid} の立場の内訳が無い")
                _band(line.select_one(".fr-mini"), stances, per, f"{iid} の理由 {bid}")
                words = "・".join(f'{s["label"]}{_fmt(per.get(s["id"], 0))}' for s in stances)
                _check(words in line.get_text(), f"{iid} の理由 {bid} の立場の内訳の文（期待「{words}」）")
                allowed.add(len(items))
                allowed.update(per.get(s["id"], 0) for s in stances)  # 0件の立場も帯に「0件」と出る
                voice = detail.select_one(".fr-voice")
                if voice is not None:
                    expected = icfg.get("reasons", {}).get(bid, {}).get("voice", "")
                    _check(bool(expected) and voice.get_text().endswith(expected), f"{iid} の理由 {bid} の説明文が設定と違う")
            _check(sum(int(b["count"]) for b in rr["buckets"].values()) + len(rr["excluded"]) == n,
                   f"{iid} の理由区分の合計と除いた明細が論点の件数と違う")
            if rr["excluded"]:
                node = panel.select_one("[data-excluded]")
                _check(node is not None and node["data-excluded"] == str(len(rr["excluded"]))
                       and _fmt(len(rr["excluded"])) + "件" in node.get_text(), f"{iid} の除いた明細の件数")
                allowed.add(len(rr["excluded"]))
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
        # 資料にしかない話：検索の母数と件数。再検索の記録は、画面の文が記録と一致するときだけ文中の件数を認める
        overrides = reading.get("sunk_issue_overrides", {})
        sunk_here = [x for x in public["ocean_layer"]["sunk_continents"]
                     if (overrides.get(x["id"]) or x.get("nearest_issue_id")) == iid]
        for sunk in sunk_here:
            node = panel.select_one(f'[data-sunk="{sunk["id"]}"]')
            _check(node is not None, f"{iid} の資料にしかない話 {sunk['id']} が無い")
            _check(all(_norm(x) in _norm(node.get_text()) for x in _note_parts(sunk["sns_note"])),
                   f"{iid} の資料にしかない話 {sunk['id']} の検索記録")
            allowed.update({int(sunk["sns_base"]), int(sunk["sns_count"])})
            allowed |= _confirmed_numbers([*_note_parts(sunk["sns_note"]), sunk["life_impact"], sunk["topic"]],
                                          _norm(node.get_text()))
        if len(sunk_here) >= 2:
            allowed.add(len(sunk_here))  # まとめた折りたたみの「◯件」
        # 立場が違っても重なる心配：読んだ投稿の数（公開JSON ocean_layer.veins の sides[].post_count）
        for vein in public["ocean_layer"].get("veins", []):
            if iid in vein["issue_ids"]:
                node = panel.select_one(f'[data-vein="{vein["id"]}"]')
                _check(node is not None, f"{iid} の重なる心配 {vein['id']} が無い")
                sides = "・".join(f'{x["stance_label"]}{_fmt(int(x["post_count"]))}件' for x in vein["sides"])
                _check(sides in node.get_text(), f"{iid} の重なる心配 {vein['id']} の読んだ投稿の数")
                allowed.update(int(x["post_count"]) for x in vein["sides"])
                allowed |= _confirmed_numbers([vein["shared_concern"], vein["diverging_reason"]], _norm(node.get_text()))
        # 設定の確認済みの文（論点の説明・理由の言い換え・制度の確認・投稿の要約）と共通の文
        allowed |= _confirmed_numbers(_strings(icfg) + common, shown)
        # 投稿の例の件数（最大2件）
        posts = len(icfg.get("posts", {}).get("items", []))
        allowed.add(posts)
        extra = set(_numbers(panel)) - allowed
        _check(not extra, f"{iid} の欄に説明できない件数 {sorted(extra)}")
        result["#issue-" + iid] = f"{PUBLIC} / {REREAD}（明細の数え直し）/ {STANCES} / {READING}（{iid}）"

    # 推移の要約の注記（1回あたりの意見の件数の幅）：推移の欄のスクリプトが持つ回ごとの件数と一致するか
    note = soup.select_one("#cap-trend .cap-trend-note")
    if note is not None:
        panels = re.search(r"const panels = (\{.*?\});\n", source, re.S)
        _check(panels is not None, "推移の欄の回ごとの件数（panels）が読めない")
        rounds = json.loads(panels.group(1))["stance"]["rounds"]
        lo, hi = min(int(r["n"]) for r in rounds), max(int(r["n"]) for r in rounds)
        _check(f"{_fmt(lo)}〜{_fmt(hi)}件" in note.get_text() or f"{lo}〜{hi}件" in note.get_text(),
               f"推移の要約の件数の幅（期待 {lo}〜{hi}件）")
        _check(set(_numbers(note)) <= {lo, hi}, "推移の要約の注記に説明できない件数")
        result["#cap-trend .cap-trend-note"] = "意見の推移（TREND_CARD）の panels.stance.rounds[].n の最小と最大"
    return result
