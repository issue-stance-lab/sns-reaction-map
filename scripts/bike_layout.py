"""自転車の青切符の新デザインを、定期更新の全生成処理の最後に適用する（憲法改正論議 constitutional_layout.py と同じ型）。

- configs/bike-layout.json の enabled が true のときだけ働く。false の間は docs/ に触らない。
- 旧形式の生成器（build_bike_arena.py・bike_issue_media.py・refresh_planet_section.py・
  refresh_adapters/bike.py の潮目と連動表示と検索入口・SEO/信頼情報の適用）はこれまでどおり「元HTML」を入力にする。
  新デザイン公開後の元HTMLは data/page-sources/bike-blue-ticket.html。
- 公開候補の隔離コピーでは、materialize が元HTMLを docs/ に戻し、全生成の最後に finish が
  元HTMLを保存し直したうえで新デザインのページを docs/ に書く。
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

PAGE = Path("docs/bike-blue-ticket-reaction-map.html")
SOURCE = Path("data/page-sources/bike-blue-ticket.html")
CONFIG = Path("configs/bike-layout.json")
MARKER = 'name="bike-layout"'
TOPIC = "bike-blue-ticket"


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
        raise ValueError("自転車の青切符の新デザインが公開されていますが更新設定が無効です。旧形式で上書きしないため停止しました。")
    source = root / SOURCE
    if not source.is_file():
        raise ValueError("自転車の青切符の新デザインの更新元HTMLがありません。公開ページは変更しません。")
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
        from .build_bike_redesign import build
    except ImportError:
        from build_bike_redesign import build  # type: ignore[no-redef]
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
    with tempfile.TemporaryDirectory(prefix="bike-layout-") as directory:
        stage = Path(directory)
        # 新デザインを最後まで作れてから、元HTMLと公開ページを置き換える
        build(page, stage, mode="release", root=root, as_of=as_of)
        source = root / SOURCE
        source.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(page, source)
        shutil.copy2(stage / PAGE.name, page)
    return {SOURCE: root / SOURCE, PAGE: page}


def legacy_refresh(root, html: str) -> str:
    """元HTMLに、公開JSON・正典から作る旧形式の部分を掛け直す（refresh_adapters/bike.py の finalize と同じ順）。

    公開JSONの集計 → 論点ごとのX投稿 → アリーナの点・立場の帯（build_bike_arena.py）→
    山なみと連動表示・検索入口（refresh_planet_section.py の refresh。最後に bike_blue_ticket_connected.apply が掛かる）。
    潮目のカードは更新回どうしの比較なので、ここでは作り直さない（更新経路の adapter が元HTMLに貼る）。
    """
    root = Path(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    if str(root / "scripts") not in sys.path:
        sys.path.insert(0, str(root / "scripts"))
    from scripts.bike_issue_media import build_section, inject
    from scripts.build_bike_arena import apply_public_counts, build as legacy_build
    from scripts.refresh_planet_section import refresh as refresh_planet

    public = json.loads((root / "data" / "public" / "themes" / f"{TOPIC}.json").read_text(encoding="utf-8"))
    html = apply_public_counts(html)
    html = inject(html, build_section(public))
    with tempfile.TemporaryDirectory(prefix="bike-legacy-") as directory:
        stage = Path(directory) / "source.html"
        stage.write_text(html, encoding="utf-8")
        legacy_build(check=False, input_path=None, html_template=stage, output_html=stage)
        html = stage.read_text(encoding="utf-8")
    _old, html, failures = refresh_planet(TOPIC, source=html)
    if failures:
        raise ValueError("山なみの独自性の検査に不合格です: " + " / ".join(map(str, failures)))
    return html


def rebuild(root, check: bool = False, as_of: str | None = None) -> bool:
    """新デザイン公開後に build_bike_arena.py を単独で動かしたとき用。元HTMLと公開ページを作り直す。

    更新経路の finalize と同じく、旧形式の部分を元HTMLへ掛け直し（legacy_refresh）、最後に新デザインを組む。
    """
    root = Path(root)
    source = source_for_refresh(root)
    with tempfile.TemporaryDirectory(prefix="bike-rebuild-") as directory:
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
