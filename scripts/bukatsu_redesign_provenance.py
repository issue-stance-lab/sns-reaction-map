"""Recount the redesign's rendered numbers before accepting their regions."""
from collections import Counter
import json
import re
from bs4 import BeautifulSoup
import yaml

def verify_counts(source, root):
    s=BeautifulSoup(source,"html.parser")
    public=json.loads((root/"data/public/themes/bukatsu-chiiki.json").read_text())
    counts={i["id"]:i["count"] for i in public["issues"]}
    cfg=yaml.safe_load((root/"configs/planet/bukatsu-chiiki.yaml").read_text())
    for issue in cfg["issues"]:
        panel=s.find(id=issue["id"])
        if panel is None:
            raise ValueError("論点がありません: "+issue["id"])
        heading=panel.select_one(".redesign-issue-count")
        if heading is None or heading.get_text()!=f"選択中の論点 · {counts[issue['id']]}件":
            raise ValueError("論点の表示件数が一致しません: "+issue["id"])
        row=next(x for x in public["issues"] if x["id"]==issue["id"])
        actual=[x.get_text() for x in panel.select(".issue-stances>span")]
        expected=[x["label"]+" "+str(x["count"])+"件" for x in row["stances"]]
        if actual!=expected:raise ValueError("論点内の立場別件数が公開集計と一致しません")
        sc=cfg["sub_issues"].get(issue["key"])
        if not sc:continue
        raw=json.loads((root/sc["file"]).read_text());records=raw
        for part in sc.get("items_path",sc["path"][:-1]+["items"]):records=records[part]
        buckets=Counter(r["bucket"] for r in records)
        gap=counts[issue["id"]]-len(records)
        if gap<0:raise ValueError("再読件数が母数を超えています")
        if gap:buckets["__unread__"]=gap
        if {b["data-reason"] for b in panel.select(".reason-choice")}!=set(buckets):
            raise ValueError("理由分類が元記録と一致しません")
        for key,n in buckets.items():
            button=panel.select_one('.reason-choice[data-reason="'+key+'"]')
            detail=panel.find(id=issue["id"]+"--"+key)
            if button.b.get_text()!=str(n)+"件" or detail.select_one(".redesign-reason-count").get_text()!=f"選んだ理由 · {n}件":
                raise ValueError("理由の件数が元記録と一致しません: "+key)
        coverage=panel.select_one(".redesign-coverage")
        expected=f"理由の再読済み {len(records)}件 ／ 未再読 {gap}件。件数はこの論点内の投稿数です。"
        if coverage is None or coverage.get_text()!=expected:raise ValueError("再読件数が元記録と一致しません")
    return {name:"公開論点集計と理由別の再読記録を独立に数え、表示件数と照合済み" for name in
            ("redesign-issue-count","reason-choice","redesign-reason-count","redesign-coverage","issue-stances")}

def verify_glance(source,root,sample_file=None):
    from scripts.trend_count_provenance import _labels, _trend_rounds
    from scripts.bukatsu_redesign.glance_chart import annotated_graph
    s=BeautifulSoup(source,"html.parser")
    labels=_labels("bukatsu-chiiki")["issue"]
    actual=_trend_rounds("bukatsu-chiiki",root,"main_issue",labels,"issue",sample_file)
    rounds=[{"d":day,"n":n,"v":v,"c":c} for day,(n,v,c) in sorted(actual.items())]
    charts=s.select(".issue-glance")
    if len(charts)!=len(labels):raise ValueError("簡易グラフの論点数が一致しません")
    for chart in charts:
        name=chart.h3.get_text()
        if name not in labels:raise ValueError("不明な簡易グラフ")
        j=labels.index(name)
        for mobile,cls in ((False,"glance-chart-desktop"),(True,"glance-chart-mobile")):
            expected=BeautifulSoup(annotated_graph(name,rounds,j,mobile),"html.parser").svg
            if str(chart.select_one("."+cls))!=str(expected):
                raise ValueError("簡易グラフが正典の独立再集計と一致しません: "+name)
        if chart.select_one(".glance-head>.fine").get_text()!=str(len(rounds))+"回の収集":
            raise ValueError("簡易グラフの収集回数が違います")
    return {"glance-chart-desktop":"非公開正典を収集日別・論点別に再集計してSVGと照合",
            "glance-chart-mobile":"非公開正典を収集日別・論点別に再集計してSVGと照合"}


# ---------------------------------------------------------------- 最新の型（scripts/build_bukatsu_redesign_v2.py、redesign-v2）
# 上の verify_counts・verify_glance は初期型（redesign-v1。2026-10-10 公開）のページ用で、初期型の経路が残る間は消さない。
# 下は消費税減税（scripts/consumption_tax_redesign_provenance.py）と同じ照合。冒頭の件数欄・7論点の欄・推移の要約の注記ごとに、
# 公開JSON・再読データの明細（3ファイル）・立場の対応表・読書面の設定から数え直し、1つでも合わなければ ValueError で止める。

V2_MARKER = '<meta name="bukatsu-layout" content="redesign-v2">'
V2_PUBLIC = "data/public/themes/bukatsu-chiiki.json"
V2_STANCES = "data/bukatsu-chiiki_reread-stances.json"
V2_PLANET = "configs/planet/bukatsu-chiiki.yaml"
V2_READING = "configs/bukatsu-chiiki-reading.json"
V2_COUNT_ID = "bko-count"


def _v2_tools():
    from scripts import consumption_tax_redesign_provenance as base  # 同じ数え方の部品（_numbers・_band・_confirmed_numbers など）
    return base


def _v2_reread(root, planet, table, excluded_cfg):
    """論点名 → 理由区分（excluded_buckets を除く）・明細（立場つき）・除いた明細。再読データは3ファイルに分かれる。"""
    import hashlib
    base = _v2_tools()
    out, keys, cache = {}, set(), {}
    for label, sub in (planet.get("sub_issues") or {}).items():
        raw = cache.setdefault(sub["file"], json.loads((root / sub["file"]).read_text(encoding="utf-8")))
        path = list(sub["path"])
        node = raw
        for key in path[:-1]:
            node = node[key]
        ex = set(excluded_cfg.get(label, []))

        def row(i):
            key = hashlib.sha256(str(i["tweet_id"]).encode()).hexdigest()
            keys.add(key)
            return {"bucket": i.get("bucket"), "stance": table.get(key)}

        rows = [row(i) for i in node["items"]]
        out[label] = {"buckets": {k: v for k, v in node["buckets"].items() if k not in ex},
                      "items": [r for r in rows if r["bucket"] not in ex],
                      "excluded": [r for r in rows if r["bucket"] in ex]}
    base._check(keys == set(table), "立場の対応表と再読データの明細の投稿が一致しない")
    return out


def _v2_trend_panels(source):
    m = re.search(r"const panels = (\{.*?\});\n", source, re.S)
    if not m:
        raise ValueError("新デザインの数字が元記録と一致しません: 推移の欄の回ごとの件数（panels）が読めない")
    return json.loads(m.group(1))


def verified_selectors_v2(source, root):
    if V2_MARKER not in source:
        return {}
    from pathlib import Path
    base = _v2_tools()
    _check, _fmt, _numbers, _band, _norm = base._check, base._fmt, base._numbers, base._band, base._norm
    root = Path(root)
    soup = BeautifulSoup(source, "html.parser")
    public = json.loads((root / V2_PUBLIC).read_text(encoding="utf-8"))
    planet = yaml.safe_load((root / V2_PLANET).read_text(encoding="utf-8"))
    reading = json.loads((root / V2_READING).read_text(encoding="utf-8"))
    table = json.loads((root / V2_STANCES).read_text(encoding="utf-8"))["stances"]
    opinions = int(public["opinion_count"])
    stances = list(planet["stances"])
    id_of_label = {}
    for s in stances:
        id_of_label[s["key"]] = s["id"]
        id_of_label[s["label"]] = s["id"]
    reread = _v2_reread(root, planet, table, reading.get("excluded_buckets", {}))
    common = base._strings({k: v for k, v in reading.items() if k != "issues"})
    trend = _v2_trend_panels(source)
    result = {}

    # 冒頭の件数欄：立場の合計（公開JSONの論点×立場を足し直す）・論点別件数・収集件数
    totals = Counter()
    for issue in public["issues"]:
        for s in issue["stances"]:
            totals[s["id"]] += int(s["count"])
    _check(sum(totals.values()) == opinions, "立場の合計が意見数と違う")
    count = soup.select(f"#{V2_COUNT_ID}")
    _check(len(count) == 1, "冒頭の件数欄が1つではない")
    allowed = {opinions, int(public["collected_count"]), *totals.values(), *(int(i["count"]) for i in public["issues"])}
    extra = set(_numbers(count[0])) - allowed
    _check(not extra, f"冒頭の件数欄に説明できない件数 {sorted(extra)}")
    shown = [b.get_text() for b in count[0].select(".bko-stance__list small")]
    _check(shown == [f"{_fmt(totals[s['id']])}件" for s in stances], "冒頭の立場の件数の並び")
    result[f"#{V2_COUNT_ID}"] = f"{V2_PUBLIC} / collected_count・opinion_count・issues[].count・issues[].stances の合計"

    for issue in public["issues"]:
        iid, label, n = issue["id"], issue["label"], int(issue["count"])
        icfg = reading["issues"].get(iid, {})
        panel = soup.find(id="issue-" + iid)
        _check(panel is not None, f"論点 {iid} の欄が無い")
        _check(panel.select_one(".fr-count b").get_text() == _fmt(n), f"{iid} の件数")
        shown = _norm(panel.get_text())
        allowed = {n, opinions}
        by = {s["id"]: int(s["count"]) for s in issue["stances"]}
        _check(sum(by.values()) == n, f"{iid} の立場の合計")
        head = panel.select_one(".fr-head-stance")
        _check(head is not None, f"{iid} の見出しの立場の帯が無い")
        _band(head.select_one(".fr-band"), stances, by, iid + " の見出し")
        _check([b.get_text() for b in head.select(".fr-stance-list b")] == [_fmt(by[s["id"]]) for s in stances],
               f"{iid} の見出しの立場の一覧")
        block = panel.select_one(".fr-stance")
        if block is not None:
            _band(block.select_one(".fr-band"), stances, by, iid)
            _check([b.get_text() for b in block.select(".fr-stance-list b")] == [_fmt(by[s["id"]]) for s in stances],
                   f"{iid} の立場の一覧")
        allowed.update(by.values())
        rr = reread.get(label)
        if rr:
            for bid, bucket in rr["buckets"].items():
                items = [i for i in rr["items"] if i["bucket"] == bid]
                _check(len(items) == int(bucket["count"]), f"{iid} の理由 {bid} の集計と明細")
                li = panel.select_one(f'li.fr-reason[data-reason="{bid}"]')
                _check(li is not None, f"{iid} の理由 {bid} の行が無い")
                _check(li.select_one(".fr-reason-n b").get_text() == _fmt(len(items)), f"{iid} の理由 {bid}（期待 {len(items)}）")
                allowed.add(len(items))
                detail = panel.select_one(f'article.fr-reason-detail[data-reason="{bid}"]')
                if detail is None:  # 完成扱いでない論点は理由の説明を出さない
                    continue
                _check(_fmt(len(items)) + "件" in detail.select_one(".fr-eyebrow").get_text(),
                       f"{iid} の理由 {bid} の説明の件数（期待 {len(items)}）")
                _check(all(i.get("stance") in id_of_label for i in items), f"{iid} の理由 {bid} の明細に立場が無い")
                per = Counter(id_of_label[i["stance"]] for i in items)
                line = detail.select_one(".fr-reason-stance")
                _check(line is not None, f"{iid} の理由 {bid} の立場の内訳が無い")
                _band(line.select_one(".fr-mini"), stances, per, f"{iid} の理由 {bid}")
                words = "・".join(f'{s["label"]}{_fmt(per.get(s["id"], 0))}' for s in stances)
                _check(words in line.get_text(), f"{iid} の理由 {bid} の立場の内訳の文（期待「{words}」）")
                allowed.update(per.get(s["id"], 0) for s in stances)
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
        for claim in public["claim_verification"]["claims"]:
            if iid in claim["issue_ids"]:
                node = panel.select_one(f'[data-claim="{claim["id"]}"]')
                _check(node is not None and _fmt(int(claim["matched_post_count"])) + "件" in node.get_text(),
                       f"{iid} の主張 {claim['id']} の投稿数")
                allowed.add(int(claim["matched_post_count"]))
                allowed |= base._confirmed_numbers([claim["claim"], claim["finding"]], _norm(node.get_text()))
        overrides = reading.get("sunk_issue_overrides", {})
        sunk_here = [x for x in public["ocean_layer"]["sunk_continents"]
                     if (x.get("nearest_issue_id") or overrides.get(x["id"])) == iid]
        for sunk in sunk_here:
            node = panel.select_one(f'[data-sunk="{sunk["id"]}"]')
            _check(node is not None, f"{iid} の資料にしかない話 {sunk['id']} が無い")
            _check(all(_norm(x) in _norm(node.get_text()) for x in base._note_parts(sunk["sns_note"])),
                   f"{iid} の資料にしかない話 {sunk['id']} の検索記録")
            allowed.update({int(sunk["sns_base"]), int(sunk["sns_count"])})
            allowed |= base._confirmed_numbers([*base._note_parts(sunk["sns_note"]), sunk["life_impact"], sunk["topic"]],
                                               _norm(node.get_text()))
        if len(sunk_here) >= 2:
            allowed.add(len(sunk_here))
        veins_here = [v for v in public["ocean_layer"].get("veins", []) if iid in v["issue_ids"]]
        for vein in veins_here:
            node = panel.select_one(f'[data-vein="{vein["id"]}"]')
            _check(node is not None, f"{iid} の重なる心配 {vein['id']} が無い")
            sides = "・".join(f'{x["stance_label"]}{_fmt(int(x["post_count"]))}件' for x in vein["sides"])
            _check(sides in node.get_text(), f"{iid} の重なる心配 {vein['id']} の読んだ投稿の数")
            allowed.update(int(x["post_count"]) for x in vein["sides"])
            allowed |= base._confirmed_numbers([vein["shared_concern"], vein["diverging_reason"]], _norm(node.get_text()))
        if len(veins_here) >= 2:
            allowed.add(len(veins_here))
        # ひと目で見る、この論点の推移：折れ線の最初と最新の回の件数は、同じページの「意見の推移」（panels.issue）と一致すること
        glance = panel.select_one(".fr-glance[data-glance]")
        if glance is not None and label in trend["issue"]["labels"]:
            j = trend["issue"]["labels"].index(label)
            counts = {int(r["c"][j]) for r in trend["issue"]["rounds"]}
            extra = set(_numbers(glance.select_one(".fr-glance-chart"))) - counts
            _check(not extra, f"{iid} のひと目の折れ線に、推移の欄に無い件数 {sorted(extra)}")
            allowed |= counts
            allowed.add(len(trend["issue"]["rounds"]))
        allowed |= base._confirmed_numbers(base._strings(icfg) + common, shown)
        allowed.add(len(icfg.get("posts", {}).get("items", [])))
        extra = set(_numbers(panel)) - allowed
        _check(not extra, f"{iid} の欄に説明できない件数 {sorted(extra)}")
        result["#issue-" + iid] = f"{V2_PUBLIC} / 再読データ3ファイル（明細の数え直し）/ {V2_STANCES} / {V2_READING}（{iid}）"

    note = soup.select_one("#cap-trend .cap-trend-note")
    if note is not None:
        rounds = trend["stance"]["rounds"]
        lo, hi = min(int(r["n"]) for r in rounds), max(int(r["n"]) for r in rounds)
        _check(f"{_fmt(lo)}〜{_fmt(hi)}件" in note.get_text() or f"{lo}〜{hi}件" in note.get_text(),
               f"推移の要約の件数の幅（期待 {lo}〜{hi}件）")
        _check(set(_numbers(note)) <= {lo, hi}, "推移の要約の注記に説明できない件数")
        result["#cap-trend .cap-trend-note"] = "意見の推移（TREND_CARD）の panels.stance.rounds[].n の最小と最大"
    return result


def verify_glance_v2(source, root, sample_file=None):
    """論点ごとの「ひと目で見る、この論点の推移」の折れ線（PC用・375px用）を、非公開正典を収集日別・論点別に数え直した値と照合する。"""
    if V2_MARKER not in source:
        return {}
    from scripts.trend_count_provenance import _labels, _trend_rounds
    from scripts.bukatsu_redesign.glance_chart import annotated_graph
    s = BeautifulSoup(source, "html.parser")
    labels = _labels("bukatsu-chiiki")["issue"]
    actual = _trend_rounds("bukatsu-chiiki", root, "main_issue", labels, "issue", sample_file)
    rounds = [{"d": day, "n": n, "v": v, "c": c} for day, (n, v, c) in sorted(actual.items())]
    boxes = [b for b in s.select(".fr-glance[data-glance]") if b.select_one(".fr-glance-chart svg")]
    if sorted(b["data-glance"] for b in boxes) != sorted(labels):
        raise ValueError("ひと目の折れ線の論点が推移の論点と一致しません")
    for box in boxes:
        name = box["data-glance"]
        j = labels.index(name)
        for mobile, cls in ((False, "glance-chart-desktop"), (True, "glance-chart-mobile")):
            expected = BeautifulSoup(annotated_graph(name, rounds, j, mobile), "html.parser").svg
            if str(box.select_one("svg." + cls)) != str(expected):
                raise ValueError("ひと目の折れ線が正典の独立再集計と一致しません: " + name)
    return {"glance-chart-desktop": "非公開正典を収集日別・論点別に再集計してSVGと照合",
            "glance-chart-mobile": "非公開正典を収集日別・論点別に再集計してSVGと照合"}
