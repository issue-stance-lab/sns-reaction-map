"""Shared input-version guard for Henoko initial conversion and later refreshes."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any


def verify_inputs(
    records: list[dict[str, Any]] | None = None,
    opinions: list[dict[str, Any]] | None = None,
    public_theme: Path | None = None,
) -> None:
    """Reject stale classifications even when aggregate opinion counts are unchanged.

    Import the existing source contracts only when called. Neither module imports
    the page renderer at module load time, so the conversion entry point can use
    this guard without a circular import.
    """
    if __package__:
        from . import build_henoko_arena as source
    else:
        import build_henoko_arena as source

    public_theme = public_theme or source.PUBLIC_THEME
    canonical, canonical_opinions = source.load_records(None)
    records = canonical if records is None else records
    opinions = canonical_opinions if opinions is None else opinions
    if records != canonical or opinions != canonical_opinions:
        raise source.IssueCountError("山なみの入力候補の本文・分類が正典に一致しません。候補の再読・公開集計を更新してください")
    

    public = json.loads(public_theme.read_text(encoding="utf-8"))
    # build_planet_data reads this registered public source. Do not silently ignore
    # an alternative function argument whose counts happen to have the same total.
    if public != json.loads(source.PUBLIC_THEME.read_text(encoding="utf-8")):
        raise source.IssueCountError("山なみの候補公開JSONが登録済みの公開JSONに一致しません")
    collected, total, *_ = source._public_counts(public)
    if collected != len(records) or total != len(opinions):
        raise source.IssueCountError("山なみの公開件数が正典に一致しません")
    for issue in public["issues"]:
        rows = [r for r in opinions if source.classification(r)["main_issue"] == issue["label"]]
        if int(issue["count"]) != len(rows):
            raise source.IssueCountError("山なみの論点別件数が正典に一致しません")
        for field, values, key in (("stance", "stances", "label"),
                                    ("intensity", "intensities", "id")):
            actual = Counter(source.classification(r).get(field) for r in rows)
            expected = Counter({v[key]: int(v["count"]) for v in issue[values]})
            if actual != expected:
                raise source.IssueCountError("山なみの公開分類が正典に一致しません: " + issue["label"])
