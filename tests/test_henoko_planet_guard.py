"""辺野古の入力ガード（henoko_planet_guard）を、合成データで固定する。

非公開の正典を使わないので、正典を持たないCIでも走る。正典が要る検査
（候補から山なみ全体を作る・CLI）は tests/test_henoko_verified_refresh.py にある。

2026-10-08まで、ガードは「候補が今ディスクにある正典と完全に一致すること」を求めていたため、
新しい回を足した候補は `--prepare-promotion` で必ず止まった。今は次の2つを両方確かめる。
- 通る: 今の正典を書き換えずに追加分を足した候補が、その候補から作った公開JSONと一致するとき
- 止まる: 既存投稿の書き換え・欠落、古い公開集計、件数が同じでも分類や本文が違うとき
"""
import copy
import unittest

from scripts import build_henoko_arena as builder
from scripts import build_planet_page_preview as preview
from scripts import henoko_planet_guard as guard

ISSUES = [issue["main_issue"] for issue in builder.ISSUE_DEFS]
STANCES = [builder.SUPPORT, builder.OPPOSE, builder.SPLIT, builder.NEUTRAL]
INTENSITIES = ["low", "medium", "high"]


def post(key: str, issue: str, stance: str, intensity: str, opinion: bool = True) -> dict:
    return {
        "tweet_id": key,
        "url": f"https://x.com/example/status/{key}",
        "text": f"合成の投稿本文 {key}",
        "classification": {
            "is_relevant": True,
            "is_opinion": opinion,
            "main_issue": issue if opinion else "その他",
            "stance": stance,
            "intensity": intensity,
        },
    }


def synthetic_canonical() -> list[dict]:
    rows = [
        post(f"c{n}", ISSUES[n % len(ISSUES)], STANCES[(n // len(ISSUES)) % len(STANCES)],
             INTENSITIES[n % len(INTENSITIES)])
        for n in range(48)
    ]
    rows += [post(f"c-other{n}", "その他", STANCES[0], INTENSITIES[0], opinion=False) for n in range(4)]
    return rows


def synthetic_wave() -> list[dict]:
    wave = [post(f"w{n}", ISSUES[n % len(ISSUES)], STANCES[n % len(STANCES)], INTENSITIES[n % len(INTENSITIES)])
            for n in range(6)]
    wave += [post(f"w-other{n}", "その他", STANCES[0], INTENSITIES[0], opinion=False) for n in range(2)]
    return wave


class CandidateInputTests(unittest.TestCase):
    def setUp(self):
        self.canonical = synthetic_canonical()
        self.wave = synthetic_wave()
        self.candidate = copy.deepcopy(self.canonical) + copy.deepcopy(self.wave)
        self.canonical_public = builder.candidate_public_theme(self.canonical)
        self.candidate_public = builder.candidate_public_theme(self.candidate)

    def verify(self, records, public, opinions=None, canonical=None):
        return guard.verify_inputs(records, opinions, public,
                                   canonical=self.canonical if canonical is None else canonical)

    # ---------------------------------------------------------------- 通る

    def test_canonical_passes_against_its_own_public_json(self):
        self.assertIs(self.verify(None, self.canonical_public), self.canonical_public)
        self.assertIs(self.verify(self.canonical, self.canonical_public), self.canonical_public)

    def test_candidate_that_adds_a_wave_passes_even_though_it_differs_from_canonical(self):
        # これが2026-10-08まで止まっていた場面。候補≠正典でも、正典を書き換えず、
        # 候補から作った公開JSONと一致していれば通る。
        self.assertNotEqual(self.candidate, self.canonical)
        public = self.verify(self.candidate, self.candidate_public)
        self.assertEqual(public["collected_count"], len(self.canonical) + len(self.wave))
        self.assertEqual(public["opinion_count"], len(builder.opinions_of(self.candidate)))
        self.assertGreater(public["opinion_count"], self.canonical_public["opinion_count"])

    def test_candidate_may_be_given_with_its_derived_opinion_list(self):
        self.verify(self.candidate, self.candidate_public, opinions=builder.opinions_of(self.candidate))

    def test_wave_that_adds_only_non_opinions_still_passes(self):
        rows = self.canonical + [post("w-x", "その他", STANCES[0], INTENSITIES[0], opinion=False)]
        self.verify(rows, builder.candidate_public_theme(rows))

    # ---------------------------------------------------------------- 止まる: 古い公開集計

    def test_candidate_is_rejected_against_the_stale_public_json(self):
        with self.assertRaisesRegex(builder.IssueCountError, "公開件数"):
            self.verify(self.candidate, self.canonical_public)

    def test_public_json_with_moved_stance_count_is_rejected_even_with_same_total(self):
        data = copy.deepcopy(self.candidate_public)
        issue = next(x for x in data["issues"] if x["count"])
        source = next(x for x in issue["stances"] if x["count"])
        target = next(x for x in issue["stances"] if x is not source)
        source["count"] -= 1
        target["count"] += 1
        with self.assertRaisesRegex(builder.IssueCountError, "公開分類"):
            self.verify(self.candidate, data)

    def test_public_json_of_another_theme_is_rejected(self):
        data = copy.deepcopy(self.candidate_public)
        data["theme_id"] = "another-topic"
        with self.assertRaises(builder.IssueCountError):
            self.verify(self.candidate, data)

    def test_count_preserving_reclassification_is_caught_by_the_source_fingerprint(self):
        # 論点が違い、立場と強度が同じ2件の論点を入れ替えると、論点別・立場別・強度別の件数は
        # 1つも変わらない。件数だけの突き合わせは素通りするので、元データの指紋で止める。
        opinions = builder.opinions_of(self.canonical)
        first = opinions[0]
        second = next(r for r in opinions
                      if builder.classification(r)["main_issue"] != builder.classification(first)["main_issue"]
                      and builder.classification(r)["stance"] == builder.classification(first)["stance"]
                      and builder.classification(r)["intensity"] == builder.classification(first)["intensity"])
        swapped = copy.deepcopy(self.canonical)
        a = next(r for r in swapped if r["tweet_id"] == first["tweet_id"])
        b = next(r for r in swapped if r["tweet_id"] == second["tweet_id"])
        a["classification"]["main_issue"], b["classification"]["main_issue"] = (
            b["classification"]["main_issue"], a["classification"]["main_issue"])
        # 正典が（手で）書き換わったが、公開JSONは古いまま、という場面。
        with self.assertRaisesRegex(builder.IssueCountError, "元データ指紋"):
            self.verify(swapped, self.canonical_public, canonical=swapped)

    def test_body_only_change_is_caught_by_the_source_fingerprint(self):
        edited = copy.deepcopy(self.canonical)
        edited[0]["text"] += " 書き換え"
        with self.assertRaisesRegex(builder.IssueCountError, "元データ指紋"):
            self.verify(edited, self.canonical_public, canonical=edited)

    # ---------------------------------------------------------------- 止まる: 既存投稿の書き換え

    def test_candidate_that_rewrites_an_existing_post_is_rejected(self):
        for kind in ("stance", "issue", "body"):
            with self.subTest(kind=kind):
                rows = copy.deepcopy(self.candidate)
                target = rows[0]
                if kind == "stance":
                    target["classification"]["stance"] = STANCES[1]
                elif kind == "issue":
                    target["classification"]["main_issue"] = ISSUES[-1]
                else:
                    target["text"] += " 書き換え"
                # 書き換えた候補に合わせて公開JSONを作り直しても、既存投稿を変えたこと自体で止まる。
                with self.assertRaisesRegex(builder.IssueCountError, "入力候補"):
                    self.verify(rows, builder.candidate_public_theme(rows))

    def test_candidate_that_drops_an_existing_post_is_rejected(self):
        rows = copy.deepcopy(self.candidate)[1:]
        with self.assertRaisesRegex(builder.IssueCountError, "入力候補"):
            self.verify(rows, builder.candidate_public_theme(rows))

    def test_candidate_older_than_the_canonical_is_rejected(self):
        # 正典がすでに今回の回を取り込んだあとで、古い候補（追加前）を渡した場面。
        with self.assertRaisesRegex(builder.IssueCountError, "入力候補"):
            self.verify(self.canonical, self.canonical_public, canonical=self.candidate)

    def test_opinion_list_that_does_not_derive_from_the_candidate_is_rejected(self):
        derived = builder.opinions_of(self.candidate)
        for given in (derived[:-1], derived + [derived[0]], list(reversed(derived))):
            with self.subTest(size=len(given)):
                with self.assertRaisesRegex(builder.IssueCountError, "入力候補"):
                    self.verify(self.candidate, self.candidate_public, opinions=given)


class PlanetBuildPairingTests(unittest.TestCase):
    """山なみの生成は、候補の本文と公開JSONを必ずセットで受け取る。"""

    def test_candidate_without_matching_public_json_is_refused_before_reading_anything(self):
        for kwargs in ({"canonical": []}, {"public": {}}):
            with self.subTest(kwargs=sorted(kwargs)):
                with self.assertRaisesRegex(ValueError, "両方"):
                    preview.bpd.build(builder.THEME, **kwargs)


if __name__ == "__main__":
    unittest.main()
