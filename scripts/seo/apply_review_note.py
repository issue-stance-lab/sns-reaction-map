#!/usr/bin/env python3
"""調査条件の「人間による代表投稿の確認あり」を、台帳の記録に合わせて書き分ける。

全11テーマが同じ文言で「AI分類・人間による代表投稿の確認あり」と表示していた。
確認そのものは実際に行われていたが（data/review-ledger.json 参照）、
何を何件確認したのかが分からず、読者にも運営にも検証できない主張になっていた。

台帳の status に応じて書き分ける。

    reviewed     → AI分類。代表投稿10件の要旨を編集部が確認
    unconfirmed  → AI分類。代表投稿は編集部が選定
    unknown      → AI分類。代表投稿は編集部が選定

「確認」と書くのは、台帳に証拠があるテーマだけにする。
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEDGER = PROJECT_ROOT / "data/review-ledger.json"
THEMES_YAML = PROJECT_ROOT / "THEMES.yaml"

OLD_NOTE = "AI分類・人間による代表投稿の確認あり"
SELECTED_NOTE = "AI分類。代表投稿は編集部が選定"

# 確認表示は <span class="review-note"> で囲む。この件数は data/review-ledger.json 由来で
# 正典（分類結果）からは導けないため、verify_number_provenance.py の
# exclude_selectors で「ここだけ」除外できるようにするための目印。
# 同じ段落にある「公開投稿 N件」は正典から導ける値なので、除外に巻き込んではいけない。
REVIEW_NOTE_CLASS = "review-note"
CONDITION_PATTERN = re.compile(
    r"（取得期間: (?P<period>[^／）]*)／"
    r'(?:<span class="review-note">)?(?P<note>[^<）]*)(?:</span>)?）'
)


def reviewed_note(samples: int) -> str:
    return f"AI分類。代表投稿{samples}件の要旨を編集部が確認"


def load_ledger() -> dict[str, dict]:
    if not LEDGER.exists():
        raise SystemExit(
            "data/review-ledger.json がありません。先に scripts/build_review_ledger.py を実行してください。"
        )
    return json.loads(LEDGER.read_text(encoding="utf-8")).get("themes") or {}


def theme_pages() -> dict[str, Path]:
    text = THEMES_YAML.read_text(encoding="utf-8")
    out: dict[str, Path] = {}
    for match in re.finditer(
        r"^  ([\w-]+):\s*$(.*?)(?=^  [\w-]+:\s*$|\Z)", text, re.MULTILINE | re.DOTALL
    ):
        body = match.group(2)
        html_match = re.search(r"^    html:\s*(\S+)", body, re.MULTILINE)
        if html_match and re.search(r"^    published:\s*done", body, re.MULTILINE):
            out[match.group(1)] = PROJECT_ROOT / html_match.group(1).strip()
    return out


def note_for(entry: dict) -> str:
    if entry.get("status") == "reviewed":
        return reviewed_note(int(entry["samples"]))
    return SELECTED_NOTE


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--check",
        action="store_true",
        help="書き換えずに、台帳と食い違うページがあれば終了コード1で報告する",
    )
    args = parser.parse_args()

    ledger = load_ledger()
    failures = 0
    changed = 0

    for theme_id, page_path in sorted(theme_pages().items()):
        entry = ledger.get(theme_id) or {}
        expected = note_for(entry)
        content = page_path.read_text(encoding="utf-8")
        match = CONDITION_PATTERN.search(content)
        if not match:
            print(f"NG  {theme_id}: 調査条件の括弧が見つかりません")
            failures += 1
            continue
        actual = match.group("note")
        # 文言だけでなく <span> で囲まれているかも見る。囲みは
        # verify_number_provenance.py が「ここだけ」除外するための目印なので、
        # 文言が合っていても囲みが無ければ書き換える必要がある。
        desired = (
            f"（取得期間: {match.group('period')}／"
            f'<span class="{REVIEW_NOTE_CLASS}">{expected}</span>）'
        )
        if match.group(0) == desired:
            print(f"OK  {theme_id}: {expected}")
            continue
        if args.check:
            reason = "台詞が台帳と不一致" if actual != expected else "review-note の囲みが無い"
            print(f"NG  {theme_id}: {reason}\n      いま: {actual}\n      あるべき: {expected}")
            failures += 1
            continue
        updated = CONDITION_PATTERN.sub(lambda m: desired, content, count=1)
        changed += 1
        print(f"{'変更予定' if args.dry_run else '変更'}  {theme_id}\n      旧: {actual}\n      新: {expected}")
        if not args.dry_run:
            page_path.write_text(updated, encoding="utf-8")

    if args.check:
        return 1 if failures else 0
    print(f"\n{'変更予定' if args.dry_run else '変更'}: {changed} ファイル")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
