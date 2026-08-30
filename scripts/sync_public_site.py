#!/usr/bin/env python3
"""Sync docs/ into the single public Pages repository.

The source repository owns generators, tests, and private operating material.
The target repository owns only the deployable site artifact.  Legacy
``/sns-reaction-map/`` URLs receive small page-by-page move notices so old
bookmarks and links continue to reach the new root URL.
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from urllib.parse import urljoin


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://sns-reaction-map.jp/"
LEGACY_PREFIX = Path("sns-reaction-map")
MANIFEST_NAME = ".public-site-manifest.json"


def resolve_from_root(value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (PROJECT_ROOT / path).resolve()


def source_files(source_dir: Path) -> dict[Path, bytes]:
    result: dict[Path, bytes] = {}
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file() or path.name == ".DS_Store":
            continue
        result[path.relative_to(source_dir)] = path.read_bytes()
    return result


def legacy_redirect(relative: Path) -> bytes:
    destination = SITE_URL if relative.as_posix() == "index.html" else urljoin(SITE_URL, relative.as_posix())
    escaped = html.escape(destination, quote=True)
    encoded = json.dumps(destination, ensure_ascii=True)
    body = f"""<!doctype html>
<html lang=\"ja\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
  <meta http-equiv=\"refresh\" content=\"0; url={escaped}\">
  <meta name=\"robots\" content=\"noindex,follow\">
  <link rel=\"canonical\" href=\"{escaped}\">
  <title>サイト移転のお知らせ｜SNS反応まっぷ</title>
</head>
<body>
  <p>SNS反応まっぷは新しいアドレスへ移転しました。</p>
  <p><a href=\"{escaped}\">新しいページを開く</a></p>
  <script>
    window.location.replace({encoded} + window.location.search + window.location.hash);
  </script>
</body>
</html>
"""
    return body.encode("utf-8")


def expected_files(source_dir: Path) -> dict[Path, bytes]:
    expected = source_files(source_dir)
    expected[Path("CNAME")] = b"sns-reaction-map.jp\n"
    expected[Path(".nojekyll")] = b""
    for relative in sorted(path for path in expected if path.suffix == ".html"):
        expected[LEGACY_PREFIX / relative] = legacy_redirect(relative)
    return expected


def manifest_path(target_dir: Path) -> Path:
    return target_dir.parent / MANIFEST_NAME


def read_manifest(target_dir: Path) -> set[Path]:
    path = manifest_path(target_dir)
    if not path.is_file():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {Path(item) for item in payload.get("managed_files") or []}


def differences(source_dir: Path, target_dir: Path) -> list[str]:
    expected = expected_files(source_dir)
    previous = read_manifest(target_dir)
    errors: list[str] = []
    for relative, content in sorted(expected.items(), key=lambda item: item[0].as_posix()):
        target = target_dir / relative
        if not target.is_file():
            errors.append(f"missing: {relative}")
        elif target.read_bytes() != content:
            errors.append(f"different: {relative}")
    for relative in sorted(previous - set(expected), key=Path.as_posix):
        if (target_dir / relative).exists():
            errors.append(f"stale: {relative}")
    if not manifest_path(target_dir).is_file():
        errors.append(f"missing: {MANIFEST_NAME}")
    return errors


def sync(source_dir: Path, target_dir: Path) -> int:
    expected = expected_files(source_dir)
    previous = read_manifest(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    for relative in sorted(previous - set(expected), key=Path.as_posix, reverse=True):
        stale = target_dir / relative
        if stale.is_file() or stale.is_symlink():
            stale.unlink()

    for relative, content in sorted(expected.items(), key=lambda item: item[0].as_posix()):
        destination = target_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.is_file() or destination.read_bytes() != content:
            destination.write_bytes(content)

    for directory in sorted((path for path in target_dir.rglob("*") if path.is_dir()), reverse=True):
        if not any(directory.iterdir()):
            directory.rmdir()

    payload = {
        "source": "sns-reaction-map/docs",
        "site_url": SITE_URL,
        "managed_files": sorted(path.as_posix() for path in expected),
    }
    manifest_path(target_dir).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(expected)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="docs")
    parser.add_argument("--target", required=True, help="Public repository's deploy directory")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    source_dir = resolve_from_root(args.source)
    target_dir = resolve_from_root(args.target)
    if not source_dir.is_dir():
        raise SystemExit(f"source directory not found: {source_dir}")

    if args.check:
        errors = differences(source_dir, target_dir)
        if errors:
            print("Public site is out of sync:")
            for error in errors[:100]:
                print(f"- {error}")
            if len(errors) > 100:
                print(f"- ... and {len(errors) - 100} more")
            return 1
        print(f"Public site is in sync: {target_dir}")
        return 0

    count = sync(source_dir, target_dir)
    print(f"Synced {count} files to {target_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
