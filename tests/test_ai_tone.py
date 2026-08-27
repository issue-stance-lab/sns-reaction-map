"""公開文章の「AI臭」検査が、通ることと、ちゃんと反応することを両方押さえる。

`verify_ai_tone.py` が exit 0 であるだけでは足りない。**検査が何も検出しない状態でも
exit 0 になる**ため、検出側が壊れても気づけない。ここでは判定関数に作り物のデータを
渡して、落とすべきものを落とすことまで確かめる。

ペルソナは社内専用で、公開物に出してはならない（`WRITING_VOICE.md`）。
この1点が破られると読者に見えるので、単体でも確認する。

**このファイルにペルソナ名を書かない。** リポジトリが公開なので、名前は
`configs/persona.private.json`（Git 管理外）から読む。無いときは飛ばす。
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "verify_ai_tone.py"

sys.path.insert(0, str(ROOT / "scripts"))
import verify_ai_tone as tone  # noqa: E402


class AiToneGateTest(unittest.TestCase):
    def test_repository_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT)], cwd=ROOT, capture_output=True, text=True
        )
        self.assertEqual(
            result.returncode, 0, f"AI臭の検査に落ちています:\n{result.stdout}\n{result.stderr}"
        )

    def test_config_requires_reason(self) -> None:
        """理由の書けない例外を書けなくする。configs/page-originality.json と同じ約束。"""
        config = tone.load()
        for group in ("banned", "mirror", "density"):
            for entry in config.get(group) or []:
                self.assertTrue(entry.get("reason"), f"{group} の {entry} に reason がない")


class DetectorTest(unittest.TestCase):
    """検出側が生きていることを、作り物のデータで確かめる。"""

    def setUp(self) -> None:
        self.config = tone.load()

    @unittest.skipUnless(tone.PERSONA.is_file(), "configs/persona.private.json が無い")
    def test_persona_leak_is_caught(self) -> None:
        term = tone.persona_terms()[0][0]
        pages = {"fake": [f"この記事は{term}が取材しました。"]}
        self.assertTrue(tone.check_persona(self.config, pages, {}))

    @unittest.skipUnless(tone.PERSONA.is_file(), "configs/persona.private.json が無い")
    def test_persona_leak_in_draft_is_caught(self) -> None:
        term = tone.persona_terms()[0][0]
        drafts = {"content/note/drafts/x.md": f"文責: {term}"}
        self.assertTrue(tone.check_persona(self.config, {}, drafts))

    def test_clean_text_has_no_persona_failure(self) -> None:
        pages = {"fake": ["SNS反応まっぷ編集部が整理しました。"]}
        self.assertEqual(tone.check_persona(self.config, pages, {}), [])

    def test_banned_phrase_is_caught(self) -> None:
        drafts = {"content/articles/drafts/x.md": "いかがでしたか。まとめました。"}
        self.assertTrue(tone.check_banned(self.config, {}, drafts))

    def test_mirror_structure_is_caught(self) -> None:
        """賛否を同じ構文で並べる鏡像。AI臭の最大要因なので、必ず落とすこと。"""
        pages = {
            "fake": [
                "推進側の最も強い根拠は、持続しにくいことです。",
                "慎重側の最も強い根拠は、費用が残ることです。",
            ]
        }
        failures, _notes = tone.check_mirror(self.config, pages, False)
        self.assertTrue(failures)

    def test_single_use_is_allowed(self) -> None:
        """1回だけなら型ではなく、その場の説明。落としてはいけない。"""
        pages = {"fake": ["推進側の最も強い根拠は、持続しにくいことです。"]}
        failures, _notes = tone.check_mirror(self.config, pages, False)
        self.assertEqual(failures, [])

    def test_density_is_caught(self) -> None:
        body = ["これは形ではなく、中身の話です。"] * 30 + ["ふつうの文を置きます。"] * 10
        failures, _notes = tone.check_density(self.config, {"fake": body}, False)
        self.assertTrue(failures)

    def test_short_page_is_not_judged_by_density(self) -> None:
        """文が少ないと1件の重みが大きくなり、比率に意味が無くなる。"""
        failures, _notes = tone.check_density(
            self.config, {"fake": ["これは形ではなく、中身の話です。"]}, False
        )
        self.assertEqual(failures, [])


class PrivatePersonaTest(unittest.TestCase):
    """ペルソナ名を公開リポジトリへ入れない（課題45と同じ方式）。"""

    def test_persona_file_is_not_tracked(self) -> None:
        """追跡されていたら、次の push で名前が公開履歴に残る。ここで止める。"""
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "configs/persona.private.json"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertNotEqual(
            result.returncode, 0,
            "configs/persona.private.json が Git 管理下にあります。.gitignore を確認してください",
        )

    def test_persona_name_is_absent_from_tracked_files(self) -> None:
        """追跡ファイルのどこにも名前が残っていないこと。"""
        if not tone.PERSONA.is_file():
            self.skipTest("configs/persona.private.json が無い")
        terms, _ = tone.persona_terms()
        tracked = subprocess.run(
            ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True
        ).stdout.split(b"\0")
        hits = []
        for raw in tracked:
            if not raw:
                continue
            path = ROOT / raw.decode()
            if path.suffix not in {".md", ".json", ".py", ".yaml", ".yml", ".html", ".js"}:
                continue
            try:
                body = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for term in terms:
                if term in body:
                    hits.append(f"{raw.decode()}: {term}")
        self.assertEqual(hits, [], f"追跡ファイルにペルソナ名が残っています: {hits}")

    @unittest.skipUnless(tone.PERSONA.is_file(), "configs/persona.private.json が無い")
    def test_persona_file_is_backed_up(self) -> None:
        """バックアップ対象から漏れると、手元にしか無いファイルになる（課題45の注意点）。

        ファイルが無いこと自体は backup_private_data.py が
        「NG ライターのペルソナが存在しない」で報せるので、ここでは飛ばす。
        """
        import backup_private_data as backup
        targets, _errors = backup.collect_targets()
        self.assertIn(
            tone.PERSONA, targets,
            "configs/persona.private.json がバックアップ対象に入っていません",
        )


class LedgerScopeTest(unittest.TestCase):
    """投稿済みの台帳は、ペルソナ流出だけを見る（過去の投稿は取り消せないため）。"""

    def test_ledger_files_are_declared(self) -> None:
        self.assertIn(Path("content/x/posts.md"), tone.LEDGER_FILES)

    def test_drafts_are_declared(self) -> None:
        self.assertIn(Path("content/note/drafts"), tone.DRAFT_DIRS)

    def test_ledger_is_excluded_from_banned_check(self) -> None:
        """台帳に禁止フレーズがあっても、検査は落ちない。下書きの段階で止める設計。"""
        ledger = tone.ledger_texts()
        self.assertTrue(ledger, "台帳が読めていない")
        drafts = tone.draft_texts()
        for name in ledger:
            self.assertNotIn(name, drafts, "台帳が下書き扱いになっている")


if __name__ == "__main__":
    unittest.main()
