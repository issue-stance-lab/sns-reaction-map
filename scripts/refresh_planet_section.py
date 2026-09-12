#!/usr/bin/env python3
"""公開済みの山なみページ（docs/{topic}-reaction-map.html）を、最新の正典データで作り直す。

初回の切り替え（build_planet_page_preview.py --for-docs）は「旧デザイン→山なみ」の
1回きりの変換で、既に山なみが入っているページに使うと安全装置が拒否する
（この課題54・63の反映作業で実際に発生し、この専用スクリプトを新設した）。

このスクリプトは <!-- PLANET_SECTION_START --> 〜 <!-- PLANET_SECTION_END --> の
区間だけを、最新の正典データから作り直した内容へ置き換える。区間の外
（ヘッダー・フッター・投票・SNS投稿サンプル・関連テーマ・広告枠・OGP・進捗バーの入れ物）は
文字列として一切変更しない。

同じ入力で2回実行しても差分が出ない（課題34の冪等性）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_planet_data as bpd  # noqa: E402
from build_planet_page_preview import build_section, render_planet, split_prototype  # noqa: E402
from issue_card_counts import card_counts, load_records, other_count  # noqa: E402
from sync_issue_counts import apply_lead, apply_note  # noqa: E402

START = "<!-- PLANET_SECTION_START -->"
END = "<!-- PLANET_SECTION_END -->"


def _sync_lead_and_note(html: str, topic: str, themes: dict) -> str:
    """sync_issue_counts.py の lead/note を、山なみページにも適用する。

    sync_theme() は「論点カード同期は対象外」として山なみ全体を早期returnし、
    lead・noteもろとも素通りしていた。しかしlead・noteは論点カードの構造に
    依存しない単純な文字列置換で、card_counts()自体は山なみでも問題なく計算できる
    （実際に部活動のconfigsは issue_counts.sync=["lead"] のまま）。ここだけ、
    既存の apply_lead / apply_note を直接呼んで正しく揃える。
    """
    config_path = ROOT / "configs" / f"{topic}-reaction-map.json"
    if not config_path.is_file():
        return html
    config = json.loads(config_path.read_text(encoding="utf-8"))
    sync = [str(name) for name in ((config.get("issue_counts") or {}).get("sync") or [])]
    if not sync:
        return html
    theme_data = themes[topic]
    sample_file = theme_data.get("verification_file") or theme_data.get("sample_file")
    cards = card_counts(topic, config, sample_file)
    if "lead" in sync:
        html = apply_lead(html, topic, cards, other_count(topic, config, sample_file))
    if "note" in sync:
        block = config.get("issue_counts") or {}
        block_source = str(block.get("source") or sample_file or "")
        html = apply_note(html, topic, len(load_records(block_source)))
    return html


def _inject_bukatsu_go_cards(block: str, data: dict) -> str:
    """build_bukatsu() が本文中に足す「この論点のなかを見る」リンクを再現する。

    build_section() 自体は作らない（build_planet_page_preview.py:build_bukatsu の
    セクション挿入後の一手間）。ここを飛ばすと、初回変換時に足された既存のリンクが
    再生成のたびに消える（課題47と同じ失われ方）。bukatsu-chiiki専用（他テーマの
    build_generic() には無い一手間のため、他テーマでは呼ばない）。
    """
    for it in data["issues"]:
        tag = f'<div class="extras" id="extras-{it["id"]}">'
        if tag in block and f'href="#issue-{it["id"]}"' not in block:
            block = block.replace(
                tag,
                tag + f'<p style="margin:14px 0 0"><a class="go-card" href="#issue-{it["id"]}">'
                      f'この論点のなかを見る ↓</a></p>', 1)
    return block


METHOD_TEXT_RE = re.compile(r"(重複を除いた累計)([\d,]+)(件を分類し、意見と判定した)([\d,]+)(件を論点分析に使用しています)")


def _sync_bukatsu_method_text(html: str, data: dict) -> str:
    """「調査条件」内の集計方法テキスト（累計N件・意見M件）を揃える。

    このテキストはbuild_bukatsu_arena.py・sync_issue_counts.pyのどちらの生成対象にも
    入っておらず（山なみ移行前からの静的文で、山なみ判定によるスキップの対象にすら
    なっていない）、初回変換以来だれも更新していなかった。bukatsu-chiiki専用。
    """
    collected, opinions = data["totals"]["collected"], data["totals"]["opinions"]
    new_html, n = METHOD_TEXT_RE.subn(
        lambda m: f"{m.group(1)}{collected:,}{m.group(3)}{opinions:,}{m.group(5)}", html, count=1
    )
    if n != 1:
        raise SystemExit("調査条件の集計方法テキストが見つからないか複数あります（bukatsu-chiiki）")
    return new_html


TOPIC_ENRICH = {"bukatsu-chiiki": _inject_bukatsu_go_cards}
TOPIC_METHOD_TEXT = {"bukatsu-chiiki": _sync_bukatsu_method_text}


def refresh(topic: str) -> tuple[str, str, list[str]]:
    page = ROOT / "docs" / f"{topic}-reaction-map.html"
    html = page.read_text(encoding="utf-8")
    if START not in html or END not in html:
        raise SystemExit(
            f"「{topic}」はまだ山なみ形式ではありません。"
            "初回切り替えは build_planet_page_preview.py --for-docs を使うこと"
        )
    i = html.index(START)
    j = html.index(END) + len(END)

    data = bpd.build(topic)
    cfg = bpd.yaml.safe_load((ROOT / "configs/planet" / f"{topic}.yaml").read_text())
    failures = bpd.independence_gate(data, cfg)
    data = bpd.stabilize(data)

    prototype_html = render_planet(data)
    parts = split_prototype(prototype_html)
    new_block = build_section(parts)
    enrich = TOPIC_ENRICH.get(topic)
    if enrich:
        new_block = enrich(new_block, data)

    new_html = html[:i] + new_block + html[j:]
    themes = bpd.yaml.safe_load((ROOT / "THEMES.yaml").read_text())["themes"]
    new_html = _sync_lead_and_note(new_html, topic, themes)
    method_text = TOPIC_METHOD_TEXT.get(topic)
    if method_text:
        new_html = method_text(new_html, data)
    return html, new_html, failures


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--topic", required=True)
    ap.add_argument("--for-docs", action="store_true", help="docs/ へ実際に書き込む（既定は見本のみ）")
    a = ap.parse_args()

    old_html, new_html, failures = refresh(a.topic)
    if failures and a.for_docs:
        print("独自性の検査に不合格のため docs/ へは書けません:")
        for x in failures:
            print(f"  - {x}")
        raise SystemExit(1)

    changed = new_html != old_html
    if a.for_docs:
        if changed:
            (ROOT / "docs" / f"{a.topic}-reaction-map.html").write_text(new_html, encoding="utf-8")
        print(("UPDATE" if changed else "OK") + f". Lines: {len(old_html.splitlines())} → {len(new_html.splitlines())}")
    else:
        out = ROOT / "quality/prototypes" / f"{a.topic}-section-refresh-preview.html"
        out.write_text(new_html, encoding="utf-8")
        print(f"見本を書き出しました（docs/は未変更）: {out}")
        print(("差分あり" if changed else "差分なし") + f". Lines: {len(old_html.splitlines())} → {len(new_html.splitlines())}")


if __name__ == "__main__":
    main()
