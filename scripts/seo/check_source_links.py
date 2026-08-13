#!/usr/bin/env python3
"""公開ページの出典リンクが生きているかを一括で確認する。

背景解説の一次情報（configs/*.json の `background.sources`）と、論拠の出典
（`arguments.sources`）のURLへ順にアクセスし、HTTPステータスを一覧で出す。

`verify_theme_page.py` にも同じ検査は入っているが、あちらはテーマごとに実行する必要があり、
件数の照合など重い検査も一緒に走る。リンクだけを短時間で確認したいときはこちらを使う。

    python3 scripts/seo/check_source_links.py            # 全テーマ
    python3 scripts/seo/check_source_links.py --theme takaichi

**作業環境によっては実行できない。** Claude Code の遠隔実行環境は組織のegressポリシーで
官公庁ドメイン（*.go.jp）への接続が 403 で拒否されるため、そこでは全件 BLOCKED になる。
その場合はオーナーのローカル環境で実行すること。
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[2]
USER_AGENT = "Mozilla/5.0 (compatible; sns-reaction-map link checker)"


def theme_configs() -> Iterator[tuple[str, Path]]:
    """公開中のテーマの (テーマID, configs/*.json) を返す。"""
    text = (PROJECT_ROOT / "THEMES.yaml").read_text(encoding="utf-8")
    for match in re.finditer(
        r"^  ([\w-]+):\s*$(.*?)(?=^  [\w-]+:\s*$|\Z)", text, re.MULTILINE | re.DOTALL
    ):
        body = match.group(2)
        if not re.search(r"^    published:\s*done", body, re.MULTILINE):
            continue
        html_match = re.search(r"^    html:\s*(\S+)", body, re.MULTILINE)
        if not html_match:
            continue
        stem = Path(html_match.group(1)).stem
        config = PROJECT_ROOT / "configs" / f"{stem}.json"
        if not config.exists():
            config = PROJECT_ROOT / "configs" / f"{match.group(1)}-reaction-map.json"
        yield match.group(1), config


def sources_of(config_path: Path) -> list[tuple[str, str, str]]:
    """(区分, ラベル, URL) の一覧。"""
    if not config_path.exists():
        return []
    data: dict[str, Any] = json.loads(config_path.read_text(encoding="utf-8"))
    out: list[tuple[str, str, str]] = []
    for kind, container in (
        ("背景", (data.get("background") or {}).get("sources")),
        ("論拠", (data.get("arguments") or {}).get("sources")),
    ):
        for item in container or []:
            url = str(item.get("url") or "").strip()
            if url:
                out.append((kind, str(item.get("label") or ""), url))
    return out


def check(url: str, timeout: float) -> tuple[str, str]:
    """(判定, 詳細) を返す。判定は OK / NG / BLOCKED / ERROR。"""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            code = response.status
            return ("OK" if 200 <= code < 300 else "NG", str(code))
    except urllib.error.HTTPError as exc:
        # 403 は「リンク切れ」ではなく、プロキシ側の遮断や bot 対策のことがある
        if exc.code in (403, 407):
            return ("BLOCKED", f"{exc.code} {exc.reason}")
        return ("NG", f"{exc.code} {exc.reason}")
    except urllib.error.URLError as exc:
        reason = str(getattr(exc, "reason", exc))
        if "403" in reason or "Forbidden" in reason or "tunnel" in reason.lower():
            return ("BLOCKED", reason[:70])
        return ("ERROR", reason[:70])
    except (ssl.SSLError, TimeoutError, OSError) as exc:
        return ("ERROR", str(exc)[:70])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theme", help="1テーマだけ確認する")
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()

    totals = {"OK": 0, "NG": 0, "BLOCKED": 0, "ERROR": 0}
    failures: list[str] = []

    for theme_id, config in theme_configs():
        if args.theme and theme_id != args.theme:
            continue
        sources = sources_of(config)
        if not sources:
            print(f"--- {theme_id}: 出典なし")
            continue
        print(f"--- {theme_id}（{len(sources)}本）")
        for kind, label, url in sources:
            verdict, detail = check(url, args.timeout)
            totals[verdict] += 1
            mark = {"OK": "OK   ", "NG": "NG   ", "BLOCKED": "遮断 ", "ERROR": "エラー"}[verdict]
            print(f"  {mark} [{kind}] {detail:<22} {url}")
            if verdict == "NG":
                failures.append(f"{theme_id}: {label} — {url}（{detail}）")

    print(
        f"\n合計: OK {totals['OK']} / NG {totals['NG']} / "
        f"遮断 {totals['BLOCKED']} / エラー {totals['ERROR']}"
    )
    if totals["BLOCKED"]:
        print(
            "遮断は、この環境から接続できないという意味でリンク切れではない。"
            "遠隔実行環境では *.go.jp が組織のegressポリシーで 403 になる。"
            "ローカル環境で実行し直すこと。"
        )
    if failures:
        print("\nリンク切れの疑い:")
        for line in failures:
            print(f"  - {line}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
