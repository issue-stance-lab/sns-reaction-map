#!/usr/bin/env python3
"""隔離コピー内で昇格順を再現し、ビルダーが再実行可能か検査する。"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BUILDERS: tuple[tuple[str, list[str]], ...] = (
    ("ai-copyright", [sys.executable, "scripts/build_ai_copyright_arena.py"]),
    ("bukatsu-chiiki", [sys.executable, "scripts/build_bukatsu_arena.py"]),
    ("koshitsu-tenpakai", [sys.executable, "scripts/build_koshitsu_arena.py"]),
    ("elderly-license-revocation", [sys.executable, "scripts/build_elderly_arena.py"]),
    ("constitutional-amendment", [sys.executable, "scripts/build_constitutional_arena.py"]),
    ("fukushuto", [sys.executable, "scripts/build_fukushuto_arena.py"]),
    ("henoko-student-accident", [sys.executable, "scripts/build_henoko_arena.py"]),
    ("consumption-tax-cut", [sys.executable, "scripts/build_consumption_tax_arena.py"]),
    ("bike-blue-ticket", [sys.executable, "scripts/build_bike_arena.py"]),
    ("school-nickname-ban", [sys.executable, "scripts/build_nickname_arena.py"]),
    ("takaichi", ["node", "scripts/upgrade_takaichi_arena.js"]),
)


def _copy_fixture(target: Path) -> None:
    for directory in ("configs", "data", "docs", "scripts", "social-samples"):
        shutil.copytree(ROOT / directory, target / directory)
    shutil.copy2(ROOT / "THEMES.yaml", target / "THEMES.yaml")


def _run(root: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=root, text=True, capture_output=True)


def _verify(root: Path, theme: str, builder: list[str]) -> tuple[bool, str]:
    steps = (
        ("テーマ別ビルダー", builder),
        ("論点件数同期", [sys.executable, "scripts/sync_issue_counts.py", theme]),
        ("信頼情報適用", [sys.executable, "scripts/seo/apply_theme_trust.py"]),
        ("ビルダー再検査", [*builder, "--check"]),
        ("信頼情報の2回目", [sys.executable, "scripts/seo/apply_theme_trust.py"]),
    )
    for label, command in steps:
        result = _run(root, command)
        output = (result.stdout + result.stderr).strip()
        if result.returncode:
            return False, f"{label} (exit {result.returncode})\n{output}"
        if label == "信頼情報の2回目" and "changed=0" not in output:
            return False, f"apply_theme_trust.py の2回目が changed=0 ではありません\n{output}"
    return True, "昇格順の後もビルダ差分なし / apply_theme_trust changed=0"


def main() -> int:
    failures = 0
    with tempfile.TemporaryDirectory(prefix="isa-rebuildability-") as temp:
        fixture = Path(temp)
        _copy_fixture(fixture)
        for theme, builder in BUILDERS:
            ok, detail = _verify(fixture, theme, builder)
            print(f"{'OK' if ok else 'NG'}  {theme}: {detail}")
            failures += int(not ok)
    print(f"=== 再生成可能性結果: {len(BUILDERS)}テーマ / NG {failures}件 ===")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
