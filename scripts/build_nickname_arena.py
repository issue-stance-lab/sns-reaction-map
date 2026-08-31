#!/usr/bin/env python3
"""学校あだ名禁止ページを、正典の「意見」投稿だけから再生成する。

生成対象は docs/school-nickname-ban-arena-data.js と、ページ内で件数を出している
すべての場所（リード文・注目ポイント4枚・論点カードの内訳文・投票STEP1の件数・
論点ナビ・論点ブロック6つ・詳細データ表）。件数をHTMLへ手書きしない。

    python3 scripts/build_nickname_arena.py
    python3 scripts/build_nickname_arena.py --check

前身は scripts/upgrade_nickname_arena.js（archive へ移動）。あれは一度きりの移行用で、
実行のたびに空行が1行増え、SEO meta を374件時代の固定文へ巻き戻した。ここでは
①境界を探して貼る方式をやめアンカーの1対1置換にする ②SEO meta と調査条件は
書かない（seo/apply_theme_trust.py と seo/generate_seo_assets.py の担当）。
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from .issue_card_counts import IssueCountError, count_by_issue_from_public_json, span_html
    from .sync_portal_stats import ROOT, THEMES_YAML, parse_themes_yaml
    from .verify_sample_periods import expected_period, summarize
    from .x_embed import embed_html, period_label
except ImportError:
    from issue_card_counts import (  # type: ignore[no-redef]
        IssueCountError,
        count_by_issue_from_public_json,
        span_html,
    )
    from sync_portal_stats import ROOT, THEMES_YAML, parse_themes_yaml  # type: ignore[no-redef]
    from verify_sample_periods import expected_period, summarize  # type: ignore[no-redef]
    from x_embed import embed_html, period_label  # type: ignore[no-redef]

THEME = "school-nickname-ban"
ARENA_DATA = Path("docs/school-nickname-ban-arena-data.js")
PUBLIC_THEME = ROOT / "data" / "public" / "themes" / f"{THEME}.json"

# 立場（正典のラベル）→ ページ側の色分けキー。
STANCE_KEY = {
    "禁止支持": "support",
    "一律禁止に反対": "oppose",
    "条件付き・個別対応": "conditional",
    "中立・情報": "neutral",
}
# temp-bar の並び順。CSS の .temp-seg 宣言順と揃える。
STANCE_ORDER = ("oppose", "conditional", "neutral", "support")
STANCE_COLORS = {
    "oppose": "#dc2626",
    "conditional": "#d97706",
    "neutral": "#94a3b8",
    "support": "#059669",
}
# 注目ポイント「最も多い立場」に出す表示名。
STANCE_DISPLAY = {
    "oppose": "一律禁止に反対",
    "support": "禁止支持",
    "conditional": "柔軟対応",
    "neutral": "中立・体験",
}
# 論点カードの内訳文に出す立場名。注目ポイントより短く書く。
BREAKDOWN_LABEL = {
    "support": "禁止支持",
    "conditional": "条件付き",
    "neutral": "中立・体験",
    "oppose": "反対",
}
INTENSITY_SCALE = {"low": 0.3, "medium": 0.64, "high": 0.94}

IMAGE_DIR = "images/topics/school-nickname-ban"

# 論点の定義。並び順は configs/school-nickname-ban-reaction-map.json の
# issue_counts.cards と同じで、アリーナのセクターと投票の choiceIdx に対応する。
# **入れ替えないこと**（既存票の意味がずれる）。
ISSUE_DEFS: tuple[dict[str, Any], ...] = (
    {
        "key": "safety",
        "main_issue": "いじめ・心理的安全",
        "title": "いじめ・心理的安全",
        "short": "心理的安全",
        "icon": "🛡️",
        "slug": "ijime",
        "image": f"{IMAGE_DIR}/school-nickname-ban-infographic-wide-safety.webp",
        "image_alt": "あだ名禁止の論点1、いじめ・心理的安全を解説するインフォグラフィック",
        "explainer_title": "呼び方のルールで、傷つく子を守れるか",
        "explainer_tail": "被害予防と、対話・教育をどう組み合わせるかが焦点です。",
        "explainer_lead": "breakdown",
        "explainer_left": "支持：傷つく呼び方を予防",
        "explainer_right": "慎重：対話・教育も必要",
        "insight_note": "いじめ予防と「禁止だけでは足りない」が交差",
        "description": "嫌なあだ名やからかいを予防し、傷つく子を出さないために学校が介入すべきか。",
        "support": "悪意の有無にかかわらず傷つく呼び方を予防し、安心を優先する。",
        "oppose": "禁止だけでなく、相手の気持ちを聞く教育や個別対応も必要。",
        "side_support_label": "予防ルールで安全を優先",
        "side_oppose_label": "対話・個別対応も組み合わせる",
        "sample_stances": ("禁止支持", "一律禁止に反対",),
        "bar_title": "傷つく呼び方への学校介入をどう見るか",
        "stance_labels": {
            "oppose": ("個別対応を重視", "一律規制より対話・個別対応を重視"),
            "conditional": ("条件付き介入", "本人の状況に応じた条件付き介入"),
            "neutral": ("被害・実態を共有", "傷ついた経験や学校現場の実態を共有"),
            "support": ("予防ルールを重視", "予防ルールで心理的安全を優先"),
        },
    },
    {
        "key": "effect",
        "main_issue": "一律禁止の実効性",
        "title": "一律禁止の実効性",
        "short": "実効性",
        "icon": "🎯",
        "slug": "kinshi",
        "image": f"{IMAGE_DIR}/school-nickname-ban-infographic-wide-effectiveness.webp",
        "image_alt": "あだ名禁止の論点2、一律禁止の実効性を解説するインフォグラフィック",
        "explainer_title": "禁止すれば、いじめは減るのか",
        "explainer_tail": "入口を減らす予防効果と、問題が別の形で残る懸念を比べます。",
        "explainer_lead": "oppose",
        "explainer_left": "予防：からかいの入口を減らす",
        "explainer_right": "批判：いじめの本質は残る",
        "insight_note": "一律の禁止で本当に減るのかが問われた",
        "description": "呼び方を一律に禁止することで、いじめの原因や関係性まで変えられるのか。",
        "support": "からかいの入口を減らす予防策として、一定の効果が期待できる。",
        "oppose": "呼称だけを変えても、いじめの本質や別の攻撃手段は残る。",
        "side_support_label": "からかいの入口を減らす",
        "side_oppose_label": "本質的な関係改善を優先",
        "sample_stances": ("条件付き・個別対応", "一律禁止に反対",),
        "bar_title": "呼び方の禁止はいじめ予防に効くか",
        "stance_labels": {
            "oppose": ("本質は変わらない", "禁止だけではいじめの本質は変わらない"),
            "conditional": ("運用次第で効果", "対象や運用を絞れば予防効果がある"),
            "neutral": ("運用実態を共有", "学校での禁止ルールや運用実態を共有"),
            "support": ("入口を減らす", "からかいの入口を減らす予防策として評価"),
        },
    },
    {
        "key": "culture",
        "main_issue": "親しさ・呼称文化",
        "title": "親しさ・呼称文化",
        "short": "呼称文化",
        "icon": "🤝",
        "slug": "shitashisa",
        "image": f"{IMAGE_DIR}/school-nickname-ban-infographic-wide-culture.webp",
        "image_alt": "あだ名禁止の論点3、親しさと呼称文化を解説するインフォグラフィック",
        "explainer_title": "あだ名は親しさか、それとも負担か",
        "explainer_tail": "愛称が生む親しさと、受け手が感じる痛みの両方を扱います。",
        "explainer_lead": "oppose",
        "explainer_left": "文化：親しさ・個性を尊重",
        "explainer_right": "受け手：嫌なら止める",
        "insight_note": "親しさの表現と受け手の痛みが正面からぶつかった",
        "description": "あだ名を親しさや個性の表現と見るか、傷つける可能性のある呼び方と見るか。",
        "support": "本人が安心できる呼び方を優先し、学校が一定の線を引くべき。",
        "oppose": "親しい愛称まで一律に禁じると、自然な関係づくりを損なう。",
        "side_support_label": "受け手の安心を優先",
        "side_oppose_label": "親しさと個性を尊重",
        "sample_stances": ("禁止支持", "一律禁止に反対",),
        "bar_title": "あだ名を親しさと負担のどちらから見るか",
        "stance_labels": {
            "oppose": ("親しさを守る", "愛称や親しさを一律ルールで奪わない"),
            "conditional": ("望む愛称だけ", "本人が望む愛称だけ柔軟に認める"),
            "neutral": ("呼称文化を共有", "学校や世代による呼称文化の違いを共有"),
            "support": ("傷つく呼称を止める", "傷つく可能性のある呼び方を学校が止める"),
        },
    },
    {
        "key": "experience",
        "main_issue": "学校運用・現場体験",
        "title": "学校運用・現場体験",
        "short": "現場体験",
        "icon": "🏫",
        "slug": "unyo",
        "image": f"{IMAGE_DIR}/school-nickname-ban-infographic-wide-field.webp",
        "image_alt": "あだ名禁止の論点4、学校運用と現場体験を解説するインフォグラフィック",
        "explainer_title": "現場では、ルールがどう受け止められるか",
        "explainer_tail": "学校・世代による差と、運用目的を説明できるかを見ます。",
        "explainer_lead": "neutral",
        "explainer_left": "実態：学校・世代で違う",
        "explainer_right": "運用：目的の説明が必要",
        "insight_note": "学校ごとの運用差と、実際に経験した呼ばれ方が語られた",
        "description": "学校ごとの運用差や、自分・子どもが実際に経験した呼ばれ方から考える論点。",
        "support": "嫌なあだ名がなくなり、安心して過ごせたという経験がある。",
        "oppose": "さん付けの強制に距離や窮屈さを感じたという経験がある。",
        "side_support_label": "安心につながった体験",
        "side_oppose_label": "窮屈さを感じた体験",
        "sample_stances": ("中立・情報", "禁止支持",),
        "bar_title": "学校の呼称ルールを現場体験からどう評価するか",
        "stance_labels": {
            "oppose": ("統一運用は窮屈", "さん付けなどの統一運用に窮屈さを感じる"),
            "conditional": ("現場ごとに調整", "学級や子どもの状況に応じた調整を求める"),
            "neutral": ("現場体験を共有", "学校・家庭・世代ごとの体験や実態を共有"),
            "support": ("安心につながった", "共通ルールで安心して過ごせた経験を共有"),
        },
    },
    {
        "key": "gender",
        "main_issue": "さん付け・ジェンダー配慮",
        "title": "さん付け・ジェンダー配慮",
        "short": "さん付け",
        "icon": "⚖️",
        "slug": "sanzuke",
        "image": f"{IMAGE_DIR}/school-nickname-ban-infographic-wide-gender.webp",
        "image_alt": "あだ名禁止の論点5、さん付けとジェンダー配慮を解説するインフォグラフィック",
        "explainer_title": "「名字＋さん」統一は、対等さにつながるか",
        "explainer_tail": "性別で呼称を分けない配慮と、形式だけの統一への疑問を整理します。",
        "explainer_lead": "oppose",
        "explainer_left": "配慮：性別で呼称を分けない",
        "explainer_right": "懸念：形式だけでは変わらない",
        "insight_note": "呼称の統一が対等さにつながるかが問われた",
        "description": "「くん・ちゃん」の性差をなくし、名字＋さんへ統一する指導をどう見るか。",
        "support": "性別や上下関係で呼び方を分けず、対等な敬称へ統一する。",
        "oppose": "さん付けの強制は形式的で、親しさや本人の希望を置き去りにする。",
        "side_support_label": "性別で呼称を分けない",
        "side_oppose_label": "形式より本人希望を重視",
        "sample_stances": ("一律禁止に反対", "中立・情報",),
        "bar_title": "「名字＋さん」統一は対等さにつながるか",
        "stance_labels": {
            "oppose": ("形式的な統一に疑問", "さん付けの形式的な統一では対等さは生まれない"),
            "conditional": ("本人希望も反映", "性別配慮と本人が望む呼び方を両立する"),
            "neutral": ("呼称実態を共有", "学校での「くん・ちゃん・さん」の実態を共有"),
            "support": ("性別で分けない", "性別で呼称を分けず対等な敬称に統一する"),
        },
    },
    {
        "key": "choice",
        "main_issue": "本人意思・柔軟運用",
        "title": "本人意思と柔軟運用",
        "short": "本人意思",
        "icon": "🗣️",
        "slug": "honnin",
        "image": f"{IMAGE_DIR}/school-nickname-ban-infographic-wide-choice.webp",
        "image_alt": "あだ名禁止の論点6、本人意思と柔軟運用を解説するインフォグラフィック",
        "explainer_title": "呼ばれる本人の意思を、中心に置けるか",
        "explainer_tail": "望む愛称は認めつつ、嫌と言いにくい子をどう守るかが焦点です。",
        "explainer_lead": "conditional",
        "explainer_left": "本人同意：望む愛称は認める",
        "explainer_right": "支援：嫌と言いにくい子を守る",
        "insight_note": "呼ばれる本人の意思をどう扱うかに集まった",
        "description": "禁止か自由かではなく、呼ばれる本人の意思をルールの中心に置けるか。",
        "support": "嫌だと言いにくい子を守るには、共通ルールを出発点にすべき。",
        "oppose": "本人が望む愛称は認め、嫌な呼び方だけを止めればよい。",
        "side_support_label": "共通ルールから守る",
        "side_oppose_label": "本人意思で柔軟に",
        "sample_stances": ("条件付き・個別対応",),
        "bar_title": "呼び方のルールを誰の意思で決めるか",
        "stance_labels": {
            "oppose": ("一律ルールに委ねない", "学校の一律ルールより個人間の関係を尊重"),
            "conditional": ("本人意思で柔軟に", "望む愛称は認め、嫌な呼び方だけを止める"),
            "neutral": ("本人の声を共有", "呼ばれる側の希望や言いにくさを共有"),
            "support": ("共通ルールから守る", "嫌と言いにくい子を共通ルールから守る"),
        },
    },
)
ISSUE_BY_MAIN = {issue["main_issue"]: issue for issue in ISSUE_DEFS}


def percent(part: int, whole: int) -> int:
    """四捨五入した百分率。

    Python の round は 0.5 を偶数へ丸めるので、12.5% が 12% になる。ページには
    ずっと 13% と出ていたため、そのままでは既存の公開ページと差分が出る。
    """
    return int(part / whole * 100 + 0.5)


def classification(record: dict[str, Any]) -> dict[str, Any]:
    nested = record.get("classification")
    if not isinstance(nested, dict):
        raise IssueCountError("classification を持たないレコードがあります")
    return nested


def load_opinions(input_path: Path | None = None) -> tuple[list[dict[str, Any]], str, list[dict[str, Any]]]:
    """正典から、カードに載る6論点の意見投稿だけを取り出す。

    `is_opinion` が欠落したレコードは黙って落とさず失敗させる。付いていないと
    論点カードの母数（basis: opinion）から丸ごと消える（自転車で実際に消えた）。
    """
    themes = parse_themes_yaml(THEMES_YAML)
    sample_file = str(themes[THEME].get("sample_file") or "")
    if not sample_file or "synthetic" in sample_file:
        raise IssueCountError(f"{THEME}: 正典 sample_file が不正です: {sample_file}")
    source = input_path or ROOT / sample_file
    records = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise IssueCountError(f"{THEME}: 正典が空、またはJSON配列ではありません")

    opinions: list[dict[str, Any]] = []
    for number, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise IssueCountError(f"{number}件目がJSONオブジェクトではありません")
        c = classification(record)
        for field in ("is_opinion", "is_relevant"):
            if field not in c or not isinstance(c[field], bool):
                raise IssueCountError(
                    f"{number}件目の classification.{field} が欠落またはboolではありません"
                )
        if not (c["is_opinion"] and c["is_relevant"]):
            continue
        stance = c.get("stance")
        intensity = c.get("intensity")
        if stance not in STANCE_KEY:
            raise IssueCountError(f"未知の stance: {stance}")
        if intensity not in INTENSITY_SCALE:
            raise IssueCountError(f"未知の intensity: {intensity}")
        if c.get("main_issue") not in ISSUE_BY_MAIN:
            continue  # 「その他」はカードに載らない
        opinions.append(record)
    if not opinions:
        raise IssueCountError("意見と判定されたレコードがありません")
    return opinions, str(source), records


def stance_of(record: dict[str, Any]) -> str:
    return STANCE_KEY[str(classification(record)["stance"])]


def issue_counts(rows: list[dict[str, Any]]) -> Counter[str]:
    return Counter(str(classification(row)["main_issue"]) for row in rows)


def stance_counts(rows: list[dict[str, Any]], issue: dict[str, Any] | None = None) -> Counter[str]:
    return Counter(
        stance_of(row)
        for row in rows
        if issue is None or classification(row)["main_issue"] == issue["main_issue"]
    )


def build_arena_data(rows: list[dict[str, Any]]) -> str:
    """アリーナの点。issue はセクター、intensity は中心からの距離。"""
    keys = [issue["key"] for issue in ISSUE_DEFS]
    points = []
    for index, row in enumerate(rows, start=1):
        c = classification(row)
        intensity = INTENSITY_SCALE[str(c["intensity"])] + (float(c["confidence"]) - 0.75) * 0.18
        points.append(
            {
                "issue": keys[keys.index(ISSUE_BY_MAIN[str(c["main_issue"])]["key"])],
                "stance": stance_of(row),
                "intensity": round(max(0.18, min(1.0, intensity)), 4),
                "summary": str(c.get("summary") or ""),
                "url": str(row.get("url") or ""),
                "seed": index,
            }
        )
    body = json.dumps(points, ensure_ascii=False, separators=(",", ":"))
    return f"window.NICKNAME_ARENA_DATA={body};\n"


def sample_period(records: list[dict[str, Any]]) -> str:
    """調査条件に出す収集日の範囲。

    THEMES.yaml の `sample_period` と同じ計算を使う。verify_theme_page.py は
    台帳の値とページの表記を突き合わせるので、別々に数えると必ずいつかズレる。
    昇格処理は adapter の後に台帳を書き換えるため、台帳から読むと1回分古くなる。
    """
    return period_label(expected_period(summarize(records)))


def build_research_conditions(collected: int, period: str) -> str:
    """調査条件（取得元・件数・期間）。

    確認表示は <span class="review-note"> で囲む（apply_review_note.py が中身を
    書き分け、verify_number_provenance.py がこの囲みだけを検査から外す）。
    落とすと再生成で検査が落ちる。
    """
    return (
        '<p style="max-width:1000px;margin:0 auto;">'
        '<strong style="color:var(--ink);">このマップの元データ:</strong> '
        f"Yahooリアルタイム検索で取得した公開投稿 {collected}件<br>\n"
        f"  （取得期間: {period}／"
        '<span class="review-note">AI分類。代表投稿は編集部が選定</span>）<br>\n'
        "  <strong>社会全体の世論調査ではありません。</strong></p>"
    )


def build_lead(rows: list[dict[str, Any]]) -> str:
    return (
        f'<p class="lead">収集したSNS投稿のうち、分析対象となった意見{len(rows)}件をAIが'
        f"{len(ISSUE_DEFS)}つの論点に整理しました。世論調査ではなく、SNS反応サンプルの論点比較です。</p>"
    )


def build_stats(rows: list[dict[str, Any]], collected: int) -> str:
    """注目ポイント4枚。文言の骨は固定で、件数と割合だけ正典から入れる。"""
    total = len(rows)
    stances = stance_counts(rows)
    issues = issue_counts(rows)
    top_stance = max(STANCE_ORDER, key=lambda key: (stances[key], -STANCE_ORDER.index(key)))
    top_share = percent(stances[top_stance], total)
    others = " ".join(
        f"{STANCE_DISPLAY[key]}{stances[key]}件、"
        for key in ("support", "conditional", "oppose")
        if key != top_stance
    ).replace("件、 ", "件、").rstrip("、")
    top_issue = max(ISSUE_DEFS, key=lambda issue: issues[issue["main_issue"]])
    issue_share = percent(issues[top_issue["main_issue"]], total)
    neutral_share = percent(stances["neutral"], total)
    return "\n".join(
        [
            '<section class="stats insight-stats" aria-label="このテーマの4つの注目ポイント">',
            '  <article class="stat insight-stat">',
            '    <div class="insight-head"><span class="insight-icon" aria-hidden="true">🗣️</span><span class="insight-label">分析対象の意見</span></div>',
            f'    <strong class="insight-value">{total}<small>件</small></strong>',
            '    <p class="insight-note">関連性と意見性の両方が認められた投稿</p>',
            '    <div class="insight-meter" aria-hidden="true"><i style="width:100%"></i></div>',
            "  </article>",
            '  <article class="stat insight-stat" data-tone="debate">',
            '    <div class="insight-head"><span class="insight-icon" aria-hidden="true">⚖️</span><span class="insight-label">最も多い立場</span></div>',
            f'    <strong class="insight-value">{html.escape(STANCE_DISPLAY[top_stance])} {top_share}%</strong>',
            f'    <p class="insight-note">{stances[top_stance]}件。{html.escape(others)}</p>',
            f'    <div class="insight-meter" aria-hidden="true"><i style="width:{top_share}%"></i></div>',
            "  </article>",
            '  <article class="stat insight-stat" data-tone="topic">',
            f'    <div class="insight-head"><span class="insight-icon" aria-hidden="true">{top_issue["icon"]}</span><span class="insight-label">最も話された論点</span></div>',
            f'    <strong class="insight-value">{html.escape(str(top_issue["short"]))} {issues[top_issue["main_issue"]]}<small>件</small></strong>',
            f'    <p class="insight-note">{html.escape(str(top_issue["insight_note"]))}</p>',
            f'    <div class="insight-meter" aria-hidden="true"><i style="width:{issue_share}%"></i></div>',
            "  </article>",
            '  <article class="stat insight-stat" data-tone="voice">',
            '    <div class="insight-head"><span class="insight-icon" aria-hidden="true">🏫</span><span class="insight-label">当事者・現場の声</span></div>',
            f'    <strong class="insight-value">体験・中立 {stances["neutral"]}<small>件</small></strong>',
            f'    <p class="insight-note">学校生活や呼ばれ方の経験から語る声が約{percent(stances["neutral"], total * 10)}割</p>',
            f'    <div class="insight-meter" aria-hidden="true"><i style="width:{neutral_share}%"></i></div>',
            "  </article>",
            "</section>",
        ]
    )


def explainer_desc(issue: dict[str, Any], rows: list[dict[str, Any]], rank: int) -> str:
    """論点カードの内訳文。先頭の1文だけを件数から作り、残りは固定文。"""
    stances = stance_counts(rows, issue)
    total = sum(stances.values())
    mode = str(issue["explainer_lead"])
    if mode == "breakdown":
        parts = "、".join(
            f"{BREAKDOWN_LABEL[key]}{stances[key]}件"
            for key in ("support", "conditional", "neutral", "oppose")
            if stances[key]
        )
        head = f"{len(ISSUE_DEFS)}論点中で最多" if rank == 1 else f"{len(ISSUE_DEFS)}論点中{rank}番目"
        lead = f"{head}。{parts}。"
    elif mode == "oppose":
        lead = f"うち一律禁止への反対が{stances['oppose']}件。"
    elif mode == "neutral":
        lead = f"うち{stances['neutral']}件が中立的な体験共有。"
    else:
        lead = (
            "すべてが条件付き・個別対応。"
            if total and stances["conditional"] == total
            else f"うち条件付き・個別対応が{stances['conditional']}件。"
        )
    return lead + str(issue["explainer_tail"])


def build_explainer_cards(rows: list[dict[str, Any]]) -> str:
    counts = issue_counts(rows)
    ranking = sorted(ISSUE_DEFS, key=lambda issue: -counts[issue["main_issue"]])
    cards = []
    for index, issue in enumerate(ISSUE_DEFS, start=1):
        rank = ranking.index(issue) + 1
        title = f'{issue["icon"]} {issue["title"]} — 「{issue["explainer_title"]}」'
        span = span_html(THEME, str(issue["slug"]), counts[issue["main_issue"]])
        cards.append(
            f'\n  <article class="explainer-card" data-img="{issue["image"]}" data-alt="{issue["image_alt"]}"'
            f' tabindex="0" role="button" aria-label="論点{index}の図解を拡大表示">\n'
            '    <div class="explainer-card-label">\n'
            f'      <span class="explainer-num">論点{index}</span>\n'
            "      <div>\n"
            f'        <p class="explainer-card-title">{title}{span}</p>\n'
            f'        <p class="explainer-card-desc">{explainer_desc(issue, rows, rank)}</p>\n'
            '        <div class="explainer-sides">\n'
            f'          <span class="explainer-side pro">{issue["explainer_left"]}</span>\n'
            f'          <span class="explainer-side con">{issue["explainer_right"]}</span>\n'
            "        </div>\n"
            "      </div>\n"
            "    </div>\n"
            f'    <img src="{issue["image"]}" alt="{issue["image_alt"]}" loading="lazy" width="1915" height="821">\n'
            "  </article>"
        )
    return (
        '<div class="explainer-grid">' + "".join(cards) + "</div>\n"
        f'  <p class="explainer-note">各画像をクリックすると拡大表示します。'
        f"件数は関連する意見投稿{len(rows)}件を主論点ごとに集計したものです。</p>"
    )


def representative_posts(issue: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """代表投稿を2件選ぶ。編集部の選定基準（article_usable かつ risk low）に従う。"""
    matches = [row for row in rows if classification(row)["main_issue"] == issue["main_issue"]]
    usable = sorted(
        (
            row
            for row in matches
            if classification(row).get("article_usable") and classification(row).get("risk") == "low"
        ),
        key=lambda row: -float(classification(row).get("confidence") or 0),
    )
    pool = usable or matches
    selected: list[dict[str, Any]] = []
    for stance in issue["sample_stances"]:
        match = next(
            (
                row
                for row in pool
                if classification(row)["stance"] == stance and row not in selected
            ),
            None,
        )
        if match is not None:
            selected.append(match)
        if len(selected) == 2:
            return selected
    for row in pool:
        if row not in selected:
            selected.append(row)
        if len(selected) == 2:
            break
    return selected


def issue_nav(counts: Counter[str]) -> str:
    """論点ナビ。件数だけが変わる。"""
    return '<nav class="quadrant-nav">' + "".join(
        f'<a href="#issue-{issue["key"]}">{issue["short"]} {counts[issue["main_issue"]]}</a>'
        for issue in ISSUE_DEFS
    ) + "</nav>"


def issue_block_head(
    issue: dict[str, Any],
    index: int,
    rows: list[dict[str, Any]],
    counts: Counter[str],
    largest: int,
) -> str:
    """論点ブロックのうち、集計と固定文だけでできる前半（代表投稿の直前まで）。

    後半（`issue-x-grid` の中身）は個々の投稿から作るので、ここには入れない。
    公開データJSON（課題57）には投稿本文もURLも入らないため、公開JSONから
    貼り直せるのはここまでになる。
    """
    total = counts[issue["main_issue"]]
    stances = stance_counts(rows, issue)
    shown = [key for key in STANCE_ORDER if stances[key]]
    labels = issue["stance_labels"]
    segments = ""
    for key in shown:
        percentage = stances[key] / total * 100
        visible = f"{percent(stances[key], total)}%" if percentage >= 10 else ""
        segments += (
            f'<div class="temp-seg {key}" style="width:{percentage:.2f}%"'
            f' aria-label="{html.escape(labels[key][1])} {stances[key]}件">{visible}</div>'
        )
    summary = " / ".join(f"{labels[key][0]} {stances[key]}" for key in shown)
    legend = "".join(
        f'<span><i style="background:{STANCE_COLORS[key]}"></i>{labels[key][1]}（{stances[key]}件）</span>'
        for key in shown
    )
    badge = " · 最大勢力" if total == largest else ""
    return (
        f'\n  <article class="issue-block" id="issue-{issue["key"]}">\n'
        '    <div class="issue-head">\n'
        f'      <span class="axis-kicker">論点{index}{badge}</span>\n'
        f'      <h3>{issue["icon"]} {issue["title"]}<span class="issue-count">{total}件</span></h3>\n'
        "    </div>\n"
        f'    <p class="issue-desc">{issue["description"]}</p>\n'
        '    <div class="temp-bar-wrap">\n'
        f'      <div class="temp-bar-label"><span>{issue["bar_title"]}</span><span>{summary}</span></div>\n'
        f'      <div class="temp-bar" role="img" aria-label="{html.escape(str(issue["bar_title"]))}。{html.escape(summary)}">{segments}</div>\n'
        f'      <div class="temp-bar-legend">{legend}</div>\n'
        "    </div>\n"
        '    <div class="issue-sides">\n'
        f'      <div class="side support"><strong>{issue["side_support_label"]}</strong>{issue["support"]}</div>\n'
        f'      <div class="side oppose"><strong>{issue["side_oppose_label"]}</strong>{issue["oppose"]}</div>\n'
        "    </div>\n"
        '    <div class="issue-x-grid">'
    )


def build_issue_blocks(rows: list[dict[str, Any]]) -> str:
    counts = issue_counts(rows)
    largest = max(counts.values())
    blocks = []
    for index, issue in enumerate(ISSUE_DEFS, start=1):
        labels = issue["stance_labels"]
        samples = "".join(
            "\n      <div class=\"issue-x-sample\">\n"
            f'        <div class="meta">{html.escape(labels[stance_of(row)][0])} / conf {float(classification(row)["confidence"]):.2f}</div>\n'
            f'        <p>{html.escape(str(classification(row).get("summary") or ""))}</p>\n'
            f'        {embed_html(str(row.get("url") or ""))}\n'
            "      </div>"
            for row in representative_posts(issue, rows)
        )
        blocks.append(
            issue_block_head(issue, index, rows, counts, largest)
            + samples
            + "</div>\n"
            "  </article>"
        )
    return (
        '<section class="panel conflict-panel" id="issue-voices-section">\n'
        f'  <div class="panel-title"><h2>{len(ISSUE_DEFS)}つの論点とXの声</h2><span>論点ごとの両側の見方と代表投稿</span></div>\n'
        f'  {issue_nav(counts)}\n'
        + "".join(blocks)
        + "\n</section>"
    )


def build_vote_issues(rows: list[dict[str, Any]]) -> str:
    """投票STEP1の選択肢。key と並び順は固定で、count だけ入れ替える。"""
    counts = issue_counts(rows)
    payload = [
        {
            "key": issue["key"],
            "title": issue["title"],
            "short": issue["short"],
            "icon": issue["icon"],
            "count": counts[issue["main_issue"]],
            "description": issue["description"],
        }
        for issue in ISSUE_DEFS
    ]
    return "var issues=" + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def build_details(rows: list[dict[str, Any]], collected: int) -> str:
    counts = issue_counts(rows)
    body = "".join(
        f'<tr><th>{html.escape(str(issue["title"]))}</th><td>{counts[issue["main_issue"]]}</td></tr>'
        for issue in ISSUE_DEFS
    )
    return (
        '<section class="panel details-panel" id="detail-data"><div class="panel-title"><h2>詳細データ</h2>'
        "<span>折りたたみ</span></div>"
        f"<details open><summary>論点別件数（関連する意見{len(rows)}件）</summary>"
        f'<div class="table-wrap"><table><tbody>{body}</tbody></table></div></details>'
        "<details><summary>分類対象と注意</summary><ul>"
        f"<li>Yahooリアルタイム検索で取得した{collected}件をHermesが再分類し、"
        f"関連性と意見性がともに認められた{len(rows)}件を表示しています。</li>"
        "<li>これは世論調査ではなく、検索語・取得時点・検索サービスの表示仕様による偏りがあります。</li>"
        "<li>論点・立場・熱量・要約はHermesによる自動分類で、誤分類を含む可能性があります。</li>"
        "</ul></details></section>"
    )


def replace_once(page: str, pattern: str, replacement: str, label: str, *, flags: int = 0) -> str:
    result, count = re.subn(pattern, lambda _: replacement, page, count=1, flags=flags)
    if count != 1:
        raise IssueCountError(f"{label}: 1箇所だけ一致する必要があります（{count}箇所）")
    return result


def _public_period(data: dict[str, Any]) -> str:
    """公開JSONの収集期間を、ページの調査条件と同じ表記へ戻す。

    `collection_period` は `THEMES.yaml` の `sample_period` を分解したものなので、
    `verify_sample_periods.expected_period()` と同じ文字列に組み直せる。
    """
    period = data["collection_period"]
    if str(period.get("status")) != "known":
        return period_label("unknown")
    start, end = str(period["start"]), str(period["end"])
    return period_label(start if start == end else f"{start}〜{end}")


def _public_rows(data: dict[str, Any]) -> tuple[int, str, list[dict[str, Any]]]:
    """公開JSONを検査し、集計表示の生成に渡せる最小行へ変換する。

    公開JSONには投稿本文・URL・confidence が入らないので、ここで作れるのは
    「論点・立場・表現強度だけを持つ行」。代表投稿とアリーナの点はこの行から
    作れないため、`apply_public_counts()` はそこに触れない。
    """
    if data.get("theme_id") != THEME:
        raise IssueCountError(f"あだ名禁止の公開JSONではありません: {data.get('theme_id')}")
    rows: list[dict[str, Any]] = []
    assigned = 0
    for item in data.get("issues", []):
        label = str(item["label"])
        count = int(item["count"])
        assigned += count
        stances = {str(value["label"]): int(value["count"]) for value in item.get("stances", [])}
        intensities = {str(value["id"]): int(value["count"]) for value in item.get("intensities", [])}
        if set(stances) - set(STANCE_KEY):
            raise IssueCountError(f"公開JSONに未知の立場があります: {label} / {sorted(set(stances) - set(STANCE_KEY))}")
        if set(intensities) - set(INTENSITY_SCALE):
            raise IssueCountError(f"公開JSONに未知の表現強度があります: {label}")
        if sum(stances.values()) != count or sum(intensities.values()) != count:
            raise IssueCountError(f"公開JSONの立場・強度の合計が論点件数と一致しません: {label}")
        if label not in ISSUE_BY_MAIN:
            # 「その他」はカードにも論点ブロックにも出さない。件数が付いたら気づけるようにする。
            if count:
                raise IssueCountError(f"ページに無い論点に件数が付きました: {label} {count}件")
            continue
        stance_values = [name for name in STANCE_KEY for _ in range(stances.get(name, 0))]
        intensity_values = [name for name in INTENSITY_SCALE for _ in range(intensities.get(name, 0))]
        rows.extend(
            {"classification": {"main_issue": label, "stance": stance, "intensity": intensity}}
            for stance, intensity in zip(stance_values, intensity_values, strict=True)
        )
    if assigned != int(data["opinion_count"]):
        raise IssueCountError("公開JSONの意見数と論点別件数の合計が一致しません")
    if not rows:
        raise IssueCountError("公開JSONにカード対象の論点がありません")
    return int(data["collected_count"]), _public_period(data), rows


def apply_public_counts(page: str, public_theme: Path = PUBLIC_THEME) -> str:
    """候補公開JSONを正典に、ページ上の集計表示を貼り直す。

    昇格が確定する前の候補ツリーで `build_public_registry.py` が作り直した
    公開JSONを読む。ここを通すことで、ページの数字の出所が公開データ契約側に
    一本化される（課題57 段階4）。代表投稿とアリーナの点は個々の投稿からしか
    作れないので、`build()` の生成結果をそのまま残す。
    """
    collected, period, rows = _public_rows(json.loads(public_theme.read_text(encoding="utf-8")))
    counts = issue_counts(rows)
    if public_theme == PUBLIC_THEME:
        # 公開JSONが非公開正典より古ければここで止める。止めないと、正しい形の
        # 古い数字が黙って貼られる（あだ名禁止の接続を一度見送った理由そのもの）。
        fresh = count_by_issue_from_public_json(THEME)
        if {key: value for key, value in counts.items()} != {
            key: value for key, value in fresh.items() if key in counts
        }:
            raise IssueCountError(f"公開JSONの論点別件数が食い違います: {dict(counts)} / {fresh}")
    largest = max(counts.values())
    page = replace_once(page, r'<p class="lead">.*?</p>', build_lead(rows), "リード文", flags=re.S)
    page = replace_once(
        page,
        r'<p style="max-width:1000px;margin:0 auto;">.*?</p>',
        build_research_conditions(collected, period),
        "調査条件",
        flags=re.S,
    )
    page = replace_once(
        page,
        r'<section class="stats insight-stats".*?</section>',
        build_stats(rows, collected),
        "注目ポイント",
        flags=re.S,
    )
    page = replace_once(
        page,
        r'<div class="explainer-grid">.*?<p class="explainer-note">.*?</p>',
        build_explainer_cards(rows),
        "論点カード",
        flags=re.S,
    )
    page = replace_once(
        page,
        r'<div class="panel-title"><h2>SNS反応マップ</h2><span>[^<]*</span></div>',
        f'<div class="panel-title"><h2>SNS反応マップ</h2><span>{len(rows)}件 | '
        "セクター=論点 / 外側ほど熱量が高い / 色=立場</span></div>",
        "マップ見出し",
    )
    vote_issues = build_vote_issues(rows)
    page = replace_once(page, r"var issues=\[[^\n]*?\];", vote_issues + ";", "投票の論点")
    page = replace_once(
        page,
        r"var issues=\[[^\n]*?\],posts=window\.NICKNAME_ARENA_DATA",
        vote_issues + ",posts=window.NICKNAME_ARENA_DATA",
        "アリーナの論点",
    )
    page = replace_once(page, r'<nav class="quadrant-nav">.*?</nav>', issue_nav(counts), "論点ナビ", flags=re.S)
    for index, issue in enumerate(ISSUE_DEFS, start=1):
        page = replace_once(
            page,
            r'\n  <article class="issue-block" id="issue-' + re.escape(str(issue["key"])) + r'">.*?<div class="issue-x-grid">',
            issue_block_head(issue, index, rows, counts, largest),
            f"論点ブロック{index}の集計",
            flags=re.S,
        )
    page = replace_once(
        page,
        r'<section class="panel details-panel" id="detail-data">.*?</section>',
        build_details(rows, collected),
        "詳細データ",
        flags=re.S,
    )
    return page


def build(
    *,
    check: bool = False,
    input_path: Path | None = None,
    html_template: Path | None = None,
    output_html: Path | None = None,
) -> tuple[list[str], bool]:
    rows, sample_file, records = load_opinions(input_path)
    collected = len(records)
    counts = issue_counts(rows)
    public_page = ROOT / "docs" / f"{THEME}-reaction-map.html"
    template = html_template or public_page
    destination = output_html or public_page
    arena_destination = (
        destination.parent / ARENA_DATA.name if output_html else ROOT / ARENA_DATA
    )

    before = template.read_text(encoding="utf-8")
    page = before
    page = replace_once(page, r'<p class="lead">.*?</p>', build_lead(rows), "リード文", flags=re.S)
    page = replace_once(
        page,
        r'<p style="max-width:1000px;margin:0 auto;">.*?</p>',
        build_research_conditions(collected, sample_period(records)),
        "調査条件",
        flags=re.S,
    )
    page = replace_once(
        page,
        r'<section class="stats insight-stats".*?</section>',
        build_stats(rows, collected),
        "注目ポイント",
        flags=re.S,
    )
    page = replace_once(
        page,
        r'<div class="explainer-grid">.*?<p class="explainer-note">.*?</p>',
        build_explainer_cards(rows),
        "論点カード",
        flags=re.S,
    )
    page = replace_once(
        page,
        r'<div class="panel-title"><h2>SNS反応マップ</h2><span>[^<]*</span></div>',
        f'<div class="panel-title"><h2>SNS反応マップ</h2><span>{len(rows)}件 | '
        "セクター=論点 / 外側ほど熱量が高い / 色=立場</span></div>",
        "マップ見出し",
    )
    # 「var issues=[...]」はページに2箇所ある（投票STEP1とアリーナ）。両方が件数を持つので
    # 両方を書き換える。片方だけを狙う正規表現にすると、貪欲さの違いで間のスクリプトを
    # 丸ごと飲み込む（実装中に投票処理ごと消えた）。終端の文字までアンカーに含める。
    vote_issues = build_vote_issues(rows)
    # どちらも1行に収まっているので、改行を跨がせない。re.S を付けて .*? を跨がせると、
    # 投票側から始まった照合がアリーナ側の終端まで伸び、間の投票処理を丸ごと飲み込む。
    page = replace_once(page, r"var issues=\[[^\n]*?\];", vote_issues + ";", "投票の論点")
    page = replace_once(
        page,
        r"var issues=\[[^\n]*?\],posts=window\.NICKNAME_ARENA_DATA",
        vote_issues + ",posts=window.NICKNAME_ARENA_DATA",
        "アリーナの論点",
    )
    page = replace_once(
        page,
        r'<section class="panel conflict-panel" id="issue-voices-section">.*?\n</section>',
        build_issue_blocks(rows),
        "論点ブロック",
        flags=re.S,
    )
    page = replace_once(
        page,
        r'<section class="panel details-panel" id="detail-data">.*?</section>',
        build_details(rows, collected),
        "詳細データ",
        flags=re.S,
    )

    arena_before = arena_destination.read_text(encoding="utf-8") if arena_destination.is_file() else ""
    arena_after = build_arena_data(rows)
    changed = page != before or arena_after != arena_before
    if not check:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(page, encoding="utf-8")
        arena_destination.parent.mkdir(parents=True, exist_ok=True)
        arena_destination.write_text(arena_after, encoding="utf-8")
    detail = " / ".join(f'{issue["title"]}={counts[issue["main_issue"]]}' for issue in ISSUE_DEFS)
    stances = stance_counts(rows)
    return (
        [
            f"出所: {sample_file}（収集{collected}件 / 意見{len(rows)}件）",
            f"論点: {detail}",
            "立場: " + " / ".join(f"{STANCE_DISPLAY[key]}={stances[key]}" for key in STANCE_ORDER),
        ],
        changed,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--html-template", type=Path)
    parser.add_argument("--output-html", type=Path)
    parser.add_argument(
        "--public-counts-only",
        action="store_true",
        help="候補公開JSON（data/public/themes/）から集計表示だけを貼り直す",
    )
    args = parser.parse_args()
    try:
        if args.public_counts_only:
            if args.check or args.input or args.html_template:
                parser.error("--public-counts-only は --output-html だけを指定してください")
            destination = args.output_html or ROOT / "docs" / f"{THEME}-reaction-map.html"
            destination.write_text(
                apply_public_counts(destination.read_text(encoding="utf-8")), encoding="utf-8"
            )
            print(f"OK: 公開JSONから集計表示を更新しました: {destination}")
            return 0
        if args.check and any((args.input, args.html_template, args.output_html)):
            parser.error("--checkは公開ページと正典の一致確認専用です")
        if any((args.input, args.html_template, args.output_html)) and not all(
            (args.input, args.html_template, args.output_html)
        ):
            parser.error("候補生成では--input/--html-template/--output-htmlをすべて指定してください")
        lines, changed = build(
            check=args.check,
            input_path=args.input,
            html_template=args.html_template,
            output_html=args.output_html,
        )
        print("\n".join(lines))
        if args.check and changed:
            print("NG: HTMLに差分があります", file=sys.stderr)
            return 1
        print("OK: 差分なし" if not changed else "UPDATE: HTMLを更新しました")
        return 0
    except (IssueCountError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
