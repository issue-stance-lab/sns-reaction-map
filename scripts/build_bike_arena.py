#!/usr/bin/env python3
"""自転車青切符ページの、正典から導ける部分をまとめて作り直す。

    python3 scripts/build_bike_arena.py
    python3 scripts/build_bike_arena.py --check
    python3 scripts/build_bike_arena.py --input ... --html-template ... --output-html ...

2026-08-17 まで、ここで生成する場所はすべて手書きだった。更新のたびに十数か所を
手で書き換えていて、書き換え漏れがそのまま公開されうる状態だった。

生成するのは次の5か所だけ。ページの文章そのものは生成しない。

    1. アリーナの点（SM_RAW）
    2. アリーナ見出しの「N件 | セクター=論点 …」
    3. 注目ポイント4枚（insight-stats）
    4. 論点ごとの帯（temp-bar）と内訳（issue-sides）を含む論点ブロック5本
    5. 「本当の対立点」段落の論点別件数

**ここが書かない場所**（1つの文の書き手は1つ）:

    論点カード・論点ナビ・議論の中心・アリーナのセクター配列・リード文
        → scripts/sync_issue_counts.py
    冒頭3セクション・全件表・区分の根拠
        → scripts/build_bike_process_sections.py
    調査条件ブロック・信頼性メタ
        → scripts/seo/apply_theme_trust.py
    世論の潮目
        → scripts/refresh_adapters/bike.py（更新回どうしの比較）
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
    from .issue_card_counts import IssueCountError
    from .sync_portal_stats import ROOT, THEMES_YAML, parse_themes_yaml
    from .x_embed import embed_html
except ImportError:
    from issue_card_counts import IssueCountError  # type: ignore[no-redef]
    from sync_portal_stats import ROOT, THEMES_YAML, parse_themes_yaml  # type: ignore[no-redef]
    from x_embed import embed_html  # type: ignore[no-redef]

THEME = "bike-blue-ticket"

# ページ内 const ISSUES=[…] と同じ並び。ここがずれるとセクターと点が食い違う。
ISSUE_ORDER = (
    "取締り強化賛成",
    "インフラ整備優先",
    "車道走行への不安",
    "免許制要求",
    "ルール曖昧・不信",
    "その他",
)
# 「その他」を除いた5論点。ページが「5つの論点に分類できたN件」と書く母数。
MAIN_ISSUES = ISSUE_ORDER[:-1]

SUPPORT = "賛成（取締り強化支持）"
NEUTRAL = "どちらでもない"
OPPOSE = "反対（インフラ・制度優先）"
STANCE_ORDER = (SUPPORT, NEUTRAL, OPPOSE)
STANCE_X = {SUPPORT: 2.0, NEUTRAL: 0.0, OPPOSE: -2.0}
INTENSITY_E = {"low": 0.5, "medium": 1.2, "high": 2.0}

# 注目ポイントの3枚目「最も話された論点」に出す短いラベルと、その説明文。
# 論点そのものの説明なので、件数が変わっても文章は変わらない。
SHORT_LABEL = {
    "取締り強化賛成": "取締り強化",
    "インフラ整備優先": "インフラ整備",
    "車道走行への不安": "車道走行",
    "免許制要求": "免許・講習",
    "ルール曖昧・不信": "ルール曖昧",
}
TOP_ISSUE_NOTE = {
    "取締り強化賛成": "危険運転やマナー違反を止めたいという声",
    "インフラ整備優先": "走れる道を先に用意すべきだという声",
    "車道走行への不安": "車道を走れというルールへの不安の声",
    "免許制要求": "罰則より先に学ぶ機会を求める声",
    "ルール曖昧・不信": "違反の基準と運用への不信の声",
}

# 論点ブロック5本。件数以外（見出し・説明・代表投稿）は編集部が決めた内容で、
# データが増えても変わらない。件数と帯の幅だけを毎回数え直す。
#
# sides は3つのスタンスをちょうど1回ずつ覆うこと（下の _check_definitions が検査する）。
# 覆えていないスタンスがあると、その件数がページのどこにも出ないまま消える。
BLOCKS: tuple[dict[str, Any], ...] = (
    {
        "issue": "取締り強化賛成",
        "anchor": "issue-torishimari",
        "heading": "取締り強化賛成・マナー違反を止めよ",
        "temp_label": "取締り強化への姿勢",
        "temp_names": ("取締り支持", "中立", "反対"),
        "legend": ("取締り強化を支持", "中立", "慎重・反対"),
        "desc": "信号無視・ながらスマホ・歩道の無謀走行など、自転車の危険行為を止めるために取り締まりは当然という立場。「歩行者が怖い思いをしている」という視点から、青切符による制裁強化を支持します。",
        "sides": (
            ("neg", "取締り強化支持", (SUPPORT,), "マナーの悪い自転車をこのまま放置するのはおかしい。事故が起きてからでは遅い。"),
            ("pos", "中立・反対", (NEUTRAL, OPPOSE), "取締りの話題に触れつつ、賛否を示さない投稿と、進め方に異議を示す投稿。"),
        ),
        "samples": (
            ("取締り支持 / 感情やや高め", "無法状態の自転車に怒り、青切符でも甘いとして厳格な対応を要求", "https://x.com/shocker108/status/2061387437340045705"),
            ("取締り支持 / 安全優先", "自転車の一時不停止に怒り、厳格な取り締まりを強く求める", "https://x.com/bjayway/status/2070305605852836233"),
        ),
    },
    {
        "issue": "インフラ整備優先",
        "anchor": "issue-infra",
        "heading": "インフラ整備が先・専用レーンなしに取締りは不公平",
        "temp_label": "インフラ整備への立場",
        "temp_names": ("取締り寄り", "中立", "インフラ優先"),
        "legend": ("取締り支持（条件付き含む）", "中立", "インフラ整備が先"),
        "desc": "「安全に走れる自転車専用レーンがないのに、車道を走れというのは無理だ」という立場。インフラ整備なしの罰則強化は自転車利用者への一方的な押しつけで、本末転倒という批判です。",
        "sides": (
            ("pos", "インフラ整備優先派", (OPPOSE,), "自転車レーンが整備されてから取り締まるべき。先にルールありきでは混乱するだけ。"),
            ("neu", "中立", (NEUTRAL,), "インフラ整備と取り締まりを並行して進める現実的な視点。"),
            ("neg", "整備を待たず取締りを", (SUPPORT,), "整備の遅れは認めつつ、危険行為の取り締まりは先に始めるべきだという立場。"),
        ),
        "samples": (
            ("インフラ優先 / 感情高め", "インフラ整備不足を批判し、青切符制度に強く反対する声", "https://x.com/15jacnamagiga/status/2070261164618158443"),
            ("条件付き支持 / 冷静", "インフラ整備優先を主張しつつ青切符制度を条件付きで支持", "https://x.com/suzuking408/status/2069735857695891855"),
        ),
    },
    {
        "issue": "車道走行への不安",
        "anchor": "issue-sharido",
        "heading": "車道走行への不安・「車道を走れ」は危険",
        "temp_label": "車道走行ルールへの評価",
        "temp_names": ("歩道批判", "中立", "車道不安派"),
        "legend": ("ルール強化支持（歩行者目線）", "中立", "車道走行が怖い（自転車目線）"),
        "desc": "青切符と合わせて「自転車は原則車道」というルールが強調されることへの不安。「子どもを車道に出せるか」「路駐があって走れない」といった現実的な危険を訴える声があります。一方で、歩道を飛ばす自転車が危険だという歩行者目線も存在します。",
        "sides": (
            ("pos", "車道走行が怖い", (OPPOSE,), "車道はトラックや路駐車があって危険。子どもや高齢者には無理なルールだ。"),
            ("neu", "中立", (NEUTRAL,), "車道・歩道どちらにも問題があるという複合的な視点。"),
            ("neg", "歩道走行こそ危険", (SUPPORT,), "歩道を飛ばす自転車が怖いという歩行者目線から、車道原則とその徹底を支持する立場。"),
        ),
        "samples": (
            ("車道不安 / 感情高め", "青切符への疑念と子どもへの車道走行要求に強く反対", "https://x.com/isaiah8_1/status/2067988251760345275"),
            ("歩行者安全重視 / 感情高め", "路駐問題の解消と自転車の安全確保を要望する", "https://x.com/Mid_observatory/status/2021148538013671884"),
        ),
    },
    {
        "issue": "免許制要求",
        "anchor": "issue-mensyo",
        "heading": "免許制が必要・青切符だけでは不十分",
        "temp_label": "免許制度要求への立場",
        "temp_names": ("免許制支持", "中立", "慎重"),
        "legend": ("免許制・講習義務化を支持", "中立", "慎重・反対"),
        "desc": "「青切符だけでは甘い」「自転車にも免許制度か事前講習を義務付けるべきだ」という主張です。標識を理解していない自転車利用者が多いため、罰則より先に教育が必要という考え方です。",
        "sides": (
            ("neg", "免許・講習義務化派", (SUPPORT,), "自転車にもルールを学ぶ機会が必要。原付のように免許制か事前講習で知識を担保すべき。"),
            ("pos", "慎重・反対派", (OPPOSE,), "免許制は自転車利用の障壁になる。費用や手続き負担が増えて利便性が下がる。"),
            ("neu", "中立", (NEUTRAL,), "条件次第では免許制や講習義務化もあり得るという立場。"),
        ),
        "samples": (
            ("免許制支持 / 感情高め", "自転車への免許制や講習制度の導入を強く主張", "https://x.com/r70OylZbSZeiIIz/status/2070149487566418240"),
            ("免許制支持 / 安全優先", "自転車に免許制導入を提唱し安全優先の立場から現行ルールに疑問", "https://x.com/yamazakibusu/status/2070074656128917921"),
        ),
    },
    {
        "issue": "ルール曖昧・不信",
        "anchor": "issue-ambiguity",
        "heading": "ルールが曖昧・警察への不信感",
        "temp_label": "ルール整備への評価",
        "temp_names": ("取締り支持", "中立", "慎重・反対"),
        "legend": ("ルール整備後の取締り支持", "中立", "現行のルールへの疑念"),
        "desc": "「何が違反になるのか現場でわからない」「警察が恣意的に取り締まるのではないか」という不信感が中心。「113種類もの違反基準は覚えられない」「点数稼ぎ目的ではないか」という批判です。",
        "sides": (
            ("pos", "ルール不信派", (OPPOSE,), "違反の基準が複雑すぎる。警察の裁量が広く、正直者がバカを見る取り締まりになりかねない。"),
            ("neu", "中立", (NEUTRAL,), "ルールの周知や整備状況を見ながら判断したい。"),
            ("neg", "周知を整えたうえで取締りを", (SUPPORT,), "基準の分かりにくさは認めつつ、周知を整えたうえで取り締まること自体は支持する立場。"),
        ),
        "samples": (
            ("ルール不信 / 感情高め", "青切符に強く反対、監視社会的な取り締まりへの怒り", "https://x.com/kress813/status/2032229649317814760"),
            ("基準複雑さへの批判", "113種は多すぎ、簡略化と周知整備の後に実施すべきと主張", "https://x.com/Clifrennie/status/2068026232860537188"),
        ),
    },
)

SEGMENT_CLASS = {SUPPORT: "neg", NEUTRAL: "neu", OPPOSE: "pos"}
# 帯の中に「N%」の文字を出す下限。狭い区画に文字を入れるとはみ出す。
SEGMENT_LABEL_MIN = 10.0


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def _check_definitions() -> None:
    """BLOCKS の定義そのものを検査する。データではなく書き手の取りこぼしを止める。"""
    anchors = [block["anchor"] for block in BLOCKS]
    if len(set(anchors)) != len(anchors):
        raise IssueCountError(f"論点ブロックのアンカーが重複しています: {anchors}")
    if tuple(block["issue"] for block in BLOCKS) != MAIN_ISSUES:
        raise IssueCountError("BLOCKS の並びが MAIN_ISSUES と一致しません")
    for block in BLOCKS:
        covered = [stance for _cls, _label, stances, _desc in block["sides"] for stance in stances]
        if sorted(covered) != sorted(STANCE_ORDER):
            raise IssueCountError(
                f"{block['issue']}: sides が3つのスタンスをちょうど1回ずつ覆っていません: {covered}"
            )


def classification(record: dict[str, Any]) -> dict[str, Any]:
    nested = record.get("classification")
    if not isinstance(nested, dict):
        raise IssueCountError("classification を持たないレコードがあります")
    return nested


def is_opinion(record: dict[str, Any]) -> Any:
    """このテーマの is_opinion はレコードのトップレベルにある（旧2D分類の名残）。"""
    return classification(record).get("is_opinion", record.get("is_opinion"))


def load_opinions(input_path: Path | None = None) -> tuple[list[dict[str, Any]], str, int]:
    themes = parse_themes_yaml(THEMES_YAML)
    sample_file = str(themes[THEME].get("sample_file") or "")
    if not sample_file or "synthetic" in sample_file:
        raise IssueCountError(f"{THEME}: 正典 sample_file が不正です: {sample_file}")
    source = input_path or ROOT / sample_file
    records = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise IssueCountError(f"{THEME}: 正典が空、またはJSON配列ではありません")

    missing = [
        str(record.get("tweet_id"))
        for record in records
        if not isinstance(record, dict) or not isinstance(is_opinion(record), bool)
    ]
    if missing:
        # 2026-08-17 の更新で実際に起きた。is_opinion が無いレコードは論点カードの
        # 母数（issue_counts.basis: opinion）から丸ごと消えるが、ページの他の場所は
        # 全件で数えるため、1つのページに2つの母数が並ぶ。
        raise IssueCountError(
            f"is_opinion が無いレコードが{len(missing)}件あります。"
            f"分類器（scripts/classify_bike_arena_hermes.py）が付けます: {missing[:5]}"
        )

    opinions: list[dict[str, Any]] = []
    for number, record in enumerate(records, start=1):
        c = classification(record)
        if not is_opinion(record):
            continue
        if c.get("main_issue") not in ISSUE_ORDER:
            raise IssueCountError(f"{number}件目: 未知の main_issue: {c.get('main_issue')}")
        if c.get("stance") not in STANCE_X:
            raise IssueCountError(f"{number}件目: 未知の stance: {c.get('stance')}")
        if c.get("intensity") not in INTENSITY_E:
            raise IssueCountError(f"{number}件目: 未知の intensity: {c.get('intensity')}")
        opinions.append(record)
    if not opinions:
        raise IssueCountError("意見と判定されたレコードがありません")
    return opinions, str(source), len(records)


def build_sm_raw(rows: list[dict[str, Any]]) -> str:
    index = {issue: i for i, issue in enumerate(ISSUE_ORDER)}
    points = []
    for row in rows:
        c = classification(row)
        points.append(
            '  {{x:{x},y:0.0,e:{e},c:{c:.2f},s:"{s}",u:"{u}",i:{i}}}'.format(
                x=STANCE_X[str(c["stance"])],
                e=INTENSITY_E[str(c["intensity"])],
                c=float(c.get("confidence") or 0.7),
                s=str(c.get("summary") or "").replace("\\", "\\\\").replace('"', '\\"'),
                u=str(row.get("url") or "").replace("\\", "\\\\").replace('"', '\\"'),
                i=index[str(c["main_issue"])],
            )
        )
    return "const SM_RAW = [\n" + ",\n".join(points) + "\n];"


def cross_tab(rows: list[dict[str, Any]]) -> dict[str, Counter[str]]:
    """論点 × 立場のクロス集計。帯と内訳はここからしか作らない。"""
    table: dict[str, Counter[str]] = {issue: Counter() for issue in ISSUE_ORDER}
    for row in rows:
        c = classification(row)
        table[str(c["main_issue"])][str(c["stance"])] += 1
    return table


def build_insight_stats(rows: list[dict[str, Any]], table: dict[str, Counter[str]]) -> str:
    issue_totals = {issue: sum(table[issue].values()) for issue in MAIN_ISSUES}
    five = sum(issue_totals.values())
    other = len(rows) - five
    if five <= 0:
        raise IssueCountError("5論点に分類された意見が0件です")
    ranked = sorted(MAIN_ISSUES, key=lambda issue: (-issue_totals[issue], MAIN_ISSUES.index(issue)))
    top = ranked[0]
    largest = issue_totals[top]
    menkyo = issue_totals["免許制要求"]

    items = "\n".join(
        f'          <li><span>{esc(issue)}</span><b>{issue_totals[issue]}件</b>'
        f'<span class="insight-issue-bar"><i style="width:{issue_totals[issue] / largest * 100:.0f}%"></i></span></li>'
        for issue in ranked
    )
    return f"""<section class="stats insight-stats" aria-label="このテーマの4つの注目ポイント">
      <article class="stat insight-stat">
        <div class="insight-head"><span class="insight-icon" aria-hidden="true">🗣️</span><span class="insight-label">分析対象の意見</span></div>
        <strong class="insight-value">{len(rows)}<small>件</small></strong>
        <p class="insight-note">うち5つの論点に分類できた{five}件（残る{other}件は「その他・分類保留」）</p>
        <div class="insight-meter" aria-hidden="true"><i style="width:100%"></i></div>
      </article>
      <article class="stat insight-stat" data-tone="debate">
        <div class="insight-head"><span class="insight-icon" aria-hidden="true">⚔️</span><span class="insight-label">5論点の内訳</span></div>
        <ul class="insight-issue-list">
{items}
        </ul>
      </article>
      <article class="stat insight-stat" data-tone="topic">
        <div class="insight-head"><span class="insight-icon" aria-hidden="true">🔥</span><span class="insight-label">最も話された論点</span></div>
        <strong class="insight-value">{esc(SHORT_LABEL[top])} {largest}<small>件</small></strong>
        <p class="insight-note">{esc(TOP_ISSUE_NOTE[top])}。5論点{five}件の{largest / five * 100:.0f}%</p>
        <div class="insight-meter" aria-hidden="true"><i style="width:{largest / five * 100:.0f}%"></i></div>
      </article>
      <article class="stat insight-stat" data-tone="option">
        <div class="insight-head"><span class="insight-icon" aria-hidden="true">💡</span><span class="insight-label">第三の選択</span></div>
        <strong class="insight-value">免許・講習 {menkyo}<small>件</small></strong>
        <p class="insight-note">罰則だけでなく、先にルールを学ぶ機会を求める</p>
        <div class="insight-meter" aria-hidden="true"><i style="width:{menkyo / five * 100:.0f}%"></i></div>
      </article>
    </section>"""


def build_issue_block(block: dict[str, Any], number: int, counts: Counter[str], is_largest: bool) -> str:
    total = sum(counts.values())
    if total <= 0:
        raise IssueCountError(f"{block['issue']}: この論点に分類された意見が0件です")

    segments = "".join(
        '<div class="temp-seg {cls}" style="width:{width:.1f}%">{label}</div>'.format(
            cls=SEGMENT_CLASS[stance],
            width=counts[stance] / total * 100,
            label=(
                f"{counts[stance] / total * 100:.0f}%"
                if counts[stance] / total * 100 >= SEGMENT_LABEL_MIN
                else ""
            ),
        )
        for stance in STANCE_ORDER
    )
    summary = " / ".join(
        f"{name} {counts[stance]}"
        for name, stance in zip(block["temp_names"], STANCE_ORDER)
    )
    legend = "".join(
        f'<span><i style="background:{color}"></i>{esc(text)}</span>'
        for text, color in zip(block["legend"], ("#e04949", "#94a3b8", "#4b9cf4"))
    )
    sides = "".join(
        '<div class="side {cls}"><strong>{label}（{n}件）</strong>{desc}</div>'.format(
            cls=cls, label=esc(label), n=sum(counts[s] for s in stances), desc=esc(desc)
        )
        for cls, label, stances, desc in block["sides"]
        if sum(counts[s] for s in stances)
    )
    samples = "\n".join(
        f'<div class="sample-card"><div class="meta">{esc(meta)}</div><p>{esc(text)}</p>{embed_html(url)}</div>'
        for meta, text, url in block["samples"]
    )
    kicker = f"論点{number}・最大勢力" if is_largest else f"論点{number}"
    return f"""<article class="issue-block" id="{block['anchor']}">
<div class="issue-head"><span class="axis-kicker">{kicker}</span>
<h3>{esc(block['heading'])}</h3>
<div class="temp-bar-wrap">
<div class="temp-bar-label"><span>{esc(block['temp_label'])}</span><span>{summary}</span></div>
<div class="temp-bar">{segments}</div>
<div class="temp-bar-legend">{legend}</div>
</div>
<p class="issue-desc">{esc(block['desc'])}</p>
<div class="issue-sides">{sides}</div>
</div>
<div class="sample-grid">
{samples}
</div>
</article>"""


def build_conflict_paragraph(table: dict[str, Counter[str]]) -> str:
    totals = {issue: sum(table[issue].values()) for issue in MAIN_ISSUES}
    return (
        '<article class="argument-point"><h3>本当の対立点</h3><p>'
        "対立しているのは取締りの有無より、安全のための責任と実施の順序です。"
        "警告・反則金という個人への働きかけを先に実効化し、道路と教育は並行して改善するのか。"
        "それとも、連続した車道上の通行空間、歩道通行の例外を現場で判断できる周知、"
        "年齢を問わない学習機会を先に保障するのか。分類データでは、"
        f"インフラ整備優先{totals['インフラ整備優先']}件と車道走行への不安{totals['車道走行への不安']}件に加え、"
        f"免許制要求{totals['免許制要求']}件とルール曖昧・不信{totals['ルール曖昧・不信']}件があり、"
        "単純な取締り反対より「現在の進め方では安全の条件が足りない」という不満が対立の中心だと読めます。"
        "</p></article>"
    )


# 投票の選択肢キー → 論点名。1文字違いのものがあるので明示する。
VOTE_ALIAS = {
    "取締り強化": "取締り強化賛成",
    "インフラ整備が先": "インフラ整備優先",
    "車道走行への不安": "車道走行への不安",
    "免許制が必要": "免許制要求",
    "ルールが曖昧": "ルール曖昧・不信",
}
VOTE_DESC = re.compile(r"(\{k:'(?P<key>[^']+)',\s*icon:'[^']*',\s*desc:'[^']*?)（\d[\d,]*件）(')")


def sync_vote_counts(page: str, totals: dict[str, int]) -> str:
    """投票の選択肢の説明文にある「（N件）」を論点別件数に合わせる。

    選択肢そのもの（k）は触らない。選択肢の数が変わると choiceIdx の意味がずれ、
    Edge Function の再デプロイと既存票の破棄が要る。ここで変えるのは説明文の中の件数だけ。
    """

    def replace(match: re.Match[str]) -> str:
        key = match.group("key")
        if key not in VOTE_ALIAS:
            raise IssueCountError(f"投票の選択肢が論点にありません: {key}")
        return f"{match.group(1)}（{totals[VOTE_ALIAS[key]]}件）{match.group(3)}"

    result, replaced = VOTE_DESC.subn(replace, page)
    if replaced != len(VOTE_ALIAS):
        raise IssueCountError(f"投票の選択肢の件数が{len(VOTE_ALIAS)}個必要です（{replaced}個）")
    return result


def replace_once(page: str, pattern: str, replacement: str, label: str, *, flags: int = 0) -> str:
    result, count = re.subn(pattern, lambda _match: replacement, page, count=1, flags=flags)
    if count != 1:
        raise IssueCountError(f"{label}: 1箇所だけ一致する必要があります（{count}箇所）")
    return result


def build(
    *,
    check: bool = False,
    input_path: Path | None = None,
    html_template: Path | None = None,
    output_html: Path | None = None,
) -> tuple[list[str], bool]:
    _check_definitions()
    rows, sample_file, collected = load_opinions(input_path)
    table = cross_tab(rows)
    totals = {issue: sum(table[issue].values()) for issue in MAIN_ISSUES}
    largest = max(totals.values())

    public_path = ROOT / "docs" / f"{THEME}-reaction-map.html"
    template = html_template or public_path
    destination = output_html or public_path
    before = template.read_text(encoding="utf-8")
    page = before

    known = {str(record.get("tweet_id")) for record in rows}
    for block in BLOCKS:
        for _meta, _text, url in block["samples"]:
            tweet_id = url.rsplit("/", 1)[-1]
            if tweet_id not in known:
                raise IssueCountError(
                    f"{block['issue']}: 代表投稿が正典の意見にありません（削除・分類変更）: {url}"
                )

    if '<script id="bike-arena-points">' not in page:
        # 要旨には「7159件」のような一次情報の数字が入る。数字の出所検査から外すために
        # この配列だけを id 付きの <script> に入れてある（configs の exclude_selectors）。
        raise IssueCountError('SM_RAW を囲む <script id="bike-arena-points"> がありません')
    page = replace_once(page, r"const SM_RAW = \[.*?\n\];", build_sm_raw(rows), "SM_RAW", flags=re.S)
    page = replace_once(
        page,
        r'<div class="panel-title"><h2>SNS反応マップ</h2><span>[^<]*</span></div>',
        f'<div class="panel-title"><h2>SNS反応マップ</h2><span>{len(rows)}件 | セクター=論点 / 中心に近いほど冷静 / 色=賛否 | ホバーで詳細</span></div>',
        "アリーナ見出し",
    )
    page = replace_once(
        page,
        r'<section class="stats insight-stats".*?</section>',
        build_insight_stats(rows, table),
        "注目ポイント",
        flags=re.S,
    )
    for number, block in enumerate(BLOCKS, start=1):
        counts = table[str(block["issue"])]
        page = replace_once(
            page,
            rf'<article class="issue-block" id="{block["anchor"]}">.*?\n</article>',
            build_issue_block(block, number, counts, sum(counts.values()) == largest),
            f'論点ブロック {block["anchor"]}',
            flags=re.S,
        )
    page = sync_vote_counts(page, totals)
    page = replace_once(
        page,
        r'<article class="argument-point"><h3>本当の対立点</h3>.*?</article>',
        build_conflict_paragraph(table),
        "本当の対立点",
        flags=re.S,
    )

    changed = page != before
    if not check:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(page, encoding="utf-8")
    detail = " / ".join(f"{issue}={totals[issue]}" for issue in MAIN_ISSUES)
    stances = Counter(str(classification(row)["stance"]) for row in rows)
    return (
        [
            f"出所: {sample_file}（収集{collected}件 / 意見{len(rows)}件）",
            f"論点: {detail} / その他={sum(table['その他'].values())}",
            "立場: " + " / ".join(f"{stance}={stances[stance]}" for stance in STANCE_ORDER),
        ],
        changed,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--html-template", type=Path)
    parser.add_argument("--output-html", type=Path)
    args = parser.parse_args()
    try:
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
