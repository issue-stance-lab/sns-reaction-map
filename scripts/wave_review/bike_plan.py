#!/usr/bin/env python3
"""自転車の青切符だけ: 確定済みの adjudicated.json（wave_review.py compare → decide）から review-plan.json と読了証拠を作る。

  python3 scripts/wave_review/bike_plan.py --stage S --work W --date YYYY-MM-DD

このあと:
  python3 scripts/build_bike_refresh_candidate.py --stage S --plan S/review-plan.json --update data/bike-blue-ticket_editorial-updates/YYYYMMDD.json
  python3 scripts/refresh_topic.py --topic bike-blue-ticket --date D --run-id <run-id> --resume --prepare-promotion ...
読み手の出力には intensity（configs/wave_review/bike-blue-ticket.yaml の extra_instructions）が要る。
強度が読み手で割れたものは decisions.json の "intensity" で確定する（decide は未知の項目もそのまま上書きする）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JST = timezone(timedelta(hours=9))
TOPIC = "bike-blue-ticket"
ISSUES = ["取締り強化賛成", "インフラ整備優先", "車道走行への不安", "免許制要求", "ルール曖昧・不信", "その他"]
STANCES = ("賛成（取締り強化支持）", "反対（インフラ・制度優先）", "どちらでもない")
# 読み手は configs/planet の立場キー（コード名）で出力する。計画ファイルには表示名を書く
STANCE_BY_KEY = {"enforcement_support": STANCES[0], "infrastructure_first": STANCES[1], "neutral": STANCES[2]}
OPP = {"strict", "scope", "place", "distrust", "abolish"}
CONCERN = {"not_opinion_candidate": "not_opinion_candidate", "possibly_off_topic": "possibly_off_topic", "undecidable": "context_missing"}
REASONS = {"not_opinion_candidate": "ニュースや告知・記事の共有、他者の発言の紹介で、投稿者自身の青切符制度への評価が本文から読み取れないため意見サンプルとして採用しない。",
           "possibly_off_topic": "主題が自動車の取締り・飲酒運転の広報・一般の交通安全など別のテーマで、自転車の青切符制度への評価が本文にないため採用しない。",
           "undecidable": "本文だけでは何に対する評価か、または青切符制度への立場を確定できないため、10/9の新ルールに従い保留にせず意見外として記録する。"}
REVIEWER = "Claude Fable 5.1（編集担当）＋Claude Sonnet 5.5 読み手2名（自動分類を伏せて本文判定）"
sha = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", required=True); ap.add_argument("--work", required=True); ap.add_argument("--date", required=True)
    a = ap.parse_args(); stage = Path(a.stage).resolve(); work = Path(a.work).resolve(); date = a.date
    now = datetime.now(JST).replace(microsecond=0)
    wave = json.loads((stage / "classified-wave.json").read_text(encoding="utf-8"))
    adj = json.loads((work / "adjudicated.json").read_text(encoding="utf-8"))
    readers = {}
    for tag in ("A", "B"):
        for f in sorted(work.glob(f"out-batch-*-{tag}.json")):
            for r in json.loads(f.read_text(encoding="utf-8")):
                readers.setdefault(str(r["tweet_id"]), {})[tag] = r
    rr = json.loads((ROOT / "data/bike-blue-ticket_issues-reread.json").read_text(encoding="utf-8"))
    buckets = {i: set(rr[i]["buckets"]) for i in ISSUES}
    sunk = json.loads((ROOT / "data/verification/bike-blue-ticket-sunk-continents.json").read_text(encoding="utf-8"))
    hits = defaultdict(list); adopt = []; groups = defaultdict(list); items = []
    for r in adj:
        row = wave[r["index"]]; text = str(row["text"]); tid = r["tweet_id"]
        r["stance"] = STANCE_BY_KEY.get(r["stance"], r["stance"])
        if r["is_opinion"] is None:
            raise SystemExit(f"index {r['index']} が未確定です")
        if r["is_opinion"]:
            if r["main_issue"] not in ISSUES or r["stance"] not in STANCES:
                raise SystemExit(f"index {r['index']}: 論点・立場が不正")
            if r["bucket"] not in buckets[r["main_issue"]]:
                raise SystemExit(f"index {r['index']}: 区分 {r['bucket']} が論点にない")
            if r["stance"] == STANCES[1] and r["bucket"] not in OPP:
                raise SystemExit(f"index {r['index']}: 反対の投稿は5区分（{sorted(OPP)}）から選ぶ")
            ra, rb = readers.get(tid, {}).get("A", {}), readers.get(tid, {}).get("B", {})
            intensity = r.get("intensity") or (ra.get("intensity") if ra.get("intensity") == rb.get("intensity") else None)
            if intensity not in ("low", "medium", "high"):
                raise SystemExit(f"index {r['index']}: 強度が未確定（decisions.json で intensity を指定）")
            notes = " ".join(r.get("notes") or []); k = r.get("kimi") or {}
            flagged = any(w in notes for w in ("中傷", "排外", "罵倒", "陰謀", "定型文", "署名"))
            risk = "high" if any(w in notes for w in ("中傷", "排外", "罵倒", "陰謀")) else (k.get("risk") if k.get("risk") in ("low", "medium", "high") else "medium")
            desc = {STANCES[0]: "制度・取締りへの支持", STANCES[1]: "制度への反対または整備優先の主張", STANCES[2]: "賛否を明示しない意見"}[r["stance"]]
            adopt.append({"index": r["index"], "main_issue": r["main_issue"], "stance": r["stance"], "bucket": r["bucket"], "intensity": intensity,
                          "intensity_reason": f"本文の表現から{intensity}と判断。読み手2名の独立判定と編集担当の確認による。",
                          "summary": r["summary"][:80], "risk": risk, "article_usable": bool(k.get("article_usable")) and not flagged and intensity != "high",
                          "reason": f"{r['summary']}。本文から青切符制度への{desc}が読める。"})
            for it in sunk["items"]:
                if re.search(it["match_rule"]["pattern"], text.replace("\tSTART\t", "").replace("\tEND\t", ""), re.I):
                    hits[it["id"]].append(tid)
        else:
            groups[r.get("exclude_kind") or "possibly_off_topic"].append(r["index"])
        items.append({"tweet_id": tid, "is_opinion": bool(r["is_opinion"]), "main_issue": r["main_issue"] if r["is_opinion"] else "その他",
                      "stance": r["stance"] if r["is_opinion"] else STANCES[2], "bucket": r["bucket"] if r["is_opinion"] else None,
                      "exclude_reason": CONCERN.get(r.get("exclude_kind") or "", ""), "summary": r["summary"], "reason_sha256": sha(r["summary"]),
                      "text_sha256": sha(text), "readers_agreed": r["agree"],
                      "auto_agreed": bool(r["is_opinion"] and r["main_issue"] == (r.get("kimi") or {}).get("main_issue") and r["stance"] == (r.get("kimi") or {}).get("stance")),
                      "new_issue_candidate": r.get("new_issue_final", ""), "note": "｜".join((r.get("notes") or []) + ["編集担当が確定"])})
    plan = {"reviewer": REVIEWER, "reviewer_type": "editorial_ai", "finalized_by": "Claude Fable 5.1（編集担当）",
            "read_at": now.isoformat(), "finalized_at": now.isoformat(), "method": "bike-k27-editorial-body-review-v2-blind-readers",
            "adopt": adopt, "exclude_groups": [{"concern": CONCERN[k], "reason": REASONS[k], "indices": v} for k, v in groups.items()],
            "defer_prior_holds": [], "opposition_bucket_overrides": [],
            "tide_display_decision": "show_without_classifier_version_note", "owner_confirmed_at": "2026-09-28",
            "unspoken_issue_review": {"reviewed_at": date, "reviewer": "editorial_ai", "scope": "all_newly_adopted_opinions",
                                      "reviewed_opinion_count": len(adopt), "topic_ids": [i["id"] for i in sunk["items"]],
                                      "result": "no_new_mentions" if not hits else "new_mentions_found", "regex_hits": dict(hits)}}
    (stage / "review-plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ops = [i for i in items if i["is_opinion"]]; other = [i for i in ops if i["main_issue"] == "その他"]
    cands = Counter(i["new_issue_candidate"] for i in items if i["new_issue_candidate"])
    check = {"rule": "その他が今回の意見の5%超、または同じ趣旨が20件以上で新論点候補として検討", "opinions": len(ops), "other_count": len(other),
             "other_share": round(len(other) / max(1, len(ops)), 3), "candidates": dict(cands),
             "candidate_ids": {c: [i["tweet_id"] for i in items if i["new_issue_candidate"] == c] for c in cands}}
    ev = {"theme": TOPIC, "run_id": stage.name, "read_at": now.isoformat(), "method": plan["method"], "reviewer_type": "editorial_ai",
          "reviewer": REVIEWER, "count": len(items), "opinions": len(ops), "auto_agreed": sum(i["auto_agreed"] for i in items),
          "readers_agreed": sum(i["readers_agreed"] for i in items), "new_issue_check": check, "items": items}
    out = ROOT / f"quality/reviews/{date}-{TOPIC}-wave-reading.json"
    out.write_text(json.dumps(ev, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"review-plan.json: 採用 {len(adopt)} / 意見外 {dict((k, len(v)) for k, v in groups.items())} / 資料にしかない話の一致 {dict(hits) or 'なし'}")
    print("新論点チェック:", json.dumps(check, ensure_ascii=False)); print(f"読了証拠 → {out.relative_to(ROOT)}")
    if hits:
        print("注意: 資料にしかない話に一致候補あり。本文を読んで machine_hits / excluded を直し、result を確定すること（adapter は一致があると止まる）")


if __name__ == "__main__":
    main()
