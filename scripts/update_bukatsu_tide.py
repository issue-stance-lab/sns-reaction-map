#!/usr/bin/env python3
"""部活動ページを、Hermes分類の最新データに合わせて更新する。

2026-10-06まで、このスクリプトは「世論の潮目」（前回と今回の2回比較）のカードも作っていた。
内容が「意見の推移」（scripts/build_trend_section.py）と重なるため外し、推移の枠だけを残す。
推移の中身は更新のたびに adapter（scripts/refresh_adapters/bukatsu.py）が貼り直す。
ファイル名の tide は、その名残。
"""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from .bukatsu_taxonomy import ISSUES, STANCES, STANCE_BY_LABEL
except ImportError:
    from bukatsu_taxonomy import ISSUES, STANCES, STANCE_BY_LABEL  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parent.parent
STANCE_SHORT = {label: item["short_label"] for label, item in STANCE_BY_LABEL.items()}
STANCE_CLASS = {
    "移行支持": "pro",
    "条件付き・改善要求": "conditional",
    "慎重・反対": "con",
    "中立・情報": "neutral",
}
STANCE_X = {label: float(item["x"]) for label, item in STANCE_BY_LABEL.items()}
INTENSITY_E = {"low": 0.5, "medium": 1.0, "high": 2.0}

# 編集確認済みの代表投稿。直近追加分（status が 208... の投稿）も含め、
# 各論点で具体的な条件・経験・制度設計を説明しているものを優先する。
# データ更新でURLが欠けた場合は、下の confidence 順の候補に安全に戻る。
REPRESENTATIVE_POSTS = {
    "費用・家庭負担": [
        ("https://x.com/TheMirageof0/status/2070621781757726855", "家計にのしかかる会費"),
        ("https://x.com/774nyannyan/status/2086731858579263880", "公費が足りないと縮小・負担増"),
    ],
    "受け皿・指導者": [
        ("https://x.com/maru_moneyy/status/2084392638506274876", "受け皿の人手・送迎が足りない"),
        ("https://x.com/kohei_okada_pt/status/2084608274377437341", "地域資源に合わせた再構築を求める"),
    ],
    "教員の働き方": [
        ("https://x.com/AtelierClutch/status/2082217044611834122", "授業に専念できる環境を求める"),
        ("https://x.com/Namenotblanko/status/2082969614196093400", "善意に頼らない仕組みを求める"),
    ],
    "教育的意義・機会": [
        ("https://x.com/ikuji_takuto/status/2083492685223215132", "学校教育としての部活を残したい"),
        ("https://x.com/39Md8/status/2082487864135393452", "生涯スポーツ・音楽につながる場にしたい"),
    ],
    "地域格差": [
        ("https://x.com/Davestaragues/status/2085511206278939102", "地方で施設が取れない"),
        ("https://x.com/mamamam4949/status/2069589990011818183", "都市部への環境偏在を懸念"),
    ],
    "制度・移行プロセス": [
        ("https://x.com/4ZYVNjQOkWBSoU8/status/2085954870243426355", "公費と負担金の仕組みが必要"),
        ("https://x.com/Goshiki2023/status/2078663825013031272", "費用・場所・責任の設計が未解決"),
    ],
    "その他": [
        ("https://x.com/m727243023/status/2085525452777795616", "吹奏楽は移行しにくいという経験"),
        ("https://x.com/mamimami_koro/status/2087383840331608316", "マネージャーの役割にある性別規範を問う"),
    ],
}

ISSUE_STANCE_LABEL = {
    "移行支持": "地域で担う形を進めたい",
    "条件付き・改善要求": "条件を整えて進めたい",
    "慎重・反対": "今のままでは進めにくい",
    "中立・情報": "経験・情報を共有",
}

HERMES_CSS = """
/* HERMES_CARD_START */
.hermes-summary-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.hermes-summary-card{border:1px solid var(--line);border-radius:12px;background:#fff;padding:16px}.hermes-summary-card .axis-count{font-size:28px}
.hermes-issue-list{display:grid;gap:14px}.hermes-issue-card{border:1px solid var(--line);border-radius:12px;background:#fff;padding:18px}.hermes-issue-head{display:flex;justify-content:space-between;gap:12px;align-items:baseline}.hermes-issue-head h3{margin:0;font-size:18px}.hermes-issue-count{font-weight:900;color:var(--accent);white-space:nowrap}
.hermes-stance-bar{display:flex;height:12px;border-radius:999px;overflow:hidden;background:#eef2f6;margin:12px 0 8px}.hermes-stance-bar span.pro{background:#059669}.hermes-stance-bar span.conditional{background:#d97706}.hermes-stance-bar span.con{background:#dc2626}.hermes-stance-bar span.neutral{background:#94a3b8}
.hermes-legend{display:flex;gap:10px;flex-wrap:wrap;color:var(--muted);font-size:11px}.hermes-samples{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-top:14px}.hermes-sample{min-width:0;overflow:hidden;border:1px solid var(--line);border-radius:10px;padding:12px;background:var(--accent-soft);font-size:12px;line-height:1.55}.hermes-sample-meta{display:block;color:var(--accent);font-size:11px;font-weight:900}.hermes-sample-summary{margin:5px 0 8px;color:var(--ink);font-weight:700}.hermes-sample .twitter-tweet,.hermes-sample .twitter-tweet-rendered{max-width:100%!important;margin:0 auto!important}.hermes-sample .twitter-tweet iframe{max-width:100%!important}
@media(max-width:720px){
  .hermes-summary-grid,.hermes-samples{grid-template-columns:1fr}
  .hermes-issue-head{display:block}.hermes-issue-count{display:block;margin-top:4px}
}
/* HERMES_CARD_END */
"""

def load(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON list")
    return data


def classification(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("classification")
    return value if isinstance(value, dict) else {}


def opinions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if classification(row).get("is_relevant") and classification(row).get("is_opinion")]


def js(value: Any) -> str:
    return json.dumps(str(value or ""), ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e")


def replace_once(source: str, pattern: str, replacement: str, label: str, flags: int = 0) -> str:
    updated, count = re.subn(pattern, lambda _match: replacement, source, count=1, flags=flags)
    if count != 1:
        raise ValueError(f"{label}: expected 1 match, found {count}")
    return updated


def sm_raw(rows: list[dict[str, Any]]) -> str:
    lines = ["const SM_RAW = ["]
    for row in rows:
        c = classification(row)
        issue = c.get("main_issue") if c.get("main_issue") in ISSUES else "その他"
        lines.append(
            "{" +
            f"x:{STANCE_X.get(str(c.get('stance')), 0):.1f}," +
            f"e:{INTENSITY_E.get(str(c.get('intensity')), 0.5):.1f}," +
            f"c:{float(c.get('confidence', 0.5)):.2f}," +
            f"i:{ISSUES.index(issue)}," +
            f"s:{js(c.get('summary'))}," +
            f"u:{js(row.get('url'))}" +
            "},"
        )
    lines.append("];")
    return "\n".join(lines)


def issue_panel(rows: list[dict[str, Any]]) -> str:
    blocks = []
    for issue in ISSUES:
        group = [row for row in rows if classification(row).get("main_issue") == issue]
        counts = Counter(classification(row).get("stance") for row in group)
        total = len(group)
        bar = "".join(
            f'<span class="{STANCE_CLASS[stance]}" style="width:{counts[stance] * 100 / total:.2f}%"></span>'
            for stance in STANCES if total and counts[stance]
        )
        legend = " ".join(
            f"<span>{html.escape(ISSUE_STANCE_LABEL[stance])} {counts[stance]}</span>"
            for stance in STANCES if counts[stance]
        )
        usable = [row for row in group if classification(row).get("article_usable") and row.get("url")]
        candidates_by_url = {str(row["url"]): row for row in usable}
        candidates = [
            (candidates_by_url[url], label)
            for url, label in REPRESENTATIVE_POSTS.get(issue, [])
            if url in candidates_by_url
        ]
        fallback = sorted(
            [row for row in usable if row not in [candidate[0] for candidate in candidates]],
            key=lambda row: float(classification(row).get("confidence", 0)),
            reverse=True,
        )
        fallback_samples = [
            (row, ISSUE_STANCE_LABEL.get(str(classification(row).get("stance")), "投稿の視点"))
            for row in fallback
        ]
        candidates = (candidates + fallback_samples)[:2]
        samples = "".join(tweet_sample(row, label) for row, label in candidates)
        blocks.append(
            '<article class="hermes-issue-card">'
            f'<div class="hermes-issue-head"><h3>{html.escape(issue)}</h3><span class="hermes-issue-count">{total}件</span></div>'
            f'<div class="hermes-stance-bar">{bar}</div><div class="hermes-legend">{legend}</div>'
            f'<div class="hermes-samples">{samples}</div>'
            "</article>"
        )
    return (
        '<section class="panel conflict-panel"><div class="panel-title"><h2>7つの論点とXの声</h2>'
        '<span>公開投稿を論点・立場・主張の強さで配置</span></div>'
        '<div class="hermes-issue-list">' + "".join(blocks) + "</div></section>"
    )


def tweet_sample(row: dict[str, Any], detail_label: str) -> str:
    """Render the same X embed used for representative posts on other themes."""
    url = html.escape(str(row.get("url") or ""), quote=True)
    handle = re.search(r"x\.com/([^/]+)/status/", str(row.get("url") or ""))
    account = f"@{handle.group(1)}" if handle else "この投稿"
    detail_label = html.escape(detail_label)
    summary = html.escape(str(classification(row).get("summary") or ""))
    return (
        '<div class="hermes-sample">'
        f'<span class="hermes-sample-meta">{detail_label}</span>'
        f'<p class="hermes-sample-summary">{summary}</p>'
        '<blockquote class="twitter-tweet" data-conversation="none" data-dnt="true">'
        f'<a href="{url}">{account} の投稿をXで見る</a></blockquote>'
        "</div>"
    )


# 論点ID・アイコンはconfigs/planet/bukatsu-chiiki.yamlのissues:と揃える
# （id・並び順はURLアンカー・投票互換のため変更禁止）。件数の多い順。
X_POSTS_ISSUE_ORDER = [
    ("教員の働き方", "kyoin", "🏫"),
    ("制度・移行プロセス", "seido", "📋"),
    ("教育的意義・機会", "kyoiku", "⭐"),
    ("受け皿・指導者", "ukezara", "👤"),
    ("費用・家庭負担", "hiyo", "💴"),
    ("その他", "sonota", "💬"),
    ("地域格差", "kakusa", "🗾"),
]

X_POSTS_CSS = """<style>
#issue-cards .ic{border-top:2px solid #0F1A3D;padding:22px 0 30px;scroll-margin-top:64px}
#issue-cards .ic + .ic{border-top-color:#DCE3EF}
#issue-cards .ic:target .ic-head h3{color:var(--accent)}
#issue-cards .ic-head{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:10px}
#issue-cards .ic-head h3{margin:0;font-size:21px;font-weight:900;line-height:1.4;letter-spacing:.01em}
#issue-cards .ic-head .cnt{margin-left:auto;font-weight:900;font-size:26px;line-height:1;
  font-variant-numeric:tabular-nums;color:#0F1A3D}
#issue-cards .ic-head .cnt small{font-size:13px;font-weight:700;color:var(--muted);margin-left:2px}
#issue-cards .ic-back{display:inline-block;margin-top:16px;font-size:13px;font-weight:700}
</style>"""


def x_post_sample(row: dict[str, Any], label: str) -> str:
    """koshitsu-tenpakaiと同じ形（2026-09-20に編集部要約を外したもの）。ラベルと埋め込みのみ。"""
    url = html.escape(str(row.get("url") or ""), quote=True)
    handle = re.search(r"x\.com/([^/]+)/status/", str(row.get("url") or ""))
    account = f"@{handle.group(1)}" if handle else "この投稿"
    return (
        '<div class="hermes-sample">'
        f'<span class="hermes-sample-meta">{html.escape(label)}</span>'
        '<blockquote class="twitter-tweet" data-conversation="none" data-dnt="true">'
        f'<a href="{url}">{account} の投稿をXで見る</a></blockquote>'
        "</div>"
    )


def x_posts_panel(rows: list[dict[str, Any]]) -> str:
    """「論点ごとのX投稿」節（koshitsu-tenpakaiと同型）。PLANET_SECTIONの外に置く。

    代表投稿はREPRESENTATIVE_POSTSを優先し、収集の入れ替わり等でURLが現行データから
    消えていればconfidence順のフォールバックに戻る（issue_panel()と同じロジック。
    山なみでは使われなくなったissue_panel()自体は呼ばず、ロジックだけをここに複製する）。
    """
    cards = []
    for issue, slug, icon in X_POSTS_ISSUE_ORDER:
        group = [row for row in rows if classification(row).get("main_issue") == issue]
        usable = [row for row in group if classification(row).get("article_usable") and row.get("url")]
        candidates_by_url = {str(row["url"]): row for row in usable}
        candidates = [
            (candidates_by_url[url], label)
            for url, label in REPRESENTATIVE_POSTS.get(issue, [])
            if url in candidates_by_url
        ]
        fallback = sorted(
            [row for row in usable if row not in [candidate[0] for candidate in candidates]],
            key=lambda row: float(classification(row).get("confidence", 0)),
            reverse=True,
        )
        fallback_samples = [
            (row, ISSUE_STANCE_LABEL.get(str(classification(row).get("stance")), "投稿の視点"))
            for row in fallback
        ]
        candidates = (candidates + fallback_samples)[:2]
        samples = "".join(x_post_sample(row, label) for row, label in candidates)
        cards.append(
            f'<article class="ic" id="issue-bukatsu-chiiki-{slug}">'
            f'<div class="ic-head"><h3>{icon} {html.escape(issue)}</h3>'
            f'<span class="cnt">{len(group)}<small>件</small></span></div>'
            f'<div class="hermes-samples">{samples}</div>'
            '<a class="ic-back" href="#planet-block">↑ 地図へ戻る</a>'
            "</article>"
        )
    return (
        '<section class="panel" id="issue-cards">'
        f"{X_POSTS_CSS}"
        '<div class="panel-title"><h2>論点ごとのX投稿</h2></div>'
        "<p>投稿の例は、それぞれの論点でよく見られる言い分を編集部がXから選びました。"
        "地域移行全体への賛否を代表するものではありません。"
        "うまく表示されないときは、リンク先のXで直接確認できます。</p>"
        + "".join(cards) + "</section>"
    )


def summary_panel(rows: list[dict[str, Any]]) -> str:
    stance_counts = Counter(classification(row).get("stance") for row in rows)
    issue_counts = Counter(classification(row).get("main_issue") for row in rows)
    intensity_counts = Counter(classification(row).get("intensity") for row in rows)
    top_issue, top_count = issue_counts.most_common(1)[0]
    top_stance, stance_count = stance_counts.most_common(1)[0]
    return f"""<section class="panel conflict-panel"><div class="panel-title"><h2>投稿の分類結果</h2><span>意見投稿のみ</span></div>
<div class="hermes-summary-grid">
<article class="hermes-summary-card"><div class="axis-kicker">最多スタンス</div><h3>{html.escape(STANCE_SHORT.get(str(top_stance), str(top_stance)))}</h3><div class="axis-count">{stance_count}</div><p>支持・条件付き・慎重反対を分けて集計しています。</p></article>
<article class="hermes-summary-card"><div class="axis-kicker">最多論点</div><h3>{html.escape(str(top_issue))}</h3><div class="axis-count">{top_count}</div><p>投稿の主眼となる論点を1つに分類しています。</p></article>
<article class="hermes-summary-card"><div class="axis-kicker">感情強度 high</div><h3>強い訴え・批判</h3><div class="axis-count">{intensity_counts["high"]}</div><p>表現の強さであり、意見の正しさを示す値ではありません。</p></article>
</div></section>"""


def details_panel(all_rows: list[dict[str, Any]], opinion_rows: list[dict[str, Any]]) -> str:
    relevant_count = sum(bool(classification(row).get("is_relevant")) for row in all_rows)
    issue_counts = Counter(classification(row).get("main_issue") for row in opinion_rows)
    stance_counts = Counter(classification(row).get("stance") for row in opinion_rows)
    issue_table = "".join(f"<tr><th>{html.escape(issue)}</th><td>{issue_counts[issue]}</td></tr>" for issue in ISSUES)
    stance_table = "".join(f"<tr><th>{html.escape(stance)}</th><td>{stance_counts[stance]}</td></tr>" for stance in STANCES)
    return f"""<section class="panel details-panel" id="detail-data"><div class="panel-title"><h2>詳細データ</h2><span>必要な人向けに折りたたみ</span></div>
<details><summary>収集・分類件数</summary><div class="table-wrap"><table><tbody>
<tr><th>累計収集投稿</th><td>{len(all_rows)}</td></tr><tr><th>テーマ関連投稿</th><td>{relevant_count}</td></tr><tr><th>意見投稿</th><td>{len(opinion_rows)}</td></tr>
</tbody></table></div></details>
<details><summary>論点別件数</summary><div class="table-wrap"><table><tbody>{issue_table}</tbody></table></div></details>
<details><summary>スタンス別件数</summary><div class="table-wrap"><table><tbody>{stance_table}</tbody></table></div></details>
<details><summary>注意</summary><ul><li>Yahooリアルタイム検索で取得したSNS投稿サンプルであり、世論調査ではありません。</li><li>Hermesが論点・スタンス・強度を自動分類しました。</li></ul></details>
</section>"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--classified", type=Path, required=True)
    parser.add_argument("--current-date", required=True)
    parser.add_argument("--html", type=Path, required=True)
    parser.add_argument("--output-html", type=Path)
    args = parser.parse_args()

    all_rows = load(args.classified)
    all_opinions = opinions(all_rows)
    if not all_opinions:
        raise ValueError("意見の投稿が1件もありません")

    issue_counts = Counter(classification(row).get("main_issue") for row in all_opinions)
    top_issue, top_count = issue_counts.most_common(1)[0]
    relevant_count = sum(bool(classification(row).get("is_relevant")) for row in all_rows)

    page = args.html.read_text(encoding="utf-8")
    # 潮目カードのCSSの塊（TIDE_CARD_*）は、潮目を外した2026-10-06に、Hermes表示用のCSS（HERMES_CARD_*）へ置き換えた。
    # 古い形のページでは、同じ場所で入れ替わる。
    for pattern in (r"/\* HERMES_CARD_START \*/.*?/\* HERMES_CARD_END \*/", r"/\* TIDE_CARD_START \*/.*?/\* TIDE_CARD_END \*/"):
        if re.search(pattern, page, flags=re.DOTALL):
            page = re.sub(pattern, lambda _m: HERMES_CSS.strip(), page, count=1, flags=re.DOTALL)
            break
    else:
        page = replace_once(page, r"</style>", HERMES_CSS + "\n</style>", "hermes CSS")
    stance_counts = Counter(classification(row).get("stance") for row in all_opinions)
    if top_issue == "教員の働き方":
        focus_title = "教員の負担を減らしながら、活動を誰が支えるのか"
        focus_detail = "教員の働き方を論点とする投稿が最も多く、学校だけに担わせない必要性と、地域で費用・指導者・責任をどう確保するかが同時に問われています。"
    else:
        focus_title = f"「{html.escape(str(top_issue))}」を、どう支えるのか"
        focus_detail = "この論点を中心に、地域展開の進め方と必要な条件が議論されています。"
    summary = (
        '<div class="thirty-summary" aria-label="議論の中心">'
        '<header class="thirty-summary-title"><h2>議論の中心</h2></header><ul>'
        f'<li class="conclusion-focus"><span class="conclusion-count"><b>{top_count}</b>件</span>'
        f'<strong>{focus_title}</strong><span class="conclusion-detail">{focus_detail}</span></li></ul></div>'
    )
    page = replace_once(page, r'<div class="thirty-summary".*?</div>', summary, "30 second summary", flags=re.DOTALL)

    # 山なみ（課題54）へ差し替えたページは、SNS反応マップ（アリーナ）・論点別内訳の
    # 2区間を #planet-block が引き継ぎ、区間ごと外している。ここを無条件で書こうと
    # すると対象が見つからずエラーで止まる（定例更新のたびに失敗し、部活動の収集だけが
    # 止まる）。PLANET_SECTION_START の有無で区別し、山なみ側ではこの2区間を書かない。
    #
    # 外枠（update-dashboard）は「意見の推移」の節の入れ物で、PLANET_SECTIONの外
    # （山を押しても書き換わらない区間）に置く。中身（TREND_CARD_*）は更新のたびに adapter が貼り直すので、
    # ここでは触らない。2026-10-06までは、この枠に「世論の潮目」カードを書いていた（外した）。
    planet_mode = "<!-- PLANET_SECTION_START -->" in page
    frame = '<section class="update-dashboard"><!-- TREND_CARD_START --><!-- TREND_CARD_END --></section>'
    if re.search(r'<section class="update-dashboard"[^>]*>\s*<!-- TREND_CARD_START -->', page):
        pass  # 通常の更新。すでに推移の枠がある
    elif '<section class="update-dashboard"' in page:
        # 古い形（潮目カード入り）。推移の枠へ直す。
        page = replace_once(
            page,
            r'<section class="update-dashboard".*?<!-- TIDE_CARD_END --></section>',
            frame,
            "update dashboard (潮目カード入りの古い形)",
            flags=re.DOTALL,
        )
    elif planet_mode:
        # 初回のみ。以後はすぐ上の分岐を通る。
        page = replace_once(
            page,
            r"<!-- PLANET_SECTION_END -->",
            f"<!-- PLANET_SECTION_END -->\n\n{frame}",
            "planet trend dashboard (initial insertion)",
        )
    else:
        page = re.sub(r"\s*<!-- TIDE_CARD_START -->.*?<!-- TIDE_CARD_END -->\s*", "\n", page, count=1, flags=re.DOTALL)
        page = replace_once(page, r'<section class="stats">.*?</section>', frame, "stats dashboard", flags=re.DOTALL)

    if planet_mode:
        # 「論点ごとのX投稿」（koshitsu-tenpakaiと同型）。山なみでは2026-09-20まで
        # issue_panel()自体が丸ごとスキップされ、対応する入れ物が無かった。
        # BUKATSU_AUDIT（一次資料照合）の直後、無ければPLANET_SECTION_END直後に置く。
        x_posts = x_posts_panel(all_opinions)
        if 'id="issue-cards"' in page:
            page = replace_once(
                page,
                r'<section class="panel" id="issue-cards">.*?</section>',
                x_posts,
                "x posts panel",
                flags=re.DOTALL,
            )
        else:
            anchor = "<!-- BUKATSU_AUDIT_END -->" if "<!-- BUKATSU_AUDIT_END -->" in page else "<!-- PLANET_SECTION_END -->"
            page = replace_once(
                page,
                re.escape(anchor),
                f"{anchor}\n\n{x_posts}",
                "x posts panel (initial insertion)",
            )

    if not planet_mode:
        page = replace_once(
            page,
            r'<div class="panel-title"><h2>(?:論点アリーナ|SNS反応マップ)</h2><span>.*?</span></div>',
            f'<div class="panel-title"><h2>SNS反応マップ</h2><span>意見{len(all_opinions)}件 | セクター=論点 / 中心に近いほど冷静 / 色=立場</span></div>',
            "arena heading",
        )
        page = replace_once(page, r"const SM_RAW = \[.*?\n\];", sm_raw(all_opinions), "SM_RAW", flags=re.DOTALL)
        issue_js = "const ISSUES=[\n" + ",\n".join(
            f"    {{k:{js(issue)},n:{issue_counts[issue]}}}" for issue in ISSUES
        ) + "\n  ];"
        arena_pos = page.index("<h2>SNS反応マップ</h2>")
        before, after = page[:arena_pos], page[arena_pos:]
        after = replace_once(after, r"const ISSUES=\[.*?\n  \];", issue_js, "arena issues", flags=re.DOTALL)
        page = before + after

        page = replace_once(
            page,
            r'<section class="panel conflict-panel"><div class="panel-title"><h2>7つの論点とXの声</h2>.*?(?=<section class="panel explainer-section")',
            issue_panel(all_opinions),
            "issue panel",
            flags=re.DOTALL,
        )
        page = replace_once(
            page,
            r'<section class="panel conflict-panel"><div class="panel-title"><h2>(?:スタンス集計|Hermes分類サマリー|投稿の分類結果)</h2>.*?(?=<section class="panel" id="related-topics">)',
            summary_panel(all_opinions),
            "summary panel",
            flags=re.DOTALL,
        )
    page = replace_once(
        page,
        r'<section class="panel details-panel" id="detail-data">.*?</section>(?=\s*</main>)',
        details_panel(all_rows, all_opinions),
        "details panel",
        flags=re.DOTALL,
    )
    page = page.replace(
        "<strong>データの集め方:</strong> Yahooリアルタイム検索からSNS投稿を取得し、AIが自動分類しました。",
        f"<strong>データの集め方:</strong> Yahooリアルタイム検索からSNS投稿を取得し、Hermesが論点・スタンス・強度を分類しました。最終更新: {args.current_date}。",
    )
    page = re.sub(
        r"(<strong>データの集め方:</strong> Yahooリアルタイム検索からSNS投稿を取得し、Hermesが論点・スタンス・強度を分類しました。最終更新: )\d{4}-\d{2}-\d{2}(。)",
        rf"\g<1>{args.current_date}\g<2>",
        page,
        count=1,
    )
    page = page.replace(
        "function colorOf(p){return p.x>=0.5?'#059669':(p.x<=-0.5?'#dc2626':'#64748b');}",
        "function colorOf(p){return p.x>=1?'#059669':(p.x>0?'#d97706':(p.x<=-0.5?'#dc2626':'#64748b'));}",
    )
    page = page.replace(
        '<span><i style="background:#059669"></i>移行支持</span>\n'
        '    <span><i style="background:#dc2626"></i>移行反対</span>\n'
        '    <span><i style="background:#64748b"></i>中立</span>',
        '<span><i style="background:#059669"></i>移行支持</span>\n'
        '    <span><i style="background:#d97706"></i>条件付き</span>\n'
        '    <span><i style="background:#dc2626"></i>慎重・反対</span>\n'
        '    <span><i style="background:#64748b"></i>中立</span>',
    )
    page = page.replace("Powered by Yahooリアルタイム検索 + AI分類", "公開投稿を収集・分類して整理")
    page = page.replace("Powered by Yahooリアルタイム検索 + Hermes分類", "公開投稿を収集・分類して整理")

    # insight-stats の件数・パーセントを正典の現在値で更新する
    opinion_total = len(all_opinions)
    top_stance = max(stance_counts, key=stance_counts.get) if stance_counts else "移行支持"
    top_stance_count = stance_counts.get(top_stance, 0)
    top_stance_pct = round(top_stance_count * 100 / opinion_total) if opinion_total else 0
    cond_count = stance_counts.get("条件付き・改善要求", 0)
    cond_pct = round(cond_count * 100 / opinion_total) if opinion_total else 0
    kyoin_count = issue_counts.get("教員の働き方", 0)
    kyoin_pct = round(kyoin_count * 100 / opinion_total) if opinion_total else 0
    # カード1: 意見件数・関連件数
    page = re.sub(
        r'(<strong class="insight-value">)\d+(<small>件</small></strong>\s*<p class="insight-note">関連)\d+(件から)',
        rf'\g<1>{opinion_total}\g<2>{relevant_count}\g<3>',
        page, count=1,
    )
    # カード2: 最も多い立場（移行支持 XX%）の値と件数とメーター
    page = re.sub(
        r'(<strong class="insight-value">移行支持 )\d+(%</strong>\s*<p class="insight-note">)\d+(件)',
        rf'\g<1>{top_stance_pct}\g<2>{top_stance_count}\g<3>',
        page, count=1,
    )
    page = re.sub(
        r'(data-tone="debate"[^>]*>.*?<i style="width:)\d+(%">)',
        rf'\g<1>{top_stance_pct}\g<2>',
        page, count=1, flags=re.DOTALL,
    )
    # カード3: 教員の働き方の件数とメーター
    page = re.sub(
        r'(<strong class="insight-value">教員の働き方 )\d+(<small>件</small></strong>)',
        rf'\g<1>{kyoin_count}\g<2>',
        page, count=1,
    )
    page = re.sub(
        r'(data-tone="topic"[^>]*>.*?<i style="width:)\d+(%">)',
        rf'\g<1>{kyoin_pct}\g<2>',
        page, count=1, flags=re.DOTALL,
    )
    # カード4: 条件付き・第三案の件数とメーター
    page = re.sub(
        r'(<strong class="insight-value">改善条件あり )\d+(%</strong>\s*<p class="insight-note">)\d+(件)',
        rf'\g<1>{cond_pct}\g<2>{cond_count}\g<3>',
        page, count=1,
    )
    page = re.sub(
        r'(data-tone="option"[^>]*>.*?<i style="width:)\d+(%">)',
        rf'\g<1>{cond_pct}\g<2>',
        page, count=1, flags=re.DOTALL,
    )

    output = args.output_html or args.html
    output.write_text(page, encoding="utf-8")
    print(json.dumps({
        "collected": len(all_rows),
        "relevant": relevant_count,
        "opinions": len(all_opinions),
        "top_issue": top_issue,
        "top_issue_count": top_count,
        "output": str(output),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
