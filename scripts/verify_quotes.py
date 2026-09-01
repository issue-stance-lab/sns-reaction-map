#!/usr/bin/env python3
"""引用文照合: 一次資料メモ中の会議録引用「...」を、国会会議録APIの発言原文と機械的に突き合わせる。
LLMは使わない。URLに含まれるminId(=issueID)の発言をすべて取得し、部分文字列として一致するかを判定する。
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

R = Path("quality/research")
API = "https://kokkai.ndl.go.jp/api/speech"

_cache = {}

def normalize(s: str) -> str:
    # 全角/半角、句読点、空白差を吸収して比較する
    s = s.replace("　", "").replace(" ", "")
    s = re.sub(r"[、。「」『』（）\(\)]", "", s)
    return s

VALID_ISSUE_ID = re.compile(r"^\d{9}X\d{11}$")

def fetch_issue_speeches(issue_id: str):
    if not VALID_ISSUE_ID.match(issue_id):
        return None  # 実在しない/不正な形式のID（捏造URLの疑い）
    if issue_id in _cache:
        return _cache[issue_id]
    speeches = []
    start = 1
    while True:
        q = urllib.parse.urlencode({
            "issueID": issue_id,
            "recordPacking": "json",
            "maximumRecords": 30,
            "startRecord": start,
        })
        url = f"{API}?{q}"
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                data = json.load(resp)
        except Exception as e:
            print(f"    !! API取得失敗 {issue_id}: {e}", file=sys.stderr)
            break
        recs = data.get("speechRecord", [])
        speeches.extend(recs)
        nxt = data.get("nextRecordPosition")
        if not nxt or not recs:
            break
        start = nxt
        time.sleep(0.3)
    _cache[issue_id] = speeches
    return speeches

def find_quotes(text: str):
    return re.findall(r"「([^」]{4,})」", text)

def main():
    files = sorted(R.glob("*-primary-sources.md"))
    total_quotes = 0
    total_ok = 0
    total_ng = 0
    report_lines = ["# 引用文の原文照合結果（機械的照合・2026-08-31）\n",
                    "国会会議録APIの発言データと、メモの「」引用を文字列一致で突き合わせた結果。LLMは使っていない。\n"]
    for f in files:
        text = f.read_text(encoding="utf-8")
        # 「URL行」直後の「確かめられる事実」行をブロックとして拾う
        blocks = re.findall(
            r"(https://kokkai\.ndl\.go\.jp/#/detail\?minId=([0-9A-Za-z_]+)[^\n]*)\n- 確かめられる事実:\s*(.+?)(?=\n(?:###|##|- 確認日|$))",
            text, flags=re.S)
        if not blocks:
            continue
        file_lines = [f"## {f.stem}\n"]
        file_has_content = False
        for url_line, issue_id, fact_text in blocks:
            quotes = find_quotes(fact_text)
            if not quotes:
                continue
            speeches = fetch_issue_speeches(issue_id)
            if speeches is None:
                total_quotes += len(quotes)
                total_ng += len(quotes)
                file_has_content = True
                file_lines.append(f"- [**不正なURL**] issueID=`{issue_id}` は国会会議録APIの形式（9桁+X+9桁）に一致しません。捏造URLの疑いあり。引用{len(quotes)}件を不一致扱い")
                continue
            full_text = normalize("".join(sp.get("speech", "") for sp in speeches))
            for q in quotes:
                total_quotes += 1
                nq = normalize(q)
                ok = bool(nq) and nq in full_text
                if ok:
                    total_ok += 1
                    mark = "一致"
                else:
                    total_ng += 1
                    mark = "**不一致**"
                file_has_content = True
                file_lines.append(f"- [{mark}] issueID={issue_id} 引用:「{q}」")
        if file_has_content:
            report_lines.extend(file_lines)
            report_lines.append("")
    report_lines.insert(2, f"\n集計: 引用{total_quotes}件中 一致{total_ok}件 / 不一致{total_ng}件\n")
    out = R / "quote-verification.md"
    out.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"引用{total_quotes}件中 一致{total_ok}件 / 不一致{total_ng}件")
    print(f"詳細: {out}")

if __name__ == "__main__":
    main()
