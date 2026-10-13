"""辺野古高校生死亡事故の新デザインを、定期更新の全生成処理の最後に適用する（学校でのあだ名禁止 nickname_layout.py と同じ型）。

- configs/henoko-layout.json の enabled が true のときだけ働く。false の間は docs/ に触らない。
- 旧形式の生成器（build_henoko_arena.py（山なみの件数・連動表示・アリーナの点。山なみの入力の版の守り
  scripts/henoko_planet_guard.py もここで働く）・
  refresh_adapters/henoko.py の潮目・SEO/信頼情報の適用）はこれまでどおり「元HTML」を入力にする。
  新デザイン公開後の元HTMLは data/page-sources/henoko-student-accident.html。
- 公開候補の隔離コピーでは、materialize が元HTMLを docs/ に戻し、全生成の最後に finish が
  元HTMLを保存し直したうえで新デザインのページを docs/ に書く。
- アリーナの点（docs/henoko-arena-data.js）は新デザインでは読み込まないが、更新経路で引き続き生成される
  （元HTMLの旧形式の部品が読む。build_henoko_arena.py が元HTMLと一緒に作る）。
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

PAGE = Path("docs/henoko-student-accident-reaction-map.html")
ARENA_DATA = Path("docs/henoko-arena-data.js")
SOURCE = Path("data/page-sources/henoko-student-accident.html")
CONFIG = Path("configs/henoko-layout.json")
MARKER = 'name="henoko-layout"'
TOPIC = "henoko-student-accident"


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
        raise ValueError("辺野古高校生死亡事故の新デザインが公開されていますが更新設定が無効です。旧形式で上書きしないため停止しました。")
    source = root / SOURCE
    if not source.is_file():
        raise ValueError("辺野古高校生死亡事故の新デザインの更新元HTMLがありません。公開ページは変更しません。")
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
        from .build_henoko_redesign import build
    except ImportError:
        from build_henoko_redesign import build  # type: ignore[no-redef]
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
    with tempfile.TemporaryDirectory(prefix="henoko-layout-") as directory:
        stage = Path(directory)
        # 新デザインを最後まで作れてから、元HTMLと公開ページを置き換える
        build(page, stage, mode="release", root=root, as_of=as_of)
        source = root / SOURCE
        source.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(page, source)
        shutil.copy2(stage / PAGE.name, page)
    return {SOURCE: root / SOURCE, PAGE: page}


def legacy_refresh(root, html: str, arena_out: Path) -> str:
    """元HTMLに、正典・公開JSONから作る旧形式の部分を掛け直す（定期更新の adapter の build → finalize と同じ順）。

    旧形式の生成（build_henoko_arena.py の build_page：山なみの件数・調査条件・詳細データの表・連動表示（henoko_connected.apply）。
    山なみの入力の版は henoko_planet_guard.verify_inputs が確かめる）→ アリーナの点 → 公開JSONの集計（apply_public_counts）。
    アリーナの点は arena_out に書く。潮目のカードは更新回どうしの比較なので、ここでは作り直さない（更新経路の adapter が元HTMLに貼る）。
    背景パネル（#bukatsu-background・#bukatsu-check）は初回の切り替えで書かれた静的な部分で、定期更新の経路でも掛からないので、ここでも掛けない。
    """
    root = Path(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    if str(root / "scripts") not in sys.path:
        sys.path.insert(0, str(root / "scripts"))
    from scripts.build_henoko_arena import apply_public_counts, arena_data_js, arena_rows, build_page, load_records

    records, opinions = load_records(None)
    html = build_page(html, records, opinions, None)
    Path(arena_out).write_text(arena_data_js(arena_rows(opinions)), encoding="utf-8")
    return apply_public_counts(html)


def rebuild(root, check: bool = False, as_of: str | None = None) -> bool:
    """新デザイン公開後に build_henoko_arena.py を単独で動かしたとき用。元HTML・アリーナの点・公開ページを作り直す。

    更新経路の finalize と同じく、旧形式の部分を元HTMLへ掛け直し（legacy_refresh）、最後に新デザインを組む。
    """
    root = Path(root)
    source = source_for_refresh(root)
    with tempfile.TemporaryDirectory(prefix="henoko-rebuild-") as directory:
        stage = Path(directory)
        updated = stage / "source.html"
        arena = stage / ARENA_DATA.name
        updated.write_text(legacy_refresh(root, source.read_text(encoding="utf-8"), arena), encoding="utf-8")
        _build()(updated, stage / "bundle", mode="release", root=root, as_of=as_of)
        new_page = (stage / "bundle" / PAGE.name).read_bytes()
        current_arena = (root / ARENA_DATA).read_bytes() if (root / ARENA_DATA).is_file() else b""
        changed = (updated.read_bytes() != source.read_bytes() or (root / PAGE).read_bytes() != new_page
                   or arena.read_bytes() != current_arena)
        if changed and not check:
            shutil.copy2(updated, source)
            shutil.copy2(arena, root / ARENA_DATA)
            (root / PAGE).write_bytes(new_page)
    return changed
