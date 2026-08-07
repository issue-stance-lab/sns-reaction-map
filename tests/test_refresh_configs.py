"""収集の設定が全テーマぶんそろっていることを、実行前に確かめる。

`refresh_topic.py` は実行時に `fetch_queries` を読む。設定が欠けていても、
その日の収集を走らせるまで気づけない（2026-08-02 に henoko で発生）。
収集日ではなくCIで落ちるように、ここで検査する。
"""

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class RefreshConfigTest(unittest.TestCase):
    def setUp(self):
        self.themes = load_yaml(ROOT / "THEMES.yaml")["themes"]

    def test_every_theme_has_usable_fetch_queries(self):
        for theme, fields in self.themes.items():
            with self.subTest(theme=theme):
                relative = fields.get("refresh_config")
                self.assertTrue(relative, f"{theme}: refresh_config が未設定")
                config_path = ROOT / relative
                self.assertTrue(config_path.is_file(), f"{theme}: {relative} が存在しない")

                queries = load_yaml(config_path).get("fetch_queries")
                self.assertIsInstance(queries, list, f"{theme}: {relative} に fetch_queries がない")
                self.assertTrue(queries, f"{theme}: {relative} の fetch_queries が空")
                self.assertEqual(
                    len(queries),
                    len({str(query) for query in queries}),
                    f"{theme}: {relative} の fetch_queries に重複がある",
                )

    def test_pipeline_covers_every_theme(self):
        pipeline = load_yaml(ROOT / "configs" / "refresh-pipeline.yaml")["topics"]
        self.assertEqual(
            sorted(pipeline),
            sorted(self.themes),
            "configs/refresh-pipeline.yaml と THEMES.yaml のテーマ集合が一致しない",
        )
        for theme, entry in pipeline.items():
            with self.subTest(theme=theme):
                classifier = entry.get("classifier")
                self.assertTrue(classifier, f"{theme}: classifier が未設定")
                self.assertTrue((ROOT / classifier).is_file(), f"{theme}: {classifier} が存在しない")

    def test_adapter_themes_declare_an_adapter(self):
        pipeline = load_yaml(ROOT / "configs" / "refresh-pipeline.yaml")["topics"]
        for theme, fields in self.themes.items():
            if fields.get("page_update_mode") != "adapter":
                continue
            with self.subTest(theme=theme):
                name = pipeline[theme].get("adapter")
                self.assertTrue(name, f"{theme}: page_update_mode が adapter なのに adapter 未設定")
                self.assertTrue(
                    (ROOT / "scripts" / "refresh_adapters" / f"{name}.py").is_file(),
                    f"{theme}: refresh_adapters/{name}.py が存在しない",
                )


if __name__ == "__main__":
    unittest.main()
