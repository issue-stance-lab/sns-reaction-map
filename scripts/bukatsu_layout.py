"""Opt-in final layout pass, after all existing data/SEO builders finish."""
from pathlib import Path
import json
import shutil
import tempfile

PAGE = Path("docs/bukatsu-chiiki-reaction-map.html")
SOURCE = Path("data/page-sources/bukatsu-chiiki.html")
CONFIG = Path("configs/bukatsu-layout.json")
MARKER = 'name="bukatsu-layout"'

def enabled(root):
    path = Path(root) / CONFIG
    return path.exists() and json.loads(path.read_text()).get("enabled") is True

def source_for_refresh(root):
    root = Path(root)
    page = root / PAGE
    if MARKER not in page.read_text():
        return page
    if not enabled(root):
        raise ValueError("新デザインが公開されていますが更新設定が無効です。旧形式で上書きしないため停止しました。")
    source = root / SOURCE
    if not source.is_file():
        raise ValueError("新デザインの更新元HTMLがありません。公開ページは変更しません。")
    return source

def materialize(root):
    """Restore legacy input only inside an isolated publication candidate tree."""
    root=Path(root)
    if not enabled(root):
        return
    source=source_for_refresh(root)
    if source != root/PAGE:
        shutil.copy2(source,root/PAGE)

def rebuild(root, check=False):
    """Standalone builder preserves both the legacy input and the published layout."""
    root=Path(root)
    from scripts.build_bukatsu_arena import transform
    from scripts.build_bukatsu_redesign import build
    source=source_for_refresh(root)
    old=source.read_text()
    updated=transform(old)
    with tempfile.TemporaryDirectory(prefix="bukatsu-rebuild-") as directory:
        stage=Path(directory)
        source_file=stage/"source.html";source_file.write_text(updated)
        manifest=build(source_file,stage/"bundle",mode="release",root=root)
        changed=old!=updated or any(
            not (root/"docs"/relative).exists() or
            (root/"docs"/relative).read_bytes()!=(stage/"bundle"/relative).read_bytes()
            for relative in manifest["files"] if not relative.startswith("evidence/"))
        if not check and changed:
            source.write_text(updated)
            for relative in manifest["files"]:
                if relative.startswith("evidence/"):continue
                target=root/"docs"/relative;target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(stage/"bundle"/relative,target)
    return changed


def finish(root):
    """Run in the isolated publication candidate, returning every changed artifact."""
    root = Path(root)
    if not enabled(root):
        return {}
    page = root / PAGE
    if MARKER in page.read_text():
        raise ValueError("最終レイアウト生成には更新済みの元HTMLが必要です。新ページの再入力は拒否しました。")
    try:
        from .build_bukatsu_redesign import build
    except ImportError:
        from build_bukatsu_redesign import build
    with tempfile.TemporaryDirectory(prefix="bukatsu-layout-") as directory:
        stage = Path(directory)
        manifest = build(page, stage, mode="release", root=root)
        # Finish rendering successfully before replacing either the source or the page.
        source = root / SOURCE
        source.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(page, source)
        targets = {SOURCE: source}
        for relative in manifest["files"]:
            if relative.startswith("evidence/"):
                continue
            destination = root / "docs" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(stage / relative, destination)
            targets[destination.relative_to(root)] = destination
    return targets
