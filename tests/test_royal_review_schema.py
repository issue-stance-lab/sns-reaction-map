"""Synthetic storage cases only; these are not body-review evidence."""
import copy
import unittest

from scripts.royal_review_schema import CORE_FIELDS, SCHEMA_VERSION, validate_decision


def decision():
    return {
        "index": 0, "is_relevant": True, "is_opinion": True,
        "attribution": "author", "main_issue": "架空の論点についての意見",
        "reform_target": "unexpressed", "mentioned_reform_target": None,
        "current_package_stance": "unexpressed", "provisions": [],
        "succession": {key: "unexpressed" for key in (
            "male_line_only", "male_only", "female_sovereign", "female_line",
            "named_successor_aiko",
        )},
        "other_succession": None, "other_evaluations": [], "unknown_fields": [],
        "uncertain": False, "evidence_sufficient": True,
        "reason": "架空の保存形式試験。実際の投稿に対する判断ではない。",
        "aggregation_route": "criteria_needed", "existing_stance_candidate": None,
    }


def evaluation(**overrides):
    return {"kind": "feasibility", "target": "架空の制度の成立",
            "assessment": "denied", "time_scope": "present_or_future", **overrides}


class RoyalReviewSchemaTests(unittest.TestCase):
    def test_contract_and_nonmutation(self):
        row = decision()
        before = copy.deepcopy(row)
        self.assertIsNone(validate_decision(row))
        self.assertEqual(row, before)
        self.assertEqual(SCHEMA_VERSION, "koshitsu-three-domains-v1")
        self.assertIsInstance(CORE_FIELDS, tuple)
        self.assertEqual(len(CORE_FIELDS), 12)

    def test_rejects_nonobjects_with_valueerror(self):
        for row in (None, [], "text", 1, True):
            with self.subTest(row=row), self.assertRaises(ValueError):
                validate_decision(row)

    def test_every_field_is_required(self):
        for key in decision():
            row = decision()
            del row[key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_decision(row)

    def test_forbids_legacy_or_unversioned_extensions(self):
        for key in ("stance", "stance_reform", "stance_succession", "new_axis"):
            row = decision()
            row[key] = "support"
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_decision(row)

    def test_exact_boolean_and_index_types(self):
        for key, values in {
            "index": [True, False, -1, 0.0, "0", None],
            "is_relevant": [0, 1, "true", None],
            "is_opinion": [0, 1, "false", []],
            "uncertain": [0, 1, "false", None],
            "evidence_sufficient": [0, 1, "true", None],
        }.items():
            for value in values:
                row = decision()
                row[key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    validate_decision(row)

    def test_all_text_fields_reject_empty_and_wrong_types(self):
        for key in ("main_issue", "reason", "mentioned_reform_target", "other_succession"):
            for value in ("", " \t\n　", [], {}, 1, True):
                row = decision()
                row[key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    validate_decision(row)
        for key in ("main_issue", "reason"):
            row = decision()
            row[key] = None
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_decision(row)

    def test_arrays_require_arrays_not_null(self):
        for key in ("provisions", "other_evaluations", "unknown_fields"):
            for value in (None, {}, "", ()):
                row = decision()
                row[key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    validate_decision(row)

    def test_enums_fail_closed_on_unhashable_and_old_values(self):
        for key in ("attribution", "reform_target", "current_package_stance", "aggregation_route"):
            for value in (None, [], {}, True, "neutral", "support "):
                row = decision()
                row[key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    validate_decision(row)

    def test_all_succession_axes_are_required_and_closed(self):
        for value in (None, [], {}, {**decision()["succession"], "other": "support"}):
            row = decision()
            row["succession"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_decision(row)
        for axis in decision()["succession"]:
            row = decision()
            del row["succession"][axis]
            with self.subTest(axis=axis), self.assertRaises(ValueError):
                validate_decision(row)
            for value in (None, [], {}, True, "neutral", " support"):
                row = decision()
                row["succession"][axis] = value
                with self.subTest(axis=axis, value=value), self.assertRaises(ValueError):
                    validate_decision(row)

    def test_unknown_major_fields_are_complete_exact_and_unique(self):
        for field in ("is_opinion", "attribution", "reform_target", "current_package_stance",
                      *["succession." + k for k in decision()["succession"]]):
            row = decision()
            if field.startswith("succession."):
                row["succession"][field.split(".")[1]] = "unknown"
            else:
                row[field] = None if field == "is_opinion" else "unknown"
            row.update(unknown_fields=[field], uncertain=True, evidence_sufficient=False)
            validate_decision(row)
            for listed in ([], [field, field], ["reason"], [None], [[]], [{}]):
                broken = copy.deepcopy(row)
                broken["unknown_fields"] = listed
                with self.subTest(field=field, listed=listed), self.assertRaises(ValueError):
                    validate_decision(broken)
            for key in ("uncertain", "evidence_sufficient"):
                broken = copy.deepcopy(row)
                broken[key] = not broken[key]
                with self.subTest(field=field, flag=key), self.assertRaises(ValueError):
                    validate_decision(broken)

    def test_nonunknown_field_cannot_be_falsely_listed(self):
        row = decision()
        row.update(unknown_fields=["succession.male_only"], uncertain=True, evidence_sufficient=False)
        with self.assertRaises(ValueError):
            validate_decision(row)

    def test_nested_unknown_requires_flags_without_duplicate_major_entry(self):
        for domain, item in (
            ("provisions", {"target": "架空の具体措置", "stance": "unknown"}),
            ("other_evaluations", evaluation(assessment="unknown")),
        ):
            row = decision()
            row[domain] = [item]
            with self.subTest(domain=domain), self.assertRaises(ValueError):
                validate_decision(row)
            row.update(uncertain=True, evidence_sufficient=False)
            validate_decision(row)
            for key in ("uncertain", "evidence_sufficient"):
                broken = copy.deepcopy(row)
                broken[key] = not broken[key]
                with self.subTest(domain=domain, flag=key), self.assertRaises(ValueError):
                    validate_decision(broken)
            row["unknown_fields"] = [f"{domain}[0]"]
            with self.assertRaises(ValueError):
                validate_decision(row)

    def test_nested_shapes_reject_missing_extra_and_nonobjects(self):
        for domain, item in (("provisions", {"target": "架空の措置", "stance": "support"}),
                             ("other_evaluations", evaluation())):
            variants = [None, [], 1, "text", {**item, "stance_old": "support"}]
            variants += [{k: v for k, v in item.items() if k != omitted} for omitted in item]
            for variant in variants:
                row = decision()
                row[domain] = [variant]
                with self.subTest(domain=domain, variant=variant), self.assertRaises(ValueError):
                    validate_decision(row)

    def test_nested_enums_and_targets_are_strict(self):
        for domain, item in (("provisions", {"target": "架空の措置", "stance": "support"}),
                             ("other_evaluations", evaluation())):
            for key in item:
                for value in (None, [], {}, True, "", " \t", "unexpressed"):
                    if key == "target" and value == "unexpressed":
                        continue  # Targets are free text, not enums.
                    row = decision()
                    row[domain] = [{**item, key: value}]
                    with self.subTest(domain=domain, key=key, value=value), self.assertRaises(ValueError):
                        validate_decision(row)

    def test_named_and_female_support_require_explicit_implications(self):
        row = decision()
        row["succession"]["named_successor_aiko"] = "support"
        with self.assertRaises(ValueError):
            validate_decision(row)
        row["succession"]["female_sovereign"] = "support"
        with self.assertRaises(ValueError):
            validate_decision(row)
        row["succession"]["male_only"] = "oppose"
        validate_decision(row)
        self.assertEqual(row["succession"]["female_line"], "unexpressed")
        self.assertEqual(row["succession"]["male_line_only"], "unexpressed")
        for unsupported in ("support", "mixed", "unexpressed", "unknown"):
            broken = copy.deepcopy(row)
            broken["succession"]["male_only"] = unsupported
            if unsupported == "unknown":
                broken.update(unknown_fields=["succession.male_only"], uncertain=True, evidence_sufficient=False)
            with self.subTest(value=unsupported), self.assertRaises(ValueError):
                validate_decision(broken)

    def test_historical_and_feasibility_evaluations_do_not_fill_policy(self):
        row = decision()
        row["other_evaluations"] = [
            evaluation(kind="historical_legitimacy", assessment="affirmed", time_scope="historical"),
            evaluation(),
        ]
        before = copy.deepcopy(row)
        validate_decision(row)
        self.assertEqual(row, before)
        self.assertTrue(all(v == "unexpressed" for v in row["succession"].values()))
        self.assertEqual(row["current_package_stance"], "unexpressed")

    def test_mixed_provisions_do_not_require_whole_package_mixed(self):
        row = decision()
        row["reform_target"] = "specific_provision"
        row["provisions"] = [
            {"target": "架空の措置A", "stance": "support"},
            {"target": "架空の措置B", "stance": "oppose"},
        ]
        validate_decision(row)
        self.assertEqual(row["current_package_stance"], "unexpressed")

    def test_support_oppose_and_mixed_package_can_be_saved_separately(self):
        for stance in ("support", "oppose", "mixed"):
            row = decision()
            row.update(reform_target="current_package", current_package_stance=stance)
            validate_decision(row)
            self.assertTrue(all(v == "unexpressed" for v in row["succession"].values()))

    def test_free_text_and_auxiliary_order_are_preserved(self):
        row = decision()
        row.update(mentioned_reform_target="比較中の別案", other_succession="別の候補への意見")
        row["other_evaluations"] = [evaluation(), evaluation(kind="argument_validity", time_scope="unspecified")]
        before = copy.deepcopy(row)
        validate_decision(row)
        self.assertEqual(row, before)

    def test_other_reasons_can_keep_evidence_insufficient_without_unknown(self):
        row = decision()
        row.update(uncertain=True, evidence_sufficient=False)
        validate_decision(row)

    def test_aggregate_route_and_candidate_cannot_escape_private_review(self):
        for key, value in (("aggregation_route", "whole_policy"), ("aggregation_route", "scoped_only"),
                           ("existing_stance_candidate", "support"), ("existing_stance_candidate", False),
                           ("existing_stance_candidate", [])):
            row = decision()
            row[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_decision(row)


if __name__ == "__main__":
    unittest.main()
