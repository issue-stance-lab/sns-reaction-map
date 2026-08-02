#!/usr/bin/env python3
"""docs/index.html の統計が THEMES.yaml の正典と一致するか検証する。"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

try:
    from .sync_portal_stats import (
        INDEX_HTML,
        ROOT,
        THEMES_YAML,
        PortalStatsError,
        compute_stats,
        parse_themes_yaml,
        replacement_specs,
    )
except ImportError:  # python3 scripts/verify_top_page.py
    from sync_portal_stats import (  # type: ignore[no-redef]
        INDEX_HTML,
        ROOT,
        THEMES_YAML,
        PortalStatsError,
        compute_stats,
        parse_themes_yaml,
        replacement_specs,
    )


FEATURED_QUESTION_LINKS = {
    "ai-copyright": "ai-copyright-reaction-map.html",
    "bike-blue-ticket": "bike-blue-ticket-reaction-map.html",
    "bukatsu-chiiki": "bukatsu-chiiki-reaction-map.html",
    "consumption-tax-cut": "consumption-tax-cut-reaction-map.html",
}

TOPIC_CARD_LINKS = {
    "ai-copyright": "ai-copyright-reaction-map.html",
    "bike-blue-ticket": "bike-blue-ticket-reaction-map.html",
    "bukatsu-chiiki": "bukatsu-chiiki-reaction-map.html",
    "constitutional-amendment": "constitutional-amendment-reaction-map.html",
    "elderly-license-revocation": "elderly-license-revocation-reaction-map.html",
    "school-nickname-ban": "school-nickname-ban-reaction-map.html",
    "henoko-student-accident": "henoko-student-accident-reaction-map.html",
    "takaichi": "takaichi-reaction-map-standard.html",
    "fukushuto": "fukushuto-reaction-map.html",
    "koshitsu-tenpakai": "koshitsu-tenpakai-reaction-map.html",
    "consumption-tax-cut": "consumption-tax-cut-reaction-map.html",
}


def _content_markup(html: str) -> str:
    """CSS/JS内の表示でない数値を禁止表示検査から除外する。"""
    return re.sub(
        r"<(?:style|script)\b[^>]*>.*?</(?:style|script)>",
        "",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )


def _visible_text(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", _content_markup(html))


def _outdated_dates(html: str, today: date) -> list[str]:
    """表示テキスト中の日付から、30日以上前のものを返す。"""
    text = _visible_text(html)
    found: dict[str, date] = {}
    for match in re.finditer(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text):
        label = match.group(0)
        try:
            found[label] = date(*map(int, match.groups()))
        except ValueError:
            continue
    for match in re.finditer(r"(?<!\d)(\d{1,2})/(\d{1,2})(?!\d)", text):
        label = match.group(0)
        try:
            candidate = date(today.year, int(match.group(1)), int(match.group(2)))
        except ValueError:
            continue
        if candidate > today and (candidate - today).days > 180:
            candidate = date(today.year - 1, candidate.month, candidate.day)
        found[label] = candidate
    return sorted(label for label, value in found.items() if (today - value).days >= 30)


def _link_target_exists(index_path: Path, href: str) -> bool:
    if re.match(r"^(?:https?:|mailto:|tel:)", href):
        return True
    path_part, _, fragment = href.partition("#")
    target = index_path if not path_part else index_path.parent / path_part
    if not target.is_file():
        return False
    if not fragment:
        return True
    target_html = target.read_text(encoding="utf-8")
    return re.search(rf'\bid=["\']{re.escape(fragment)}["\']', target_html) is not None


def _media_blocks(css: str) -> list[str]:
    """CSSからネストを考慮して @media ブロックを取り出す。"""
    blocks: list[str] = []
    for match in re.finditer(r"@media\b", css, flags=re.IGNORECASE):
        start = css.find("{", match.end())
        if start < 0:
            continue
        depth = 1
        pos = start + 1
        while pos < len(css) and depth:
            if css[pos] == "{":
                depth += 1
            elif css[pos] == "}":
                depth -= 1
            pos += 1
        if depth == 0:
            blocks.append(css[start + 1 : pos - 1])
    return blocks


def _hero_side_hidden_in_media(html: str) -> bool:
    styles = "\n".join(re.findall(r"<style\b[^>]*>(.*?)</style>", html, re.DOTALL | re.IGNORECASE))
    return any(
        re.search(r"\.hero-side\s*\{[^}]*\bdisplay\s*:\s*none\b", block, re.IGNORECASE)
        for block in _media_blocks(styles)
    )


def _unmanaged_count_labels(html: str) -> list[str]:
    """id付き要素で生成されていない「○件」表示を返す。"""
    content = _content_markup(html)
    managed = re.compile(
        r'<(?P<tag>[a-z][\w:-]*)\b[^>]*\bid="[^"]+"[^>]*>'
        r'\s*\d[\d,]*\s*</(?P=tag)>\s*件',
        flags=re.IGNORECASE,
    )
    remaining = managed.sub(" ", content)
    return re.findall(r"(?<![\d,])\d[\d,]*\s*件", _visible_text(remaining))


def _card_count(
    body: str,
    *,
    css_class: str,
    id_prefix: str,
) -> tuple[str, int] | None:
    match = re.search(
        rf'<[^>]*class="{re.escape(css_class)}"[^>]*>'
        rf'\s*分類済み\s*<strong id="{re.escape(id_prefix)}-([^"]+)">'
        r'([\d,]+)</strong>\s*件',
        body,
    )
    if not match:
        return None
    return match.group(1), int(match.group(2).replace(",", ""))


def verify_top_page(
    root: Path = ROOT,
    themes_path: Path = THEMES_YAML,
    index_path: Path = INDEX_HTML,
) -> tuple[list[str], int]:
    """検証結果の行とNG件数を返す。tests/ からも呼び出せる。"""
    themes = parse_themes_yaml(themes_path)
    stats = compute_stats(themes, root, allow_synthetic=True)
    html = index_path.read_text(encoding="utf-8")
    lines = [
        "=== 数値の出所 ===",
        f"分類済み投稿   {stats['total_posts']:,}   ← sample_file の実レコード合計（{stats['theme_count']}テーマ）",
        f"公開テーマ数      {stats['theme_count']}   ← THEMES.yaml published:done",
        f"最終更新    {stats['last_updated'].isoformat()}  ← THEMES.yaml updated_at 最大",
        f"次回更新    {stats['next_update'].isoformat() if stats['next_update'] else '未定'}  ← THEMES.yaml refresh_at の今日以降の最小",
        "",
        "=== 置換の空振り検査 ===",
    ]

    failures = 0
    for label, pattern, replacement in replacement_specs(stats):
        matches = len(re.findall(pattern, html))
        replaced = re.sub(pattern, replacement, html)
        if matches > 0 and replaced == html:
            lines.append(f"OK  {label:<24} {matches}件マッチ")
        elif matches == 0:
            lines.append(f"NG  {label:<24} 0件マッチ")
            failures += 1
        else:
            lines.append(f"NG  {label:<24} {matches}件マッチ（値不一致）")
            failures += 1

    lines.extend(["", "=== 件数の網羅検査 ==="])
    unmanaged_counts = _unmanaged_count_labels(html)
    dynamic_delta_has_id = (
        "fn.id=countEl.id.replace('topic-count-','topic-delta-')" in html
    )
    if unmanaged_counts or not dynamic_delta_has_id:
        detail = unmanaged_counts or ["更新バッジの動的件数に id がない"]
        lines.append(
            "NG  ページ内の「○件」表示は全て id 付き: "
            + ", ".join(detail)
        )
        failures += 1
    else:
        lines.append("OK  ページ内の「○件」表示は全て id 付き（手入力の件数が残っていない）")

    topic_cards = re.findall(
        r'<a\s+class="topic-card"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
        html,
        flags=re.DOTALL,
    )
    topic_counts: dict[str, int] = {}
    invalid_topic_cards: list[str] = []
    href_to_topic = {href: theme for theme, href in TOPIC_CARD_LINKS.items()}
    for href, body in topic_cards:
        expected_theme = href_to_topic.get(href)
        parsed = _card_count(body, css_class="topic-meta", id_prefix="topic-count")
        if not expected_theme or not parsed or parsed[0] != expected_theme:
            invalid_topic_cards.append(href)
            continue
        topic_counts[expected_theme] = parsed[1]
    topic_values_match = (
        len(topic_cards) == len(TOPIC_CARD_LINKS)
        and not invalid_topic_cards
        and topic_counts == stats["sample_counts"]
    )
    if topic_values_match:
        lines.append(
            f"OK  テーマカード{len(TOPIC_CARD_LINKS)}枚の件数が sample_file と一致する"
        )
    else:
        mismatches = [
            f"{theme}={topic_counts.get(theme, '未検出')}"
            f"/正典{stats['sample_counts'].get(theme, 'なし')}"
            for theme in TOPIC_CARD_LINKS
            if topic_counts.get(theme) != stats["sample_counts"].get(theme)
        ]
        lines.append(
            f"NG  テーマカード{len(TOPIC_CARD_LINKS)}枚の件数が sample_file と一致する: "
            + ", ".join(mismatches + invalid_topic_cards)
        )
        failures += 1

    question_cards = re.findall(
        r'<a\s+class="question-card"\s+data-theme="([^"]+)"[^>]*>(.*?)</a>',
        html,
        flags=re.DOTALL,
    )
    question_counts: dict[str, int] = {}
    for theme, body in question_cards:
        parsed = _card_count(body, css_class="question-count", id_prefix="featured-count")
        if parsed and parsed[0] == theme:
            question_counts[theme] = parsed[1]
    expected_question_counts = {
        theme: stats["sample_counts"][theme] for theme in FEATURED_QUESTION_LINKS
    }
    if len(question_cards) == 4 and question_counts == expected_question_counts:
        lines.append("OK  問いカード4枚の件数が sample_file と一致する")
    else:
        lines.append("NG  問いカード4枚の件数が sample_file と一致する")
        failures += 1

    hero_match = re.search(
        r'<strong id="hero-total-samples">([\d,]+)</strong>', html
    )
    hero_total = int(hero_match.group(1).replace(",", "")) if hero_match else None
    topic_total = sum(topic_counts.values())
    if topic_values_match and hero_total == topic_total == stats["total_posts"]:
        lines.append(f"OK  テーマカード合計 {topic_total:,} = ヒーロー表示 {hero_total:,}")
    else:
        lines.append(f"NG  テーマカード合計 {topic_total:,} = ヒーロー表示 {hero_total}")
        failures += 1

    count_cards = re.findall(
        r'<(?:div|span)\s+class="(?:topic-meta|question-count)"[^>]*>(.*?)</(?:div|span)>',
        html,
        flags=re.DOTALL,
    )
    if len(count_cards) == 15 and all("分類済み" in body for body in count_cards):
        lines.append("OK  件数の用語が「分類済み」で統一されている")
    else:
        lines.append("NG  件数の用語が「分類済み」で統一されている")
        failures += 1

    lines.extend(["", "=== 正典ファイル検査 ==="])
    for name, synthetic_count in stats["synthetic_counts"].items():
        if synthetic_count:
            lines.append(f"NG  {name:<28} synthetic {synthetic_count}件")
            failures += 1
        else:
            lines.append(f"OK  {name:<28} synthetic 0件")

    lines.extend(["", "=== 日付検査 ==="])
    if stats["overdue_count"]:
        lines.append(f"OK  期限超過 {stats['overdue_count']}テーマを「更新予定を確認中」と表示")
    elif stats["next_update"] and stats["next_update"] >= stats["today"]:
        lines.append(
            f"OK  次回更新 {stats['next_update'].isoformat()} "
            f"≥ 今日 {stats['today'].isoformat()}"
        )
    else:
        lines.append("OK  次回更新日は未定")
    missing = stats["refresh_at_missing"]
    if missing:
        lines.append(f"OK  refresh_at 空欄は候補から除外: {', '.join(missing)}")
    else:
        lines.append("OK  refresh_at 空欄 0件")

    lines.extend(["", "=== 禁止表示 ==="])
    content_markup = _content_markup(html)
    forbidden = (
        ("「割れ度」なし", "割れ度"),
        ("「公開テーマの分類比率」なし", "公開テーマの分類比率"),
        ("「どっちが多い」なし", "どっちが多い"),
    )
    for label, needle in forbidden:
        if needle in content_markup:
            lines.append(f"NG  {label}")
            failures += 1
        else:
            lines.append(f"OK  {label}")

    old_dates = _outdated_dates(html, stats["today"])
    if old_dates:
        lines.append(f"NG  30日以上前の日付を含む要素なし: {', '.join(old_dates)}")
        failures += 1
    else:
        lines.append("OK  30日以上前の日付を含む要素なし")

    percentages = re.findall(r"\d{1,3}(?:\.\d+)?%", content_markup)
    if percentages:
        lines.append(f"NG  ハードコードされた割合（NN%）なし: {', '.join(percentages[:5])}")
        failures += 1
    else:
        lines.append("OK  ハードコードされた割合（NN%）なし")

    lines.extend(["", "=== リンク ==="])
    cards = re.findall(
        r'<a\s+class="question-card"\s+data-theme="([^"]+)"\s+href="([^"]+)"',
        html,
    )
    valid_cards = sum(
        FEATURED_QUESTION_LINKS.get(theme) == href
        and _link_target_exists(index_path, href)
        for theme, href in cards
    )
    if len(cards) == 4 and valid_cards == 4 and len(dict(cards)) == 4:
        lines.append("OK  問いカード 4/4 リンク有効（リンク先HTMLが実在する）")
    else:
        lines.append(f"NG  問いカード {valid_cards}/4 リンク有効")
        failures += 1

    growth_text = (root / "GROWTH.yaml").read_text(encoding="utf-8")
    featured_theme_match = re.search(
        r"^featured:\s*([\w-]+)", growth_text, flags=re.MULTILINE
    )
    feature_card_match = re.search(
        r'<a\s+class="feature-card"\s+href="([^"]+)"', html
    )
    featured_theme = featured_theme_match.group(1) if featured_theme_match else None
    featured_href = feature_card_match.group(1) if feature_card_match else None
    expected_feature_href = (
        Path(themes[featured_theme]["html"]).name
        if featured_theme in themes and themes[featured_theme].get("html")
        else None
    )
    if featured_href and featured_href == expected_feature_href:
        lines.append(
            f"OK  今週の注目テーマ {featured_theme} が GROWTH.yaml の featured と一致する"
        )
    else:
        lines.append(
            "NG  今週の注目テーマが GROWTH.yaml の featured と一致する"
        )
        failures += 1

    if "#ranking" in html:
        lines.append("NG  #ranking 参照なし")
        failures += 1
    else:
        lines.append("OK  #ranking 参照なし")

    nav_match = re.search(
        r'<nav\s+class="main-nav"[^>]*>(.*?)</nav>',
        html,
        flags=re.DOTALL,
    )
    nav_links = re.findall(r'href="([^"]+)"', nav_match.group(1)) if nav_match else []
    invalid_nav = [href for href in nav_links if not _link_target_exists(index_path, href)]
    if nav_links and not invalid_nav:
        lines.append(f"OK  ナビの全リンク先が実在する（{len(nav_links)}件）")
    else:
        detail = ", ".join(invalid_nav) if invalid_nav else "ナビ未検出"
        lines.append(f"NG  ナビの全リンク先が実在する: {detail}")
        failures += 1

    lines.extend(["", "=== レスポンシブ ==="])
    if _hero_side_hidden_in_media(html):
        lines.append("NG  .hero-side に display:none を適用するメディアクエリなし")
        failures += 1
    else:
        lines.append("OK  .hero-side に display:none を適用するメディアクエリなし")

    disclaimer = "世論調査ではありません"
    disclaimer_pos = html.find(disclaimer)
    stats_pos = html.find('class="hero-stats')
    if disclaimer_pos >= 0:
        lines.append(f"OK  「{disclaimer}」がページ内に存在する")
    else:
        lines.append(f"NG  「{disclaimer}」がページ内に存在する")
        failures += 1
    if disclaimer_pos >= 0 and stats_pos >= 0 and disclaimer_pos < stats_pos:
        lines.append("OK  注意書きが hero-stats より前に出現する")
    else:
        lines.append("NG  注意書きが hero-stats より前に出現する")
        failures += 1
    return lines, failures


def main() -> int:
    try:
        lines, failures = verify_top_page()
    except (OSError, PortalStatsError) as exc:
        print(f"ERROR: {exc}")
        return 1
    print("\n".join(lines))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
