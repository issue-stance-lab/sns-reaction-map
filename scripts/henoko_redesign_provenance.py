"""辺野古高校生死亡事故・新デザインのページに出る件数を、公開JSON・再読データ・立場の対応表・設定から独立に数え直して照合する。

学校でのあだ名禁止（scripts/nickname_redesign_provenance.py）と同じ役目。辺野古の再読データの明細（items）は立場を持たないので、
区分ごとの立場は立場の対応表（data/henoko-student-accident_reread-stances.json。post_key → 立場の名前）から数える。
あだ名と違い、論点の見出しの下と理由ごとの立場は帯ではなく1文（件数のある立場だけ、多い順）なので、文の中身を数え直して比べる。
旧ページ（新デザインの目印が無いページ）では何も照合せず、空を返す（旧ページは scripts/henoko_count_provenance.py が照合する）。
verify_number_provenance.py が
「正典の1次元集計では説明できない」数字（論点×立場・理由区分・理由区分×立場・主張に当たる投稿数・
資料にしかない話の検索件数・確認済みの文に含まれる件数）を、冒頭の件数欄・短答・論点の欄ごとに1つずつ確かめる。
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
PUBLIC = "data/public/themes/henoko-student-accident.json"
REREAD = "data/henoko-student-accident_issues-reread.json"
STANCES = "data/henoko-student-accident_reread-stances.json"
PLANET = "configs/planet/henoko-student-accident.yaml"
READING = "configs/henoko-student-accident-reading.json"
OPENING = "configs/henoko-student-accident-opening.json"
MARKER = 'name="henoko-layout"'
COUNT_ID = "hop-count"
SUPPORT = "henoko-student-accident-ministry-support"
OPPOSE = "henoko-student-accident-ministry-oppose"


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


RECHECK = re.compile(r"\((\d{4}-\d{2}-\d{2})再確認[:：]\s*([^)]*)\)")


def _note_parts(note: str) -> list[str]:
    """公開JSONの sns_note を、読書面の表示と同じく本文と再確認の履歴の本文に分ける（日付の書き方は表示で変わるので比べない）。"""
    parts = [RECHECK.sub("", note).strip().rstrip("。")]
    parts += [text.strip().rstrip("。") for _when, text in RECHECK.findall(note)]
    return [p for p in parts if p]


def _stance_band(node, stances: list[dict], counts: dict[str, int], where: str) -> None:
    """立場の帯（aria-label）の数字が、数え直した件数と一致するか。"""
    _check(node is not None, f"{where} の立場の帯が無い")
    label = node.get("aria-label", "")
    expected = "、".join(f'{s["label"]} {_fmt(counts.get(s["id"], 0))}件' for s in stances)
    _check(label == expected, f"{where} の立場の帯（期待「{expected}」）")


def _stance_words(stances: list[dict], counts: dict[str, int]) -> str:
    """件数のある立場だけを、多い順に「名前N件」で並べる（henoko_reading.stance_words と同じ並べ方を、独立に書き直したもの）。"""
    order = {s["id"]: k for k, s in enumerate(stances)}
    rows = sorted((s for s in stances if counts.get(s["id"], 0)), key=lambda s: (-counts[s["id"]], order[s["id"]]))
    return "・".join(f'{s["label"]}{_fmt(counts[s["id"]])}件' for s in rows)


def verified_selectors(source: str, root: Path) -> dict[str, str]:
    if MARKER not in source:
        return {}
    root = Path(root)
    soup = BeautifulSoup(source, "html.parser")
    public = json.loads((root / PUBLIC).read_text(encoding="utf-8"))
    raw = json.loads((root / REREAD).read_text(encoding="utf-8"))
    planet = yaml.safe_load((root / PLANET).read_text(encoding="utf-8"))
    reading = json.loads((root / READING).read_text(encoding="utf-8"))
    opening = json.loads((root / OPENING).read_text(encoding="utf-8"))
    table = json.loads((root / STANCES).read_text(encoding="utf-8"))["stances"]
    opinions = int(public["opinion_count"])
    id_of_label = {}
    for s in planet["stances"]:
        id_of_label[s["key"]] = s["id"]
        id_of_label[s["label"]] = s["id"]
    # 辺野古の再読データは buckets[論点名] と、全論点の平坦な items（post_key・main_issue・bucket）を持つ。立場は対応表から写す
    _check(set(table) == {i["post_key"] for i in raw["items"]}, "立場の対応表と再読データの明細の投稿が一致しない")
    reread = {label: {"buckets": raw["buckets"][label],
                      "items": [dict(i, stance=table.get(i["post_key"])) for i in raw["items"] if i.get("main_issue") == label]}
              for label in (planet.get("sub_issues") or {})}
    common = _strings({k: v for k, v in reading.items() if k != "issues"})
    result: dict[str, str] = {}

    # 冒頭の件数欄：立場の合計（公開JSONの論点×立場を足し直す）・論点別件数・論点ごとの理由区分の件数
    totals: Counter = Counter()
    for issue in public["issues"]:
        for s in issue["stances"]:
            totals[s["id"]] += int(s["count"])
    _check(sum(totals.values()) == opinions, "立場の合計が意見数と違う")
    stances = list(planet["stances"])
    _check({s["id"] for s in stances} == set(totals), "公開JSONの立場と planet 設定の立場が違う")
    count = soup.select(f"#{COUNT_ID}")
    _check(len(count) == 1, "冒頭の件数欄が1つではない")
    allowed = {opinions, int(public["collected_count"]), *totals.values(), *(int(i["count"]) for i in public["issues"])}
    for label, rr in reread.items():
        items = Counter(i["bucket"] for i in rr["items"])
        for bid, bucket in rr["buckets"].items():
            _check(items[bid] == int(bucket["count"]), f"{label} の理由 {bid} の集計と明細")
            allowed.add(items[bid])
    extra = set(_numbers(count[0])) - allowed
    _check(not extra, f"冒頭の件数欄に説明できない件数 {sorted(extra)}")
    stance_line = count[0].select_one(".hop-count__stance").get_text()
    for sid in (SUPPORT, OPPOSE, "henoko-student-accident-distinguish-issues"):
        _check(_fmt(totals[sid]) + "件" in stance_line, f"冒頭の立場の1文に {sid} の {totals[sid]} 件が無い")
    result[f"#{COUNT_ID}"] = f"{PUBLIC} / collected_count・opinion_count・issues[].count・issues[].stances の合計、{REREAD}（理由区分の明細の数え直し）"

    # 冒頭の短答「何が争点？」：多い論点3つの件数と、文科省判断への賛否を書いた意見（支持＋反発）
    voice = soup.select("article.hop-answer.hop-zone--voice")
    _check(len(voice) == 1, "冒頭のSNSの意見の短答が1つではない")
    decided = totals[SUPPORT] + totals[OPPOSE]
    top3 = sorted((i for i in public["issues"] if i.get("kind") != "other"), key=lambda i: -int(i["count"]))[:3]
    body = voice[0].select_one(".hop-answer__body").get_text()
    for i in top3:
        _check(f'{i["label"]}（{_fmt(int(i["count"]))}件）' in body, f"短答の論点 {i['label']} の件数")
    _check(f"{_fmt(decided)}件" in body, f"短答の賛否を書いた意見（期待 {decided}）")
    extra = set(_numbers(voice[0])) - ({int(i["count"]) for i in top3} | {decided})
    _check(not extra, f"冒頭の短答に説明できない件数 {sorted(extra)}")
    result["hop-zone--voice"] = f"{PUBLIC} / issues[].count の上位3つ・文科省判断を支持と反発の合計（短答と件数欄）"

    small = int(opening["count"].get("small_threshold", reading.get("small", {}).get("threshold", 0)) or 0)
    for issue in public["issues"]:
        iid, label, n = issue["id"], issue["label"], int(issue["count"])
        icfg = reading["issues"].get(iid, {})
        panel = soup.find(id="issue-" + iid)
        if panel is None and n == 0:
            continue  # 0件の論点（いまは「その他」）はタブも欄も出さない（henoko_reading.ordered_issues）
        _check(panel is not None, f"論点 {iid} の欄が無い")
        _check(panel.select_one(".fr-count b").get_text() == _fmt(n), f"{iid} の件数")
        shown = _norm(panel.get_text())
        allowed = {n, opinions}
        # 論点×立場：公開JSONの論点ごとの立場
        by = {s["id"]: int(s["count"]) for s in issue["stances"]}
        _check(sum(by.values()) == n, f"{iid} の立場の合計")
        block = panel.select_one(".fr-stance")
        _check(block is not None, f"{iid} の立場の欄が無い")
        _stance_band(block.select_one(".fr-band"), stances, by, iid)
        _check([b.get_text() for b in block.select(".fr-stance-list b")] == [_fmt(by[s["id"]]) for s in stances],
               f"{iid} の立場の一覧")
        # 見出しの下の立場の1文（件数のある立場だけ、多い順）
        head = panel.select_one(".fr-head-stance")
        _check(head is not None, f"{iid} の見出しの立場の1文が無い")
        words = _stance_words(stances, by)
        top = max(stances, key=lambda s: by.get(s["id"], 0))
        _check(words in head.get_text() or (by[top["id"]] == n and top["label"] in head.get_text()),
               f"{iid} の見出しの立場の1文（期待「{words}」）")
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
                detail = panel.select_one(f'article.fr-reason-detail[data-reason="{bid}"]')
                _check(detail is not None, f"{iid} の理由 {bid} の説明が無い")
                _check(_fmt(len(items)) + "件" in detail.select_one(".fr-eyebrow").get_text(),
                       f"{iid} の理由 {bid} の説明の件数（期待 {len(items)}）")
                _check(all(i.get("stance") in id_of_label for i in items), f"{iid} の理由 {bid} の明細に立場が無い")
                per = Counter(id_of_label[i["stance"]] for i in items)
                stance_line = detail.select_one(".fr-reason-stance")
                _check(stance_line is not None and _stance_words(stances, per) in stance_line.get_text(),
                       f"{iid} の理由 {bid} の立場の1文")
                allowed.add(len(items))
                allowed.update(per.values())
                voice_node = detail.select_one(".fr-voice")
                if voice_node is not None:
                    expected = icfg.get("reasons", {}).get(bid, {}).get("voice", "")
                    _check(bool(expected) and voice_node.get_text().endswith(expected), f"{iid} の理由 {bid} の説明文が設定と違う")
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
        overrides = reading.get("sunk_issue_overrides", {})
        for sunk in public["ocean_layer"]["sunk_continents"]:
            if (sunk.get("nearest_issue_id") or overrides.get(sunk["id"])) == iid:
                node = panel.select_one(f'[data-sunk="{sunk["id"]}"]')
                _check(node is not None, f"{iid} の資料にしかない話 {sunk['id']} が無い")
                _check(_norm(sunk["sns_note"]).replace("。", "") in _norm(node.get_text()).replace("。", "")
                       or all(_norm(x) in _norm(node.get_text()) for x in _note_parts(sunk["sns_note"])),
                       f"{iid} の資料にしかない話 {sunk['id']} の検索記録")
                allowed.update({int(sunk["sns_base"]), int(sunk["sns_count"])})
                allowed |= _confirmed_numbers([sunk["sns_note"], *_note_parts(sunk["sns_note"]), sunk["life_impact"], sunk["topic"]],
                                              _norm(node.get_text()))
                group = node.find_parent("details", attrs={"data-sunk-group": True})
                if group is not None:
                    allowed.add(len(group.select("[data-sunk]")))
        # 立場が違っても共通する心配：読んだ投稿の数（公開JSON ocean_layer.veins の sides[].post_count）
        for vein in public["ocean_layer"].get("veins", []):
            if iid in vein["issue_ids"]:
                node = panel.select_one(f'[data-vein="{vein["id"]}"]')
                _check(node is not None, f"{iid} の共通する心配 {vein['id']} が無い")
                sides = "・".join(f'{x["stance_label"]}{_fmt(int(x["post_count"]))}件' for x in vein["sides"])
                _check(sides in node.get_text(), f"{iid} の共通する心配 {vein['id']} の読んだ投稿の数")
                allowed.update(int(x["post_count"]) for x in vein["sides"])
                allowed |= _confirmed_numbers([vein["shared_concern"], vein["diverging_reason"]], _norm(node.get_text()))
        # 制度の確認（背景台帳の checklist のうち、設定 issues[].checks でこの論点に割り当てた項目）
        for cid in icfg.get("checks", []):
            _check(panel.select_one(f'[data-check="{cid}"]') is not None, f"{iid} の制度の確認 {cid} が無い")
        # 設定の確認済みの文（論点の説明・理由の言い換え・注記・投稿の要約）と共通の文
        allowed |= _confirmed_numbers(_strings(icfg) + common, shown)
        filled = []
        for text in common:
            try:
                filled.append(text.format(count=_fmt(n)))
            except (KeyError, IndexError, ValueError):
                continue
        allowed |= _confirmed_numbers(filled, shown)
        # 投稿例の件数（最大2件）と、「少数」の注記のしきい値
        allowed.add(len(icfg.get("posts", {}).get("items", [])))
        if small:
            allowed.add(small)
        extra = set(_numbers(panel)) - allowed
        _check(not extra, f"{iid} の欄に説明できない件数 {sorted(extra)}")
        result["#issue-" + iid] = f"{PUBLIC} / {REREAD}（明細の数え直し）/ {STANCES} / {READING}（{iid}）"
    return result
