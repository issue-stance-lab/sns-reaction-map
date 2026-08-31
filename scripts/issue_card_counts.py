#!/usr/bin/env python3
"""論点カードに併記する件数を、分類結果から計算する。

`configs/{theme}-reaction-map.json` の `issue_counts` ブロックを読む。

    "issue_counts": {
      "source": "social-samples/foo.json",   # 省略時は THEMES.yaml の sample_file
      "basis": "all" | "opinion" | "public_json",  # 省略時は all
      "cards": [
        {"slug": "gakushu", "title": "学習データ・無断利用 — ...", "main_issue": ["学習データ・無断利用"]}
      ]
    }

`basis: "public_json"`（課題57）は `source` を無視し、`data/public/themes/{theme}.json`
（`scripts/build_public_registry.py` の生成物）の論点別意見数をそのまま使う。
正典（social-samples）は再計算しない。

`title` は docs/*.html の `<p class="explainer-card-title">` と完全一致させる。
`main_issue` は分類結果側のラベル（複数指定でカードへ合算できる）。

件数はここでしか作らない。HTMLに数字を直接書かないこと。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent


class IssueCountError(ValueError):
    """設定と分類結果が噛み合っていない。"""


def _classification(record: dict[str, Any]) -> dict[str, Any]:
    nested = record.get("classification")
    return nested if isinstance(nested, dict) else record


def load_records(source: str) -> list[dict[str, Any]]:
    path = (ROOT / source).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise IssueCountError(f"リポジトリ外を指しています: {source}") from exc
    try:
        records = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise IssueCountError(f"分類結果が存在しません: {source}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise IssueCountError(f"分類結果を読めません: {source}: {exc}") from exc
    if not isinstance(records, list) or not records:
        raise IssueCountError(f"分類結果はJSON配列である必要があります: {source}")
    return [record for record in records if isinstance(record, dict)]


def count_by_issue_from_public_json(theme: str, *, check_freshness: bool = True) -> dict[str, int]:
    """課題57: 公開データJSON（data/public/themes/{theme}.json）の論点別意見数を読む。

    正典（social-samples）を再計算しない。ここで数える意見はcatalog生成時の
    is_relevant/is_opinionと同じ定義（scripts/public_registry_common.py）に固定される。

    `check_freshness=True`（既定）では、`THEMES.yaml` の非公開正典 `sample_file` が
    ローカルにあれば、公開データJSONの `source_sha256` が現在内容と一致するかを確認する。
    **この確認を省くと、昇格直後に build_public_registry.py の再実行を忘れたとき、
    古い件数を公開ページへ出し続けてしまう**（段階5でrefresh_topic.pyへ自動接続するまでの間、
    手動再実行が必要）。呼び出し側が渡す sample_file/verification_file はテーマによって
    仮名化データを指すことがあり信用できないため、THEMES.yaml を自分で読み直す。
    非公開正典が手元に無い環境（監査のみ）では確認をスキップする。
    """
    path = ROOT / "data" / "public" / "themes" / f"{theme}.json"
    if not path.is_file():
        raise IssueCountError(
            f"{theme}: 公開データJSONがありません: {path}"
            f"（scripts/build_public_registry.py --topic {theme} を先に実行する）"
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    if check_freshness:
        try:
            from .public_registry_common import load_themes_yaml, source_sha256
        except ImportError:  # python3 scripts/*.py
            from public_registry_common import load_themes_yaml, source_sha256  # type: ignore[no-redef]
        canon_relpath = load_themes_yaml().get(theme, {}).get("sample_file")
        canon_path = ROOT / canon_relpath if canon_relpath else None
        if canon_path is not None and canon_path.is_file():
            canon_records = json.loads(canon_path.read_text(encoding="utf-8"))
            actual_hash = source_sha256(canon_records)
            if data.get("source_sha256") != actual_hash:
                raise IssueCountError(
                    f"{theme}: 公開データJSONのsource_sha256が非公開正典の現在内容と"
                    f"不一致です（scripts/build_public_registry.py --topic {theme} を再実行する）"
                )
    return {str(issue["label"]): int(issue["count"]) for issue in data["issues"]}


def count_by_issue(records: list[dict[str, Any]], basis: str) -> dict[str, int]:
    if basis not in ("all", "opinion"):
        raise IssueCountError(f"basis は all / opinion のいずれかです: {basis}")
    counts: dict[str, int] = {}
    for record in records:
        classification = _classification(record)
        # 旧2D分類には is_opinion がトップレベルにあるテーマもある。
        # ネスト側を優先し、欠落時だけ旧形式へフォールバックする。
        is_opinion = classification.get("is_opinion", record.get("is_opinion"))
        if basis == "opinion" and not bool(is_opinion):
            continue
        issue = classification.get("main_issue")
        if not issue:
            continue
        counts[str(issue)] = counts.get(str(issue), 0) + 1
    return counts


def card_counts(theme: str, config: dict[str, Any], sample_file: str | None) -> list[dict[str, Any]]:
    """[{slug, title, count}] を、設定に書かれたカード順で返す。"""
    block = config.get("issue_counts")
    if not isinstance(block, dict):
        raise IssueCountError(f"{theme}: configs に issue_counts がありません")

    cards = block.get("cards")
    if not isinstance(cards, list) or not cards:
        raise IssueCountError(f"{theme}: issue_counts.cards が空です")

    basis = str(block.get("basis") or "all")
    if basis == "public_json":
        counts = count_by_issue_from_public_json(theme)
    else:
        source = str(block.get("source") or sample_file or "")
        if not source:
            raise IssueCountError(f"{theme}: 件数の出所（source / sample_file）が決まりません")
        counts = count_by_issue(load_records(source), basis)

    resolved = []
    for card in cards:
        if not isinstance(card, dict):
            raise IssueCountError(f"{theme}: cards の要素はオブジェクトである必要があります")
        slug = str(card.get("slug") or "").strip()
        title = str(card.get("title") or "").strip()
        issues = card.get("main_issue")
        if not slug or not title:
            raise IssueCountError(f"{theme}: cards に slug / title がありません: {card}")
        if not isinstance(issues, list) or not issues:
            raise IssueCountError(f"{theme}: {slug} の main_issue が空です")
        unknown = [issue for issue in issues if str(issue) not in counts]
        if unknown:
            raise IssueCountError(
                f"{theme}: {slug} の main_issue が分類結果にありません: {', '.join(map(str, unknown))}"
                f"（分類結果のラベル: {', '.join(sorted(counts))}）"
            )
        resolved.append(
            {
                "slug": slug,
                "title": title,
                "count": sum(counts[str(issue)] for issue in issues),
                # 論点セクションと論点ナビが使うアンカー。ページ側のidがslugと違う
                # テーマがあるので、違う場合だけ configs に anchor を書く。
                "anchor": str(card.get("anchor") or f"issue-{slug}"),
                # 件数spanを出す場所。カード見出しの下に分類ラベルの行がある
                # テーマは、見出しではなくその行へ付ける（例: ai-copyright）。
                "display_label": str(card.get("display_label") or "").strip(),
                # アリーナのセクター配列 ISSUES のキー。表示名が分類ラベルと
                # 違うテーマ（例: データ「技術競争・推進」／表示「技術競争・AI推進」）がある。
                "arena_label": str(card.get("arena_label") or "").strip(),
                # 件数spanをカードの meta 行（論点名の直後）に置くテーマの目印。
                # ここで落とすと sync_issue_counts.apply_counts がタイトル行に
                # 別のspanを足し、meta行の古い件数が残る（2026-08-16、生成AIで
                # 「419件」と「340件」が同じカードに並んだ）。
                "display_label": str(card.get("display_label") or "").strip(),
            }
        )
    return resolved


def other_count(theme: str, config: dict[str, Any], sample_file: str | None) -> int:
    """カードに載らない意見（「その他」）の件数を返す。"""
    block = config.get("issue_counts")
    if not isinstance(block, dict):
        raise IssueCountError(f"{theme}: configs に issue_counts がありません")
    basis = str(block.get("basis") or "all")
    if basis == "public_json":
        counts = count_by_issue_from_public_json(theme)
    else:
        source = str(block.get("source") or sample_file or "")
        counts = count_by_issue(load_records(source), basis)
    carded = {
        str(issue)
        for card in block.get("cards", [])
        if isinstance(card, dict)
        for issue in (card.get("main_issue") or [])
    }
    return sum(value for name, value in counts.items() if name not in carded)


def span_id(theme: str, slug: str) -> str:
    return f"issue-count-{theme}-{slug}"


def span_html(theme: str, slug: str, count: int) -> str:
    return f'<span class="explainer-count" id="{span_id(theme, slug)}">{count}件</span>'
