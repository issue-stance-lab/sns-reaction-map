"""部活動の地域移行の新デザインを、定期更新の全生成処理の最後に適用する（opt-in の最終レイアウト工程）。

- configs/bukatsu-layout.json の enabled が true のときだけ働く。元HTMLは data/page-sources/bukatsu-chiiki.html。
- 設定の version で組み立て方を選ぶ。
  - "redesign-v2"（最新の型、2026-10-14〜）: scripts/build_bukatsu_redesign_v2.py。冒頭・読書面・背景は設定JSONと公開JSON・
    再読データ・立場の対応表から作り、照合が合わなければ止まる（データが変わっても指紋で止まらない）。公開物はページと全文・印刷版の2つ。
  - それ以外（"redesign-v1" か未設定。2026-10-10 公開の初期型）: scripts/build_bukatsu_redesign.py。凍結した本文と
    scripts/bukatsu_redesign/editorial-review.json の指紋で、データが1件変わると止まる（指紋の更新手順は DATA_REFRESH.md）。
- 旧形式の生成器（adapter の update_bukatsu_tide.py・意見の推移・連動表示、finalize の refresh_planet_section.py・
  build_bukatsu_arena.py、SEO・授業節）は、どちらの版でもこれまでどおり「元HTML」に掛ける。
"""
from pathlib import Path
import json
import shutil
import tempfile

PAGE = Path("docs/bukatsu-chiiki-reaction-map.html")
SOURCE = Path("data/page-sources/bukatsu-chiiki.html")
CONFIG = Path("configs/bukatsu-layout.json")
MARKER = 'name="bukatsu-layout"'
V2 = "redesign-v2"


def _config(root):
    path = Path(root) / CONFIG
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def enabled(root):
    return _config(root).get("enabled") is True


def version(root):
    """組み立てる版。"redesign-v2" なら最新の型、それ以外は初期型。"""
    return V2 if _config(root).get("version") == V2 else "redesign-v1"


def source_for_refresh(root):
    root = Path(root)
    page = root / PAGE
    if MARKER not in page.read_text(encoding="utf-8"):
        return page
    if not enabled(root):
        raise ValueError("新デザインが公開されていますが更新設定が無効です。旧形式で上書きしないため停止しました。")
    source = root / SOURCE
    if not source.is_file():
        raise ValueError("新デザインの更新元HTMLがありません。公開ページは変更しません。")
    return source


def materialize(root):
    """Restore legacy input only inside an isolated publication candidate tree."""
    root = Path(root)
    if not enabled(root):
        return
    source = source_for_refresh(root)
    if source != root / PAGE:
        shutil.copy2(source, root / PAGE)


def _builder(root):
    if version(root) == V2:
        try:
            from .build_bukatsu_redesign_v2 import build
        except ImportError:
            from build_bukatsu_redesign_v2 import build  # type: ignore[no-redef]
    else:
        try:
            from .build_bukatsu_redesign import build
        except ImportError:
            from build_bukatsu_redesign import build  # type: ignore[no-redef]
    return build


def _published(manifest):
    """docs/ に置く生成物（初期型の確認用の evidence/ は置かない）。"""
    return [relative for relative in manifest["files"] if not relative.startswith("evidence/")]


def rebuild(root, check=False):
    """Standalone builder preserves both the legacy input and the published layout."""
    root = Path(root)
    from scripts.build_bukatsu_arena import transform
    source = source_for_refresh(root)
    old = source.read_text(encoding="utf-8")
    updated = transform(old)
    with tempfile.TemporaryDirectory(prefix="bukatsu-rebuild-") as directory:
        stage = Path(directory)
        source_file = stage / "source.html"
        source_file.write_text(updated, encoding="utf-8")
        manifest = _builder(root)(source_file, stage / "bundle", mode="release", root=root)
        changed = old != updated or any(
            not (root / "docs" / relative).exists() or
            (root / "docs" / relative).read_bytes() != (stage / "bundle" / relative).read_bytes()
            for relative in _published(manifest))
        if not check and changed:
            source.write_text(updated, encoding="utf-8")
            for relative in _published(manifest):
                target = root / "docs" / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(stage / "bundle" / relative, target)
    return changed


def finish(root, as_of=None):
    """Run in the isolated publication candidate, returning every changed artifact."""
    root = Path(root)
    if not enabled(root):
        return {}
    page = root / PAGE
    if MARKER in page.read_text(encoding="utf-8"):
        raise ValueError("最終レイアウト生成には更新済みの元HTMLが必要です。新ページの再入力は拒否しました。")
    build = _builder(root)
    with tempfile.TemporaryDirectory(prefix="bukatsu-layout-") as directory:
        stage = Path(directory)
        if version(root) == V2:
            manifest = build(page, stage, mode="release", root=root, as_of=as_of)
        else:
            manifest = build(page, stage, mode="release", root=root)
        # Finish rendering successfully before replacing either the source or the page.
        source = root / SOURCE
        source.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(page, source)
        targets = {SOURCE: source}
        for relative in _published(manifest):
            destination = root / "docs" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(stage / relative, destination)
            targets[destination.relative_to(root)] = destination
    return targets
