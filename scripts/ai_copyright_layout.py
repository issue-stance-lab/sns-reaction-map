"""生成AIと著作権の新デザインを、定期更新の全生成処理の最後に適用する（副首都 fukushuto_layout.py・皇室 koshitsu_layout.py と同じ型）。

- configs/ai-copyright-layout.json の enabled が true のときだけ働く。false の間は docs/ に触らない。
- 旧形式の生成器（build_ai_copyright_arena.py・refresh_adapters/ai_copyright.py・SEO/信頼情報の適用）は
  これまでどおり「元HTML」を入力にする。新デザイン公開後の元HTMLは data/page-sources/ai-copyright.html。
- 公開候補の隔離コピーでは、materialize が元HTMLを docs/ に戻し、全生成の最後に finish が
  元HTMLを保存し直したうえで新デザインのページを docs/ に書く。
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

PAGE = Path("docs/ai-copyright-reaction-map.html")
SOURCE = Path("data/page-sources/ai-copyright.html")
CONFIG = Path("configs/ai-copyright-layout.json")
MARKER = 'name="ai-copyright-layout"'
ARENA = Path("docs/ai-copyright-arena-data.js")  # 新デザインは読まないが、旧形式の生成器が引き続き作る


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
        raise ValueError("生成AIと著作権の新デザインが公開されていますが更新設定が無効です。旧形式で上書きしないため停止しました。")
    source = root / SOURCE
    if not source.is_file():
        raise ValueError("生成AIと著作権の新デザインの更新元HTMLがありません。公開ページは変更しません。")
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
        from .build_ai_copyright_redesign import build
    except ImportError:
        from build_ai_copyright_redesign import build  # type: ignore[no-redef]
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
    with tempfile.TemporaryDirectory(prefix="ai-copyright-layout-") as directory:
        stage = Path(directory)
        # 新デザインを最後まで作れてから、元HTMLと公開ページを置き換える
        build(page, stage, mode="release", root=root, as_of=as_of)
        source = root / SOURCE
        source.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(page, source)
        shutil.copy2(stage / PAGE.name, page)
    return {SOURCE: root / SOURCE, PAGE: page}


def rebuild(root, check: bool = False, as_of: str | None = None) -> bool:
    """新デザイン公開後に build_ai_copyright_arena.py を単独で動かしたとき用。元HTML・公開ページ・アリーナデータを作り直す。

    更新経路の finalize と同じく、公開JSONの集計を元HTMLへ貼り直してから旧形式の生成器を掛け、最後に新デザインを組む。
    sync_issue_counts.py（論点カードの件数バッジ）は公開ページを直接書くので、ここでは呼ばない（更新経路では元HTMLに掛かる）。
    """
    root = Path(root)
    from scripts.build_ai_copyright_arena import apply_public_counts, build as legacy_build

    source = source_for_refresh(root)
    with tempfile.TemporaryDirectory(prefix="ai-copyright-rebuild-") as directory:
        stage = Path(directory)
        updated = stage / "source.html"
        arena = stage / "arena-data.js"
        updated.write_text(apply_public_counts(source.read_text(encoding="utf-8")), encoding="utf-8")
        legacy_build(check=False, source=None, template=updated, output=updated, data_output=arena)
        _build()(updated, stage / "bundle", mode="release", root=root, as_of=as_of)
        new_page = (stage / "bundle" / PAGE.name).read_bytes()
        published_arena = root / ARENA
        changed = (updated.read_bytes() != source.read_bytes() or (root / PAGE).read_bytes() != new_page
                   or not published_arena.is_file() or published_arena.read_bytes() != arena.read_bytes())
        if changed and not check:
            shutil.copy2(updated, source)
            (root / PAGE).write_bytes(new_page)
            shutil.copy2(arena, published_arena)
    return changed
