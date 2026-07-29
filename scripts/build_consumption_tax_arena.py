#!/usr/bin/env python3
"""消費税減税 Hermes分類 → 論点アリーナ用データブロックを生成する。

出力:
  - ISSUES 配列（論点別の意見件数、多い順）
  - SM_RAW 配列（意見投稿1件=1点）
  - スタンス集計・論点別スタンス内訳
  - 論点別の代表投稿（Xの声セクション用）
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent

# 表示ラベル（アリーナのセクター名は短く）
ISSUE_LABELS = {
    "減税の対象範囲": "対象範囲",
    "財源と社会保障": "財源・保障",
    "減税の効果": "減税の効果",
    "給付など他策との比較": "給付比較",
    "事業者の実務負担": "事業者負担",
    "公約と政治不信": "公約・不信",
    "その他": "その他",
}

# stance → アリーナのx値（賛否軸）と配色インデックス
STANCE_ORDER = ["減税推進", "条件付き賛成・政府案に不満", "減税反対・慎重", "中立・情報"]
STANCE_X = {
    "減税推進": 2.0,
    "条件付き賛成・政府案に不満": 1.0,
    "減税反対・慎重": -2.0,
    "中立・情報": 0.0,
}
INTENSITY_E = {"low": 0.6, "medium": 1.3, "high": 2.0}


def load_opinions(path: Path) -> list[dict[str, Any]]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    return [r for r in rows if r["classification"].get("is_opinion")]


def escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "social-samples" / "consumption-tax-cut_hermes_arena_classified.json",
    )
    parser.add_argument("--output", type=Path, default=ROOT / "social-samples" / "consumption-tax-cut_arena_data.json")
    args = parser.parse_args()

    all_rows = json.loads(args.input.read_text(encoding="utf-8"))
    opinions = load_opinions(args.input)
    relevant = [r for r in all_rows if r["classification"].get("is_relevant")]

    issue_counts = Counter(r["classification"]["main_issue"] for r in opinions)
    # 「その他」は必ず末尾、それ以外は件数の多い順
    ordered = [k for k, _ in issue_counts.most_common() if k != "その他"]
    if issue_counts.get("その他"):
        ordered.append("その他")
    issue_index = {name: i for i, name in enumerate(ordered)}

    issues_js = ",\n    ".join(
        f'{{k:"{ISSUE_LABELS.get(name, name)}", n:{issue_counts[name]}}}' for name in ordered
    )

    sm_lines = []
    for row in opinions:
        c = row["classification"]
        i = issue_index[c["main_issue"]]
        x = STANCE_X[c["stance"]]
        e = INTENSITY_E.get(c["intensity"], 1.0)
        st = STANCE_ORDER.index(c["stance"])
        summary = escape((c.get("summary") or "")[:60])
        sm_lines.append(
            f'{{x:{x},e:{e},c:{round(float(c.get("confidence", 0.7)), 2)},'
            f'i:{i},st:{st},s:"{summary}",u:"{row.get("url", "")}"}}'
        )

    stance_counts = Counter(r["classification"]["stance"] for r in opinions)
    per_issue_stance = defaultdict(Counter)
    for row in opinions:
        c = row["classification"]
        per_issue_stance[c["main_issue"]][c["stance"]] += 1

    # 論点別の代表投稿（Xの声）: article_usable かつ risk=low を confidence 降順
    samples: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for name in ordered:
        by_stance: dict[str, list[dict[str, Any]]] = {}
        for stance in STANCE_ORDER:
            picks = [
                r
                for r in opinions
                if r["classification"]["main_issue"] == name
                and r["classification"]["stance"] == stance
                and r["classification"].get("article_usable")
                and r["classification"].get("risk") == "low"
                and r.get("url")
            ]
            picks.sort(key=lambda r: float(r["classification"]["confidence"]), reverse=True)
            by_stance[stance] = [
                {
                    "summary": r["classification"]["summary"],
                    "url": r["url"],
                    "intensity": r["classification"]["intensity"],
                    "confidence": r["classification"]["confidence"],
                }
                for r in picks[:4]
            ]
        samples[name] = by_stance

    report = {
        "total_classified": len(all_rows),
        "relevant": len(relevant),
        "opinions": len(opinions),
        "issue_order": ordered,
        "issue_counts": dict(issue_counts),
        "stance_counts": dict(stance_counts),
        "stance_share": {
            k: round(v / len(opinions) * 100, 1) for k, v in stance_counts.items()
        },
        "per_issue_stance": {k: dict(v) for k, v in per_issue_stance.items()},
        "intensity_counts": dict(Counter(r["classification"]["intensity"] for r in opinions)),
        "issues_js": f"const ISSUES = [\n    {issues_js}\n  ];",
        "sm_raw_js": "const SM_RAW = [\n" + ",\n".join(sm_lines) + "\n];",
        "samples": samples,
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"分類 {len(all_rows)}件 / 関連 {len(relevant)}件 / 意見 {len(opinions)}件")
    print("\n論点別（意見）:")
    for name in ordered:
        share = issue_counts[name] / len(opinions) * 100
        print(f"  {name:12s} {issue_counts[name]:4d} ({share:4.1f}%)")
    print("\nスタンス別（意見）:")
    for stance in STANCE_ORDER:
        n = stance_counts.get(stance, 0)
        print(f"  {stance:20s} {n:4d} ({n / len(opinions) * 100:4.1f}%)")
    print(f"\nwrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
