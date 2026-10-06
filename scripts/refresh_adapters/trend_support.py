"""「意見の推移」（節と単体の画像）を、テーマの更新処理（adapter）から作り直すための共通の部品。

消費税減税と部活動の地域移行が使う。節の本体は scripts/build_trend_section.py、画像は
scripts/build_trend_images.py にあり、ここは「更新のたびに累積候補から貼り直す」「画像を2回作って
同じバイト列になることを確かめる」ところだけを持つ。
"""

from __future__ import annotations

import sys
from pathlib import Path


def _import_trend(root: Path):
    sys.path.insert(0, str(root / "scripts"))
    import build_trend_section  # type: ignore[import-not-found]

    return build_trend_section


def render_trend(root: Path, topic: str, html: str, source: Path | None) -> str:
    """ページの「意見の推移」の節を、元データから数え直して貼り直したHTMLを返す。

    元データが無い隔離環境（テストなど）では、既存の節をそのまま残す（黙って消さない）。
    """
    trend = _import_trend(root)
    if source is not None and source.is_file():
        return trend.render_for(topic, html, source)
    return html


def check_model_break(root: Path, topic: str, current_date: str, previous_model: str | None,
                      current_model: str | None) -> None:
    """分類に使うAIが前の回から変わったのに、推移の注意書きに記録が無ければ止める。

    回の間の差にAIの違いが混じる。記録（TREND_THEMES の model_breaks）に日付を足すと、
    グラフの注意書きに「この回からAIを切り替えました」が出る。記録しないまま公開しない。
    """
    if not previous_model or not current_model or previous_model == current_model:
        return
    trend = _import_trend(root)
    if current_date not in trend.TREND_THEMES[topic].get("model_breaks", []):
        raise ValueError(
            f"分類に使うAIが変わりました（{previous_model} → {current_model}）。推移のグラフの注意書きに、"
            f"この回（{current_date}）からAIを切り替えたことを出す必要があります。"
            f"scripts/build_trend_section.py の TREND_THEMES[\"{topic}\"][\"model_breaks\"] に \"{current_date}\" を足して、"
            "もう一度実行してください。"
        )


def build_images(root: Path, topic: str, stage: Path, candidate: Path) -> dict[Path, Path]:
    """単体で配る画像（意見の推移の折れ線）を2回作り、同じバイト列になることを確かめて公開物にする。

    日本語フォントが無い環境では作れず、ここで止まる（文字が□の画像を公開しない）。
    戻り値は {公開先の相対パス: 作った画像}。
    """
    sys.path.insert(0, str(root / "scripts"))
    from build_trend_images import render_for as render_images  # type: ignore[import-not-found]
    from build_trend_section import IMAGE_DIR  # type: ignore[import-not-found]

    first = render_images(topic, candidate, stage / "trend-images")
    second = render_images(topic, candidate, stage / "idempotence" / "trend-images")
    for (kind, variant), path in first.items():
        if path.read_bytes() != second[(kind, variant)].read_bytes():
            raise ValueError(f"{topic}の推移画像（{kind}/{variant}）は同じ候補の2回目実行でバイト列が変わりました")
    return {IMAGE_DIR / path.name: path for path in first.values()}
