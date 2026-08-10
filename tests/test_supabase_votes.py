"""投票数の取得が、公開されている入口だけを使い続けることを守る。

2026-07-31 の security migration で public.votes への直接の権限が全部剥がされ、
PostgREST 経由の読み取り（`/rest/v1/votes?select=...`）は 401 になった。
KPI が2週間 12 のまま止まっていた原因がこれ。同じ壊れ方を繰り返さないよう、
取得経路と topic 一覧の出所を検査で固定する。
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "fetch_supabase_votes.py"
EDGE = ROOT / "supabase" / "functions" / "cast-vote" / "index.ts"
MIGRATION = ROOT / "supabase" / "migrations" / "202607310001_secure_votes.sql"

import sys  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
import fetch_supabase_votes as votes  # noqa: E402


def _code_only(path: Path) -> str:
    """説明文（docstring・コメント）を除いた、実際に動く部分だけを返す。"""
    import ast
    import io
    import tokenize

    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = {
        ast.get_docstring(node, clean=False)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    pieces = []
    for token in tokenize.generate_tokens(io.StringIO(path.read_text(encoding="utf-8")).readline):
        if token.type == tokenize.COMMENT:
            continue
        if token.type == tokenize.STRING and token.string.strip("\"'") in docstrings:
            continue
        pieces.append(token.string)
    return "\n".join(pieces)


class ReadPathTests(unittest.TestCase):
    def test_does_not_read_the_votes_table_directly(self):
        code = _code_only(SCRIPT)
        self.assertNotIn("/rest/v1/", code, "PostgREST 経由に戻っている（anon では 401 になる）")
        self.assertNotIn("service_role", code.lower(), "service_role キーを持ち込んでいる")

    def test_uses_the_public_edge_function(self):
        body = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("/functions/v1/", body)
        self.assertEqual(votes.EDGE_FUNCTION, "cast-vote")

    def test_migration_really_revoked_direct_access(self):
        """前提が変わったら（再び直接読めるようになったら）気づけるようにする。"""
        if not MIGRATION.exists():
            self.skipTest("migration ファイルがない")
        self.assertRegex(MIGRATION.read_text(encoding="utf-8"), r"REVOKE ALL ON TABLE public\.votes FROM anon")


class TopicListTests(unittest.TestCase):
    def test_topics_come_from_the_edge_function(self):
        expected = re.findall(
            r'"([^"]+)"\s*:\s*\d+',
            re.search(r"const TOPIC_CHOICES[^{]*\{(.*?)\n\};", EDGE.read_text(encoding="utf-8"), re.S).group(1),
        )
        self.assertEqual(votes.known_topics(), expected)

    def test_every_published_theme_has_a_topic(self):
        import yaml

        themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
        topics = votes.known_topics()
        for key, value in themes.items():
            if value.get("published") != "done":
                continue
            self.assertTrue(
                any(topic.startswith(f"{key}-issue-stance-v") for topic in topics),
                f"{key} は公開済みだが Edge Function に投票トピックがない",
            )


if __name__ == "__main__":
    unittest.main()
