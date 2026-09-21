#!/usr/bin/env python3
"""「授業・ディベートで使うとき」節を、テーマページへ適用する（課題77 案2 Part B）。

`configs/classroom/{theme_id}.json` から、賛成・反対の理由、確かめる一次資料、
問いの例を読み、共有ブロック `<!-- CLASSROOM_START -->`〜`<!-- CLASSROOM_END -->` を
組み立てる。仕組みは `apply_theme_trust.py` と同じ: マーカー間を置き換える・
同じ入力で2回実行しても差分ゼロ。

新規ページには、相手（ARTICLE_TRUST_START）のマーカーそのものをアンカーにして
その直前へ挿入する。共有アンカーへ後付けする側は、相対順序を保証するために
相手のマーカーを直接アンカーにする（自分専用の目印を新設すると、どちらが先に
実行されるかで順序が変わってしまう）。
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLASSROOM_START = "<!-- CLASSROOM_START -->"
CLASSROOM_END = "<!-- CLASSROOM_END -->"
TRUST_START = "<!-- ARTICLE_TRUST_START -->"
PROTECTED_TOKENS = (
    "G-K10S4YCZFH",
    "ca-pub-2542211932832864",
    "supabase",
    "topic-modern.js",
)

REASONS_PER_SIDE = 3
SOURCES_COUNT = 3
QUESTIONS_COUNT = 3
MIN_REASON_LENGTH = 20

# 固定の使い方指示（全テーマ共通）。configs/page-originality.json の allow に
# 同じ文言を登録してある（編集で書き分ける対象ではないため）。
USAGE_TEXT = "読む前に理由を書き出す→ページで確かめる→自分の理由と比べる。"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def esc(value: str) -> str:
    return html.escape(str(value), quote=True)


def replace_marked(source: str, start: str, end: str, replacement: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if not pattern.search(source):
        raise ValueError(f"missing managed block: {start}")
    return pattern.sub(replacement, source, count=1)


def public_theme_data(theme_id: str) -> dict[str, Any]:
    path = PROJECT_ROOT / "data" / "public" / "themes" / f"{theme_id}.json"
    if not path.is_file():
        raise FileNotFoundError(f"{theme_id}: 公開JSONがありません: {path}")
    return load_json(path)


def issue_labels(theme_data: dict[str, Any]) -> dict[str, str]:
    return {str(issue["id"]): str(issue["label"]) for issue in theme_data.get("issues") or []}


def validate_config(theme_id: str, config: dict[str, Any], valid_issue_ids: set[str]) -> None:
    if config.get("theme_id") != theme_id:
        raise ValueError(f"{theme_id}: theme_id がファイル名と一致しません: {config.get('theme_id')!r}")
    for key in ("pro_label", "con_label"):
        if not str(config.get(key) or "").strip():
            raise ValueError(f"{theme_id}: {key} が空です")
    for key in ("reasons_pro", "reasons_con"):
        reasons = config.get(key) or []
        if len(reasons) != REASONS_PER_SIDE:
            raise ValueError(f"{theme_id}: {key} は{REASONS_PER_SIDE}件必要です（{len(reasons)}件）")
        for reason in reasons:
            text = str(reason.get("text") or "")
            if len(text) < MIN_REASON_LENGTH:
                raise ValueError(f"{theme_id}: {key} の理由が短すぎます（{MIN_REASON_LENGTH}字未満）: {text!r}")
            issue_id = str(reason.get("issue_id") or "")
            if issue_id not in valid_issue_ids:
                raise ValueError(f"{theme_id}: {key} の issue_id が実在しません: {issue_id!r}")
    sources = config.get("primary_sources") or []
    if len(sources) != SOURCES_COUNT:
        raise ValueError(f"{theme_id}: primary_sources は{SOURCES_COUNT}件必要です（{len(sources)}件）")
    for source in sources:
        if not str(source.get("title") or "").strip():
            raise ValueError(f"{theme_id}: primary_sources に title の無い項目があります")
        url = str(source.get("url") or "")
        if not url.startswith("http"):
            raise ValueError(f"{theme_id}: primary_sources の url が不正です: {url!r}")
        if not str(source.get("note") or "").strip():
            raise ValueError(f"{theme_id}: primary_sources に note の無い項目があります")
    questions = config.get("questions") or []
    if len(questions) != QUESTIONS_COUNT:
        raise ValueError(f"{theme_id}: questions は{QUESTIONS_COUNT}件必要です（{len(questions)}件）")
    for question in questions:
        if not str(question or "").strip():
            raise ValueError(f"{theme_id}: questions に空の項目があります")


def reasons_html(reasons: list[dict[str, Any]], labels: dict[str, str]) -> str:
    items = []
    for reason in reasons:
        issue_id = str(reason["issue_id"])
        issue_label = labels.get(issue_id, issue_id)
        text = esc(str(reason["text"]))
        items.append(
            "      <li><p>"
            f"{text} "
            f'<a href="#issue-{esc(issue_id)}">→ 論点「{esc(issue_label)}」を見る</a>'
            "</p></li>"
        )
    return "\n".join(items)


def sources_html(sources: list[dict[str, Any]]) -> str:
    items = []
    for source in sources:
        title = esc(str(source["title"]))
        url = esc(str(source["url"]))
        note = esc(str(source["note"]))
        items.append(f'      <li><p><a href="{url}">{title}</a>：{note}</p></li>')
    return "\n".join(items)


def questions_html(questions: list[str]) -> str:
    return "\n".join(f"      <li><p>{esc(str(question))}</p></li>" for question in questions)


def classroom_block(theme_id: str, config: dict[str, Any], theme_data: dict[str, Any]) -> str:
    labels = issue_labels(theme_data)
    pro_label = esc(str(config["pro_label"]))
    con_label = esc(str(config["con_label"]))
    return f"""\
{CLASSROOM_START}
<section class="classroom-section" aria-labelledby="classroom-title">
  <div class="classroom-heading">
    <p class="classroom-kicker">授業・探究学習で使う</p>
    <h2 id="classroom-title">授業・ディベートで使うとき</h2>
    <p class="classroom-tagline">賛成・反対それぞれの理由を、まず3つずつ。メリット・デメリットを自分の言葉で書き出してから読み進めてください。</p>
  </div>
  <div class="classroom-reasons-grid">
    <div class="classroom-reasons">
      <h3>「{pro_label}」側の理由</h3>
      <ul>
{reasons_html(config["reasons_pro"], labels)}
      </ul>
    </div>
    <div class="classroom-reasons">
      <h3>「{con_label}」側の理由</h3>
      <ul>
{reasons_html(config["reasons_con"], labels)}
      </ul>
    </div>
  </div>
  <div class="classroom-sources">
    <h3>確かめる一次資料</h3>
    <ul>
{sources_html(config["primary_sources"])}
    </ul>
  </div>
  <div class="classroom-questions">
    <h3>問いの例</h3>
    <ul>
{questions_html(config["questions"])}
    </ul>
  </div>
  <div class="classroom-usage">
    <h3>使い方</h3>
    <p>{USAGE_TEXT}</p>
    <button type="button" class="classroom-print-btn">この節を印刷する</button>
  </div>
</section>
{CLASSROOM_END}"""


def apply_theme(source: str, theme_id: str, config: dict[str, Any], theme_data: dict[str, Any]) -> str:
    before_counts = {token: source.count(token) for token in PROTECTED_TOKENS}
    block = classroom_block(theme_id, config, theme_data)
    if CLASSROOM_START in source:
        updated = replace_marked(source, CLASSROOM_START, CLASSROOM_END, block)
    else:
        if TRUST_START not in source:
            raise ValueError(f"{theme_id}: 挿入位置の目印がありません: {TRUST_START}")
        updated = source.replace(TRUST_START, f"{block}\n{TRUST_START}", 1)
    after_counts = {token: updated.count(token) for token in PROTECTED_TOKENS}
    for token in PROTECTED_TOKENS:
        if before_counts[token] and after_counts[token] < before_counts[token]:
            raise ValueError(f"{theme_id}: protected token removed: {token}")
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seo-config", default="configs/theme-seo.json")
    parser.add_argument("--classroom-dir", default="configs/classroom")
    parser.add_argument("--docs-dir", default="docs")
    parser.add_argument("--check", action="store_true", help="validate and report without writing")
    args = parser.parse_args()

    seo_config = load_json(PROJECT_ROOT / args.seo_config)
    docs_dir = PROJECT_ROOT / args.docs_dir
    classroom_dir = PROJECT_ROOT / args.classroom_dir

    changed = 0
    for theme in seo_config["themes"]:
        theme_id = str(theme["id"])
        config_path = classroom_dir / f"{theme_id}.json"
        if not config_path.is_file():
            raise FileNotFoundError(f"{theme_id}: 設定がありません: {config_path}")
        config = load_json(config_path)
        theme_data = public_theme_data(theme_id)
        valid_issue_ids = {str(issue["id"]) for issue in theme_data.get("issues") or []}
        validate_config(theme_id, config, valid_issue_ids)

        path = docs_dir / theme["url"]
        if not path.is_file():
            raise FileNotFoundError(path)
        source = path.read_text(encoding="utf-8")
        updated = apply_theme(source, theme_id, config, theme_data)
        if updated != source:
            changed += 1
            if not args.check:
                path.write_text(updated, encoding="utf-8")
        status = "unchanged"
        if updated != source:
            status = "would update" if args.check else "updated"
        print(f"{status} {path.relative_to(PROJECT_ROOT)}")

    print(f'Validated {len(seo_config["themes"])} classroom sections; changed={changed}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
