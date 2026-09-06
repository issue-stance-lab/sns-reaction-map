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
作成・復元検査の成功時は company/data-backup-status.json に本文なしの記録を残す。
この記録の git_commit はバックアップ時点の HEAD（記録自身を含む後続コミットではない）。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path, PurePosixPath

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


def git_identity() -> dict:
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                            capture_output=True, text=True, check=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                           cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return {"git_commit": commit, "git_tracked_dirty": bool(dirty.strip())}


def build_manifest(targets: list[Path]) -> dict:
    return {
        "schema_version": 1,
        **git_identity(),
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


def backup(dest: Path, *, receipt_path: Path | None = None) -> int:
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

    write_receipt(archive, manifest, receipt_path or ROOT / "company/data-backup-status.json")
    total = sum(item["bytes"] for item in manifest["files"])
    print(f"OK  {len(targets)}ファイル / {total:,}バイト → {archive}")
    print(f"    アーカイブSHA-256: {sha256_of(archive)}")
    print("    復元確認: OK")
    print("    注意: tar.gz 自体は暗号化されません。暗号化済み保存先を使用してください")
    return 0


def safe_member_path(name: str) -> str:
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or "\\" in name
            or any(part in ("", ".", "..") for part in name.split("/"))
            or str(path) != name or ":" in name or "\x00" in name):
        raise ValueError("unsafe archive path")
    return name


def unique_json_object(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate manifest JSON key")
        result[key] = value
    return result


def validated_manifest(tar: tarfile.TarFile) -> tuple[dict, dict]:
    members = {}
    for member in tar.getmembers():
        name = safe_member_path(member.name)
        if name in members or not member.isfile():
            raise ValueError("duplicate or non-regular archive member")
        members[name] = member
    if MANIFEST_NAME not in members:
        raise ValueError("manifest missing")
    with tar.extractfile(members[MANIFEST_NAME]) as handle:
        manifest = json.load(handle, object_pairs_hook=unique_json_object)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
        raise ValueError("invalid manifest")
    names = set()
    for item in manifest["files"]:
        if not isinstance(item, dict):
            raise ValueError("invalid manifest entry")
        name = safe_member_path(item["path"])
        if name == MANIFEST_NAME or name in names:
            raise ValueError("duplicate manifest path")
        names.add(name)
        if (type(item.get("bytes")) is not int or item["bytes"] < 0
                or not isinstance(item.get("sha256"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"])
                or (item.get("records") is not None
                    and (type(item["records"]) is not int or item["records"] < 0))):
            raise ValueError("invalid manifest metadata")
        if name not in members or members[name].size != item["bytes"]:
            raise ValueError("missing member or byte count mismatch")
    if set(members) != names | {MANIFEST_NAME}:
        raise ValueError("unexpected archive members")
    return manifest, members


def write_receipt(archive: Path, manifest: dict, destination: Path) -> None:
    """復元検査成功後だけ呼ぶ。本文や非公開保存先の絶対パスを残さない。"""
    receipt = {
        "schema_version": 1,
        "verified_at": datetime.now().astimezone().isoformat(),
        "git_commit": manifest["git_commit"],
        "git_tracked_dirty": manifest.get("git_tracked_dirty", False),
        "archive_name": archive.name,
        "archive_sha256": sha256_of(archive),
        "file_count": len(manifest["files"]),
        "total_bytes": sum(item["bytes"] for item in manifest["files"]),
        "files": [{key: item[key] for key in ("path", "sha256", "bytes", "records")}
                  for item in manifest["files"]],
        "restore_verified": True,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=destination.parent,
                                     prefix=".backup-receipt-", delete=False) as handle:
        temporary = Path(handle.name)
        try:
            json.dump(receipt, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def verify(archive: Path, *, quiet: bool = False) -> int:
    if not archive.is_file():
        print(f"NG  アーカイブがない: {archive}")
        return 1
    try:
        with tempfile.TemporaryDirectory() as tmp, tarfile.open(archive, "r:gz") as tar:
            manifest, members = validated_manifest(tar)
            # 全メンバー検査後に通常ファイルだけを自分で書き出す。リンクは展開しない。
            for item in manifest["files"]:
                path = Path(tmp) / item["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(members[item["path"]]) as source, path.open("wb") as out:
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        out.write(chunk)
                if path.stat().st_size != item["bytes"] or sha256_of(path) != item["sha256"]:
                    raise ValueError("restored content mismatch")
                if item["records"] is not None and record_count(path) != item["records"]:
                    raise ValueError("restored record count mismatch")
                if not quiet:
                    print(f"OK  {item['path']}（{item['bytes']:,}バイト）")
        if not quiet:
            print(f"=== 復元確認: {len(manifest['files'])}ファイル / NG 0件 ===")
        return 0
    except (OSError, tarfile.TarError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        print(f"NG  復元確認に失敗: {type(exc).__name__}")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dest", type=Path, help="バックアップの保存先ディレクトリ")
    group.add_argument("--verify", type=Path, help="検証するアーカイブのパス")
    parser.add_argument("--receipt", type=Path, help="復元確認済み記録の保存先（既定: company/data-backup-status.json）")
    args = parser.parse_args()
    if args.verify and args.receipt:
        parser.error("--receipt は --dest と併用すること（--verify は検査のみ）")
    return verify(args.verify) if args.verify else backup(args.dest, receipt_path=args.receipt)


if __name__ == "__main__":
    raise SystemExit(main())
