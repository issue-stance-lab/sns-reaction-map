#!/usr/bin/env python3
"""非公開データが無くても回せる検査をまとめて実行する（GitHub Actions用）。

**なぜ要るか。** 検査は揃っているのに、回すことを強制する仕組みが無かった。
配信ワークフローはデプロイしかしておらず、検査は「作業した人が忘れずに手で回す」
に依存していた。2026-09-01に3テーマを公開したときSEO台帳（configs/theme-seo.json）が
置き去りになり、翌日の部活動公開まで誰も気づかなかった（公開前検査で9件失敗）。
同じ場所のズレは 2026-07-30 / 08-08 / 09-02 と3回起きている。3回とも、その検査だけが
`release` スキルの標準4検査に入っておらず、更新スクリプトの内側でしか動いていなかった。

**ここに入れてよいもの。** `social-samples/`（本文付きの非公開正典）を読まない検査だけ。
GitHub Actions には非公開データが無いので、正典を読む検査を入れると常に赤になり、
赤が当たり前になって誰も見なくなる。

**ここに入らないもの**（手元でしか回せない。`release` スキルの手順どおり、本番反映の前に
共有ツリーで回すこと）:
`verify_theme_page.py` / `verify_number_provenance.py` / `verify_top_page.py` /
`verify_builder_rebuildability.py` / `verify_public_registry.py --against-private` /
下の PRIVATE_DATA_TESTS に挙げたテスト。
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 公開ファイルだけを読む検査。ラベルは失敗したとき何を見ればよいかが分かる言い方にする。
CHECKS: tuple[tuple[str, list[str]], ...] = (
    ("公開データJSONとcatalogの整合", ["scripts/verify_public_registry.py", "--public-only"]),
    ("主張の判定語・件数・照合の追いつき", ["scripts/verify_claim_verdicts.py"]),
    ("SEO台帳（更新日・JSON-LD・sitemap）", ["scripts/seo/validate_theme_seo.py"]),
    ("収集期間の記録", ["scripts/verify_sample_periods.py"]),
    ("ページ文の使い回し", ["scripts/verify_page_originality.py"]),
)

# ここに入れなかったもの:
# - verify_quotes.py は quality/research/quote-verification.md を毎回上書きし、人が後から
#   足した補足（機械では不一致に見えるが e-Gov で条文と一致を確認済み、等）を消してしまう。
#   検査に副作用があるうちは自動実行に載せない。


# 非公開正典を読むテスト。除外する理由を1件ずつ書く（理由の書けない除外を増やさないため）。
PRIVATE_DATA_TESTS: dict[str, str] = {
    "test_builder_rebuildability": "全テーマのビルダーを正典から再生成して比べる",
    "test_data_sheet": "DATA_SHEET.md を正典から作り直して比べる",
    "test_elderly_adapter": "高齢者免許返納の更新回（非公開）を読む",
    "test_fukushuto_taxonomy": "副首都の正典レコードを分類体系と突き合わせる",
    "test_nickname_adapter": "あだ名禁止の更新回（非公開）を読む",
    "test_portal_stats": "トップページの件数を正典から数え直す",
    "test_taxonomy_continuity": "全テーマの正典ラベルが定義の内側かを見る",
}


def run_command_checks() -> list[str]:
    failures = []
    for label, argv in CHECKS:
        result = subprocess.run([sys.executable, *argv], cwd=ROOT, text=True, capture_output=True)
        head = (result.stdout or result.stderr).strip().splitlines()
        print(f"--- {label}: {' '.join(argv)}")
        print("\n".join(head[-12:]) if head else "(出力なし)")
        if result.returncode != 0:
            failures.append(f"{label}（{' '.join(argv)}）")
        print()
    return failures


def public_test_suite() -> unittest.TestSuite:
    """除外リスト以外のテストを集める。除外に挙げたファイルが消えていたら止める。"""
    tests_dir = ROOT / "tests"
    missing = [name for name in PRIVATE_DATA_TESTS if not (tests_dir / f"{name}.py").exists()]
    if missing:
        raise SystemExit(
            "除外リストに、もう存在しないテストが残っています: "
            f"{missing}\nscripts/run_public_checks.py の PRIVATE_DATA_TESTS を直してください"
        )
    def flatten(suite: unittest.TestSuite):
        for item in suite:
            if isinstance(item, unittest.TestSuite):
                yield from flatten(item)
            else:
                yield item

    kept = unittest.TestSuite()
    discovered = unittest.defaultTestLoader.discover(str(tests_dir), top_level_dir=str(tests_dir))
    for case in flatten(discovered):
        module = type(case).__module__.split(".")[0]
        if module in PRIVATE_DATA_TESTS:
            continue
        kept.addTest(case)
    return kept


def main() -> int:
    print("=== 非公開データ無しで回せる検査 ===\n")
    failures = run_command_checks()

    # `python3 -m unittest discover -s tests` と同じ import 環境にする
    # （ROOTが入っていないと tests 側の `from scripts...` が落ちる）
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "tests"))
    suite = public_test_suite()
    print(f"--- テスト（非公開正典を読む{len(PRIVATE_DATA_TESTS)}ファイルを除く / {suite.countTestCases()}件）")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        failures.append("テスト")

    print()
    if failures:
        print(f"NG {len(failures)}件: " + " / ".join(failures))
        return 1
    print("OK: 公開ファイルだけで確かめられる範囲はすべて通りました")
    print("注意: 正典を読む検査は手元でしか回せません。本番反映の前に release スキルの手順で回すこと")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
