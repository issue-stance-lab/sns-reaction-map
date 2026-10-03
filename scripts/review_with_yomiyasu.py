#!/usr/bin/env python3
"""公開文章だけを抽出し、よみやすと保護トークンの検査を実行する。

上流のリンター（.claude/skills/yomiyasu/upstream）は、ダッシュ記号・1文の読点の数・
文の長さを検査しない。この3つはこのスクリプトが検査する。しきい値と除外する行は
configs/yomiyasu.json の mechanical_checks にあり、機械で止まる項目の一覧は
.claude/skills/yomiyasu/references/sns-reaction-map.md にある。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "yomiyasu.json"
LINTER = ROOT / ".claude" / "skills" / "yomiyasu" / "upstream" / "scripts" / "yomiyasu_lint.py"
URL_RE = re.compile(r"https?://[^\s)>]+")
NUMBER_RE = re.compile(r"(?<![A-Za-z0-9_])[0-9０-９]+(?:[,，.．][0-9０-９]+)*(?:兆円|億円|万円|[%％]|件|円|年|月|日)?")
NOTE_SEPARATOR_RE = re.compile(r"(?m)^---\s*$")

# 文の長さを数える前に本文から外すもの。URL_RE は全角の閉じかっこ以降まで飲み込むので、
# 文中のURLは半角の文字だけで切る。
INLINE_URL_RE = re.compile(r"https?://[A-Za-z0-9\-._~:/?#@!$&'*+,;=%\[\]()]+")
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
EMPHASIS_RE = re.compile(r"\*\*|\*|__")
LIST_ITEM_RE = re.compile(r"[-*+]\s|\d+\.\s")
# 「。」の直後が閉じかっこなら文を切らない（「…です。」と言う人もいる、を1文に数える）。
SENTENCE_END_RE = re.compile(r"(?<=[。！？])(?![」』）)])")
# 上流リンターと同じ減点（warn/error は5点、それ以外は2点）。
PENALTY = {"warn": 5, "error": 5}
INFO_PENALTY = 2
MECHANICAL_KEYS = (
    "dash_chars",
    "comma_chars",
    "comma_warn_at",
    "comma_info_at",
    "sentence_warn_over",
    "average_target",
    "average_info_below",
    "average_info_above",
    "average_skip_mediums",
    "exempt_line_prefixes",
)


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def load_linter():
    if not LINTER.is_file():
        raise SystemExit(f"よみやす本体がありません: {LINTER}")
    spec = importlib.util.spec_from_file_location("project_yomiyasu_lint", LINTER)
    if spec is None or spec.loader is None:
        raise SystemExit(f"よみやす本体を読み込めません: {LINTER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def infer_medium(path: Path) -> str:
    if path.suffix.lower() in {".html", ".htm"}:
        return "website"
    label = str(path).lower()
    if "/note/" in label or path.name.endswith(("-FINAL.md", "-CANDIDATE.md")):
        return "note"
    if "/x/" in label:
        return "x"
    return "seo"


def note_body(text: str) -> str:
    matches = list(NOTE_SEPARATOR_RE.finditer(text))
    if not matches:
        return text
    if text.lstrip().startswith("---") and len(matches) >= 2:
        return text[matches[1].end():].lstrip()
    return text[matches[0].end():].lstrip()


def website_body(path: Path) -> str:
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from verify_page_originality import load_config as load_originality
        from verify_page_originality import visible_parts
    finally:
        sys.path.pop(0)
    shared = load_originality().get("shared_selectors", [])
    headings, _leads, paragraphs = visible_parts(path, shared)
    lines = [*(f"## {heading}" for heading in headings), *paragraphs]
    return "\n\n".join(lines)


def public_text(path: Path, medium: str) -> str:
    if medium == "website":
        return website_body(path)
    text = path.read_text(encoding="utf-8")
    if medium == "note":
        return note_body(text)
    return text


def protected_tokens(text: str) -> dict[str, Counter[str]]:
    return {
        "urls": Counter(URL_RE.findall(text)),
        "numbers": Counter(NUMBER_RE.findall(text)),
    }


def compare_protected(before: str, after: str, enabled: list[str]) -> list[str]:
    old = protected_tokens(before)
    new = protected_tokens(after)
    failures = []
    for kind in enabled:
        if old[kind] == new[kind]:
            continue
        removed = list((old[kind] - new[kind]).elements())
        added = list((new[kind] - old[kind]).elements())
        failures.append(f"{kind}: 消えた値={removed or 'なし'} / 増えた値={added or 'なし'}")
    return failures


def mechanical_settings(config: dict[str, Any]) -> dict[str, Any]:
    section = config.get("mechanical_checks")
    if not isinstance(section, dict):
        raise SystemExit(f"{CONFIG.name} に mechanical_checks がありません")
    missing = [key for key in MECHANICAL_KEYS if key not in section]
    if missing:
        raise SystemExit(f"{CONFIG.name} の mechanical_checks に項目がありません: {', '.join(missing)}")
    return section


def make_finding(rule: str, line: int, severity: str, message: str, snippet: str) -> dict[str, Any]:
    """上流リンターの指摘と同じ形にする。"""
    return {"rule": rule, "line": line, "severity": severity, "message": message, "snippet": snippet}


def shorten(sentence: str, limit: int = 24) -> str:
    return sentence if len(sentence) <= limit else sentence[:limit] + "…"


def frontmatter_line_count(lines: list[str]) -> int:
    """先頭のYAMLフロントマター（--- から --- まで）の行数。無ければ0。"""
    if not lines or lines[0].strip() != "---":
        return 0
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return index + 1
    return 0


def body_lines(text: str) -> Iterator[tuple[int, str]]:
    """フロントマターとコードブロックを除いた行を (行番号, 行) で返す。"""
    lines = text.split("\n")
    skipped = frontmatter_line_count(lines)
    in_code = False
    for number, line in enumerate(lines, 1):
        if number <= skipped:
            continue
        if line.strip().startswith(("```", "~~~")):
            in_code = not in_code
            continue
        if not in_code:
            yield number, line


def is_prose_line(line: str, exempt_prefixes: tuple[str, ...]) -> bool:
    """文の長さと読点の数を数える行か。

    数えない行: 空行、インデント行、見出し、表、引用、画像、HTML、リスト、URLで始まる行、
    configs/yomiyasu.json の exempt_line_prefixes で始まる行（画像の指示行・注記・「・」の箇条書き）。
    """
    stripped = line.strip()
    if not stripped or line.startswith(("  ", "\t")):
        return False
    if stripped.startswith(("#", "|", "![", "[![", "<", ">", "http://", "https://")):
        return False
    return not (LIST_ITEM_RE.match(stripped) or stripped.startswith(exempt_prefixes))


def plain_prose(line: str) -> str:
    """リンクはリンク文字だけ、URL・インラインコード・強調記号は外した、文として読む部分。"""
    line = MARKDOWN_LINK_RE.sub(r"\1", line)
    line = INLINE_URL_RE.sub("", line)
    line = INLINE_CODE_RE.sub("", line)
    return EMPHASIS_RE.sub("", line).strip()


def split_sentences(text: str, settings: dict[str, Any]) -> list[tuple[int, str]]:
    """文の長さと読点を数える文を (行番号, 文) で返す。1行ずつ区切るので、改行は文をまたがない。"""
    exempt = tuple(prefix for group in settings["exempt_line_prefixes"].values() for prefix in group)
    sentences = []
    for number, line in body_lines(text):
        if not is_prose_line(line, exempt):
            continue
        for piece in SENTENCE_END_RE.split(plain_prose(line)):
            piece = piece.strip()
            if re.search(r"\w", piece):
                sentences.append((number, piece))
    return sentences


def dash_findings(text: str, settings: dict[str, Any]) -> list[dict[str, Any]]:
    """ダッシュ記号は、見出し・引用・注記・URL行も含めて公開本文のどこにあっても止める（絵文字と同じ扱い）。

    外すのはフロントマター、コードブロック、インラインコードだけ。
    """
    dash_re = re.compile("[" + re.escape("".join(settings["dash_chars"])) + "]")
    findings = []
    for number, line in body_lines(text):
        scan = INLINE_CODE_RE.sub("", line)
        match = dash_re.search(scan)
        if match is None:
            continue
        found = " ".join(f"{char} U+{ord(char):04X}" for char in sorted(set(dash_re.findall(scan))))
        context = scan[max(0, match.start() - 12) : match.end() + 12].strip()
        findings.append(
            make_finding(
                "dash_prohibited",
                number,
                "warn",
                f"ダッシュ記号が検出されました（{found}）。公開本文では使いません。"
                f"読点や句点で整えるか、2文に分けてください。「{context}」",
                line.strip(),
            )
        )
    return findings


def sentence_findings(
    text: str, medium: str, settings: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """1文の読点の数、1文の長さ、平均文長を検査する。(指摘, 文の長さの実測) を返す。"""
    comma_warn = int(settings["comma_warn_at"])
    comma_info = int(settings["comma_info_at"])
    long_over = int(settings["sentence_warn_over"])
    findings: list[dict[str, Any]] = []
    lengths: list[int] = []
    longest, longest_line = 0, 0
    for number, sentence in split_sentences(text, settings):
        length = len(re.sub(r"\s+", "", sentence))
        commas = sum(sentence.count(char) for char in settings["comma_chars"])
        lengths.append(length)
        if length > longest:
            longest, longest_line = length, number
        severity, advice = None, ""
        if commas >= comma_warn:
            severity = "warn"
            advice = (
                f"。{comma_warn}個以上は完成を止めます）。"
                "つながりを残せる形で文を分けるか、言い換えて減らしてください。"
            )
        elif commas >= comma_info:
            severity = "info"
            advice = "）。並べ書きなど必要なら残してかまいません。"
        if severity:
            findings.append(
                make_finding(
                    "comma_count",
                    number,
                    severity,
                    f"1文に読点が{commas}個あります（目安は{comma_info - 1}個まで{advice}"
                    f"「{shorten(sentence)}」",
                    sentence,
                )
            )
        if length > long_over:
            findings.append(
                make_finding(
                    "sentence_too_long",
                    number,
                    "warn",
                    f"1文が{length}字あります（{long_over}字超は完成を止めます）。"
                    "手段・理由・順序・対比のつながりを後ろの文に残せるなら分けてください。"
                    f"分けると意味が変わる文は、理由を添えて残します。「{shorten(sentence)}」",
                    sentence,
                )
            )
    average = sum(lengths) / len(lengths) if lengths else None
    low, high = settings["average_target"]
    below, above = settings["average_info_below"], settings["average_info_above"]
    if average is not None and medium not in settings["average_skip_mediums"]:
        if average < below or average > above:
            direction = "短い" if average < below else "長い"
            findings.append(
                make_finding(
                    "average_sentence_length",
                    1,
                    "info",
                    f"平均文長が{average:.1f}字です（目安は{low}〜{high}字。{below}字未満または"
                    f"{above}字超で知らせます）。{direction}文が続いていないか確認してください。",
                    f"文数{len(lengths)} / 最長{longest}字",
                )
            )
    metrics = {
        "sentences": len(lengths),
        "average": round(average, 1) if average is not None else None,
        "longest": longest,
        "longest_line": longest_line,
        "target": [low, high],
    }
    return findings, metrics


def mechanical_findings(
    text: str, medium: str, config: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """上流リンターが見ない項目（ダッシュ記号・読点・文の長さ）の指摘と、文の長さの実測を返す。"""
    settings = mechanical_settings(config)
    sentence_results, metrics = sentence_findings(text, medium, settings)
    findings = [*dash_findings(text, settings), *sentence_results]
    findings.sort(key=lambda finding: finding["line"])
    return findings, metrics


def review(path: Path, medium: str, original: Path | None = None) -> dict[str, Any]:
    config = load_config()
    text = public_text(path, medium)
    lint = load_linter().lint_text(text)
    extra, sentence_metrics = mechanical_findings(text, medium, config)
    findings = [*lint["findings"], *extra]
    protected_failures: list[str] = []
    if original is not None:
        before = public_text(original, medium)
        protected_failures = compare_protected(
            before, text, list(config.get("protected_tokens") or [])
        )
    strict = set(config.get("strict_severities") or ["warn", "error"])
    blocking = [finding for finding in findings if finding["severity"] in strict]
    penalty = sum(PENALTY.get(finding["severity"], INFO_PENALTY) for finding in extra)
    return {
        "file": str(path),
        "medium": medium,
        "score": max(0, lint["score"] - penalty),
        "findings": findings,
        "sentence_metrics": sentence_metrics,
        "blocking_count": len(blocking),
        "protected_failures": protected_failures,
        "passed": not blocking and not protected_failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("file", type=Path)
    parser.add_argument("--medium", choices=("auto", "note", "website", "seo", "x"), default="auto")
    parser.add_argument("--original", type=Path)
    parser.add_argument("--strict", action="store_true", help="warn/errorまたは保護値の変化で終了コード1")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.file.is_file():
        parser.error(f"対象ファイルがありません: {args.file}")
    if args.original is not None and not args.original.is_file():
        parser.error(f"変更前ファイルがありません: {args.original}")

    medium = infer_medium(args.file) if args.medium == "auto" else args.medium
    result = review(args.file, medium, args.original)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"よみやす検査: {result['file']} ({result['medium']})")
        print(f"スコア: {result['score']}/100 / 完成を止める指摘: {result['blocking_count']}件")
        metrics = result["sentence_metrics"]
        if metrics["sentences"]:
            low, high = metrics["target"]
            print(
                f"文の長さ: 平均{metrics['average']}字（目安{low}〜{high}字） / "
                f"最長{metrics['longest']}字（L{metrics['longest_line']}） / 文数{metrics['sentences']}"
            )
        else:
            print("文の長さ: 数える文がありません")
        for finding in result["findings"]:
            print(f"L{finding['line']} [{finding['severity']}] {finding['message']}")
        for failure in result["protected_failures"]:
            print(f"[protected] {failure}")
        print("判定: " + ("PASS" if result["passed"] else "要修正"))
    return 1 if args.strict and not result["passed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
