"""消費税減税の新デザインを、定期更新の全生成処理の最後に適用する（辺野古 henoko_layout.py・あだ名禁止 nickname_layout.py と同じ型）。

- configs/consumption-tax-layout.json の enabled が true のときだけ働く。false の間は docs/ に触らない。
- 旧形式の生成器（build_consumption_tax_page.py（山なみの件数・論点カード・主張の照合・連動表示 consumption_tax_connected.apply）・
  refresh_adapters/consumption_tax.py の意見の推移（_apply_trend）と立場の対応表・SEO/信頼情報・授業節の適用）は
  これまでどおり「元HTML」を入力にする。新デザイン公開後の元HTMLは data/page-sources/consumption-tax-cut.html。
- 公開候補の隔離コピーでは、materialize が元HTMLを docs/ に戻し、全生成の最後に finish が
  元HTMLを保存し直したうえで新デザインのページを docs/ に書く。
- 旧ページの検索入口（docs/consumption-tax-search-entry.*）・連動表示（docs/consumption-tax-connected*）は新デザインでは読み込まないが、
  元HTMLが読むので docs/ に残す（更新経路でも元HTMLの中で作り直される）。
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

PAGE = Path("docs/consumption-tax-cut-reaction-map.html")
SOURCE = Path("data/page-sources/consumption-tax-cut.html")
CONFIG = Path("configs/consumption-tax-layout.json")
MARKER = 'name="consumption-tax-layout"'
TOPIC = "consumption-tax-cut"


def enabled(root) -> bool:
    path = Path(root) / CONFIG
    return path.exists() and json.loads(path.read_text(encoding="utf-8")).get("enabled") is True


def source_for_refresh(root) -> Path:
    """旧形式の生成器が読むべき元HTML。新デザインの公開ページを旧形式で上書きさせない。"""
    root = Path(root)
    page = root / PAGE
    if MARKER not in page.read_text(encoding="utf-8"):
        return page
    if not enabled(root):
        raise ValueError("消費税減税の新デザインが公開されていますが更新設定が無効です。旧形式で上書きしないため停止しました。")
    source = root / SOURCE
    if not source.is_file():
        raise ValueError("消費税減税の新デザインの更新元HTMLがありません。公開ページは変更しません。")
    return source


def materialize(root) -> None:
    """公開候補の隔離コピーの中だけで、旧形式の入力（元HTML）を docs/ に戻す。"""
    root = Path(root)
    if not enabled(root):
        return
    source = source_for_refresh(root)
    if source != root / PAGE:
        shutil.copy2(source, root / PAGE)


def _build():
    try:
        from .build_consumption_tax_redesign import build
    except ImportError:
        from build_consumption_tax_redesign import build  # type: ignore[no-redef]
    return build


def finish(root, as_of: str | None = None) -> dict:
    """隔離コピーで全生成の最後に呼ぶ。変わり得る公開物（元HTML・公開ページ）を返す。"""
    root = Path(root)
    if not enabled(root):
        return {}
    page = root / PAGE
    if MARKER in page.read_text(encoding="utf-8"):
        raise ValueError("最終レイアウト生成には更新済みの元HTMLが必要です。新ページの再入力は拒否しました。")
    build = _build()
    with tempfile.TemporaryDirectory(prefix="consumption-tax-layout-") as directory:
        stage = Path(directory)
        # 新デザインを最後まで作れてから、元HTMLと公開ページを置き換える
        build(page, stage, mode="release", root=root, as_of=as_of)
        source = root / SOURCE
        source.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(page, source)
        shutil.copy2(stage / PAGE.name, page)
    return {SOURCE: root / SOURCE, PAGE: page}


def legacy_refresh(root, html: str) -> str:
    """元HTMLに、正典・公開JSONから作る旧形式の部分を掛け直す（定期更新の adapter の build → finalize と同じ順）。

    ページ生成（build_consumption_tax_page.build：山なみの件数・論点カード・主張の照合・背景・立場の内訳・検索入口・連動表示）→
    意見の推移（refresh_adapters/consumption_tax._apply_trend。正典から数え直す）→ 調査条件（research_conditions）→
    公開JSONの集計（apply_public_counts と山なみの作り直し）。どれも正典（非公開）と公開JSONだけを読む。
    最後にテーマ共通の見た目（apply_theme_design.transform。件数の札 THEME_COUNT など）を掛け直す（更新経路では公開候補生成の
    apply_theme_design.finish が元HTMLに掛ける。掛けないと単独実行のたびに元HTMLから件数の札が落ちる）。
    SEO・信頼情報（apply_theme_trust.py）と授業節（apply_classroom_section.py）は更新経路の共通処理なので、ここでは掛けない。
    """
    root = Path(root)
    for path in (root, root / "scripts"):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    from scripts.build_consumption_tax_page import apply_public_counts, build, research_conditions
    from scripts.refresh_adapters.consumption_tax import _apply_trend
    from consumption_tax_connected import apply as connect_page
    from refresh_planet_section import refresh

    with tempfile.TemporaryDirectory(prefix="consumption-tax-legacy-") as directory:
        stage = Path(directory)
        template = stage / "template.html"
        output = stage / "page.html"
        template.write_text(html, encoding="utf-8")
        # 主張の照合の出所ファイル（data/verification/consumption-tax-cut-claims.json）は claim_posts の写しで、
        # 更新経路の adapter が書く。ここ（--check を含む単独実行）では隔離した場所へ書き、作業ツリーに触らない
        build(template=template, output=output, verification_dest=stage / "verification")
        _apply_trend(root, output)
        html = connect_page(research_conditions(output.read_text(encoding="utf-8")))
    html = apply_public_counts(html)
    _, html, failures = refresh(TOPIC, source=html)
    if failures:
        raise ValueError("連動表示の再生成検査: " + "; ".join(failures))
    from scripts.apply_theme_design import transform
    return transform(connect_page(html), TOPIC)


def rebuild(root, check: bool = False, as_of: str | None = None) -> bool:
    """新デザイン公開後に build_consumption_tax_page.py を単独で動かしたとき用。元HTMLと公開ページを作り直す。

    更新経路と同じく、旧形式の部分を元HTMLへ掛け直し（legacy_refresh）、最後に新デザインを組む。
    """
    root = Path(root)
    source = source_for_refresh(root)
    with tempfile.TemporaryDirectory(prefix="consumption-tax-rebuild-") as directory:
        stage = Path(directory)
        updated = stage / "source.html"
        updated.write_text(legacy_refresh(root, source.read_text(encoding="utf-8")), encoding="utf-8")
        _build()(updated, stage / "bundle", mode="release", root=root, as_of=as_of)
        new_page = (stage / "bundle" / PAGE.name).read_bytes()
        changed = updated.read_bytes() != source.read_bytes() or (root / PAGE).read_bytes() != new_page
        if changed and not check:
            shutil.copy2(updated, source)
            (root / PAGE).write_bytes(new_page)
    return changed
