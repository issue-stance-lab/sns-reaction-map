#!/usr/bin/env python3
"""代表投稿の確認状況を台帳に記録する。

全11テーマの調査条件に「AI分類・人間による代表投稿の確認あり」と表示していたが、
確認の記録がどこにも無く、読者にも運営にも「何を何件確認したのか」が分からなかった。

確認そのものは実際に行われていた。ページに出している代表投稿の要旨を正典（AIの分類結果）
と突き合わせると、多くが書き換えられている。断定的・党派的な表現を中立化する編集が
入っており、これは人が1件ずつ読まないとできない。

    正典: 愛子さまに継承権はなく、未来は悠仁親王にあると主張
    公開: 継承権は制度が定めるものであり個人の人気では決まらないと主張

この差分を証拠として数え、テーマごとに台帳へ残す。台帳は公開しない（docs/ の外）。
ページに出す文言は台帳に合わせる。台帳に記録が無いテーマで「確認あり」とは書かない。

正典は本文を含むため一部が Git 管理外で、環境によっては存在しない。
その場合そのテーマは判定不能として記録し、既存の記録は消さない。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
LEDGER = PROJECT_ROOT / "data/review-ledger.json"
THEMES_YAML = PROJECT_ROOT / "THEMES.yaml"

# ページ上の「要旨 + 埋め込み」の組。要旨の直後に投稿の埋め込みが来る。
SAMPLE_PATTERN = re.compile(
    r'<p[^>]*>([^<]{5,}?)</p>\s*'
    r'<blockquote class="twitter-tweet"[^>]*><a href="(https://x\.com/[^"]+)"'
)


def theme_entries() -> list[dict[str, str]]:
    """THEMES.yaml から id / html / sample_file を取り出す（YAML依存を足さない）。"""
    text = THEMES_YAML.read_text(encoding="utf-8")
    out = []
    for match in re.finditer(
        r"^  ([\w-]+):\s*$(.*?)(?=^  [\w-]+:\s*$|\Z)", text, re.MULTILINE | re.DOTALL
    ):
        body = match.group(2)
        html_match = re.search(r"^    html:\s*(\S+)", body, re.MULTILINE)
        file_match = re.search(r"^    sample_file:\s*[\"']?([^\"'#\n]+)", body, re.MULTILINE)
        published = re.search(r"^    published:\s*done", body, re.MULTILINE)
        if html_match and file_match and published:
            out.append(
                {
                    "id": match.group(1),
                    "html": html_match.group(1).strip(),
                    "sample_file": file_match.group(1).strip(),
                }
            )
    return out


def canon_summaries(path: Path) -> dict[str, str]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for row in rows:
        url = str(row.get("url") or "").strip()
        if not url:
            continue
        classification = row.get("classification") or {}
        out[url] = str(classification.get("summary") or "")
    return out


def measure(theme: dict[str, str]) -> dict[str, Any]:
    page_path = PROJECT_ROOT / theme["html"]
    canon_path = PROJECT_ROOT / theme["sample_file"]
    if not canon_path.exists():
        return {"status": "unknown", "reason": f"正典が見つかりません: {theme['sample_file']}"}

    summaries = canon_summaries(canon_path)
    pairs = SAMPLE_PATTERN.findall(page_path.read_text(encoding="utf-8"))
    adjusted = [url for note, url in pairs if url in summaries and note.strip() != summaries[url].strip()]
    verbatim = [url for note, url in pairs if url in summaries and note.strip() == summaries[url].strip()]
    outside = [url for _, url in pairs if url not in summaries]

    if not pairs:
        return {"status": "no_samples", "samples": 0}
    status = "reviewed" if len(adjusted) > len(verbatim) else "unconfirmed"
    return {
        "status": status,
        "samples": len(pairs),
        "summaries_adjusted": len(adjusted),
        "summaries_verbatim": len(verbatim),
        "urls_outside_canon": len(outside),
    }


def build(today: date) -> dict[str, Any]:
    existing = json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {}
    themes: dict[str, Any] = dict(existing.get("themes") or {})

    for theme in theme_entries():
        result = measure(theme)
        if result["status"] == "unknown":
            # 正典が無い環境では既存の記録を消さない
            if theme["id"] in themes:
                continue
            themes[theme["id"]] = {"status": "unknown", "note": result["reason"]}
            continue
        result["checked_on"] = today.isoformat()
        result["method"] = "ページの代表投稿の要旨を正典（AI分類結果）と突き合わせ、書き換えの有無を数える"
        themes[theme["id"]] = result

    return {
        "_comment": (
            "代表投稿の確認記録。公開しない（docs/ の外）。"
            "scripts/build_review_ledger.py が生成する。"
            "status=reviewed のテーマだけ、ページに確認件数を表示してよい。"
        ),
        "generated_on": today.isoformat(),
        "themes": dict(sorted(themes.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="書き換えずに内容を表示する")
    args = parser.parse_args()

    ledger = build(date.today())
    for theme_id, entry in ledger["themes"].items():
        status = entry.get("status")
        if status == "reviewed":
            detail = (
                f"代表投稿{entry['samples']}件 / 要旨の書き換え{entry['summaries_adjusted']}件"
                f" / AI出力のまま{entry['summaries_verbatim']}件"
            )
        elif status == "unconfirmed":
            detail = (
                f"代表投稿{entry['samples']}件 / 書き換えの痕跡が少なく確認の証拠にならない"
                f"（書き換え{entry['summaries_adjusted']}件 / そのまま{entry['summaries_verbatim']}件）"
            )
        else:
            detail = entry.get("note") or status or ""
        print(f"{status:12s} {theme_id:28s} {detail}")
        outside = entry.get("urls_outside_canon")
        if outside:
            print(f"{'':12s} {'':28s} ★ 正典に無いURLが{outside}件（古い収集分の可能性）")

    if not args.check:
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        LEDGER.write_text(
            json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"\n書き出し: {LEDGER.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
