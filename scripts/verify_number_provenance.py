#!/usr/bin/env python3
"""ページに出るすべての数字に出所があることを確かめる。

## なぜ場所を数えないか

「表示される数字が合わない」は 2026-08-08〜09 の2日間で5回起きた。原因はいつも同じで、
数字の正典は1つなのに、**表示している場所が何か所あるかを誰も知らない**。人が場所を
列挙して、列挙した場所だけを同期する。新しい場所が見つかるたびに列挙を足す。終わらない。

この検査は列挙をやめる。ページ（と、ページが読み込む同ディレクトリのJS）から
`N件` と アリーナのセクター `{k:'…', n:N}` を**総当たりで**拾い、正典から導けない数字が
1つでもあれば落とす。新しい表示場所が増えても、同期し忘れれば必ずここで落ちる。

## 「導ける」の中身

正典（THEMES.yaml の sample_file、および configs で足した追加ソース）のレコードから、
カテゴリらしきフィールドを**自動で見つけて**集計する。フィールド名を列挙しない。

- 母集団: 全件 / 意見のみ / 関連のみ / 関連かつ意見。さらに `fetched_at` の収集日ごと（波）
- 1次元: 各カテゴリ値の件数（母集団ごと）
- 合算: 論点（main_issue）2つまでの和。論点カードが複数ラベルを合算するテーマがあるため
- クロス集計: カテゴリ2つの組み合わせすべて（母集団ごと）

クロス集計は値が小さく、集合に入れると 0〜数十の整数がほぼ全部「説明できる」ことになる。
そこで**クロス集計は既定では使わない**。使えるのは configs の `cross_tab_selectors` に
書いた領域（詳細データの `heat-table` など）の中だけ。**書いていない場所＝新しく現れた
場所は、常に厳しいほう（1次元）で判定される。** これが「知らない場所ほど厳しい」を守る。

割合（％）は集合に入れていない。拾う対象が `N件` と `n:N` の2つだけで、％はどちらの形でも
現れないため、入れても比較されず、0〜100の整数を集合に足して検査を鈍らせるだけになる。

## 設定（configs/{theme}-reaction-map.json）

    "number_provenance": {
      "sources": ["social-samples/foo_2d_classified.json"],  // 追加の正典（任意）
      "regions": { "cross_tab": ["heat-table"] },             // 種類ごとに使える領域
      "exclude_selectors": ["quote-block", "#sources"],        // 本文がそのまま載る領域
      "allow": [
        { "value": 67470, "reason": "警察庁 令和7年中の自転車関連事故件数（一次情報）" }
      ]
    }

`exclude_selectors` / `cross_tab_selectors` の書き方は3通り。

    "foo"      … class に foo を持つ要素の内側
    "#bar"     … id が bar の要素の内側
    "<tag>"    … その要素の内側（例: "<blockquote>"）

`allow` は `value` と `reason` の両方が要る。**理由が書けない数字は、たいてい古い数字。**

    python3 scripts/verify_number_provenance.py            # 全テーマ
    python3 scripts/verify_number_provenance.py takaichi
    python3 scripts/verify_number_provenance.py -v         # 説明できた数字の根拠も出す
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable

try:
    from .issue_card_counts import IssueCountError, card_counts
    from .sync_portal_stats import ROOT, THEMES_YAML, parse_themes_yaml
except ImportError:  # python3 scripts/verify_number_provenance.py
    from issue_card_counts import IssueCountError, card_counts  # type: ignore[no-redef]
    from sync_portal_stats import ROOT, THEMES_YAML, parse_themes_yaml  # type: ignore[no-redef]


class ProvenanceError(ValueError):
    """設定か正典データが噛み合っていない。"""


# ---------------------------------------------------------------- 拾う

# 「1,234件」「56 件」、それに「389<small>件</small>」。小数や年号の一部（2026.08）は拾わない。
# 数字と「件」の間にタグが入る書き方（注目ポイントのカード）を見落とすと、
# ページで一番大きく出ている数字が検査から漏れる。
COUNT_RE = re.compile(r"(?<![\d.,])(\d{1,3}(?:,\d{3})+|\d+)\s*(?:<[^>]{1,40}>\s*)*件")
# アリーナのセクター配列 const ISSUES=[{k:'ラベル', n:N}]
SECTOR_RE = re.compile(r"\{\s*k\s*:\s*(['\"])(?:[^'\"\\]|\\.)*\1\s*,\s*n\s*:\s*(\d+)")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
STYLE_RE = re.compile(r"<style\b.*?</style>", re.S | re.I)
# ページが読み込む同ディレクトリのJS（外部CDNは対象外）
LOCAL_SCRIPT_RE = re.compile(r'<script[^>]*\bsrc="(?!https?:|//)([^"?#]+)')

VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


class Found:
    __slots__ = ("value", "start", "doc", "line", "context", "kind")

    def __init__(self, value: int, start: int, doc: str, line: int, context: str, kind: str):
        self.value = value
        self.start = start
        self.doc = doc
        self.line = line
        self.context = context
        self.kind = kind


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _context(text: str, start: int, end: int, width: int = 34) -> str:
    left = text.rfind("\n", 0, start) + 1
    right = text.find("\n", end)
    right = len(text) if right < 0 else right
    snippet = text[max(left, start - width) : min(right, end + width)]
    snippet = re.sub(r"\s+", " ", snippet).strip()
    head = "…" if start - width > left else ""
    tail = "…" if end + width < right else ""
    return f"{head}{snippet}{tail}"


def _blanked(text: str) -> str:
    """コメントとCSSを空白に潰す。表示されない数字は拾わない。"""

    def blank(match: re.Match[str]) -> str:
        return re.sub(r"[^\n]", " ", match.group(0))

    return STYLE_RE.sub(blank, COMMENT_RE.sub(blank, text))


def extract_numbers(text: str, doc: str) -> list[Found]:
    scan = _blanked(text)
    found: list[Found] = []
    for match in COUNT_RE.finditer(scan):
        value = int(match.group(1).replace(",", ""))
        found.append(
            Found(value, match.start(1), doc, _line_of(text, match.start(1)),
                  _context(text, match.start(), match.end()), "件")
        )
    for match in SECTOR_RE.finditer(scan):
        found.append(
            Found(int(match.group(2)), match.start(2), doc, _line_of(text, match.start(2)),
                  _context(text, match.start(), match.end()), "セクター")
        )
    found.sort(key=lambda item: item.start)
    return found


# ---------------------------------------------------------------- 領域

class _RegionScanner(HTMLParser):
    """class / id / タグ名ごとに、要素の占める文字範囲を集める。"""

    def __init__(self, text: str) -> None:
        super().__init__(convert_charrefs=False)
        self._text = text
        self._line_starts = [0]
        for index, char in enumerate(text):
            if char == "\n":
                self._line_starts.append(index + 1)
        self._stack: list[tuple[str, int, tuple[str, ...]]] = []
        self.regions: dict[str, list[tuple[int, int]]] = defaultdict(list)

    def _offset(self) -> int:
        line, column = self.getpos()
        return self._line_starts[line - 1] + column

    @staticmethod
    def _keys(tag: str, attrs: list[tuple[str, str | None]]) -> tuple[str, ...]:
        keys = [f"<{tag}>"]
        for name, value in attrs:
            if name == "class" and value:
                keys.extend(value.split())
            elif name == "id" and value:
                keys.append(f"#{value}")
        return tuple(keys)

    def _close(self, index: int, end: int) -> None:
        for tag, start, keys in self._stack[index:]:
            for key in keys:
                self.regions[key].append((start, end))
        del self._stack[index:]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        start = self._offset()
        if tag in VOID_TAGS:
            end = self._text.find(">", start)
            self._close_single(tag, start, (end + 1) if end >= 0 else start, attrs)
            return
        self._stack.append((tag, start, self._keys(tag, attrs)))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        start = self._offset()
        end = self._text.find(">", start)
        self._close_single(tag, start, (end + 1) if end >= 0 else start, attrs)

    def _close_single(self, tag: str, start: int, end: int,
                      attrs: list[tuple[str, str | None]]) -> None:
        for key in self._keys(tag, attrs):
            self.regions[key].append((start, end))

    def handle_endtag(self, tag: str) -> None:
        end = self._offset()
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index][0] == tag:
                # 閉じ忘れた内側の要素は、ここで一緒に閉じたことにする
                self._close(index, end)
                return

    def close(self) -> None:  # type: ignore[override]
        super().close()
        self._close(0, len(self._text))


def selector_regions(text: str, selectors: Iterable[str]) -> list[tuple[int, int]]:
    wanted = [str(name).strip() for name in selectors if str(name).strip()]
    if not wanted:
        return []
    scanner = _RegionScanner(text)
    scanner.feed(text)
    scanner.close()
    regions: list[tuple[int, int]] = []
    for name in wanted:
        regions.extend(scanner.regions.get(name, []))
    return regions


def in_regions(offset: int, regions: list[tuple[int, int]]) -> bool:
    return any(start <= offset < end for start, end in regions)


# ラベルと数字の間に入ってよい「言葉」の数。記号・引用符・タグは何個あっても構わない。
#   インフラ優先派（30件）        → 「派」の1文字だけ  → 添えられている
#   {k:"義務化・事故防止",n:0}     → 記号だけ           → 添えられている
#   禁止支持8件、中立・体験10件    → 10 の手前に6文字   → 添えられていない（別の数字）
LABEL_GAP_WORDS = 1
WORDISH = re.compile(r"[0-9A-Za-z぀-ヿ㐀-鿿０-９]")


def nearest_label(text: str, offset: int, labels: set[str]) -> str | None:
    """数字に添えられている分類ラベル。いちばん近いものを1つだけ返す。

    ラベルが添えられている数字は「その論点／立場の集計」を名乗っているので、
    値がどこかの集計と一致するだけでは足りない。**そのラベルの集計**である必要がある。
    """
    window = text[max(0, offset - 48) : offset]
    best: tuple[int, str] | None = None
    for label in labels:
        position = window.rfind(label)
        if position < 0:
            continue
        between = window[position + len(label) :]
        distance = len(WORDISH.findall(between))
        if distance > LABEL_GAP_WORDS:
            continue
        if best is None or distance < best[0] or (distance == best[0] and len(label) > len(best[1])):
            best = (distance, label)
    return best[1] if best else None


# ---------------------------------------------------------------- 導く

# 値ではなく本文・識別子であって、カテゴリではないフィールド
NON_DIMENSION = {
    "text", "url", "tweet_id", "user_id", "record_id_hash", "summary", "reason",
    "title", "id", "seed", "fetched_at",
}
MAX_DISTINCT = 60


def _classification(record: dict[str, Any]) -> dict[str, Any]:
    nested = record.get("classification")
    return nested if isinstance(nested, dict) else {}


def _flatten(record: dict[str, Any]) -> dict[str, Any]:
    """トップレベルと classification を1枚に混ぜる（classification を優先）。"""
    flat: dict[str, Any] = {}
    for key, value in record.items():
        if key != "classification":
            flat[key] = value
    flat.update(_classification(record))
    fetched = record.get("fetched_at")
    if isinstance(fetched, str) and len(fetched) >= 10:
        flat["fetched_date"] = fetched[:10]
    return flat


def _dimensions(records: list[dict[str, Any]]) -> list[str]:
    values: dict[str, set[Any]] = defaultdict(set)
    for record in records:
        for key, value in _flatten(record).items():
            if key in NON_DIMENSION or not isinstance(value, (str, bool)):
                continue
            if isinstance(value, str) and (not value or len(value) > 60):
                continue
            values[key].add(value)
    return sorted(key for key, seen in values.items() if 0 < len(seen) <= MAX_DISTINCT)


def _truthy(record: dict[str, Any], field: str, default: bool) -> bool:
    flat = _flatten(record)
    value = flat.get(field, default)
    return bool(value)


# 導出の種類。base はどこでも使える。それ以外は configs の regions に領域を
# 書いた場所でしか使えない。**書いていない場所＝新しく現れた場所は必ず base で判定される。**
LEVELS = ("base", "cross_tab", "wave", "combined")


class Derived:
    """1つの正典ファイルから導ける値を、導出の種類ごとに持つ。

    base      … 母集団（全件／関連／意見／関連かつ意見）の総数と、各カテゴリの1次元件数
    cross_tab … カテゴリ2つのクロス集計（詳細データの表、論点内のスタンス分布）
    wave      … 収集日ごとに切り出した件数（「世論の潮目」の比較対象）
    combined  … 論点・スタンス2つの和と差（カードの合算、「A と B を合わせると N件」）
    """

    def __init__(self, label: str, records: list[dict[str, Any]]) -> None:
        self.label = label
        # level -> 値 -> (代表的な根拠, その値を作れる集計に出てくる分類ラベル)
        self.values: dict[str, dict[int, tuple[str, set[str]]]] = {level: {} for level in LEVELS}
        self.labels: set[str] = set()
        self._build(records)

    def _note(self, level: str, value: int, why: str, *labels: Any) -> None:
        entry = self.values[level].get(int(value))
        if entry is None:
            entry = (f"{self.label}: {why}", set())
            self.values[level][int(value)] = entry
        entry[1].update(str(item) for item in labels if isinstance(item, str))

    def add_base(self, value: int, why: str, labels: Iterable[str]) -> None:
        """外から base に足す（論点カードの合算件数など、設定の定義そのもの）。"""
        self._note("base", value, why, *labels)

    def lookup(self, value: int, levels: Iterable[str], label: str | None) -> str | None:
        """value を説明する根拠。label が添えられた数字は、そのラベルの集計に限る。"""
        levels = list(levels)
        # クロス集計は組み合わせが無い＝0件のセルも表に出る。0だけは相手を問わない。
        if value == 0 and "cross_tab" in levels:
            return f"{self.label}: クロス集計の空セル"
        for level in levels:
            entry = self.values[level].get(value)
            if entry is None:
                continue
            if label is None:
                return entry[0]
            if label in entry[1]:
                return f"{entry[0]}（ラベル {label} を含む集計）"
        return None

    @staticmethod
    def _counts(subset: list[dict[str, Any]], dims: list[str]) -> dict[str, Counter[Any]]:
        per_dim: dict[str, Counter[Any]] = {dim: Counter() for dim in dims}
        for record in subset:
            flat = _flatten(record)
            for dim in dims:
                value = flat.get(dim)
                if isinstance(value, (str, bool)) and value != "":
                    per_dim[dim][value] += 1
        return per_dim

    def _build(self, records: list[dict[str, Any]]) -> None:
        dims = _dimensions(records)
        for record in records:
            flat = _flatten(record)
            for dim in dims:
                value = flat.get(dim)
                # 1文字のラベルは本文にたまたま現れるので、突き合わせには使わない
                if isinstance(value, str) and len(value) >= 2:
                    self.labels.add(value)
        populations = {
            "全件": records,
            "意見": [r for r in records if _truthy(r, "is_opinion", False)],
            "関連": [r for r in records if _truthy(r, "is_relevant", True)],
            "関連かつ意見": [
                r for r in records
                if _truthy(r, "is_relevant", True) and _truthy(r, "is_opinion", False)
            ],
        }

        for name, subset in populations.items():
            per_dim = self._counts(subset, dims)
            self._note("base", len(subset), f"{name} の総数")
            for dim, counter in per_dim.items():
                for key, count in counter.items():
                    self._note("base", count, f"{name} の {dim}={key}", key)
                # 「賛否双方の検索語20件」のような、値ではなく種類の数
                self._note("base", len(counter), f"{name} の {dim} の種類数")

            issues = per_dim.get("main_issue")
            if issues:
                # アリーナは「その他」セクターを持たないテーマがあり、点の総数が
                # 「その他」を除いた合計になる
                self._note(
                    "base",
                    sum(count for key, count in issues.items() if key != "その他"),
                    f"{name} の main_issue（その他を除く）合計",
                )

            # 「A と B を合わせると N件」「N件差」「潮目ウィジェットが表示する立場だけの合計」。
            # 論点・立場のいくつかを足した数と、その差まで。combined を有効にした領域でしか使えない。
            for dim in ("main_issue", "stance"):
                items = sorted((per_dim.get(dim) or {}).items())
                if not items or len(items) > 12:
                    continue
                sums: dict[int, list[str]] = {}
                for index in range(1, 1 << len(items)):
                    picked = [items[bit] for bit in range(len(items)) if index >> bit & 1]
                    sums.setdefault(
                        sum(count for _, count in picked), [label for label, _ in picked]
                    )
                for value, picked in sums.items():
                    self._note("combined", value, f"{name} の {dim}={'+'.join(picked)}", *picked)
                ordered = sorted(sums)
                for i, small in enumerate(ordered):
                    for large in ordered[i + 1 :]:
                        self._note(
                            "combined", large - small,
                            f"{name} の {dim}: {'+'.join(sums[large])} と {'+'.join(sums[small])} の差",
                            *sums[large], *sums[small],
                        )

            for i, first in enumerate(dims):
                for second in dims[i + 1 :]:
                    cross: Counter[tuple[Any, Any]] = Counter()
                    for record in subset:
                        flat = _flatten(record)
                        a, b = flat.get(first), flat.get(second)
                        if isinstance(a, (str, bool)) and isinstance(b, (str, bool)):
                            cross[(a, b)] += 1
                    for (a, b), count in cross.items():
                        self._note(
                            "cross_tab", count, f"{name} の {first}={a} × {second}={b}", a, b
                        )
            # クロス集計は「0件」の組み合わせも表に出る
            self._note("cross_tab", 0, "クロス集計の空セル")

            waves: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for record in subset:
                date = _flatten(record).get("fetched_date")
                if isinstance(date, str):
                    waves[date].append(record)
            for date, wave in sorted(waves.items()):
                label = f"{name}/{date}収集"
                self._note("wave", len(wave), f"{label} の総数")
                for dim, counter in self._counts(wave, dims).items():
                    for key, count in counter.items():
                        self._note("wave", count, f"{label} の {dim}={key}", key)


def load_records(relative_path: str) -> list[dict[str, Any]]:
    path = (ROOT / relative_path).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ProvenanceError(f"リポジトリ外を指しています: {relative_path}") from exc
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProvenanceError(f"正典が存在しません: {relative_path}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProvenanceError(f"正典を読めません: {relative_path}: {exc}") from exc
    if not isinstance(data, list) or not data:
        raise ProvenanceError(f"正典はJSON配列である必要があります: {relative_path}")
    return [record for record in data if isinstance(record, dict)]


# ---------------------------------------------------------------- 検査

def _allow_map(theme: str, block: dict[str, Any]) -> list[tuple[int, str, list[str] | None]]:
    """[(値, 理由, 使える領域のセレクタ or None=ページ全体)]"""
    allowed: list[tuple[int, str, list[str] | None]] = []
    entries = block.get("allow") or []
    if not isinstance(entries, list):
        raise ProvenanceError(f"{theme}: number_provenance.allow は配列です")
    for entry in entries:
        if not isinstance(entry, dict):
            raise ProvenanceError(f"{theme}: allow の要素はオブジェクトです: {entry!r}")
        if "value" not in entry:
            raise ProvenanceError(f"{theme}: allow に value がありません: {entry!r}")
        reason = str(entry.get("reason") or "").strip()
        if not reason:
            raise ProvenanceError(
                f"{theme}: allow の {entry.get('value')!r} に reason がありません。"
                "理由が書けない数字は、たいてい古い数字です"
            )
        try:
            value = int(entry["value"])
        except (TypeError, ValueError) as exc:
            raise ProvenanceError(f"{theme}: allow の value が整数ではありません: {entry!r}") from exc
        selectors = entry.get("selectors")
        if selectors is not None and not isinstance(selectors, list):
            raise ProvenanceError(f"{theme}: allow の selectors は配列です: {entry!r}")
        allowed.append(
            (value, reason, None if selectors is None else [str(name) for name in selectors])
        )
    return allowed


def _documents(html_path: Path) -> list[tuple[str, str]]:
    """ページ本体と、ページが読み込む同ディレクトリのJS。"""
    page = html_path.read_text(encoding="utf-8")
    docs = [(str(html_path.relative_to(ROOT)), page)]
    seen = set()
    for match in LOCAL_SCRIPT_RE.finditer(page):
        src = match.group(1)
        target = (html_path.parent / src).resolve()
        if target in seen or not target.is_file():
            continue
        try:
            target.relative_to(ROOT.resolve())
        except ValueError:
            continue
        seen.add(target)
        docs.append((str(target.relative_to(ROOT)), target.read_text(encoding="utf-8")))
    return docs


def check_theme(theme: str, theme_data: dict[str, Any], *, verbose: bool = False) -> tuple[str, list[str]]:
    config_path = ROOT / "configs" / f"{theme}-reaction-map.json"
    if not config_path.is_file():
        raise ProvenanceError(f"{theme}: config がありません: {config_path}")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    block = config.get("number_provenance")
    if block is None:
        block = {}
    if not isinstance(block, dict):
        raise ProvenanceError(f"{theme}: number_provenance はオブジェクトです")

    html_path = ROOT / str(theme_data.get("html") or "")
    if not html_path.is_file():
        raise ProvenanceError(f"{theme}: ページがありません: {html_path}")

    sample_file = str(theme_data.get("sample_file") or "")
    if not sample_file:
        raise ProvenanceError(f"{theme}: 正典（sample_file）が決まりません")
    extra = block.get("sources") or []
    if not isinstance(extra, list):
        raise ProvenanceError(f"{theme}: number_provenance.sources は配列です")
    # (Derived, その正典が使える領域のセレクタ or None=どこでも)
    sources: list[tuple[str, list[str] | None]] = [(sample_file, None)]
    for entry in extra:
        if isinstance(entry, str):
            sources.append((entry, None))
            continue
        if not isinstance(entry, dict) or not entry.get("path"):
            raise ProvenanceError(f"{theme}: sources の要素は文字列か path つきオブジェクトです: {entry!r}")
        selectors = entry.get("selectors")
        if selectors is not None and not isinstance(selectors, list):
            raise ProvenanceError(f"{theme}: sources の selectors は配列です: {entry!r}")
        if not str(entry.get("reason") or "").strip():
            raise ProvenanceError(
                f"{theme}: sources の {entry['path']} に reason がありません。"
                "追加の正典は、なぜその数字の出所なのかを書かないと登録できません"
            )
        # selectors を書かない追加正典はページ全体で使える。空配列はどこでも使えない指定。
        sources.append(
            (str(entry["path"]), None if selectors is None else [str(name) for name in selectors])
        )
    derived = [
        (Derived(Path(path).name, load_records(path)), selectors) for path, selectors in sources
    ]
    # 論点カードは複数の分類ラベルを1枚に合算するテーマがある。合算後の件数は
    # issue_counts の定義そのものなので、当て推量の和ではなく定義から入れる。
    try:
        raw_cards = {
            str(card.get("slug")): card
            for card in (config.get("issue_counts") or {}).get("cards") or []
            if isinstance(card, dict)
        }
        for card in card_counts(theme, config, sample_file):
            raw = raw_cards.get(str(card["slug"]), {})
            labels = [str(name) for name in (raw.get("main_issue") or [])]
            if raw.get("arena_label"):
                labels.append(str(raw["arena_label"]))
            derived[0][0].add_base(
                int(card["count"]), f"論点カード {card['slug']}（{'+'.join(labels)}）", labels
            )
    except IssueCountError as exc:
        raise ProvenanceError(f"{theme}: 論点カードの件数を計算できません: {exc}") from exc

    allowed = _allow_map(theme, block)
    excludes = block.get("exclude_selectors") or []
    if not isinstance(excludes, list):
        raise ProvenanceError(f"{theme}: number_provenance.exclude_selectors は配列です")
    regions_cfg = block.get("regions") or {}
    if not isinstance(regions_cfg, dict):
        raise ProvenanceError(f"{theme}: number_provenance.regions はオブジェクトです")
    unknown = [name for name in regions_cfg if name not in LEVELS or name == "base"]
    if unknown:
        raise ProvenanceError(
            f"{theme}: number_provenance.regions に未知の指定があります: {', '.join(unknown)}"
            f"（使えるのは {', '.join(LEVELS[1:])}）"
        )

    total = explained = 0
    problems: list[str] = []
    notes: list[str] = []
    for doc_name, text in _documents(html_path):
        numbers = extract_numbers(text, doc_name)
        if not numbers:
            continue
        excluded = selector_regions(text, excludes)
        level_regions = {
            level: selector_regions(text, regions_cfg.get(level) or []) for level in LEVELS[1:]
        }
        source_regions = [
            (source, None if selectors is None else selector_regions(text, selectors))
            for source, selectors in derived
        ]
        allow_regions = [
            (value, reason, None if selectors is None else selector_regions(text, selectors))
            for value, reason, selectors in allowed
        ]
        for item in numbers:
            if in_regions(item.start, excluded):
                continue
            total += 1
            levels = ["base"] + [
                level for level in LEVELS[1:] if in_regions(item.start, level_regions[level])
            ]
            why = None
            label = None
            for source, regions in source_regions:
                if regions is not None and not in_regions(item.start, regions):
                    continue
                label = nearest_label(text, item.start, source.labels)
                why = source.lookup(item.value, levels, label)
                if why:
                    break
            if why is None:
                for value, reason, regions in allow_regions:
                    if value == item.value and (regions is None or in_regions(item.start, regions)):
                        why = f"許可リスト: {reason}"
                        break
            if why is None:
                hint = f"（「{label}」の集計に {item.value} は無い）" if label else ""
                problems.append(f"      {doc_name}:L{item.line}: {item.context}{hint}")
            else:
                explained += 1
                if verbose:
                    notes.append(
                        f"      {doc_name}:L{item.line}: {item.value} ← [{'/'.join(levels)}] {why}"
                    )

    status = "NG " if problems else "OK "
    line = (
        f"{status} {theme}: 拾った{total} / 説明できた{explained} / 説明できない{len(problems)}"
    )
    if verbose:
        problems = notes + problems
    return line, problems


def main() -> int:
    parser = argparse.ArgumentParser(description="ページ上の数字に出所があることを確かめる")
    parser.add_argument("theme", nargs="?", help="THEMES.yaml のテーマslug（省略時は全テーマ）")
    parser.add_argument("-v", "--verbose", action="store_true", help="説明できた数字の根拠も出す")
    args = parser.parse_args()

    themes = parse_themes_yaml(THEMES_YAML)
    targets = [args.theme] if args.theme else list(themes)
    unknown = [name for name in targets if name not in themes]
    if unknown:
        print(f"ERROR: THEMES.yaml にありません: {', '.join(unknown)}", file=sys.stderr)
        return 1

    ng = 0
    try:
        for theme in targets:
            line, problems = check_theme(theme, themes[theme], verbose=args.verbose)
            print(line)
            for problem in problems:
                print(problem)
            if line.startswith("NG"):
                ng += 1
    except ProvenanceError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"=== 数字の出所: {len(targets)}テーマ / NG {ng}件 ===")
    return 1 if ng else 0


if __name__ == "__main__":
    raise SystemExit(main())
