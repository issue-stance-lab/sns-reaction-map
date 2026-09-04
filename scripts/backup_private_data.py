#!/usr/bin/env python3
"""Git管理外の正典データと更新履歴を1コマンドでバックアップする（課題33）。

対象は THEMES.yaml の `sample_file` のうち Git が追跡していないもの（本文・URL・
ユーザー識別子を含むため公開リポジトリに置けない）と、`social-samples/` 配下で
Git ignore されている更新履歴・旧raw・分類ファイル一式。`data/verification/` は
Git にあるのでバックアップ対象に含めない。

    # バックアップを作る（保存先は課題33で決めた非公開ストレージ）
    python3 scripts/backup_private_data.py --dest /Volumes/Backup/issue-stance

    # 作ったアーカイブが壊れていないか、別マシンで復元できるかを確認する
    python3 scripts/backup_private_data.py --verify /Volumes/Backup/issue-stance/private-data-<run-id>.tar.gz

検証は「アーカイブを展開して、マニフェストのSHA-256と件数に一致するか」を見る。
失敗したら exit 1 を返すので、定期実行しても失敗を検知できる。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sync_portal_stats import THEMES_YAML, parse_themes_yaml  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
UPDATES_DIR = ROOT / "social-samples" / "updates"
MANIFEST_NAME = "manifest.json"


def is_tracked(path: Path) -> bool:
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(path.relative_to(ROOT))],
        cwd=ROOT,
        capture_output=True,
    )
    return result.returncode == 0


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def record_count(path: Path) -> int | None:
    """JSONの配列なら件数を返す。件数の照合に使うだけなので、読めなければ None。"""
    if path.suffix != ".json":
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return len(data) if isinstance(data, list) else None


def ignored_private_files() -> list[Path]:
    """social-samples 配下のGit管理外・ignore対象ファイルを全て返す。"""
    result = subprocess.run(
        [
            "git", "ls-files", "--others", "--ignored", "--exclude-standard", "-z",
            "--", "social-samples",
        ],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    return [ROOT / value.decode() for value in result.stdout.split(b"\0") if value]


def collect_targets() -> tuple[list[Path], list[str]]:
    """バックアップ対象と、バックアップを停止すべき欠落理由を返す。"""
    targets: list[Path] = []
    errors: list[str] = []

    for theme, fields in parse_themes_yaml(THEMES_YAML).items():
        relative = fields.get("sample_file")
        if not relative:
            errors.append(f"{theme}: sample_file が未設定")
            continue
        path = ROOT / relative
        if not path.is_file():
            if not is_tracked(path):
                errors.append(f"{theme}: 非公開 sample_file が存在しない（{relative}）")
            continue
        if is_tracked(path):
            continue  # Git にあるので非公開バックアップの対象外
        targets.append(path)

    if not UPDATES_DIR.is_dir() or not any(p.is_file() for p in UPDATES_DIR.rglob("*")):
        errors.append(f"更新履歴が存在しない（{UPDATES_DIR.relative_to(ROOT)}）")

    # 現行正典と標準 updates/ だけでなく、標準化前のraw・分類履歴も保全する。
    targets.extend(ignored_private_files())

    # ライターのペルソナ。公開リポジトリに置けないため Git 管理外にしてある（課題45と同じ方式）。
    # ここに入れておかないと、worktree を消した時点で世界から消える。
    persona = ROOT / "configs" / "persona.private.json"
    if persona.is_file():
        targets.append(persona)
    else:
        errors.append(f"ライターのペルソナが存在しない（{persona.relative_to(ROOT)}）")

    return sorted(set(path for path in targets if path.is_file())), errors


def build_manifest(targets: list[Path]) -> dict:
    return {
        "created_at": datetime.now().astimezone().isoformat(),
        "root": str(ROOT),
        "files": [
            {
                "path": str(path.relative_to(ROOT)),
                "bytes": path.stat().st_size,
                "sha256": sha256_of(path),
                "records": record_count(path),
            }
            for path in targets
        ],
    }


def backup(dest: Path) -> int:
    try:
        dest.resolve().relative_to(ROOT.resolve())
    except ValueError:
        pass
    else:
        print("NG  保存先はリポジトリ外の非公開ストレージを指定すること")
        return 1

    targets, errors = collect_targets()
    for error in errors:
        print(f"NG  {error}")
    if errors:
        return 1
    if not targets:
        print("NG  バックアップ対象が1件もない。THEMES.yaml と .gitignore を確認すること")
        return 1

    dest.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(targets)
    run_id = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    archive = dest / f"private-data-{run_id}.tar.gz"

    with tempfile.TemporaryDirectory(dir=dest, prefix=".private-data-") as tmp:
        manifest_path = Path(tmp) / MANIFEST_NAME
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        partial = Path(tmp) / "archive.tar.gz"
        with tarfile.open(partial, "w:gz") as tar:
            tar.add(manifest_path, arcname=MANIFEST_NAME)
            for path in targets:
                tar.add(path, arcname=str(path.relative_to(ROOT)))
        partial.replace(archive)

    if verify(archive, quiet=True):
        archive.unlink(missing_ok=True)
        print("NG  作成直後の復元確認に失敗したためアーカイブを破棄しました")
        return 1

    total = sum(item["bytes"] for item in manifest["files"])
    print(f"OK  {len(targets)}ファイル / {total:,}バイト → {archive}")
    print(f"    アーカイブSHA-256: {sha256_of(archive)}")
    print("    復元確認: OK")
    print("    注意: tar.gz 自体は暗号化されません。暗号化済み保存先を使用してください")
    return 0


def verify(archive: Path, *, quiet: bool = False) -> int:
    if not archive.is_file():
        print(f"NG  アーカイブがない: {archive}")
        return 1

    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(tmp)
        extracted = Path(tmp)
        manifest_path = extracted / MANIFEST_NAME
        if not manifest_path.is_file():
            print("NG  マニフェストがアーカイブに含まれていない")
            return 1
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        for item in manifest["files"]:
            path = extracted / item["path"]
            if not path.is_file():
                print(f"NG  復元できない: {item['path']}")
                failures += 1
                continue
            if sha256_of(path) != item["sha256"]:
                print(f"NG  内容が一致しない: {item['path']}")
                failures += 1
                continue
            if item["records"] is not None and record_count(path) != item["records"]:
                print(f"NG  件数が一致しない: {item['path']}")
                failures += 1
                continue
            if not quiet:
                print(f"OK  {item['path']}（{item['bytes']:,}バイト" + (f" / {item['records']}件）" if item["records"] is not None else "）"))

    if not quiet:
        print(f"=== 復元確認: {len(manifest['files'])}ファイル / NG {failures}件（作成日 {manifest['created_at']}）===")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dest", type=Path, help="バックアップの保存先ディレクトリ")
    group.add_argument("--verify", type=Path, help="検証するアーカイブのパス")
    args = parser.parse_args()
    return verify(args.verify) if args.verify else backup(args.dest)


if __name__ == "__main__":
    raise SystemExit(main())
