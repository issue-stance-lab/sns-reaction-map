#!/usr/bin/env python3
"""Apply SEO metadata, Article JSON-LD, and visible trust details to theme pages."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urljoin


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from consumption_tax_connected import apply as connect_consumption_tax_page
from issue_card_counts import IssueCountError, count_by_issue_from_public_json
from koshitsu_connected import apply as connect_koshitsu_page
SEO_START = "<!-- SEO_META_START -->"
SEO_END = "<!-- SEO_META_END -->"
JSONLD_START = "<!-- ARTICLE_JSON_LD_START -->"
JSONLD_END = "<!-- ARTICLE_JSON_LD_END -->"
TRUST_START = "<!-- ARTICLE_TRUST_START -->"
TRUST_END = "<!-- ARTICLE_TRUST_END -->"
PROTECTED_TOKENS = (
    "G-K10S4YCZFH",
    "ca-pub-2542211932832864",
    "supabase",
    "topic-modern.js",
)
TOPIC_CSS_VERSION = "32"  # 2026-09-27 課題95: 全テーマの見出し字体を共通化


def connect_page(source: str, *, topic: str) -> str:
    """SEO再生成後も、テーマ固有の接続仕上げを最後に戻す。"""
    source = connect_consumption_tax_page(source, topic=topic)
    return connect_koshitsu_page(source, topic=topic)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def replace_marked(source: str, start: str, end: str, replacement: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if not pattern.search(source):
        raise ValueError(f"missing managed block: {start}")
    return pattern.sub(replacement, source, count=1)


def japanese_date(value: str) -> str:
    parsed = date.fromisoformat(value)
    return f"{parsed.year}年{parsed.month}月{parsed.day}日"


def sample_file_for(theme_id: str) -> Path:
    """THEMES.yaml から sample_file を引く（YAML依存を足さないため正規表現で読む）。"""
    text = (PROJECT_ROOT / "THEMES.yaml").read_text(encoding="utf-8")
    pattern = rf"^  {re.escape(theme_id)}:\s*$(.*?)(?=^  [\w-]+:\s*$|\Z)"
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    if not match:
        raise ValueError(f"THEMES.yamlにテーマがありません: {theme_id}")
    file_match = re.search(r"^    sample_file:\s*[\"']?([^\"'#\n]+)", match.group(1), re.MULTILINE)
    if not file_match:
        raise ValueError(f"{theme_id}: sample_file がありません")
    return PROJECT_ROOT / file_match.group(1).strip()


def is_opinion(row: dict) -> bool:
    """意見と判定されたか。

    テーマによって置き場所が違う。`classification` の下にある形と、レコード直下にある形の
    両方がある。さらに自転車の青切符のように、**`classification` はあるがその中に
    `is_opinion` が無く、直下にだけある**テーマもある。
    `classification` があれば必ずそちらを見る書き方だと、この形で常に0件になる
    （2026-08-08 に「意見と判定した0件」を公開しかけた）。キーの有無で判断する。
    """
    nested = row.get("classification")
    if isinstance(nested, dict) and "is_opinion" in nested:
        return bool(nested["is_opinion"])
    return bool(row.get("is_opinion"))


# 論点カードに出さない受け皿ラベル。ここに落ちた投稿は {issue_opinions} から外す。
CATCH_ALL_ISSUES = {"その他", "その他・分類保留", "その他・わからない"}


def main_issue(row: dict) -> str:
    """主論点のラベル。is_opinion と同じく置き場所がテーマで違うのでキーの有無で判断する。"""
    nested = row.get("classification")
    if isinstance(nested, dict) and "main_issue" in nested:
        return str(nested.get("main_issue") or "")
    return str(row.get("main_issue") or "")


# 論点別の意見数の差し込み。{issue_count:地方の足・移動権} のように論点名を書く。
ISSUE_COUNT_PLACEHOLDER = re.compile(r"\{issue_count:([^{}]+)\}")


def resolve_issue_counts(text: str, theme_id: str) -> str:
    """{issue_count:論点名} を、公開データJSONの論点別の意見数へ置き換える。

    出所は data/public/themes/<theme>.json（論点カードの件数と同じ）。正典を数え直さないので
    正典が無い環境でも動く。非公開の正典が手元にあれば、公開データJSONが現在の正典と
    食い違っていないか（source_sha256）を読み込み側が確かめ、古ければ止まる。

    論点名が公開データJSONに無いときも止まる。数字を空欄や古い値のまま出すより、
    更新作業が止まって気づくほうがよい。
    """
    labels = ISSUE_COUNT_PLACEHOLDER.findall(text)
    if not labels:
        return text
    try:
        counts = count_by_issue_from_public_json(theme_id)
    except IssueCountError as exc:
        raise ValueError(f"{theme_id}: 論点別の件数を公開データJSONから読めません: {exc}") from exc
    missing = sorted({label for label in labels if label not in counts})
    if missing:
        raise ValueError(
            f"{theme_id}: 公開データJSONに無い論点名が {{issue_count:…}} に書かれています: "
            f"{', '.join(missing)}（あるのは {', '.join(sorted(counts))}）"
        )
    return ISSUE_COUNT_PLACEHOLDER.sub(lambda match: f"{counts[match.group(1)]:,}", text)


def resolve_counts(text: str, theme_id: str) -> str:
    """収集方法の文中の {total} / {opinions} を分類結果の実数へ置き換える。

    以前はここが件数のべた書きで、更新しても誰も直さないまま公開ページに古い数字が
    残っていた（部活動は累計467件・意見389件のまま実際は732件・599件だった）。
    昇格処理がこのスクリプトを呼ぶので、差し込みにしておけば毎回ずれない。

    論点別の件数は {issue_count:論点名}（resolve_issue_counts）。分析メモ（observations）に
    「この論点は○件」と書くときは数字を打たず、必ずこちらを使う。高齢者テーマで
    設定へべた書きした 29／221 が 2026-09-04 時点のまま残り、作り直すたびに
    正しい 39／283 を打ち消した。
    """
    text = resolve_issue_counts(text, theme_id)
    placeholders = ("{total}", "{opinions}", "{issue_opinions}")
    if not any(name in text for name in placeholders):
        return text
    rows = json.loads(sample_file_for(theme_id).read_text(encoding="utf-8"))
    counts = {
        "total": len(rows),
        "opinions": sum(1 for row in rows if is_opinion(row)),
        # 論点カードに載る件数。受け皿の「その他」を含めるかはテーマで違い、
        # 高市ページは除いた359件で図と指標を作っているのに、この欄だけ360件と
        # 書いていた（2026-08-12）。件数をべた書きせずに済ませるための差し込み。
        "issue_opinions": sum(
            1
            for row in rows
            if is_opinion(row) and main_issue(row) not in CATCH_ALL_ISSUES
        ),
    }
    for key, value in counts.items():
        text = text.replace("{" + key + "}", f"{value:,}")
    return text


def seo_block(theme: dict[str, Any], base_url: str) -> str:
    canonical = urljoin(base_url, theme["url"])
    image_url = urljoin(base_url, theme["image"])
    headline = html.escape(theme["headline"], quote=True)
    description = html.escape(theme["description"], quote=True)
    return "\n".join(
        [
            SEO_START,
            f'  <meta name="description" content="{description}">',
            f'  <link rel="canonical" href="{canonical}">',
            '  <meta property="og:type" content="article">',
            '  <meta property="og:site_name" content="SNS反応まっぷ">',
            f'  <meta property="og:title" content="{headline}">',
            f'  <meta property="og:description" content="{description}">',
            f'  <meta property="og:url" content="{canonical}">',
            f'  <meta property="og:image" content="{image_url}">',
            '  <meta name="twitter:card" content="summary_large_image">',
            f'  <meta name="twitter:title" content="{headline}">',
            f'  <meta name="twitter:description" content="{description}">',
            f'  <meta name="twitter:image" content="{image_url}">',
            SEO_END,
        ]
    )


def jsonld_block(theme: dict[str, Any], config: dict[str, Any]) -> str:
    base_url = config["site_url"]
    canonical = urljoin(base_url, theme["url"])
    organization_url = urljoin(base_url, config["organization"]["url"])
    organization = {
        "@type": "Organization",
        "name": config["organization"]["name"],
        "url": organization_url,
    }
    payload = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": theme["headline"],
        "description": theme["description"],
        "image": [urljoin(base_url, theme["image"])],
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "datePublished": theme["datePublished"],
        "dateModified": theme["dateModified"],
        "author": organization,
        "publisher": organization,
    }
    if theme.get("temporalCoverage"):
        payload["temporalCoverage"] = theme["temporalCoverage"]
    encoded = json.dumps(payload, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return f'{JSONLD_START}\n  <script type="application/ld+json">\n{encoded}\n  </script>\n{JSONLD_END}'


def observations_html(theme: dict[str, Any]) -> str:
    """「収集・分類で分かったこと」。

    セオリコの診断で Experience（体験・経験）が NG になった。記事が収集結果の整理だけで、
    運営側が実際に手を動かして分かったことが1行も書かれていなかったため。

    ここに書くのは**実際の作業ログにある事実だけ**。材料は
    data/verification/updates/<theme>/<date>/report.json（機械検証済みの件数）、
    THEMES.yaml の notes（作業中に起きたこと）、configs/topics/<theme>.yaml（検索語）。
    作り話を書かない。材料が無いテーマには節ごと出さない。
    """
    items = theme.get("observations") or []
    if not items:
        return ""
    rows = "\n".join(
        f"      <li>{html.escape(resolve_counts(str(item), theme['id']))}</li>" for item in items
    )
    return (
        "    <h3>収集・分類で分かったこと</h3>\n"
        '    <ul class="article-trust-observations">\n'
        f"{rows}\n"
        "    </ul>\n"
    )


def trust_block(theme: dict[str, Any], organization: dict[str, str]) -> str:
    published = theme["datePublished"]
    modified = theme["dateModified"]
    collection = html.escape(resolve_counts(theme["collection"], theme["id"]))
    organization_name = html.escape(organization["name"])
    observations = observations_html(theme)
    ai_process = "" if theme.get("show_ai_process") is False else """\
    <h3>AIを使用した工程</h3>
    <p>収集後の投稿について、AIを関連性・意見性の判定、論点・立場・表現強度の分類、要旨作成の補助に使用しています。ページ内にAI生成の図解・漫画がある場合は、その制作補助にも使用しています。AIによる分類には誤りや偏りが含まれる可能性があります。</p>
"""
    return f"""\
{TRUST_START}
<aside class="article-trust" aria-labelledby="article-trust-title">
  <div class="article-trust-heading">
    <p class="article-trust-kicker">編集・分析情報</p>
    <h2 id="article-trust-title">このページの作り方</h2>
  </div>
  <dl class="article-trust-meta">
    <div><dt>公開日</dt><dd><time datetime="{published}">{japanese_date(published)}</time></dd></div>
    <div><dt>最終更新日</dt><dd><time datetime="{modified}">{japanese_date(modified)}</time></dd></div>
    <div><dt>編集・分析</dt><dd><a href="about.html">{organization_name}</a></dd></div>
  </dl>
  <div class="article-trust-method">
    <h3>SNS投稿の収集方法</h3>
    <p>{collection}</p>
{ai_process}
{observations}  </div>
  <p class="article-trust-caution"><strong>データの読み方:</strong> このページは世論調査ではなく、検索語と収集時点に基づくSNS投稿サンプルの分類結果です。社会全体の意見割合や事実認定を示すものではありません。</p>
  <p class="article-trust-contact">内容の訂正、引用の削除依頼、調査方法への問い合わせは、<a href="about.html#corrections">運営者情報・訂正窓口</a>をご確認ください。</p>
</aside>
{TRUST_END}"""


def validate_config(config: dict[str, Any], site_cases: dict[str, Any]) -> None:
    themes = config.get("themes") or []
    urls = [item["url"] for item in themes]
    if len(urls) != len(set(urls)):
        raise ValueError("theme SEO config contains duplicate URLs")
    case_urls = {
        item["reaction_map_url"]
        for item in site_cases.get("cases") or []
        if item.get("reaction_map_url")
    }
    if set(urls) != case_urls:
        missing = sorted(case_urls - set(urls))
        extra = sorted(set(urls) - case_urls)
        raise ValueError(f"theme URL mismatch: missing={missing}, extra={extra}")
    for theme in themes:
        date.fromisoformat(theme["datePublished"])
        date.fromisoformat(theme["dateModified"])
        if theme["dateModified"] < theme["datePublished"]:
            raise ValueError(f'{theme["id"]}: dateModified precedes datePublished')


def apply_theme(source: str, theme: dict[str, Any], config: dict[str, Any]) -> str:
    before_counts = {token: source.count(token) for token in PROTECTED_TOKENS}
    title = html.escape(f'{theme["headline"]}｜SNS反応まっぷ')
    updated = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", source, count=1, flags=re.DOTALL)
    updated = re.sub(
        r"topic-modern\.css\?v=\d+",
        f"topic-modern.css?v={TOPIC_CSS_VERSION}",
        updated,
    )
    updated = updated.replace(
        'src="ogp/fukushuto.png"',
        'src="images/topics/fukushuto/fukushuto-hero.webp"',
    )
    seo_start_index = updated.find(SEO_START)
    if seo_start_index < 0:
        raise ValueError(f'{theme["id"]}: missing SEO metadata block')
    prefix = re.sub(
        r'\s*<meta\s+name=["\']description["\']\s+content=["\'].*?["\']\s*/?>',
        "",
        updated[:seo_start_index],
        flags=re.DOTALL | re.IGNORECASE,
    )
    updated = prefix + updated[seo_start_index:]
    updated = replace_marked(updated, SEO_START, SEO_END, seo_block(theme, config["site_url"]))

    jsonld = jsonld_block(theme, config)
    if JSONLD_START in updated:
        updated = replace_marked(updated, JSONLD_START, JSONLD_END, jsonld)
    else:
        updated = updated.replace(SEO_END, f"{SEO_END}\n{jsonld}", 1)

    headline = html.escape(theme["headline"])
    updated, h1_count = re.subn(r"(<h1[^>]*>).*?(</h1>)", rf"\1{headline}\2", updated, count=1, flags=re.DOTALL)
    if h1_count != 1:
        raise ValueError(f'{theme["id"]}: unable to update H1')

    trust = trust_block(theme, config["organization"])
    if TRUST_START in updated:
        updated = replace_marked(updated, TRUST_START, TRUST_END, trust)
    else:
        method_pattern = re.compile(
            r"<div[^>]*>\s*<strong>データの集め方:</strong>.*?</div>",
            re.DOTALL,
        )
        updated, method_count = method_pattern.subn(trust, updated, count=1)
        if method_count != 1:
            raise ValueError(f'{theme["id"]}: unable to replace existing collection method')

    after_counts = {token: updated.count(token) for token in PROTECTED_TOKENS}
    for token in PROTECTED_TOKENS:
        if before_counts[token] and after_counts[token] < before_counts[token]:
            raise ValueError(f'{theme["id"]}: protected token removed: {token}')
    return connect_page(updated, topic=theme["id"])


# 「収集・分類で分かったこと」だけを差し替えるための目印。
OBSERVATIONS_PATTERN = re.compile(
    r"    <h3>収集・分類で分かったこと</h3>\n"
    r'    <ul class="article-trust-observations">\n.*?    </ul>\n',
    re.DOTALL,
)


def apply_observations_only(source: str, theme: dict[str, Any]) -> str:
    """分析メモだけを入れ替える。件数表示には触れない。

    ブロック全体を作り直すには正典（本文を含むため一部が Git 管理外）が要る。
    正典が手元に無い環境でも分析メモを更新できるように、この経路を残す。
    """
    block = observations_html(theme)
    if OBSERVATIONS_PATTERN.search(source):
        return connect_page(OBSERVATIONS_PATTERN.sub(lambda _: block, source, count=1), topic=theme["id"])
    if not block:
        return source
    anchor = "  </div>\n  <p class=\"article-trust-caution\">"
    if anchor not in source:
        raise ValueError(f'{theme["id"]}: 分析メモの差し込み位置が見つかりません')
    return connect_page(source.replace(anchor, block + anchor, 1), topic=theme["id"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/theme-seo.json")
    parser.add_argument("--site-cases", default="configs/site-cases.json")
    parser.add_argument("--docs-dir", default="docs")
    parser.add_argument("--theme", help="指定したテーマだけを更新する")
    parser.add_argument("--check", action="store_true", help="validate and report without writing")
    parser.add_argument(
        "--observations-only",
        action="store_true",
        help="「収集・分類で分かったこと」だけを更新する（正典が無い環境用）",
    )
    args = parser.parse_args()

    config = load_json(PROJECT_ROOT / args.config)
    site_cases = load_json(PROJECT_ROOT / args.site_cases)
    validate_config(config, site_cases)
    docs_dir = PROJECT_ROOT / args.docs_dir

    themes = config["themes"]
    if args.theme:
        themes = [theme for theme in themes if theme["id"] == args.theme]
        if not themes:
            raise ValueError(f"unknown theme: {args.theme}")

    changed = 0
    for theme in themes:
        path = docs_dir / theme["url"]
        if not path.is_file():
            raise FileNotFoundError(path)
        source = path.read_text(encoding="utf-8")
        if args.observations_only:
            updated = apply_observations_only(source, theme)
        else:
            updated = apply_theme(source, theme, config)
        if updated != source:
            changed += 1
            if not args.check:
                path.write_text(updated, encoding="utf-8")
        status = "unchanged"
        if updated != source:
            status = "would update" if args.check else "updated"
        print(f"{status} {path.relative_to(PROJECT_ROOT)}")

    print(f'Validated {len(themes)} theme pages; changed={changed}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
