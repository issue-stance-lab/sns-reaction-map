#!/usr/bin/env python3
"""Git管理外の正典データと更新履歴を1コマンドでバックアップする（課題33）。

対象は THEMES.yaml の `sample_file` のうち Git が追跡していないもの（本文・URL・
ユーザー識別子を含むため公開リポジトリに置けない）と、`social-samples/updates/` の
更新履歴一式。`data/verification/` は Git にあるのでバックアップ対象に含めない。

    # バックアップを作る（保存先は課題33で決めた非公開ストレージ）
    python3 scripts/backup_private_data.py --dest /Volumes/Backup/issue-stance

    # 作ったアーカイブが壊れていないか、別マシンで復元できるかを確認する
    python3 scripts/backup_private_data.py --verify /Volumes/Backup/issue-stance/private-data-2026-08-02.tar.gz

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
from datetime import date
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


def collect_targets() -> tuple[list[Path], list[str]]:
    """バックアップ対象のファイルと、対象が見つからなかったテーマの警告を返す。"""
    targets: list[Path] = []
    warnings: list[str] = []

    for theme, fields in parse_themes_yaml(THEMES_YAML).items():
        relative = fields.get("sample_file")
        if not relative:
            warnings.append(f"{theme}: sample_file が未設定")
            continue
        path = ROOT / relative
        if not path.is_file():
            warnings.append(f"{theme}: sample_file が存在しない（{relative}）")
            continue
        if is_tracked(path):
            continue  # Git にあるので非公開バックアップの対象外
        targets.append(path)

    if UPDATES_DIR.is_dir():
        targets.extend(sorted(p for p in UPDATES_DIR.rglob("*") if p.is_file()))

    return sorted(set(targets)), warnings


def build_manifest(targets: list[Path]) -> dict:
    return {
        "created_at": date.today().isoformat(),
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
    targets, warnings = collect_targets()
    for warning in warnings:
        print(f"WARN {warning}")
    if not targets:
        print("NG  バックアップ対象が1件もない。THEMES.yaml と .gitignore を確認すること")
        return 1

    dest.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(targets)
    archive = dest / f"private-data-{manifest['created_at']}.tar.gz"

    with tempfile.TemporaryDirectory() as tmp:
        manifest_path = Path(tmp) / MANIFEST_NAME
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(manifest_path, arcname=MANIFEST_NAME)
            for path in targets:
                tar.add(path, arcname=str(path.relative_to(ROOT)))

    total = sum(item["bytes"] for item in manifest["files"])
    print(f"OK  {len(targets)}ファイル / {total:,}バイト → {archive}")
    print(f"    アーカイブSHA-256: {sha256_of(archive)}")
    print("    復元確認: python3 scripts/backup_private_data.py --verify " + str(archive))
    return 0


def verify(archive: Path) -> int:
    if not archive.is_file():
        print(f"NG  アーカイブがない: {archive}")
        return 1

    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(tmp, filter="data")
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
            print(f"OK  {item['path']}（{item['bytes']:,}バイト" + (f" / {item['records']}件）" if item["records"] is not None else "）"))

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
