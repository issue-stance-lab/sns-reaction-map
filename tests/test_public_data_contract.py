import importlib
import json
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class PublicDataContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.taxonomy = json.loads(
            (ROOT / "configs/public-data-taxonomy.json").read_text(encoding="utf-8")
        )["themes"]
        cls.themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]

    def _public_slugs(self) -> list[str]:
        return sorted(slug for slug, item in self.themes.items() if item.get("published") == "done")

    def test_every_public_theme_reads_its_counts_from_public_json(self) -> None:
        """公開10テーマの件数の出所は公開データJSONに一本化する（課題57 段階4）。

        1テーマでも `basis` を戻すと、そのページだけ非公開正典から直接数える状態に
        なり、公開データ契約から再現できなくなる。
        """
        for slug in self._public_slugs():
            config = json.loads(
                (ROOT / "configs" / f"{slug}-reaction-map.json").read_text(encoding="utf-8")
            )
            with self.subTest(slug=slug):
                self.assertEqual(config.get("issue_counts", {}).get("basis"), "public_json")

    def test_every_public_theme_repastes_counts_after_the_public_json_is_rebuilt(self) -> None:
        """公開テーマのadapterは `finalize` を持つ（課題57 段階4・段階5）。

        候補ツリーでは 公開JSON生成 → `finalize` の順に走る。`finalize` が無いテーマは
        候補生成の時点の数字で止まり、「2回生成して差分ゼロ」は通るのに数字だけ古い、
        という自動検査をすり抜ける不具合になる（2026-08-31、あだ名禁止で実際に
        接続を見送った理由）。
        """
        pipeline = yaml.safe_load((ROOT / "configs/refresh-pipeline.yaml").read_text(encoding="utf-8"))
        topics = pipeline["topics"]
        for slug in self._public_slugs():
            name = topics.get(slug, {}).get("adapter")
            with self.subTest(slug=slug):
                self.assertIsNotNone(name, f"{slug}: refresh-pipeline.yaml に adapter がありません")
                module = importlib.import_module(f"scripts.refresh_adapters.{name}")
                self.assertTrue(
                    callable(getattr(module, "finalize", None)),
                    f"{slug}: {name} adapter に finalize がありません",
                )

    def test_taxonomy_matches_exactly_the_public_theme_set(self) -> None:
        public = {slug for slug, item in self.themes.items() if item.get("published") == "done"}
        self.assertEqual(set(self.taxonomy), public)

    def test_every_theme_has_one_other_and_unique_prefixed_ids(self) -> None:
        for slug, item in self.taxonomy.items():
            issues = item["issues"]
            stances = item["stances"]
            self.assertEqual(sum(value["kind"] == "other" for value in issues.values()), 1, slug)
            self.assertEqual(len({value["id"] for value in issues.values()}), len(issues), slug)
            self.assertEqual(len({value["id"] for value in stances.values()}), len(stances), slug)
            for value in [*issues.values(), *stances.values()]:
                self.assertTrue(value["id"].startswith(f"{slug}-"), (slug, value["id"]))

    def test_each_stance_carries_its_own_intensity_split(self) -> None:
        """立場ごとに、その立場の中での表現の強さを持つ。

        これが無いと「幅は立場で絞った件数、高さは全体の割合」という
        分母のねじれた図しか描けない（課題54の山なみ）。
        """
        for path in sorted((ROOT / "data" / "public" / "themes").glob("*.json")):
            theme = json.loads(path.read_text(encoding="utf-8"))
            slug = theme["theme_id"]
            for issue in theme["issues"]:
                for stance in issue["stances"]:
                    where = f"{slug}/{issue['id']}/{stance['id']}"
                    self.assertIn("intensities", stance, where)
                    self.assertEqual(
                        [x["id"] for x in stance["intensities"]],
                        ["low", "medium", "high"], where)
                    self.assertEqual(
                        sum(x["count"] for x in stance["intensities"]),
                        stance["count"], where)
                # 立場ごとの内訳を足すと、論点の強度別件数に一致する
                for level in ("low", "medium", "high"):
                    per_stance = sum(
                        x["count"] for s in issue["stances"]
                        for x in s["intensities"] if x["id"] == level)
                    whole = next(x["count"] for x in issue["intensities"] if x["id"] == level)
                    self.assertEqual(per_stance, whole, f"{slug}/{issue['id']}/{level}")

    def test_hash_fields_explain_their_different_targets(self) -> None:
        theme_schema = json.loads(
            (ROOT / "schemas/public-theme.schema.json").read_text(encoding="utf-8")
        )
        catalog_schema = json.loads(
            (ROOT / "schemas/public-catalog.schema.json").read_text(encoding="utf-8")
        )
        source_note = theme_schema["properties"]["source_sha256"]["description"]
        data_note = catalog_schema["properties"]["themes"]["items"]["properties"]["data_sha256"]["description"]
        self.assertIn("非公開正典", source_note)
        self.assertIn("公開テーマJSON", data_note)


if __name__ == "__main__":
    unittest.main()
