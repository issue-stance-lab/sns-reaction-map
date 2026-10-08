"""Shared input-version guard for Henoko initial conversion and later refreshes.

入力は「候補」（定期更新では、正典に今回の追加分を足した累積候補）、または省略時の正典そのもの。
2026-10-08までは「候補が今ディスクにある正典と完全に一致すること」を求めていたため、
正典を書き換える前（`--prepare-promotion`）に新しい回を入れた候補は必ず止まった。
今は、候補を入力にして次の3点を検査する。古い分類・古い公開集計を黙って通さない点は変えていない。

1. 候補は今の正典を1件も書き換えていない（正典の全投稿が、そのままの中身で候補に含まれる）。
   既存投稿の本文・分類を新しい回に混ぜて書き換えたり、古い候補を使ったりすると止まる。
2. 候補に対応する公開JSONが、候補と一致する。意見の一覧、収集・意見の件数、論点別の件数、
   論点×立場×強度の件数、元データの指紋（source_sha256）を見る。件数が同じでも、
   分類や本文が1件でも違えば指紋で止まる。
3. 再読記録（data/verification/reread/）は、この関数のあとで山なみを作る `bpd.build` が
   候補を入力に検査する（再読済み投稿の本文・論点・意見判定が変わっていたら止まる）。
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any


def _modules():
    """Import lazily: neither module imports the renderer at load time, so the
    conversion entry point can use this guard without a circular import."""
    if __package__:
        from . import build_henoko_arena as source
        from . import public_registry_common as common
    else:
        import build_henoko_arena as source
        import public_registry_common as common
    return source, common


def _load_public(source: Any, public_theme: Path | dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(public_theme, dict):
        return public_theme
    return json.loads(Path(public_theme or source.PUBLIC_THEME).read_text(encoding="utf-8"))


def _verify_extends_canonical(source: Any, common: Any, canonical: list[dict[str, Any]],
                              records: list[dict[str, Any]]) -> None:
    """正典の全投稿が、中身を変えずに候補へ含まれていることを確かめる。"""
    missing = (Counter(common.canonical_compact(r) for r in canonical)
               - Counter(common.canonical_compact(r) for r in records))
    if missing:
        raise source.IssueCountError(
            f"山なみの入力候補が、今の正典の投稿{sum(missing.values())}件をそのままの形では含んでいません"
            "（既存投稿の本文・分類を書き換えたか、古い候補です）。"
            "新しい回は、正典に足す形の候補にしてください")


def verify_inputs(
    records: list[dict[str, Any]] | None = None,
    opinions: list[dict[str, Any]] | None = None,
    public_theme: Path | dict[str, Any] | None = None,
    *,
    canonical: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """候補（省略時は正典）・公開JSON・意見一覧が同じ版であることを確かめ、公開JSONを返す。

    public_theme を省くと登録済みの公開JSON（正典と同じ版のときの入力）を読む。候補を入力にする
    ときは、候補から作った公開JSON（build_henoko_arena.candidate_public_theme）を渡す。
    返した公開JSONを、そのまま山なみの生成（bpd.build）の入力にすること。
    canonical は正典の代わりに比べる相手（テスト用）。省くとディスク上の正典を読む。
    """
    source, common = _modules()
    if canonical is None:
        canonical, _ = source.load_records(None)
    records = canonical if records is None else records
    derived = source.opinions_of(records)
    if opinions is not None and opinions != derived:
        raise source.IssueCountError(
            "山なみの入力候補の意見一覧が、候補の本文・分類から導かれる意見と一致しません")
    opinions = derived
    _verify_extends_canonical(source, common, canonical, records)

    public = _load_public(source, public_theme)
    collected, total, *_ = source._public_counts(public)
    if collected != len(records) or total != len(opinions):
        raise source.IssueCountError("山なみの公開件数が入力候補に一致しません")
    for issue in public["issues"]:
        rows = [r for r in opinions if source.classification(r)["main_issue"] == issue["label"]]
        if int(issue["count"]) != len(rows):
            raise source.IssueCountError("山なみの論点別件数が入力候補に一致しません")
        for field, values, key in (("stance", "stances", "label"),
                                    ("intensity", "intensities", "id")):
            actual = Counter(source.classification(r).get(field) for r in rows)
            expected = Counter({v[key]: int(v["count"]) for v in issue[values]})
            if actual != expected:
                raise source.IssueCountError("山なみの公開分類が入力候補に一致しません: " + issue["label"])
    if public.get("source_sha256") != common.source_sha256(records):
        raise source.IssueCountError(
            "山なみの公開JSONの元データ指紋（source_sha256）が入力候補に一致しません。"
            "候補の本文・分類が公開集計の元データと違います。公開JSONを作り直してください")
    return public
