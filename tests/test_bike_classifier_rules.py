import unittest

from scripts.classify_bike_arena_hermes import apply_signature_petition_rule


class BikeSignaturePetitionRuleTests(unittest.TestCase):
    def test_reason_free_change_org_signature_share_is_not_an_infrastructure_argument(self):
        source = {
            "main_issue": "インフラ整備優先",
            "stance": "反対（インフラ・制度優先）",
            "intensity": "medium",
            "summary": "署名への賛同を呼びかける",
            "reason": "道路整備を重視している",
            "confidence": 0.85,
            "article_usable": True,
            "risk": "low",
        }
        text = (
            "このオンライン署名に賛同をお願いします！"
            "「自転車に対する青切符制度の導入に強く反対します」"
            " https://t.co/example @change_jpより"
        )

        result = apply_signature_petition_rule(text, source)

        self.assertEqual(result["main_issue"], "その他")
        self.assertEqual(result["stance"], "反対（インフラ・制度優先）")
        self.assertFalse(result["article_usable"])
        self.assertNotEqual(result, source)

    def test_signature_share_with_an_authored_infrastructure_reason_is_not_overridden(self):
        source = {"main_issue": "インフラ整備優先", "article_usable": True}

        result = apply_signature_petition_rule(
            "地方では車道走行が危険です。このオンライン署名に賛同をお願いします！"
            "「自転車に対する青切符制度の導入に強く反対します」 https://t.co/example @change_jpから",
            source,
        )

        self.assertEqual(result, source)

    def test_unrelated_signature_reference_is_unchanged(self):
        source = {"main_issue": "その他", "article_usable": True}

        result = apply_signature_petition_rule("オンライン署名についてのニュースを読んだ", source)

        self.assertEqual(result, source)


if __name__ == "__main__":
    unittest.main()
