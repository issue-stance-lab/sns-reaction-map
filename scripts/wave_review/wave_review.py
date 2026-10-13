#!/usr/bin/env python3
"""定期収集の今回分を、読み手の伏せ読み → Kimi分類との突き合わせ → 編集担当の確定 → 記録へ反映する（テーマ共通）。

使い方（<stage> は .staging/refresh/<topic>/<run-id>、<work> は作業用フォルダー）:
  python3 scripts/wave_review/wave_review.py batches  --topic T --stage S --work W [--batch-size 55]
  python3 scripts/wave_review/wave_review.py compare  --topic T --stage S --work W
  python3 scripts/wave_review/wave_review.py decide   --topic T --stage S --work W --decisions W/decisions.json
  python3 scripts/wave_review/wave_review.py apply    --topic T --stage S --work W --date YYYY-MM-DD
  python3 scripts/wave_review/wave_review.py fill     --topic T --stage S --work W --date YYYY-MM-DD
  python3 scripts/wave_review/wave_review.py sunk-check --topic T --stage S --work W --date YYYY-MM-DD

手順の全体は .claude/skills/theme-refresh/SKILL.md と DATA_REFRESH.md「新ルールの本文確認工程」を見ること。
自転車の青切符は本文確認記録の形式が独自（review-plan.json）なので bike_plan.py を使う。

出力（apply）:
  data/verification/<topic>-wave-review-<YYYYMMDD>.json  … 候補への補正（adapter の review_candidate が読む）
  quality/reviews/<date>-<topic>-wave-reading.json        … 読了証拠（本文なし）。new_issue_check を含む
  専用再読ファイル（configs/planet/<topic>.yaml の sub_issues.file）… 今回の意見の理由区分を追加
  data/verification/reread/<topic>.json                    … 再読共通台帳があるテーマは今回分を登録
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
JST = timezone(timedelta(hours=9))
REVIEWER = "Claude Fable 5.1（編集担当）＋Claude Sonnet 5.5 読み手2名（自動分類を伏せて本文判定）"
EXCLUDE_KINDS = ("not_opinion_candidate", "possibly_off_topic", "undecidable")
RISK_WORDS = ("排外", "中傷", "根拠のない", "陰謀", "罵倒", "代表投稿に使わない", "署名", "定型文")
NEW_ISSUE_RULE = "その他が今回の意見の5%超、または同じ趣旨が20件以上で新論点候補として検討"


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(text: str) -> str:
    return str(text).replace("\tSTART\t", "").replace("\tEND\t", "")


def dig(data, path):
    for key in path:
        data = data[key]
    return data


def method_text(date: str) -> str:
    return (f"{date} 定期収集（10/9の新ルール・新論点チェック付き）: 今回の新規投稿全件を、読み手2名が自動分類を見ずに本文で"
            "意見判定・論点・立場・理由区分・要約・新論点候補を付け、読み手どうしとKimiの自動分類を突き合わせた。"
            "食い違いは編集担当が本文を読んで確定。判断できない投稿は意見外として残す。意見外も本文確認済み。")


class Theme:
    """planet 設定と専用再読ファイルの置き方（入れ子／平坦、tweet_id／post_key）を読む。"""

    def __init__(self, topic: str):
        self.topic = topic
        self.cfg = yaml.safe_load((ROOT / "configs/planet" / f"{topic}.yaml").read_text(encoding="utf-8"))
        self.issues = [i["key"] for i in self.cfg["issues"]]
        self.stances = [s["key"] for s in self.cfg["stances"]]
        self.neutral = next((s for s in self.stances if "中立" in s or "どちらでもない" in s), self.stances[-1])
        self.sub = self.cfg.get("sub_issues") or {}
        # 専用再読ファイル（論点ごとに別ファイルのテーマもある）
        self.files: dict[str, dict] = {}
        for spec in self.sub.values():
            if spec["file"] not in self.files:
                self.files[spec["file"]] = json.loads((ROOT / spec["file"]).read_text(encoding="utf-8"))
        self.reread_path = ROOT / next(iter(self.files)) if len(self.files) == 1 else None
        self.reread = self.files[next(iter(self.files))] if len(self.files) == 1 else None
        guide = ROOT / "configs/wave_review" / f"{topic}.yaml"
        self.guide = yaml.safe_load(guide.read_text(encoding="utf-8")) if guide.exists() else {}
        themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
        self.sample_file = ROOT / themes[topic]["sample_file"]

    def data_of(self, issue: str) -> dict:
        return self.files[self.sub[issue]["file"]]

    def buckets(self, issue: str) -> dict[str, str]:
        if issue not in self.sub:
            return {}
        raw = dig(self.data_of(issue), self.sub[issue]["path"])
        return {k: (v["label"] if isinstance(v, dict) else str(v)) for k, v in raw.items()}

    def bucket_definitions(self) -> dict[str, dict[str, str]]:
        return {issue: self.buckets(issue) for issue in self.issues if issue in self.sub}

    def items_of(self, issue: str) -> list:
        spec = self.sub[issue]
        return dig(self.data_of(issue), spec.get("items_path", spec["path"][:-1] + ["items"]))

    def item_style(self, issue: str) -> set[str]:
        items = self.items_of(issue)
        keys: set[str] = set()
        for item in items[:30]:
            keys |= set(item)
        return keys

    def have(self) -> set[str]:
        """既に専用ファイルにある投稿（tweet_id または post_key）。"""
        found: set[str] = set()
        for issue in self.sub:
            spec = self.sub[issue]
            for item in self.items_of(issue):
                found.add(str(item.get("tweet_id") or item.get("post_key")))
            parent = dig(self.data_of(issue), spec["path"][:-1])
            if isinstance(parent, dict):
                for item in parent.get("excluded_items", []) or []:
                    found.add(str(item.get("tweet_id") or item.get("post_key")))
        return found


def load_stage(stage: Path):
    wave = json.loads((stage / "classified-wave.json").read_text(encoding="utf-8"))
    new = json.loads((stage / "new-only.json").read_text(encoding="utf-8"))
    if [str(r["tweet_id"]) for r in wave] != [str(r["tweet_id"]) for r in new]:
        raise SystemExit("classified-wave.json と new-only.json の投稿順・集合が一致しません")
    return wave


def render_prompt(theme: Theme, batch_in: Path, batch_out: Path) -> str:
    template = (ROOT / "scripts/wave_review/reader_prompt.md").read_text(encoding="utf-8")
    g = theme.guide
    issue_guide = g.get("issue_guide") or "／".join(theme.issues)
    stance_guide = g.get("stance_guide") or "／".join(theme.stances)
    bucket_issues = "・".join(i for i in theme.issues if i in theme.sub) or "（理由区分のある論点はありません）"
    named = [i for i in theme.issues if i != "その他"]
    return (template.replace("{THEME_TITLE}", g.get("title") or theme.cfg.get("title", theme.topic))
            .replace("{INPUT}", str(batch_in)).replace("{OUTPUT}", str(batch_out))
            .replace("{N_ISSUES}", str(len(theme.issues))).replace("{N_STANCES}", str(len(theme.stances)))
            .replace("{BUCKET_ISSUES}", bucket_issues)
            .replace("{OPINION_GUIDE}", g.get("opinion_guide") or "投稿者自身の、このテーマへの評価・感情・主張が本文から読めるなら true。")
            .replace("{ISSUE_GUIDE}", issue_guide).replace("{STANCE_GUIDE}", stance_guide)
            .replace("{NAMED_ISSUES}", "／".join(named)).replace("{NEW_ISSUE_EXAMPLES}", g.get("new_issue_examples") or "「◯◯の是非」など")
            .replace("{EXTRA_INSTRUCTIONS}", g.get("extra_instructions") or "").replace("{EXTRA_FIELDS}", g.get("extra_fields") or ""))


def cmd_batches(a, theme: Theme):
    stage = Path(a.stage).resolve(); work = Path(a.work).resolve(); work.mkdir(parents=True, exist_ok=True)
    new = json.loads((stage / "new-only.json").read_text(encoding="utf-8"))
    posts = [{"tweet_id": str(r["tweet_id"]), "text": clean(r["text"])} for r in new]
    n = max(1, -(-len(posts) // a.batch_size)); size = -(-len(posts) // n)
    for k in range(n):
        chunk = posts[k * size:(k + 1) * size]
        name = f"batch-{k + 1}"
        (work / f"{name}.json").write_text(json.dumps({
            "topic": theme.topic, "batch": name, "issues": theme.issues, "stances": theme.stances,
            "bucket_definitions": theme.bucket_definitions(), "posts": chunk}, ensure_ascii=False, indent=1), encoding="utf-8")
        for reader in ("A", "B"):
            (work / f"prompt-{name}-{reader}.md").write_text(
                render_prompt(theme, work / f"{name}.json", work / f"out-{name}-{reader}.json"), encoding="utf-8")
        print(f"{name}: {len(chunk)}件 → {work / (name + '.json')}（読み手A/B用の指示文 prompt-{name}-A.md / -B.md）")
    if not theme.guide:
        print(f"注意: configs/wave_review/{theme.topic}.yaml が無いため、論点・立場の説明は名前だけです。初回に作ること。")


def load_readers(work: Path, tag: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for f in sorted(work.glob(f"out-batch-*-{tag}.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            out[str(r["tweet_id"])] = r
    return out


def key_of(r: dict):
    return (bool(r["is_opinion"]), r["main_issue"] if r["is_opinion"] else None, r["stance"] if r["is_opinion"] else None)


def kimi_key(c: dict):
    op = bool(c.get("is_opinion"))
    return (op, c.get("main_issue") if op else None, c.get("stance") if op else None)


def cmd_compare(a, theme: Theme):
    stage = Path(a.stage).resolve(); work = Path(a.work).resolve()
    wave = load_stage(stage)
    A, B = load_readers(work, "A"), load_readers(work, "B")
    ids = {str(r["tweet_id"]) for r in wave}
    if set(A) != ids or set(B) != ids:
        raise SystemExit(f"読み手の出力が揃っていません: A={len(A)} B={len(B)} 今回分={len(ids)}")
    adj, lines, n_agree = [], [], 0
    for idx, row in enumerate(wave):
        tid = str(row["tweet_id"]); ra, rb = A[tid], B[tid]; k = row.get("classification") or {}
        agree = key_of(ra) == key_of(rb); n_agree += agree
        bucket = ra.get("bucket") if ra.get("bucket") == rb.get("bucket") else None
        rec = {"index": idx, "tweet_id": tid, "agree": agree,
               "is_opinion": ra["is_opinion"] if agree else None,
               "main_issue": ra["main_issue"] if agree else None,
               "stance": ra["stance"] if agree else None,
               "bucket": bucket if agree else None,
               "bucket_choices": sorted({x for x in (ra.get("bucket"), rb.get("bucket")) if x}),
               "exclude_kind": ra.get("exclude_kind") if agree and not ra["is_opinion"] else None,
               "summary": ra["summary"], "summary_b": rb["summary"],
               "kimi": {kk: k.get(kk) for kk in ("is_opinion", "main_issue", "stance", "risk", "article_usable", "summary", "reason")},
               "new_issue": [x for x in (ra.get("new_issue_candidate"), rb.get("new_issue_candidate")) if x],
               "notes": [x for x in (ra.get("note"), rb.get("note")) if x]}
        adj.append(rec)
        lines.append(
            f"[{idx}] {'AGREE' if agree else 'DIFF '} {tid}\n  TEXT: {clean(row['text'])[:400]}\n"
            f"  A: {ra['is_opinion']}/{ra.get('exclude_kind')}|{ra['main_issue']}|{ra['stance']}|{ra.get('bucket')}|{ra['summary']}|new={ra.get('new_issue_candidate')}|{ra.get('note')}\n"
            f"  B: {rb['is_opinion']}/{rb.get('exclude_kind')}|{rb['main_issue']}|{rb['stance']}|{rb.get('bucket')}|{rb['summary']}|new={rb.get('new_issue_candidate')}|{rb.get('note')}\n"
            f"  K: op={k.get('is_opinion')}|{k.get('main_issue')}|{k.get('stance')}|risk={k.get('risk')}|usable={k.get('article_usable')}|{k.get('summary')}|{k.get('reason')}")
    (work / "adjudicated.json").write_text(json.dumps(adj, ensure_ascii=False, indent=1), encoding="utf-8")
    (work / "compare.txt").write_text("\n".join(lines), encoding="utf-8")
    blocks = {r["index"]: lines[r["index"]] for r in adj}
    review = ["##### DIFF（読み手の食い違い。編集担当が本文を読んで決める）"]
    review += [blocks[r["index"]] + "\n" for r in adj if not r["agree"]]
    review += ["##### BUCKET CONFLICT（意見判定・論点・立場は一致、区分だけ違う）"]
    review += [blocks[r["index"]] + "\n" for r in adj if r["agree"] and r["is_opinion"] and r["main_issue"] in theme.sub and not r["bucket"]]
    review += ["##### KIMI DISAGREES（読み手2名は一致、Kimiだけ違う。読み手の判定を基本に、気になるものだけ見る）"]
    review += [f"[{r['index']}] R: {r['is_opinion']}/{r.get('exclude_kind')}|{r['main_issue']}|{r['stance']}|{r['bucket']} ‖ K: {r['kimi']['is_opinion']}|{r['kimi']['main_issue']}|{r['kimi']['stance']} ‖ {r['summary'][:40]} ‖ {';'.join(r['notes'])[:40]}"
               for r in adj if r["agree"] and kimi_key(r["kimi"]) != key_of({"is_opinion": r["is_opinion"], "main_issue": r["main_issue"], "stance": r["stance"]})]
    (work / "review.txt").write_text("\n".join(review), encoding="utf-8")
    n_bucket = sum(1 for r in adj if r["agree"] and r["is_opinion"] and r["main_issue"] in theme.sub and not r["bucket"])
    n_kimi = sum(1 for r in adj if r["agree"] and kimi_key(r["kimi"]) == key_of({"is_opinion": r["is_opinion"], "main_issue": r["main_issue"], "stance": r["stance"]}))
    print(f"{len(wave)}件 読み手一致 {n_agree} 食い違い {len(wave) - n_agree} / 区分未確定 {n_bucket} / Kimiと一致（読み手一致のうち）{n_kimi}")
    print(f"→ {work / 'review.txt'} を読み、decisions.json に確定を書いて decide を実行する")


def cmd_decide(a, theme: Theme):
    """decisions.json: {"<index>": {...上書き...}, "_normalize": {"読み手の論点名": "統一名"}}。
    上書きに使える項目: is_opinion, main_issue, stance, bucket, exclude_kind, summary, note_add。"""
    work = Path(a.work).resolve()
    adj = json.loads((work / "adjudicated.json").read_text(encoding="utf-8"))
    dec = json.loads(Path(a.decisions).read_text(encoding="utf-8"))
    norm = dec.pop("_normalize", {})
    unknown = set(dec) - {str(r["index"]) for r in adj}
    if unknown:
        raise SystemExit(f"decisions.json に無い index があります: {sorted(unknown)}")
    for r in adj:
        o = dict(dec.get(str(r["index"]), {}))
        if "note_add" in o:
            r["notes"] = (r.get("notes") or []) + [o.pop("note_add")]
        if o.get("is_opinion") is False:
            o.setdefault("main_issue", None); o.setdefault("stance", None); o.setdefault("bucket", None)
            o.setdefault("exclude_kind", "possibly_off_topic")
        if o.get("is_opinion") is True:
            o.setdefault("exclude_kind", None)
        r.update(o)
        if r["is_opinion"] is False and not r.get("exclude_kind"):
            r["exclude_kind"] = "possibly_off_topic"
        cands = [norm.get(x, x) for x in (r.get("new_issue") or [])]
        r["new_issue_final"] = (cands[0] if cands else "") if r["is_opinion"] else ""
        r["notes"] = sorted(set(r.get("notes") or []))
    (work / "adjudicated.json").write_text(json.dumps(adj, ensure_ascii=False, indent=1), encoding="utf-8")
    problems = []
    for r in adj:
        if r["is_opinion"] is None:
            problems.append(f"{r['index']}: 意見判定が未確定"); continue
        if r["is_opinion"]:
            if r["main_issue"] not in theme.issues: problems.append(f"{r['index']}: 論点 {r['main_issue']} が設定にない")
            if r["stance"] not in theme.stances: problems.append(f"{r['index']}: 立場 {r['stance']} が設定にない")
            if r["main_issue"] in theme.sub and r["bucket"] not in theme.buckets(r["main_issue"]):
                problems.append(f"{r['index']}: 区分 {r['bucket']} が論点 {r['main_issue']} にない")
        elif r.get("exclude_kind") not in EXCLUDE_KINDS:
            problems.append(f"{r['index']}: 意見外の種類 {r.get('exclude_kind')} が不正")
    if problems:
        print("未確定・不正:"); [print("  ", p) for p in problems]; raise SystemExit(1)
    print(f"確定済み {len(adj)}件。次は apply")


def finals(theme: Theme, adj: list[dict]):
    out = {}
    for r in adj:
        if r["is_opinion"] is None:
            raise SystemExit(f"index {r['index']} が未確定です。decide を先に実行してください")
        out[r["tweet_id"]] = {
            "is_opinion": bool(r["is_opinion"]),
            "main_issue": r["main_issue"] if r["is_opinion"] else ((r.get("kimi") or {}).get("main_issue") or "その他"),
            "stance": r["stance"] if r["is_opinion"] else theme.neutral,
            "bucket": r["bucket"] if (r["is_opinion"] and r["main_issue"] in theme.sub) else None,
            "summary": r["summary"], "notes": r.get("notes") or [], "new_issue": r.get("new_issue_final", ""),
            "exclude_kind": r.get("exclude_kind") or "", "agree": r["agree"]}
    return out


def cmd_apply(a, theme: Theme):
    stage = Path(a.stage).resolve(); work = Path(a.work).resolve(); date = a.date
    now = datetime.now(JST).replace(microsecond=0)
    wave = load_stage(stage); by_id = {str(r["tweet_id"]): r for r in wave}
    adj = json.loads((work / "adjudicated.json").read_text(encoding="utf-8"))
    fv_all = finals(theme, adj)
    method = method_text(date)
    evidence_rel = Path(f"quality/reviews/{date}-{theme.topic}-wave-reading.json")
    review_rel = Path(f"data/verification/{theme.topic}-wave-review-{date.replace('-', '')}.json")

    overrides, items = [], []
    for tid, fv in fv_all.items():
        c = by_id[tid].get("classification") or {}
        auto = {"is_opinion": bool(c.get("is_opinion")), "main_issue": c.get("main_issue"), "stance": c.get("stance")}
        changes = {k: fv[k] for k in auto if auto[k] != fv[k]}
        note = " ".join(fv["notes"])
        if (("is_opinion" in changes and not fv["is_opinion"]) or any(w in note for w in RISK_WORDS)) and c.get("article_usable") is not False:
            changes["article_usable"] = False
        if changes:
            overrides.append({"tweet_id": tid, "review_reason": (note or ("編集担当が確定" if not fv["agree"] else "読み手2名の本文判定で補正"))[:120],
                              "classification": changes})
        items.append({"tweet_id": tid, "is_opinion": fv["is_opinion"], "main_issue": fv["main_issue"], "stance": fv["stance"],
                      "bucket": fv["bucket"], "exclude_reason": fv["exclude_kind"], "summary": fv["summary"],
                      "reason_sha256": sha(fv["summary"]), "text_sha256": sha(by_id[tid]["text"]),
                      "readers_agreed": fv["agree"], "auto_agreed": auto == {k: fv[k] for k in auto},
                      "new_issue_candidate": fv["new_issue"], "note": "｜".join(fv["notes"] + ["編集担当が確定"])})
    ids = [str(r["tweet_id"]) for r in wave]
    review = {"topic": theme.topic, "run_id": stage.name, "reviewed_at": date, "reviewer": REVIEWER, "method": method,
              "source_sha256": digest(stage / "classified-wave.json"),
              "ids_sha256": sha("\n".join(ids)), "reviewed_count": len(wave), "overrides": overrides}
    (ROOT / review_rel).write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ops = [i for i in items if i["is_opinion"]]
    other = [i for i in ops if i["main_issue"] == "その他"]
    cands = Counter(i["new_issue_candidate"] for i in items if i["new_issue_candidate"])
    check = {"rule": NEW_ISSUE_RULE, "opinions": len(ops), "other_count": len(other),
             "other_share": round(len(other) / max(1, len(ops)), 3), "candidates": dict(cands),
             "candidate_ids": {c: [i["tweet_id"] for i in items if i["new_issue_candidate"] == c] for c in cands}}
    ev = {"theme": theme.topic, "run_id": stage.name, "read_at": now.isoformat(), "method": method, "reviewer_type": "editorial_ai",
          "reviewer": REVIEWER, "count": len(items), "opinions": len(ops), "auto_agreed": sum(i["auto_agreed"] for i in items),
          "readers_agreed": sum(i["readers_agreed"] for i in items), "new_issue_check": check, "items": items}
    (ROOT / evidence_rel).write_text(json.dumps(ev, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"補正 {len(overrides)}件 → {review_rel}")
    print(f"証拠 {len(items)}件（意見 {len(ops)}・読み手一致 {ev['readers_agreed']}・Kimi一致 {ev['auto_agreed']}）→ {evidence_rel}")
    print("新論点チェック:", json.dumps(check, ensure_ascii=False))

    # 専用再読ファイルへ今回の意見の理由区分を追加
    if theme.files:
        have = theme.have(); added = Counter(); touched = set()
        for i in items:
            if not i["is_opinion"] or i["main_issue"] not in theme.sub:
                continue
            tid = i["tweet_id"]; key = sha(tid)
            if tid in have or key in have:
                continue
            spec = theme.sub[i["main_issue"]]
            style = theme.item_style(i["main_issue"])
            itemlist = theme.items_of(i["main_issue"])
            buckets = dig(theme.data_of(i["main_issue"]), spec["path"]); touched.add(spec["file"])
            label = theme.buckets(i["main_issue"])[i["bucket"]]
            row = {}
            if "post_key" in style and "tweet_id" not in style:
                row["post_key"] = key
            else:
                row["tweet_id"] = tid
                if "url" in style: row["url"] = by_id[tid].get("url")
            if "main_issue" in style or spec.get("item_issue_field"): row[spec.get("item_issue_field", "main_issue")] = i["main_issue"]
            if "stance" in style: row["stance"] = i["stance"]
            row["bucket"] = i["bucket"]
            if "bucket_label" in style: row["bucket_label"] = label
            if "summary" in style: row["summary"] = i["summary"]
            if "risk" in style: row["risk"] = (by_id[tid].get("classification") or {}).get("risk", "low")
            if "body_reviewed" in style: row["body_reviewed"] = True
            if "review_kind" in style: row["review_kind"] = "editorial_body_reread"
            if "read_at" in style: row["read_at"] = now.isoformat()
            if "reviewer" in style: row["reviewer"] = REVIEWER
            row["text_sha256"] = i["text_sha256"]
            if "reason_sha256" in style: row["reason_sha256"] = i["reason_sha256"]
            itemlist.append(row)
            if isinstance(buckets[i["bucket"]], dict) and "count" in buckets[i["bucket"]]:
                buckets[i["bucket"]]["count"] += 1
            added[i["main_issue"]] += 1
        for rel in (touched or set(theme.files)):
            data = theme.files[rel]
            ra = str(data.get("read_at", ""))
            data["read_at"] = now.isoformat() if "T" in ra else f"{ra} / {date}（定期収集分）"
            data[f"wave_{date.replace('-', '_')}"] = {"added": sum(n for issue, n in added.items() if theme.sub[issue]["file"] == rel),
                                                       "evidence": str(evidence_rel), "evidence_sha256": digest(ROOT / evidence_rel)}
            (ROOT / rel).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("理由区分の追加:", dict(added), "→", ", ".join(sorted(touched or theme.files)))
        for issue in theme.issues:
            if issue in theme.sub:
                continue
            n = sum(1 for i in ops if i["main_issue"] == issue)
            if n:
                print(f"  （論点「{issue}」は理由区分の設定が無いので {n}件は専用ファイルに入れない）")

    # 再読共通台帳（あるテーマだけ）: 候補が無いとまだ登録できないので、register で別に行う
    registry = ROOT / "data/verification/reread" / f"{theme.topic}.json"
    if registry.exists():
        print(f"次: --prepare-promotion で候補を作ってから  wave_review.py register ... を実行（{registry.relative_to(ROOT)}）")
    print("立場:", dict(Counter(i["stance"] for i in ops)), "論点:", dict(Counter(i["main_issue"] for i in ops)))


def cmd_register(a, theme: Theme):
    """再読共通台帳へ今回分（意見・意見外とも）を verified で登録し、専用ファイルの指紋を更新する。候補（cumulative-candidate.json）が必要。"""
    stage = Path(a.stage).resolve(); date = a.date
    sys.path.insert(0, str(ROOT))
    from scripts.reread_registry import create_target, record_reviews  # type: ignore
    evidence_rel = Path(f"quality/reviews/{date}-{theme.topic}-wave-reading.json")
    ev = json.loads((ROOT / evidence_rel).read_text(encoding="utf-8")); ev_sha = digest(ROOT / evidence_rel)
    cand = json.loads((stage / "cumulative-candidate.json").read_text(encoding="utf-8")); by_id = {str(r["tweet_id"]): r for r in cand}
    mp = ROOT / "data/verification/reread" / f"{theme.topic}.json"; m = json.loads(mp.read_text(encoding="utf-8"))
    items = {i["tweet_id"]: i for i in ev["items"]}
    for tid, it in items.items():
        if sha(by_id[tid]["text"]) != it["text_sha256"]:
            raise SystemExit(f"候補の本文が読了証拠と一致しません: {tid}")
    existing = {r["post_key"] for r in m["records"]}
    selected = sorted(sha(t) for t in items if sha(t) not in existing or True)
    reviews = [{"post_key": sha(t), "review": {
        "kind": "editorial_body_reread", "evidence_quality": "verified", "read_at": ev["read_at"], "reviewer_type": "editorial_ai",
        "reviewer": ev["reviewer"], "method_version": "sha256:" + sha(ev["method"]), "text_sha256": it["text_sha256"],
        "reason_sha256": it["reason_sha256"], "source_file": str(evidence_rel), "source_sha256": ev_sha,
        "bucket": it["bucket"] or ("opinion" if it["is_opinion"] else "non-opinion")}} for t, it in items.items()]
    upd = record_reviews(m, create_target(m, selected, current_rows=cand), reviews, current_rows=cand)
    for rel in theme.files:
        upd["sources"][rel] = digest(ROOT / rel)
    upd["sources"][str(evidence_rel)] = ev_sha
    upd.setdefault("source_date_labels", {})[str(evidence_rel)] = date
    mp.write_text(json.dumps(upd, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"再読共通台帳 {len(m['records'])} → {len(upd['records'])}件（{mp.relative_to(ROOT)}）")


def cmd_fill(a, theme: Theme):
    stage = Path(a.stage).resolve(); date = a.date
    now = datetime.now(JST).replace(microsecond=0)
    evidence_rel = Path(f"quality/reviews/{date}-{theme.topic}-wave-reading.json")
    ev = json.loads((ROOT / evidence_rel).read_text(encoding="utf-8")); ev_sha = digest(ROOT / evidence_rel)
    its = {i["tweet_id"]: i for i in ev["items"]}
    proof_path = stage / "editorial-completion.json"; proof = json.loads(proof_path.read_text(encoding="utf-8"))
    cand = {sha(str(r["tweet_id"])): r for r in json.loads((stage / "cumulative-candidate.json").read_text(encoding="utf-8"))}
    k2t = {sha(t): t for t in its}
    for rec in proof["records"]:
        tid = k2t.get(rec["post_key"])
        if not tid:
            raise SystemExit(f"今回分以外が完了記録の対象に入っています: {rec['post_key'][:12]}（既存投稿の分類が変わった？）")
        row = cand[rec["post_key"]]; it = its[tid]
        if sha(row["text"]) != it["text_sha256"]:
            raise SystemExit(f"候補の本文が読了証拠と一致しません: {tid}")
        rec["review"] = {"kind": "editorial_body_reread", "evidence_quality": "verified", "read_at": now.isoformat(),
                         "reviewer_type": "editorial_ai", "reviewer": ev["reviewer"], "method_version": "sha256:" + sha(ev["method"]),
                         "text_sha256": it["text_sha256"], "reason_sha256": it["reason_sha256"],
                         "source_file": str(evidence_rel), "source_sha256": ev_sha,
                         "bucket": it["bucket"] or ("opinion" if it["is_opinion"] else "non-opinion")}
    proof_path.write_text(json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"完了記録の review を埋めた: {len(proof['records'])}件 → 次は refresh_completion.py check")


def cmd_sunk_check(a, theme: Theme):
    """「資料にしかない話」の条件語を今回の意見に再実行し、候補を本文つきで出す（書き換えはしない）。"""
    stage = Path(a.stage).resolve(); date = a.date
    path = ROOT / "data/verification" / f"{theme.topic}-sunk-continents.json"
    if not path.exists():
        print("このテーマには資料にしかない話の記録がありません"); return
    S = json.loads(path.read_text(encoding="utf-8"))
    ev = json.loads((ROOT / f"quality/reviews/{date}-{theme.topic}-wave-reading.json").read_text(encoding="utf-8"))
    wave = {str(r["tweet_id"]): r for r in load_stage(stage)}
    ops = [i for i in ev["items"] if i["is_opinion"]]
    print(f"今回の意見 {len(ops)}件")
    for it in S["items"]:
        mr = it.get("match_rule") or {}
        if mr.get("type") != "regex" or not mr.get("pattern"):
            print(f"== {it['id']}: type={mr.get('type')}（正規表現でないので手で確認）"); continue
        pat = re.compile(mr["pattern"], re.I); hits = []
        for i in ops:
            t = clean(wave[i["tweet_id"]]["text"]); m = pat.search(t)
            if m: hits.append((i["tweet_id"], m.group(0), t[:200].replace("\n", " ")))
        print(f"== {it['id']} 母数 {it.get('sns_base')} 確認日 {it.get('checked_on')} 候補 {len(hits)}")
        for h in hits: print(f"   {h[0]} | {h[1]} | {h[2]}")
    print("→ 候補を読み、該当なら sns_count・machine_hits、該当しなければ excluded に why を足す。全件で sns_base を今回の意見数へ、checked_on を今回の日付へ。")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["batches", "compare", "decide", "apply", "register", "fill", "sunk-check"])
    ap.add_argument("--topic", required=True); ap.add_argument("--stage", required=True); ap.add_argument("--work", required=True)
    ap.add_argument("--date"); ap.add_argument("--decisions"); ap.add_argument("--batch-size", type=int, default=55)
    a = ap.parse_args()
    if a.command in ("apply", "register", "fill", "sunk-check") and not a.date:
        ap.error("--date YYYY-MM-DD が必要です")
    if a.command == "decide" and not a.decisions:
        ap.error("--decisions が必要です")
    theme = Theme(a.topic)
    {"batches": cmd_batches, "compare": cmd_compare, "decide": cmd_decide, "apply": cmd_apply,
     "register": cmd_register, "fill": cmd_fill, "sunk-check": cmd_sunk_check}[a.command](a, theme)


if __name__ == "__main__":
    main()
