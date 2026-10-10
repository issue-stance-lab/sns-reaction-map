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
