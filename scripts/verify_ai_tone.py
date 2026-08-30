#!/usr/bin/env python3
"""公開する文章から「AIが書いた感じ」を取り除いたままに保つ。

## なぜ機械で見張るか

2026-08-27、公開11ページの本文1,007文を数えたところ、安っぽい定型
（「いかがでしたか」「注目が集まっています」）は**0件**だった。代わりに見つかったのが
**賛否を同じ構文で並べる鏡像**で、これが読者に「AIが書いた」と感じさせる最大の要因だった。

    推進側の最も強い根拠は、〜ことです。慎重側の最も強い根拠は、〜ことです。

人間の記者は、賛成側を3文で書いて反対側を7文で書く。揃えない。

`WRITING_VOICE.md` に禁止として書いたが、**文章で書いた禁止は破られる**
（2026-08-18、発注書の「見出しをコピーするな」が守られず `verify_page_originality.py` を作った）。
ここで止める。

## 何を見るか

1. **ペルソナ流出**: 内部設定の書き手名が公開物に出ていないか。例外なし
   （名前は `configs/persona.private.json`。リポジトリが公開のため Git 管理外）
2. **禁止フレーズ**: まとめブログの定型。現在0件なので1件でも落とす
3. **鏡像構文**: 同じページ内で賛否を同じ型に流し込んでいないか
4. **定型の密度**: 「AではなくB」「一方で」を100文あたり何回使ったか
5. **語尾の連続**: note下書きで「〜しました。〜しました。」のように同じ語尾が
   続けて並んでいないか（2026-08-30、オーナー指摘を受けて追加）

対象は「編集で書いた本文」だけ。フッター・調査条件・免責など全ページ共通の枠は
`configs/page-originality.json` の `shared_selectors` を使って除く。
1と2は X・note の公開実績（`content/x/posts.md`, `content/note/`）にも掛ける。

## 既存分の扱い

検査を新設した時点で既にある違反は `configs/ai-tone.json` の `baseline` に量を書いてある。
**baseline を超えたら落ちる。減らすのは自由。** 既存ページの手直しは TASK_BOARD の別案件。

    python3 scripts/verify_ai_tone.py
    python3 scripts/verify_ai_tone.py -v     # baseline との増減と、密度の実測も出す
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from .sync_portal_stats import ROOT, parse_themes_yaml
    from .verify_page_originality import load_config as load_originality
    from .verify_page_originality import sentences, visible_parts
except ImportError:  # python3 scripts/verify_ai_tone.py
    from sync_portal_stats import ROOT, parse_themes_yaml  # type: ignore[no-redef]
    from verify_page_originality import load_config as load_originality  # type: ignore[no-redef]
    from verify_page_originality import sentences, visible_parts  # type: ignore[no-redef]

CONFIG = ROOT / "configs" / "ai-tone.json"
# ペルソナの名前そのもの。公開リポジトリに置けないので Git 管理外（課題45と同じ方式）。
PERSONA = ROOT / "configs" / "persona.private.json"

# 投稿済みの台帳。過去の投稿は取り消せないので、ここは**ペルソナ流出だけ**を見る。
# 言い回しの癖は下書きの段階で止める（下の DRAFT_DIRS）。
LEDGER_FILES = [
    Path("content/x/posts.md"),
    Path("content/note/posts.md"),
]
# これから公開するもの。禁止フレーズまで含めて全部見る。
DRAFT_DIRS = [
    Path("content/note/drafts"),
    Path("content/articles/drafts"),
    Path("content/x/research"),
]


def persona_terms() -> tuple[list[str], str | None]:
    """(検査する語, 飛ばした理由) を返す。

    非公開ファイルは新しい worktree に複製されない。**無いことに気づかず
    「検査が通った」と思い込むのが一番危ない**ので、飛ばしたことを必ず表に出す。
    """
    if not PERSONA.is_file():
        return [], (
            f"{PERSONA.relative_to(ROOT)} が無いため、ペルソナ流出の検査を飛ばしました。"
            " 新しい worktree には複製されません。OPERATIONS.md ⓪ の手順で復元してください。"
        )
    data = json.loads(PERSONA.read_text(encoding="utf-8"))
    terms = [term for term in data.get("persona_terms") or [] if term]
    if not terms:
        return [], f"{PERSONA.name} に persona_terms がありません。"
    return terms, None


def load() -> dict:
    if not CONFIG.is_file():
        raise SystemExit(f"{CONFIG} がありません")
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    for group in ("banned", "mirror", "density"):
        for entry in data.get(group) or []:
            if not entry.get("pattern") or not entry.get("reason"):
                raise SystemExit(
                    f"{CONFIG.name}: {group} には pattern と reason の両方が要ります: {entry!r}"
                )
    return data


def page_bodies() -> dict[str, list[str]]:
    """テーマ名 -> 編集で書いた本文の文リスト。"""
    shared = load_originality().get("shared_selectors", [])
    out: dict[str, list[str]] = {}
    for name, theme in parse_themes_yaml().items():
        html = theme.get("html")
        if not html:
            continue
        path = ROOT / html
        if not path.is_file():
            continue
        _headings, _leads, paragraphs = visible_parts(path, shared)
        out[name] = sentences(paragraphs)
    return out


def ledger_texts() -> dict[str, str]:
    """投稿済みの記録。ペルソナ流出だけを見る。"""
    out: dict[str, str] = {}
    for rel in LEDGER_FILES:
        path = ROOT / rel
        if path.is_file():
            out[str(rel)] = path.read_text(encoding="utf-8")
    return out


def draft_texts() -> dict[str, str]:
    """これから公開する下書き。全部の検査を掛ける。"""
    out: dict[str, str] = {}
    for rel in DRAFT_DIRS:
        directory = ROOT / rel
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*.md")):
            out[str(path.relative_to(ROOT))] = path.read_text(encoding="utf-8")
    return out


def check_note_counts(config: dict, drafts: dict[str, str]) -> list[str]:
    """note下書きの本文に件数を並べすぎていないか。

    2026-08-28、note第2回で「件数ばかり列挙してつまらない」とオーナー指摘。
    件数は図と記事末の注記が担い、本文は人と仕組みで進める（note-operation「数字の扱い」）。
    数えるのは貼り付け用の本文だけ。記事末の注記（データについて／制度についての記述）は除く。
    """
    limit = int((config.get("note_counts") or {}).get("max_per_draft", 8))
    failures = []
    for label, text in drafts.items():
        # 対象は貼り付け用の本文だけ。指示書・画像プロンプト・引き継ぎメモは数えない
        if "/note/" not in label or not label.endswith(("-FINAL.md", "-CANDIDATE.md")):
            continue
        if "\n---\n" not in text:
            continue
        body = text.split("\n---\n", 1)[1]
        lines = [
            line
            for line in body.splitlines()
            if not line.startswith(("データについて", "制度についての記述"))
        ]
        hits = re.findall(r"[0-9][0-9,]*件", "\n".join(lines))
        if len(hits) > limit:
            failures.append(
                f"件数の並べすぎ: {label} の本文に「◯件」が{len(hits)}件（上限{limit}）。"
                "内訳は図と記事末の注記に預ける（note-operation「数字の扱い」）"
            )
    return failures


def _classify_ending(sentence: str, patterns: list[str]) -> str | None:
    """文末が endings.patterns のどれと一致するか。最長一致を優先する。

    「しました」は「ました」を含むため、短い方から先に判定すると
    「しました。」が「ました」として分類され、同じ文が二重に数えられない。
    """
    for pattern in patterns:  # 呼び出し側で長い順に渡す
        if sentence.endswith(pattern + "。"):
            return pattern
    return None


def check_ending_repeat(config: dict, drafts: dict[str, str]) -> list[str]:
    """同じ語尾の文が続けて並んでいないか。

    2026-08-30、note第3回の下書きにオーナーから「〜しました。〜しました。と続く」と指摘。
    `verify_ai_tone.py` は当時この種類の単調さを見ていなかった
    （鏡像構文＝賛否を同じ型で並べる、は見ていたが、賛否に関係ない語尾の連続は対象外だった）。
    `WRITING_VOICE.md`「対称にしない」の考え方を語尾の連続にも広げる。
    数えるのは note_counts と同じ、貼り付け用の本文だけ（記事末の注記は除く）。

    既に公開済みの第1回・第2回にも該当箇所があった。投稿済みの記事は「新論点が出たときだけ
    更新する」（note-operation「記事の更新ルール」）ため、語尾だけを理由に書き直さない。
    ai-tone.json の baseline にラベルごとの許容件数を書いて、その分だけ見逃す。
    baseline を超えて増えたら（＝新しい下書きで同じ癖が増えたら）落とす。
    """
    endings = config.get("endings") or {}
    patterns = sorted((endings.get("patterns") or []), key=len, reverse=True)
    max_consecutive = int(endings.get("max_consecutive", 1))
    if not patterns:
        return []
    baseline = config.get("baseline") or {}
    failures = []
    for label, text in drafts.items():
        if "/note/" not in label or not label.endswith(("-FINAL.md", "-CANDIDATE.md")):
            continue
        if "\n---\n" not in text:
            continue
        body = text.split("\n---\n", 1)[1]
        lines = [
            line
            for line in body.splitlines()
            if line.strip()
            and not line.startswith(("データについて", "制度についての記述", "#", "|", "http", "▼", "👉", ">"))
        ]
        counts: dict[str, int] = {}
        run_pattern: str | None = None
        run_len = 0
        reported = False
        for line in lines:
            for sentence in re.split(r"(?<=。)", line):
                sentence = sentence.strip()
                if not sentence:
                    continue
                matched = _classify_ending(sentence, patterns)
                if matched and matched == run_pattern:
                    run_len += 1
                else:
                    run_pattern = matched
                    run_len = 1 if matched else 0
                    reported = False
                if matched and run_len > max_consecutive and not reported:
                    counts[matched] = counts.get(matched, 0) + 1
                    reported = True
        allowed = baseline.get(label, {})
        for pattern, count in counts.items():
            limit = int(allowed.get(f"endings:{pattern}", 0))
            if count > limit:
                failures.append(
                    f"語尾の連続: {label} に「{pattern}。」で{max_consecutive + 1}文以上続く箇所が"
                    f"{count}か所（上限{limit}）。WRITING_VOICE.md「対称にしない」に従い、語尾か構文を変える"
                )
    return failures


def check_persona(config: dict, pages: dict[str, list[str]], extras: dict[str, str]) -> list[str]:
    """ペルソナは社内専用。公開物に1文字でも出たら落とす。"""
    terms, _skipped = persona_terms()
    if not terms:
        return []
    failures = []
    for label, body in [(k, "\n".join(v)) for k, v in pages.items()] + list(extras.items()):
        for term in terms:
            if term in body:
                failures.append(
                    f"ペルソナ流出: {label} に「{term}」がある。"
                    f"書き手は組織名義『SNS反応まっぷ編集部』（WRITING_VOICE.md）"
                )
    return failures


def check_banned(config: dict, pages: dict[str, list[str]], extras: dict[str, str]) -> list[str]:
    failures = []
    for entry in config.get("banned") or []:
        regex = re.compile(entry["pattern"])
        for label, body in [(k, "\n".join(v)) for k, v in pages.items()] + list(extras.items()):
            hits = regex.findall(body)
            if hits:
                failures.append(
                    f"禁止フレーズ: {label} に「{entry['pattern']}」が{len(hits)}件。{entry['reason']}"
                )
    return failures


def check_mirror(config: dict, pages: dict[str, list[str]], verbose: bool) -> tuple[list[str], list[str]]:
    """賛否を同じ構文で並べる鏡像。1ページ内での回数を見る。"""
    baseline = config.get("baseline") or {}
    failures, notes = [], []
    for entry in config.get("mirror") or []:
        pattern = entry["pattern"]
        regex = re.compile(pattern)
        limit = int(entry.get("max_per_page", 1))
        key = f"mirror:{pattern}"
        for theme, body in pages.items():
            count = len(regex.findall("\n".join(body)))
            allowed = max(limit, int(baseline.get(theme, {}).get(key, 0)))
            if count > allowed:
                failures.append(
                    f"鏡像構文: {theme} に「{pattern}」が{count}件（上限{allowed}）。{entry['reason']}"
                )
            elif verbose and count:
                room = "baseline" if count > limit else "上限内"
                notes.append(f"  {theme}: {pattern} ×{count} ({room}{allowed})")
    return failures, notes


def check_density(config: dict, pages: dict[str, list[str]], verbose: bool) -> tuple[list[str], list[str]]:
    """便利な接続・対比の使いすぎ。文数で割って比べる。短いページを不利にしないため。"""
    baseline = config.get("baseline") or {}
    failures, notes = [], []
    for entry in config.get("density") or []:
        pattern = entry["pattern"]
        regex = re.compile(pattern)
        limit = float(entry["max_per_100_sentences"])
        for theme, body in pages.items():
            total = len(body)
            if total < 20:  # 文が少なすぎると1件の重みが大きくなり、意味のある比率にならない
                continue
            count = len(regex.findall("\n".join(body)))
            per100 = count / total * 100
            allowed = max(limit / 100 * total, float(baseline.get(theme, {}).get(f"density:{pattern}", 0)))
            if count > allowed:
                failures.append(
                    f"定型の使いすぎ: {theme} の「{pattern}」が{count}件/{total}文 "
                    f"= 100文あたり{per100:.1f}（上限{limit}）。{entry['reason']}"
                )
            elif verbose and count:
                mark = " ←baseline" if count > limit / 100 * total else ""
                notes.append(f"  {theme}: {pattern} ×{count}/{total}文 = {per100:.1f}/100（上限{limit}）{mark}")
    return failures, notes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-v", "--verbose", action="store_true", help="上限内の実測値も出す")
    args = parser.parse_args()

    config = load()
    pages = page_bodies()
    ledgers = ledger_texts()
    drafts = draft_texts()
    if not pages:
        print("対象ページが見つかりません", file=sys.stderr)
        return 1

    failures: list[str] = []
    _terms, skipped = persona_terms()
    failures += check_persona(config, pages, {**ledgers, **drafts})
    failures += check_banned(config, pages, drafts)
    failures += check_note_counts(config, drafts)
    failures += check_ending_repeat(config, drafts)
    mirror_fail, mirror_notes = check_mirror(config, pages, args.verbose)
    density_fail, density_notes = check_density(config, pages, args.verbose)
    failures += mirror_fail + density_fail

    if args.verbose:
        print(f"対象: 公開ページ{len(pages)}本 / 下書き{len(drafts)}件 / 台帳{len(ledgers)}件（台帳はペルソナ流出のみ）")
        if mirror_notes:
            print("鏡像構文（上限内）:")
            print("\n".join(mirror_notes))
        if density_notes:
            print("定型の密度（上限内）:")
            print("\n".join(density_notes))
        print()

    if skipped:
        print(f"注意: {skipped}", file=sys.stderr)

    if failures:
        print("AI臭の検査に落ちました。WRITING_VOICE.md を読んで直してください。\n", file=sys.stderr)
        for line in failures:
            print(f"  - {line}", file=sys.stderr)
        print(
            f"\n例外にする場合は {CONFIG.name} に理由つきで書く。理由の書けない例外は書けません。",
            file=sys.stderr,
        )
        return 1

    scope = "（ペルソナ検査は飛ばしています）" if skipped else ""
    print(f"AI臭の検査: 問題なし（公開ページ{len(pages)}本、下書き{len(drafts)}件、台帳{len(ledgers)}件）{scope}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
