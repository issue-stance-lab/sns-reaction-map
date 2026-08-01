#!/usr/bin/env python3
"""公開ページのアリーナ点データから、1投稿1論点の割り当てを data/issue-counts/ に書き出す。

4テーマ（constitutional-amendment / elderly-license-revocation / henoko-student-accident /
koshitsu-tenpakai）は、論点カードに出ている件数を再現できる分類ファイルがリポジトリに残って
いない。件数の出所がページのHTML／arena-data.js の中にしか無い状態なので、そこから
`{url, main_issue}` の一覧を1度だけ取り出してデータファイルにする。

以降 sync_issue_counts.py / verify_theme_page.py はこのファイルだけを読む。ページのHTMLは
参照しないため、spanの数字を手で書き換えれば検査が落ちる。

**このファイルは暫定措置。** 各テーマの次回データ補充で Hermes 分類をやり直したら、
sample_file を直接見るように configs の `issue_counts.source` を差し替えること
（TASK_BOARD 課題29）。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "issue-counts"

# theme -> (アリーナ点データの在り処, i インデックス順の論点ラベル)
CONSTITUTIONAL_ISSUES = [
    "改憲全般",
    "9条・自衛隊",
    "緊急事態条項",
    "国民投票・広告",
    "政党・発議手続き",
    "情報・議論の質",
]
ELDERLY_ISSUES = [
    "義務化・事故防止",
    "地方の足・移動権",
    "適性検査強化",
    "代替交通整備",
    "自主返納支援",
    "その他",
]
HENOKO_ISSUES = [
    "政治的中立性",
    "安全管理・事故原因",
    "追悼・被害者の尊厳",
    "平和教育の萎縮",
    "政治利用・基地問題",
    "報道・行政対応",
]
# koshitsu はページ内 arenaIssueOf() が SM_RAW を7カテゴリへ振り直している。
KOSHITSU_ISSUES = [
    "女性皇族の皇籍維持",
    "旧宮家男系男子の養子制度",
    "男系維持 vs 女系容認",
    "女性天皇・愛子天皇",
    "憲法・制度上の妥当性",
    "国会審議・成立手続き",
    "その他・判断困難",
]


def _js_records(text: str, array_name: str) -> list[dict[str, str]]:
    """`NAME=[{...},{...}]` から各要素の i と u と s を拾う。JSON/JS両方の記法に対応。"""
    match = re.search(rf"{array_name}\s*=\s*\[(.*?)\n?\s*\];", text, re.DOTALL)
    if not match:
        raise ValueError(f"{array_name} が見つかりません")
    records = []
    for chunk in re.findall(r"\{[^{}]*\}", match.group(1)):
        index = re.search(r'["\']?\bi["\']?\s*:\s*(\d+)', chunk)
        url = re.search(r'["\']?\bu["\']?\s*:\s*["\']([^"\']*)["\']', chunk)
        summary = re.search(r'["\']?\bs["\']?\s*:\s*["\']([^"\']*)["\']', chunk)
        if not index or not url:
            continue
        records.append(
            {
                "url": url.group(1),
                "index": int(index.group(1)),
                "summary": summary.group(1) if summary else "",
            }
        )
    if not records:
        raise ValueError(f"{array_name} からレコードを取り出せませんでした")
    return records


def _koshitsu_issue(record: dict[str, str]) -> int:
    """docs/koshitsu-tenpakai-reaction-map.html の arenaIssueOf() と同じ振り分け。"""
    summary = record["summary"]
    index = record["index"]
    if re.search(r"女性皇族|皇籍維持|皇籍残留|婚后|結婚後", summary):
        return 0
    if re.search(r"憲法|14条|合憲|法的|法の下|正統性|制度設計", summary):
        return 4
    if index == 1:
        return 1
    if index == 2:
        return 5
    if index in (3, 4) or re.search(r"愛子|女性天皇|女系天皇", summary):
        return 3
    if index == 0:
        return 2
    return 6


def extract() -> dict[str, list[dict[str, str]]]:
    docs = ROOT / "docs"
    result: dict[str, list[dict[str, str]]] = {}

    text = (docs / "constitutional-amendment-reaction-map.html").read_text(encoding="utf-8")
    result["constitutional-amendment"] = [
        {"url": row["url"], "main_issue": CONSTITUTIONAL_ISSUES[row["index"]]}
        for row in _js_records(text, "const P")
    ]

    text = (docs / "elderly-license-revocation-reaction-map.html").read_text(encoding="utf-8")
    result["elderly-license-revocation"] = [
        {"url": row["url"], "main_issue": ELDERLY_ISSUES[row["index"]]}
        for row in _js_records(text, "const SM_RAW")
    ]

    text = (docs / "henoko-arena-data.js").read_text(encoding="utf-8")
    result["henoko-student-accident"] = [
        {"url": row["url"], "main_issue": HENOKO_ISSUES[row["index"]]}
        for row in _js_records(text, "const HENOKO_ARENA_RAW")
    ]

    text = (docs / "koshitsu-tenpakai-reaction-map.html").read_text(encoding="utf-8")
    result["koshitsu-tenpakai"] = [
        {"url": row["url"], "main_issue": KOSHITSU_ISSUES[_koshitsu_issue(row)]}
        for row in _js_records(text, "const SM_RAW")
    ]

    return result


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for theme, rows in extract().items():
        path = OUT_DIR / f"{theme}.json"
        path.write_text(
            json.dumps(rows, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8",
        )
        counts: dict[str, int] = {}
        for row in rows:
            counts[row["main_issue"]] = counts.get(row["main_issue"], 0) + 1
        print(f"{path.relative_to(ROOT)}  {len(rows)}件")
        for label, count in sorted(counts.items(), key=lambda item: -item[1]):
            print(f"    {count:5d}  {label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
