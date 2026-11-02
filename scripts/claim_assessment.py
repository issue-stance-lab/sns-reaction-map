"""主張の資料照合と、条件・評価の説明を区別する公開契約。"""
from __future__ import annotations

VERDICTS = {"fact", "gap", "miss"}
CONTEXT_LABELS = {
    "conditional_explanation": "条件を確認",
    "evaluation_context": "評価の論点",
}


def validate_assessment(claim: dict) -> None:
    kind = claim.get("assessment_kind", "source_comparison")
    verdict = claim.get("verdict")
    if kind == "source_comparison":
        if verdict not in VERDICTS:
            raise ValueError(f"資料照合の判定語が不正です: {verdict!r}")
    elif kind in CONTEXT_LABELS:
        if verdict is not None:
            raise ValueError("条件・評価の説明に正誤の判定を付けることはできません")
    else:
        raise ValueError(f"説明の種類が不正です: {kind!r}")


def context_label(claim: dict) -> str:
    validate_assessment(claim)
    return CONTEXT_LABELS[claim["assessment_kind"]]
