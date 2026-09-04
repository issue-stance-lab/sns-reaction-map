#!/usr/bin/env python3
"""THEMES.yaml（テーマの登録簿）が小さいまま保たれているかを検査する。

THEMES.yaml は毎セッション読まれるので、経緯や調査記録を書き足すと
その分だけ他の作業に使える余力が減る。2026-09-04 に登録簿と作業記録を分けた
（課題60）。登録簿にはスクリプトが読む工程の状態だけを置き、
更新のたびに書き足す経緯は themes/{テーマ名}.md に置く。

  python3 scripts/verify_themes_yaml.py

NG が1件も無ければ exit 0。
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "THEMES.yaml"
NOTES_DIR = ROOT / "themes"

# 登録簿の上限。分割直後で約9千バイト。倍まで太ったら見直しの合図にする
MAX_REGISTRY_BYTES = 20_000
# 1つの欄の長さ。これを超える説明は themes/{テーマ名}.md へ移す
MAX_FIELD_CHARS = 200
# 作業記録1本の長さ。超えたら quality/designs/・quality/reviews/ へ切り出す
MAX_NOTES_LINES = 300

# 経緯を書き込むために使われがちな欄。登録簿に復活させない
BANNED_KEYS = {"notes", "note", "memo", "history", "log", "経緯", "作業記録"}


def main() -> int:
    problems: list[str] = []

    size = REGISTRY.stat().st_size
    if size > MAX_REGISTRY_BYTES:
        problems.append(
            f"THEMES.yaml が {size:,} バイトある（上限 {MAX_REGISTRY_BYTES:,}）。"
            "経緯や調査記録は themes/{テーマ名}.md へ移すこと"
        )

    themes = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))["themes"]

    for name, value in themes.items():
        tag = f"THEMES.yaml「{name}」"
        for key, field in value.items():
            if key in BANNED_KEYS:
                problems.append(
                    f"{tag}: `{key}` 欄が復活している。"
                    f"中身は themes/{name}.md へ移し、この欄は消すこと"
                )
                continue
            if isinstance(field, str) and len(field) > MAX_FIELD_CHARS:
                problems.append(
                    f"{tag}: `{key}` が {len(field)} 文字（上限 {MAX_FIELD_CHARS}）。"
                    f"説明は themes/{name}.md へ書くこと"
                )

    if not NOTES_DIR.is_dir():
        problems.append("themes/ が無い（テーマごとの作業記録の置き場）")
        NOTES_DIR.mkdir(exist_ok=True)

    for name in themes:
        path = NOTES_DIR / f"{name}.md"
        if not path.exists():
            problems.append(
                f"themes/{name}.md が無い。THEMES.yaml にあるテーマには作業記録を置くこと"
            )
            continue
        lines = len(path.read_text(encoding="utf-8").splitlines())
        if lines > MAX_NOTES_LINES:
            problems.append(
                f"themes/{name}.md: {lines} 行ある（上限 {MAX_NOTES_LINES}）。"
                "設計や調査の記録は quality/designs/・quality/reviews/ へ切り出すこと"
            )

    for path in sorted(NOTES_DIR.glob("*.md")):
        if path.stem not in themes:
            problems.append(
                f"{path.relative_to(ROOT)}: THEMES.yaml に該当テーマが無い"
                "（登録簿に足すか archive/ へ移す）"
            )

    if problems:
        print(f"NG: {len(problems)} 件")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f"OK: 登録簿 {size:,} バイト / テーマ {len(themes)} 件。すべてに作業記録があります")
    return 0


if __name__ == "__main__":
    sys.exit(main())
